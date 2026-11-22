"""Offline retrieval contracts and controlled vectors, not semantic embedding scores."""

import copy
import io
import json
from pathlib import Path
import tempfile
from unittest import TestCase, mock

from scripts import retrieval as retrieval
from scripts import retrieval_probe as probe


class RetrievalTests(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.documents, cls.raw, cls.linked, cls.plan = retrieval.load_snapshot(8)

    def cache(self):
        items = retrieval.embedding_items(self.documents, self.plan["queries"])
        return {"complete": True, "model": "test/controlled-vectors", "dimensions": 2,
                "fingerprint": retrieval.fingerprint(self.documents, self.plan["queries"], "test/controlled-vectors", 2),
                "vectors": {key: [1.0, 0.0] for key, _ in items}, "trace": []}

    def test_snapshot_is_deterministic_and_larger_than_context(self):
        documents, raw, linked, plan = retrieval.load_snapshot(8)
        self.assertEqual(documents, self.documents)
        self.assertEqual(raw, self.raw)
        self.assertEqual(linked, self.linked)
        self.assertGreater(retrieval.context_size(list(documents.values())), plan["contextBytes"] * 3)

    def test_explicit_reply_and_knowledge_links_are_distinct(self):
        self.assertEqual(self.documents["retry-safety/no"]["replyTo"], "retry-safety/proposal")
        self.assertIn("retry-safety/incident", self.documents["retry-safety/handbook"]["derivedFrom"])
        self.assertIn("retry-safety/proposal", self.raw["retry-safety/no"])
        self.assertNotIn("retry-safety/manual", self.raw["retry-safety/incident"])
        self.assertIn("retry-safety/manual", self.linked["retry-safety/incident"])

    def test_all_twelve_arms_respect_identical_serialized_budget(self):
        report = retrieval.benchmark(self.documents, self.raw, self.linked, self.plan, self.cache(), budget=512)
        self.assertEqual(len(report["summary"]), 12)
        self.assertEqual(len(report["rows"]), 7 * 12)
        for row in report["rows"]:
            self.assertEqual(row["selected_bytes"], retrieval.context_size(row["context"]))
            self.assertLessEqual(row["selected_bytes"], 512)
            self.assertEqual(row["semantic_quality"], "not-evaluated")

    def test_unlinked_baseline_fills_budget_beyond_initial_seeds(self):
        report = retrieval.benchmark(self.documents, self.raw, self.linked, self.plan, self.cache())
        rows = {(row["query"], row["method"]): row for row in report["rows"]}
        for query in self.plan["queries"]:
            for method in ("lexical", "vector", "hybrid"):
                full = {doc["id"] for doc in rows[query, method]["context"]}
                seeds = {doc["id"] for doc in rows[query, method + "+seeds-only"]["context"]}
                self.assertTrue(seeds <= full)

    def test_oracle_labels_do_not_change_selected_context_or_cache_identity(self):
        plan = copy.deepcopy(self.plan)
        first = retrieval.benchmark(self.documents, self.raw, self.linked, plan, self.cache())
        for query in plan["queries"].values():
            query["requiredSources"] = ["code-review/policy"]
            query["negative"] = False
        second = retrieval.benchmark(self.documents, self.raw, self.linked, plan, self.cache())
        self.assertEqual([row["context"] for row in first["rows"]], [row["context"] for row in second["rows"]])

    def test_embedding_inputs_exclude_expected_ids_and_metadata(self):
        plan = copy.deepcopy(self.plan)
        for query in plan["queries"].values():
            query["requiredSources"] = ["ORACLE_CANARY"]
        inputs = [text for _, text in retrieval.embedding_items(self.documents, plan["queries"])]
        self.assertNotIn("ORACLE_CANARY", json.dumps(inputs))
        self.assertNotIn("fixture://", json.dumps(inputs))

    def test_negative_probe_does_not_receive_a_vacuous_perfect_score(self):
        report = retrieval.benchmark(self.documents, self.raw, self.linked, self.plan)
        negative = [row for row in report["rows"] if row["negative_probe"]]
        self.assertEqual(len(negative), 4)
        self.assertTrue(all(row["oracle_complete"] is None and row["oracle_recall"] is None for row in negative))

    def test_stale_text_and_anchor_invalidate_cache(self):
        for field in ("text", "anchor"):
            documents = copy.deepcopy(self.documents)
            documents["retry-safety/no"][field] = "changed"
            with self.subTest(field=field), self.assertRaisesRegex(ValueError, "stale"):
                retrieval.validate_cache(self.cache(), documents, self.plan["queries"])

    def test_relationship_metadata_is_preserved_but_does_not_rebuy_text_vectors(self):
        documents = copy.deepcopy(self.documents)
        documents["retry-safety/no"]["replyTo"] = "retry-safety/manual"
        cache = self.cache()
        retrieval.validate_cache(cache, documents, self.plan["queries"])
        before = retrieval.benchmark(self.documents, self.raw, self.linked, self.plan, cache)
        after = retrieval.benchmark(documents, self.raw, self.linked, self.plan, cache)
        self.assertNotEqual(before["context_fingerprint"], after["context_fingerprint"])

    def test_cache_requires_all_identities_and_complete_status(self):
        cache = self.cache()
        cache["vectors"].pop(next(iter(cache["vectors"])))
        with self.assertRaisesRegex(ValueError, "identities"):
            retrieval.validate_cache(cache, self.documents, self.plan["queries"])
        cache = self.cache()
        cache["complete"] = False
        with self.assertRaisesRegex(ValueError, "incomplete"):
            retrieval.validate_cache(cache, self.documents, self.plan["queries"])

    def test_invalid_vectors_are_rejected(self):
        for vector in ([0, 0], [float("nan"), 1], [True, 1], [1], [float("inf"), 0]):
            with self.subTest(vector=vector), self.assertRaises(ValueError):
                retrieval.unit(vector, 2)

    def test_cosine_and_rank_fusion_use_rankings_not_oracle(self):
        documents = {"a": {"text": "a"}, "b": {"text": "b"}}
        vectors = {"d:a": [1, 0], "d:b": [0, 1], "q:q": [0, 1]}
        self.assertEqual(retrieval.vector_rank(documents, vectors, "q"), ["b", "a"])
        self.assertEqual(retrieval.fuse(["a", "b"], ["b", "a"]), ["a", "b"])

    def test_link_expansion_recovers_one_word_correction(self):
        ranking = ["retry-safety/manual"]
        raw, _ = retrieval.neighborhood(self.documents, ranking, self.raw, budget=2560, seeds=1, hops=3)
        linked, _ = retrieval.neighborhood(self.documents, ranking, self.linked, budget=2560, seeds=1, hops=3)
        self.assertNotIn("retry-safety/no", {doc["id"] for doc in raw})
        self.assertIn("retry-safety/no", {doc["id"] for doc in linked})

    def test_budget_skips_whole_sources_and_exposes_missing_known_links(self):
        plan = copy.deepcopy(self.plan)
        plan["queries"] = {"tiny": {"text": "manual replay", "requiredSources": ["retry-safety/manual"], "negative": False}}
        report = retrieval.benchmark(self.documents, self.raw, self.linked, plan, budget=128)
        self.assertTrue(all(row["oracle_missing"] == ["retry-safety/manual"] for row in report["rows"]))
        self.assertTrue(any(row["skipped_for_budget"] for row in report["rows"]))

    def test_empty_known_boundary_does_not_prove_coverage(self):
        documents = {
            "a": {"id": "a", "text": "apples", "anchor": "fixture://a", "kind": "document"},
            "b": {"id": "b", "text": "unlinked exception", "anchor": "fixture://b", "kind": "document"},
        }
        graph = {key: set() for key in documents}
        plan = dict(self.plan, queries={"q": {"text": "apples", "requiredSources": ["b"], "negative": False}})
        report = retrieval.benchmark(documents, graph, graph, plan)
        self.assertTrue(all(not row["known_link_boundary"] and not row["oracle_complete"] for row in report["rows"]))

    def test_default_cli_is_offline_even_with_a_token(self):
        with tempfile.TemporaryDirectory() as directory, \
                mock.patch.dict(probe.os.environ, {"OPENROUTER_API_KEY": "SECRET_CANARY"}), \
                mock.patch.object(probe, "embed") as embed, \
                mock.patch("sys.stdout", new_callable=io.StringIO):
            output = Path(directory) / "report.json"
            self.assertEqual(probe.main(["--noise", "8", "--output", str(output)]), 0)
            embed.assert_not_called()
            self.assertEqual(len(json.loads(output.read_text())["summary"]), 4)
            self.assertNotIn("SECRET_CANARY", output.read_text())


class EmbeddingClientTests(TestCase):
    def setUp(self):
        self.documents = {"s/a": {"id": "s/a", "text": "One synthetic observation.", "anchor": "fixture://a", "kind": "document"}}
        self.plan = {"queries": {"q": {"text": "A question?"}}, "embeddingDimensions": 2,
                     "batchSize": 2, "maxRequestBytes": 65536, "maxPromptPricePerMillion": "0.03"}

    def response(self):
        return {"model": "openai/text-embedding-3-small", "data": [
            {"index": 1, "embedding": [0, 1]}, {"index": 0, "embedding": [1, 0]}],
            "usage": {"prompt_tokens": 12, "total_tokens": 12, "cost": 0.00000024}}

    def run_embed(self, path, sender, **changes):
        options = dict(budget=0.02, max_calls=1, cache_path=path, sender=sender)
        options.update(changes)
        with mock.patch.dict(probe.os.environ, {"OPENROUTER_API_KEY": "SECRET_CANARY"}):
            return probe.embed(self.documents, self.plan, "openai/text-embedding-3-small", **options)

    def test_batch_indices_are_reordered_and_reusable_offline(self):
        sender = mock.Mock(return_value=self.response())
        with tempfile.TemporaryDirectory() as directory:
            cache = self.run_embed(Path(directory) / "cache.json", sender)
        sender.assert_called_once()
        self.assertEqual(cache["vectors"]["d:s/a"], [1, 0])
        self.assertEqual(cache["vectors"]["q:q"], [0, 1])
        self.assertEqual(len(retrieval.validate_cache(cache, self.documents, self.plan["queries"])), 2)
        self.assertNotIn("SECRET_CANARY", json.dumps(cache))

    def test_missing_cost_uses_explicit_price_ceiling_not_zero(self):
        response = self.response()
        response["usage"].pop("cost")
        with tempfile.TemporaryDirectory() as directory:
            cache = self.run_embed(Path(directory) / "cache.json", mock.Mock(return_value=response))
        record = cache["trace"][0]
        self.assertIsNone(record["reported_cost_usd"])
        self.assertEqual(record["cost_basis"], "tokens-times-price-ceiling")
        self.assertGreater(record["accounted_usd"], 0)

    def test_duplicate_indices_fail_without_retry_and_leave_incomplete_cache(self):
        response = self.response()
        response["data"][0]["index"] = 0
        sender = mock.Mock(return_value=response)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "cache.json"
            with self.assertRaisesRegex(ValueError, "no retry"):
                self.run_embed(path, sender)
            cache = json.loads(path.read_text())
        sender.assert_called_once()
        self.assertFalse(cache["complete"])
        self.assertEqual(cache["vectors"], {})
        self.assertEqual(cache["trace"][0]["status"], "failed-or-unaccounted")

    def test_budget_and_call_preflight_prevent_network(self):
        for changes in (dict(budget=0.000000001), dict(max_calls=0)):
            sender = mock.Mock()
            with tempfile.TemporaryDirectory() as directory, self.subTest(changes=changes), self.assertRaises(ValueError):
                self.run_embed(Path(directory) / "cache.json", sender, **changes)
            sender.assert_not_called()

    def test_oversize_input_is_rejected_before_network(self):
        self.documents["s/a"]["text"] = "x" * 4097
        sender = mock.Mock()
        with tempfile.TemporaryDirectory() as directory, self.assertRaises(ValueError):
            self.run_embed(Path(directory) / "cache.json", sender)
        sender.assert_not_called()

    def test_existing_cache_is_never_overwritten_or_rebilled(self):
        sender = mock.Mock()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "cache.json"
            path.write_text("preserve")
            with self.assertRaisesRegex(ValueError, "already exists"):
                self.run_embed(path, sender)
            self.assertEqual(path.read_text(), "preserve")
        sender.assert_not_called()
