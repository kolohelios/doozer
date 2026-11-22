"""Controlled experiment plumbing and leakage checks, never model-quality tests."""

import copy
import io
import json
from pathlib import Path
import tempfile
from unittest import TestCase, mock

from scripts import understanding as experiment
from scripts.evaluation_client import CallFailure, Client, Contracts, OutputFailure
from scripts.retrieval import embedding_items, fingerprint, validate_cache


class FakeClient:
    """Abstentions and uncertain judgments deliberately do NOT confirm the hypothesis."""
    def __init__(self, contracts):
        self.contracts, self.calls, self.trace = contracts, [], []

    def call(self, role, definition, context, label):
        self.calls.append((role, copy.deepcopy(context), label))
        self.trace.append({"role": role, "network": False, "status": "controlled-test"})
        if role == "link":
            value = {"links": []}
        elif role == "reason":
            value = {"summary": "No live understanding was evaluated.", "claims": [], "directives": [],
                     "uncertainties": ["Recorded plumbing only."]}
        else:
            source = context["authoritative_sources"][0]
            value = {"checks": {check["id"]: {
                "result": "uncertain", "rationale": "No semantic evaluation in this controlled test.",
                "answerQuotes": [], "citations": [{"source": source["id"], "quote": source["text"]}],
            } for check in context["rubric"]}, "unsupported": []}
        self.contracts.validate(definition, value)
        return value


class UnderstandingTests(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.inputs = experiment.load_inputs(noise=2)
        cls.contracts = Contracts(experiment.DIRECTORY / "contracts.cue")

    def cache(self, inputs=None):
        data, documents, raw, embedding_plan, case_ids, incoming = inputs or self.inputs
        items = embedding_items(documents, embedding_plan["queries"])
        return {"complete": True, "model": "test/controlled", "dimensions": 2, "trace": [],
                "fingerprint": fingerprint(documents, embedding_plan["queries"], "test/controlled", 2),
                "vectors": {key: [1, 0] for key, _ in items}}

    def run_controlled(self, inputs=None):
        inputs = copy.deepcopy(inputs or self.inputs)
        client = FakeClient(self.contracts)
        report = {"trace": client.trace}
        experiment.run(*inputs, self.cache(inputs), client, report, lambda: None)
        return report, client

    def test_new_cases_and_opaque_global_source_ids(self):
        data, docs, raw, embed_plan, case_ids, incoming = self.inputs
        self.assertEqual(len(data["cases"]), 3)
        self.assertEqual(len(incoming), 21)
        self.assertEqual(len(set(incoming)), 21)
        self.assertEqual(sum(len(case["checks"]) for case in data["cases"].values()), 14)
        self.assertTrue(all(key.startswith("heldout/d-") for key in incoming))
        self.assertEqual(docs["heldout/d-b2"]["replyTo"], "heldout/d-77")

    def test_three_conditions_and_latin_square_order(self):
        report, client = self.run_controlled()
        self.assertEqual(len(report["rows"]), 9)
        orders = []
        for case in dict.fromkeys(row["case"] for row in report["rows"]):
            group = [row for row in report["rows"] if row["case"] == case]
            orders.append(tuple(row["arm"] for row in group))
            self.assertEqual(set(row["arm"] for row in group), set(experiment.ARMS))
            for row in group:
                if row["arm"] != "full":
                    self.assertLessEqual(row["context_bytes"], self.inputs[0]["plan"]["contextBytes"])
                self.assertEqual([doc["id"] for doc in row["context"]], sorted(doc["id"] for doc in row["context"]))
        self.assertEqual(len(set(orders)), 3)

    def test_linker_never_receives_queries_partitions_or_rubrics(self):
        report, client = self.run_controlled()
        for role, context, _ in client.calls:
            if role == "link":
                self.assertEqual(set(context), {"incoming", "candidates", "sources"})
                self.assertNotIn("payout-recovery", json.dumps(context))
                self.assertNotIn("archive-access", json.dumps(context))

    def test_generation_is_isolated_from_oracle_and_arm_labels(self):
        inputs = copy.deepcopy(self.inputs)
        for case in inputs[0]["cases"].values():
            for check in case["checks"]:
                check["requirement"] = "ORACLE_CANARY"
        report, client = self.run_controlled(inputs)
        for role, context, _ in client.calls:
            if role in ("link", "reason"):
                self.assertNotIn("ORACLE_CANARY", json.dumps(context))
            if role == "reason":
                self.assertEqual(set(context), {"question", "sources"})
            if role == "judge":
                self.assertNotIn("arm", context)
                self.assertNotIn("retrieval", context)
                self.assertNotIn("model", context)
                self.assertIn("ORACLE_CANARY", json.dumps(context))

    def test_judging_happens_after_all_generation(self):
        report, client = self.run_controlled()
        roles = [role for role, _, _ in client.calls]
        last_reason = max(index for index, role in enumerate(roles) if role == "reason")
        first_judge = min(index for index, role in enumerate(roles) if role == "judge")
        self.assertLess(last_reason, first_judge)

    def test_identical_inputs_reuse_samples_and_uncertain_is_not_pass(self):
        original = experiment.make_contexts
        def equivalent(*args):
            rows = original(*args)
            documents, case_ids = args[0], args[6]
            for row in rows:
                row["context"] = [documents[key] for key in sorted(case_ids[row["case"]])]
            return rows
        with mock.patch.object(experiment, "make_contexts", side_effect=equivalent):
            report, client = self.run_controlled()
        self.assertTrue(any("generation_reused_from" in row for row in report["rows"]))
        self.assertTrue(any(row.get("judgment_reused") for row in report["rows"]))
        for values in report["summary"]["by_arm"].values():
            self.assertEqual(values["provisional_pass_fraction"], 0)
            self.assertEqual(values["fully_passing"], 0)
        self.assertEqual(len(report["summary"]["complete_pairs"]), 3)

    def test_invalid_generation_is_retained_not_resampled(self):
        inputs = copy.deepcopy(self.inputs)
        client = FakeClient(self.contracts)
        original = client.call
        failed = []
        def invalid(role, definition, context, label):
            if role == "reason" and not failed:
                failed.append(label)
                raise OutputFailure("controlled invalid output")
            return original(role, definition, context, label)
        client.call = invalid
        report = {"trace": client.trace}
        experiment.run(*inputs, self.cache(inputs), client, report, lambda: None)
        self.assertEqual(len([row for row in report["rows"] if row["status"] == "invalid-understanding-no-replacement"]), 1)
        self.assertEqual(len(report["summary"]["complete_pairs"]), 2)

    def test_protocol_binds_labels_prompts_and_source_snapshot(self):
        data, docs, raw, embed_plan, case_ids, incoming = copy.deepcopy(self.inputs)
        first = experiment.protocol(data, docs, raw, embed_plan, case_ids, self.contracts)
        data["cases"]["payout-recovery"]["checks"][0]["requirement"] += " changed"
        second = experiment.protocol(data, docs, raw, embed_plan, case_ids, self.contracts)
        self.assertNotEqual(first["sha256"], second["sha256"])
        validate_cache(self.cache(), docs, embed_plan["queries"])
        self.assertIn("scripts/understanding.py", first["frozen"]["implementation"])

    def test_quotes_and_passes_require_actual_answer_support(self):
        context = {"answer_text": "Bounded understanding.", "rubric": [{"id": "r"}],
                   "authoritative_sources": [{"id": "heldout/d-a", "text": "Source text."}]}
        base = {"checks": {"r": {"result": "pass", "rationale": "why", "answerQuotes": ["Bounded understanding."],
                                 "citations": [{"source": "heldout/d-a", "quote": "Source text."}]}}, "unsupported": []}
        experiment.validate_judgment(base, context)
        for key, value in (("answerQuotes", ["fabricated"]), ("answerQuotes", []), ("answerQuotes", [" "])):
            invalid = copy.deepcopy(base)
            invalid["checks"]["r"][key] = value
            with self.assertRaises(OutputFailure):
                experiment.validate_judgment(invalid, context)
        invalid = copy.deepcopy(base)
        invalid["checks"] = {}
        with self.assertRaises(OutputFailure):
            experiment.validate_judgment(invalid, context)

    def test_unavailable_citations_and_projection_support_are_rejected(self):
        answer = {"summary": "x", "claims": [{"text": "x", "scope": "x", "attribution": "inferred",
                   "evidence": [{"source": "heldout/d-a", "quote": "Source text."}]}], "directives": [], "uncertainties": []}
        for docs in ([], [{"id": "heldout/d-a", "text": "Source text.", "kind": "projection"}]):
            with self.assertRaises(OutputFailure):
                experiment.validate_understanding(answer, docs)

    def test_source_scopes_are_available_for_answer_quote_validation(self):
        answer = {"summary": "x", "claims": [{"text": "y", "scope": "manual-only", "attribution": "inferred"}],
                  "directives": [], "uncertainties": []}
        self.assertIn("manual-only", experiment.answer_text(answer))

    def test_links_require_candidate_membership_exact_quotes_and_limits(self):
        docs = {"heldout/a": {"text": "One."}, "heldout/b": {"text": "Two."}, "heldout/c": {"text": "Three."}}
        link = {"from": "heldout/a", "to": "heldout/b", "kind": "related", "fromQuote": "One.", "toQuote": "Two.", "reason": "why"}
        experiment.validate_links({"links": [link]}, ["heldout/a"], {"heldout/a": ["heldout/b"]}, docs, 2)
        for invalid in (dict(link, to="heldout/c"), dict(link, fromQuote="fake")):
            with self.assertRaises(OutputFailure):
                experiment.validate_links({"links": [invalid]}, ["heldout/a"], {"heldout/a": ["heldout/b"]}, docs, 2)
        with self.assertRaises(OutputFailure):
            experiment.validate_links({"links": [link, link]}, ["heldout/a"], {"heldout/a": ["heldout/b"]}, docs, 2)

    def test_judge_only_audit_never_regenerates_or_relinks(self):
        report, _ = self.run_controlled()
        data, docs, raw, embed_plan, case_ids, incoming = self.inputs
        report["protocol"] = experiment.protocol(data, docs, raw, embed_plan, case_ids, self.contracts)
        fake = FakeClient(self.contracts)
        with tempfile.TemporaryDirectory() as directory, \
                mock.patch.object(experiment, "Client", return_value=fake), \
                mock.patch("sys.stdout", new_callable=io.StringIO):
            parent, output = Path(directory) / "parent.json", Path(directory) / "audit.json"
            parent.write_text(json.dumps(report))
            before = parent.read_text()
            self.assertEqual(experiment.main(["--audit", str(parent), "--noise", "2", "--output", str(output), "--budget-usd", "0.1"]), 0)
            self.assertEqual(parent.read_text(), before)
            audit = json.loads(output.read_text())
            self.assertTrue(audit["audit_only"])
            self.assertEqual(audit["parent_protocol"], report["protocol"]["sha256"])
            self.assertEqual([row["understanding"] for row in audit["rows"]], [row["understanding"] for row in report["rows"]])
        self.assertTrue(fake.calls)
        self.assertTrue(all(role == "judge" for role, _, _ in fake.calls))

    def test_default_prepare_makes_no_calls_even_with_token(self):
        with tempfile.TemporaryDirectory() as directory, \
                mock.patch.dict("scripts.evaluation_client.os.environ", {"OPENROUTER_API_KEY": "SECRET_CANARY"}), \
                mock.patch.object(experiment, "Client") as client, mock.patch.object(experiment, "embed") as embed, \
                mock.patch("sys.stdout", new_callable=io.StringIO):
            output = Path(directory) / "protocol.json"
            self.assertEqual(experiment.main(["--noise", "2", "--output", str(output)]), 0)
            client.assert_not_called()
            embed.assert_not_called()
            report = json.loads(output.read_text())
            self.assertEqual(report["status"], "prepared")
            self.assertNotIn("SECRET_CANARY", output.read_text())


class EvaluationClientTests(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plan = experiment.load_inputs(noise=0)[0]["plan"]
        cls.contracts = Contracts(experiment.DIRECTORY / "contracts.cue")

    def response(self):
        return {"model": self.plan["roles"]["reason"]["model"], "provider": "test",
                "usage": {"prompt_tokens": 10, "completion_tokens": 10, "cost": 0.00001},
                "choices": [{"finish_reason": "stop", "message": {"content": json.dumps({
                    "summary": "Controlled response.", "claims": [], "directives": [], "uncertainties": [],
                })}}]}

    def client(self, sender, **overrides):
        with mock.patch.dict("scripts.evaluation_client.os.environ", {"OPENROUTER_API_KEY": "SECRET_CANARY"}):
            return Client(copy.deepcopy(self.plan), self.contracts, sender=sender,
                          **{**dict(budget=1.0, max_calls=10), **overrides})

    def test_fixed_model_provider_prompt_and_temperature(self):
        sender = mock.Mock(return_value=self.response())
        client = self.client(sender)
        for sources in ([], [{"id": "heldout/x", "text": "new"}]):
            client.call("reason", "#Understanding", {"question": "q", "sources": sources}, "local-label")
        payloads = [call.args[1] for call in sender.call_args_list]
        self.assertEqual(payloads[0]["messages"][0], payloads[1]["messages"][0])
        for payload in payloads:
            self.assertEqual(payload["model"], self.plan["roles"]["reason"]["model"])
            self.assertEqual(payload["provider"]["only"], [self.plan["roles"]["reason"]["provider"]])
            self.assertEqual(payload["temperature"], 0)
            self.assertFalse(payload["provider"]["allow_fallbacks"])
            self.assertNotIn("local-label", json.dumps(payload))
        self.assertNotIn("SECRET_CANARY", json.dumps(client.trace))

    def test_invalid_outputs_are_not_retried(self):
        response = self.response()
        response["choices"][0]["finish_reason"] = "length"
        sender = mock.Mock(return_value=response)
        client = self.client(sender)
        with self.assertRaises(OutputFailure):
            client.call("reason", "#Understanding", {}, "x")
        sender.assert_called_once()
        self.assertEqual(client.trace[0]["status"], "invalid-output")

    def test_unknown_cost_halts_all_subsequent_calls(self):
        response = self.response()
        response["usage"].pop("cost")
        sender = mock.Mock(return_value=response)
        client = self.client(sender)
        for _ in range(2):
            with self.assertRaises(CallFailure):
                client.call("reason", "#Understanding", {}, "x")
        sender.assert_called_once()

    def test_submitted_trace_persists_before_transport_and_rejected_values_redact_token(self):
        seen = []
        response = self.response()
        response["choices"][0]["message"]["content"] = json.dumps({"summary": "SECRET_CANARY"})
        def sender(*args):
            self.assertEqual(seen[-1]["status"], "submitted")
            return response
        client = self.client(sender)
        client.on_trace = lambda: seen.append(copy.deepcopy(client.trace[-1]))
        with self.assertRaises(OutputFailure):
            client.call("reason", "#Understanding", {}, "x")
        self.assertIn("rejected_value", client.trace[-1])
        self.assertNotIn("SECRET_CANARY", json.dumps(client.trace))

    def test_budget_limit_prevents_transport(self):
        sender = mock.Mock()
        client = self.client(sender, budget=0.000000001)
        with self.assertRaises(CallFailure):
            client.call("reason", "#Understanding", {}, "x")
        sender.assert_not_called()

    def test_required_empty_containers_cannot_be_silently_filled(self):
        for definition, value in (("#Links", {}), ("#Understanding", {"summary": "x"}), ("#Judgment", {"unsupported": []})):
            with self.subTest(definition=definition), self.assertRaises(OutputFailure):
                self.contracts.validate(definition, value)
