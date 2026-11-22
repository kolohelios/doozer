"""Deterministic mechanics and isolation tests, not claims of semantic accuracy."""

import copy
import hashlib
import io
import json
import math
import os
from pathlib import Path
import tempfile
from unittest import TestCase, mock

from scripts import calibration, split_judgment as split
from scripts.evaluation_client import Contracts, OutputFailure


class SplitTests(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data, _, _ = calibration.load()
        cls.contracts = Contracts(split.CONTRACT)

    def prepare(self):
        return split.prepare(self.data, self.contracts, 0.50, 40)

    def sender(self, endpoint, payload, token):
        self.assertEqual(token, "SECRET_CANARY")
        self.assertFalse(payload["provider"]["allow_fallbacks"])
        self.assertNotIn("reference", payload)
        response = {"model": payload["model"], "usage": {"cost": 0.001, "input_tokens": 100, "output_tokens": 20}}
        if endpoint == split.DECISIONS:
            response["answers"] = {"verdict": {"type": "choice", "choice": "pass", "confidence": 0.8}}
        elif endpoint == split.EMBEDDINGS:
            response["data"] = [{"index": index, "embedding": [1.0 + index % 3, 2.0] + [0.0] * (payload["dimensions"] - 2)} for index in range(len(payload["input"]))]
        else:
            context = json.loads(payload["messages"][1]["content"])
            if "requirements" in context:
                self.assertEqual(set(context), {"candidateSentences", "requirements"})
                value = {"checks": [{"id": check["id"], "result": "conveyed", "rationale": "Recorded mechanical fixture.", "answerQuotes": [context["candidateSentences"][0]["text"]]} for check in context["requirements"]]}
            else:
                self.assertEqual(set(context), {"candidateSentences", "authoritative_sources"})
                source = context["authoritative_sources"][0]
                value = {"sentences": [{"id": sentence["id"], "result": "supported", "rationale": "Recorded mechanical fixture.", "citations": [{"source": source["id"], "quote": source["text"]}]} for sentence in context["candidateSentences"]]}
            response["choices"] = [{"finish_reason": "stop", "message": {"content": json.dumps(value)}}]
        return response

    def test_saved_comparison_is_immutable_and_math_recomputes_offline(self):
        observation = self.data["splitObservations"]
        path = calibration.ROOT / observation["artifact"]
        self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), observation["artifactSHA256"])
        report = json.loads(path.read_text())
        frozen = report["protocol"]["frozen"]
        self.assertEqual(split.pilot.digest(frozen), observation["protocolSHA256"])
        self.assertEqual(report["source_commit"], observation["sourceCommit"])
        self.assertEqual(len(report["trace"]), 31)
        self.assertAlmostEqual(sum(trace["reported_cost_usd"] for trace in report["trace"]), observation["reportedCostUSD"])
        self.assertEqual(split.summarize(report["rows"]), report["summary"])
        rows = copy.deepcopy(report["rows"])
        split.decide(rows)
        self.assertEqual(rows, report["rows"])
        self.assertTrue(all(row["decisions"]["jev"] == row["reference"] for row in rows))
        self.assertEqual(sum(row["decisions"]["combined"] == "uncertain" for row in rows), 3)
        self.assertEqual(sum(row["grounding"]["status"] == "invalid" for row in rows), 2)
        for operation, trace in zip(frozen["operations"], report["trace"]):
            self.assertEqual(hashlib.sha256(json.dumps(operation["payload"], allow_nan=False).encode()).hexdigest(), trace["request_sha256"])
        inputs = frozen["embedding_inputs"]
        dense = {inputs[item["index"]]["text"]: split.normalize(item["embedding"]) for item in report["trace"][-1]["response"]["data"]}
        for field, vectors in (("lexical_math", split.tfidf(inputs)), ("dense_math", dense)):
            calculated = split.vector_diagnostics(frozen["samples"], vectors)
            for saved, recalculated in zip(report[field], calculated):
                self.assertEqual(saved["id"], recalculated["id"])
                for metric in ("required_meaning_similarity", "sentence_source_similarity", "same_criterion_answer_similarity"):
                    self.assertEqual(set(saved[metric]), set(recalculated[metric]))
                    for key, value in saved[metric].items():
                        self.assertAlmostEqual(value, recalculated[metric][key], places=12)
        audit = observation["audit"]["inventedContextStillAcceptedLocally"]
        row = next(row for row in rows if row["id"] == audit["sample"])
        sentence = next(item for item in row["grounding"]["value"]["sentences"] if item["id"] == audit["sentence"])
        self.assertEqual(sentence["result"], audit["result"])
        self.assertIn(audit["rationaleQuote"], sentence["rationale"])

    def test_frozen_roles_and_data_isolation_with_no_labels_in_requests(self):
        report = self.prepare()
        frozen = report["protocol"]["frozen"]
        self.assertEqual(len(frozen["operations"]), 31)
        self.assertEqual(split.pilot.digest(frozen), report["protocol"]["sha256"])
        for op in frozen["operations"]:
            self.assertNotIn("draft_expected", json.dumps(op["payload"]))
            if op["kind"] == "coverage":
                context = json.loads(op["payload"]["messages"][1]["content"])
                self.assertEqual(set(context), {"candidateSentences", "requirements"})
            if op["kind"] == "grounding":
                context = json.loads(op["payload"]["messages"][1]["content"])
                self.assertNotIn("requirements", context)
        for sample in frozen["samples"]:
            self.assertEqual("".join(sample["judge_input"]["candidate"].split()), "".join("".join(sentence["text"].split()) for sentence in sample["sentences"]))

    def test_preparation_has_no_network_and_existing_output_is_immutable(self):
        with tempfile.TemporaryDirectory() as directory, mock.patch.object(split, "transport") as network, mock.patch("sys.stdout", new_callable=io.StringIO):
            path = Path(directory) / "plan.json"
            self.assertEqual(split.main(["--output", str(path)]), 0)
            before = path.read_bytes()
            self.assertEqual(split.main(["--output", str(path)]), 2)
            self.assertEqual(before, path.read_bytes())
            network.assert_not_called()

    def test_recorded_full_run_uses_one_shared_ledger(self):
        report = self.prepare()
        with mock.patch.dict(os.environ, {"OPENROUTER_API_KEY": "SECRET_CANARY"}):
            split.run(report, self.contracts, lambda: None, sender=self.sender)
        self.assertEqual(report["status"], "completed")
        self.assertEqual(len(report["trace"]), 31)
        self.assertAlmostEqual(report["accounted_or_reserved_usd"], 0.031)
        self.assertTrue(all(row["decisions"]["combined"] == "pass" for row in report["rows"]))
        self.assertEqual(len(report["dense_math"]), 10)
        self.assertEqual(report["summary"]["primary"]["planned"], 7)
        self.assertNotIn("SECRET_CANARY", json.dumps(report))
        with self.assertRaises(ValueError):
            split.run(report, self.contracts, lambda: None, sender=self.sender)

    def test_limits_and_frozen_inputs_cannot_be_silently_changed(self):
        for budget, calls in ((0.51, 40), (0.50, 41), (0.50, 30), (float("nan"), 40)):
            with self.subTest(budget=budget, calls=calls), self.assertRaises(ValueError):
                split.prepare(self.data, self.contracts, budget, calls)
        report = self.prepare()
        report["protocol"]["frozen"]["plan"]["temperature"] = 1
        sender = mock.Mock()
        with self.assertRaises(ValueError):
            split.run(report, self.contracts, lambda: None, sender=sender)
        sender.assert_not_called()

    def test_accounting_failure_halts_without_replacement(self):
        report = self.prepare()
        def bad(endpoint, payload, token):
            response = self.sender(endpoint, payload, token)
            response["usage"].pop("cost")
            return response
        with mock.patch.dict(os.environ, {"OPENROUTER_API_KEY": "SECRET_CANARY"}), self.assertRaises(ValueError):
            split.run(report, self.contracts, lambda: None, sender=bad)
        self.assertEqual(len(report["trace"]), 1)
        self.assertEqual(report["trace"][0]["status"], "failed-or-unaccounted")
        self.assertGreater(report["accounted_or_reserved_usd"], 0)

    def test_invalid_known_billed_outputs_do_not_trigger_replacements(self):
        report = self.prepare()
        def bad(endpoint, payload, token):
            response = self.sender(endpoint, payload, token)
            if endpoint == split.CHAT_ENDPOINT:
                response["choices"][0]["message"]["content"] = "not JSON"
            return response
        with mock.patch.dict(os.environ, {"OPENROUTER_API_KEY": "SECRET_CANARY"}):
            split.run(report, self.contracts, lambda: None, sender=bad)
        self.assertEqual(len(report["trace"]), 31)
        self.assertEqual(sum(group["invalid_stages"] for group in report["summary"].values()), 20)
        self.assertTrue(all(row["decisions"]["combined"] == "uncertain" for row in report["rows"]))

    def test_coverage_and_grounding_require_complete_ids_and_exact_quotes(self):
        sample = self.prepare()["protocol"]["frozen"]["samples"][0]
        value = {"checks": [{"id": check["id"], "result": "conveyed", "rationale": "Fixture", "answerQuotes": [sample["sentences"][0]["text"]]} for check in sample["checks"]]}
        split.validate_stage("coverage", value, sample, self.contracts)
        for mutation in ("quote", "membership"):
            bad = copy.deepcopy(value)
            if mutation == "quote":
                bad["checks"][0]["answerQuotes"] = ["fabricated candidate quote"]
            else:
                bad["checks"].pop()
            with self.subTest(mutation=mutation), self.assertRaises(OutputFailure):
                split.validate_stage("coverage", bad, sample, self.contracts)
        grounding = {"sentences": [{"id": sentence["id"], "result": "supported", "rationale": "Fixture", "citations": []} for sentence in sample["sentences"]]}
        with self.assertRaises(OutputFailure):
            split.validate_stage("grounding", grounding, sample, self.contracts)

    def test_combination_abstains_on_disagreement_instead_of_averaging_confidence(self):
        row = {"coverage": {"status": "valid", "value": {"checks": [{"result": "absent"}]}},
               "jev": {"status": "valid", "value": {"choice": "pass", "confidence": 1.0}}}
        split.decide([row])
        self.assertEqual(row["decisions"], {"generative": "fail", "jev": "pass", "combined": "uncertain"})

    def test_vector_math_preserves_negation_tokens_but_does_not_claim_entailment(self):
        texts = ["staff may enter", "staff may not enter", "visitors need an escort"]
        vectors = split.tfidf([{"text": text} for text in texts])
        score = split.cosine(vectors[texts[0]], vectors[texts[1]])
        self.assertGreater(score, 0.5)
        self.assertLess(score, 1)
        self.assertAlmostEqual(split.cosine(vectors[texts[0]], vectors[texts[0]]), 1)
        for values in ([0.0, 0.0], [math.nan, 1.0], [math.inf, 1.0]):
            with self.assertRaises(OutputFailure):
                split.normalize(values)
