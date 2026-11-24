import copy
from contextlib import redirect_stdout
import io
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import Mock, patch

from scripts import maintenance_call as trial


class MaintenanceContrastTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data, cls.scenario = trial.proposer.load()
        with patch("urllib.request.urlopen", side_effect=AssertionError("offline preparation")):
            cls.report = trial.prepare_contrast(cls.data, cls.scenario)
        cls.frozen = cls.report["protocol"]["frozen"]

    def checkpoint(self, case):
        return self.frozen["trials"][case]["protocol"]["frozen"]["checkpoint"]["protocol"]["frozen"]

    def response(self, value=None):
        value = value if value is not None else {"baseRevision": 5, "accounting": {}, "operations": [], "rationale": "Mock no-op, not a semantic judgment."}
        return {"model": "openai/gpt-4.1", "choices": [{"finish_reason": "stop", "message": {"content": json.dumps(value)}}],
                "usage": {"prompt_tokens": 2000, "completion_tokens": 400, "cost": 0.001}}

    def run_in(self, directory, sender=None, report=None):
        sender = sender if sender is not None else Mock(return_value=self.response())
        report = copy.deepcopy(self.report) if report is None else report
        snapshots = []
        with patch.dict(os.environ, {"OPENROUTER_API_KEY": "offline-test-token"}):
            trial.run_contrast(report, lambda: snapshots.append(copy.deepcopy(report)), authorized_protocol_sha256=report["protocol"]["sha256"], sender=sender, receipt_directory=directory)
        return report, sender, snapshots

    def test_exact_same_evidence_revision_history_and_shared_v05_instructions(self):
        a, b = self.checkpoint("case-a"), self.checkpoint("case-b")
        self.assertEqual((len(a["before"]["claims"]), len(b["before"]["claims"])), (3, 6))
        for key in ("received", "processed", "history", "revision"):
            self.assertEqual(a["before"][key], b["before"][key])
        self.assertEqual(len(a["before"]["received"]), 11)
        self.assertEqual(a["messages"][0], b["messages"][0])
        self.assertIn("Lack of new sources alone does not justify no-op", a["messages"][0]["content"])
        ca, cb = [json.loads(c["messages"][1]["content"]) for c in (a, b)]
        for key in ca.keys() - {"current_claims", "existing_aliases"}:
            self.assertEqual(ca[key], cb[key])
        self.assertNotEqual(ca["existing_aliases"], cb["existing_aliases"])
        self.assertEqual(self.frozen["limits"], {"max_calls": 2, "budget_usd": 0.30, "retries": 0})
        self.assertEqual(self.frozen["design"]["designVersion"], "0.5")
        self.assertEqual(self.report["trace"], [])
        self.assertNotIn("cases", self.report)

    def test_only_representation_differs_in_actual_requests(self):
        a, b = [copy.deepcopy(self.frozen["trials"][key]["protocol"]["frozen"]["operation"]["payload"]) for key in ("case-a", "case-b")]
        ma, mb = a.pop("messages"), b.pop("messages")
        self.assertEqual(a, b)
        self.assertEqual(ma[0], mb[0])
        for message in (ma, mb):
            self.assertNotIn("retry-safety-current", json.dumps(message))
            self.assertNotIn("case-a", json.dumps(message))
            self.assertNotIn("case-b", json.dumps(message))
            self.assertNotIn("payments", json.dumps(message))
        self.assertLessEqual(sum(c["protocol"]["frozen"]["reservation_usd"] for c in self.frozen["trials"].values()), 0.30)

    def test_private_targets_labels_future_and_previous_output_canaries_not_sent(self):
        data, scenario = copy.deepcopy(self.data), copy.deepcopy(self.scenario)
        data["proposerContrast"]["privateReviewNote"] = "SECRET_LABEL_CANARY"
        data["maintenance"]["consolidation"] = {"secret": "SECRET_TARGET_CANARY"}
        data["proposerObservations"]["proposal"] = {"secret": "SECRET_PREVIOUS_OUTPUT_CANARY"}
        data["proposerCheckpoint"]["readerQueries"] = ["SECRET_QUERY_CANARY"]
        data["proposerCheckpoint"]["references"] = ["SECRET_REFERENCE_CANARY"]
        for step in scenario["steps"]:
            step["expect"]["must"][0]["meaning"] = "SECRET_RUBRIC_CANARY"
        scenario["sources"]["future"] = {**scenario["sources"]["manual"], "text": "SECRET_FUTURE_CANARY"}
        scenario["steps"].append({"id": "future", "receive": ["future"], "reconcile": [], "expect": {}})
        r = trial.prepare_contrast(data, scenario)
        for child in r["protocol"]["frozen"]["trials"].values():
            self.assertNotIn("SECRET_", json.dumps(child["protocol"]["frozen"]["operation"]["payload"]))
        self.assertIn("SECRET_LABEL_CANARY", json.dumps(r["protocol"]["frozen"]["design"]))

    def test_two_mock_calls_no_forced_transform_or_semantic_pass(self):
        with TemporaryDirectory() as directory:
            r, sender, snapshots = self.run_in(directory)
        self.assertEqual(sender.call_count, 2)
        self.assertEqual(r["status"], "completed-contrast")
        self.assertEqual(r["summary"]["submitted_calls"], 2)
        self.assertAlmostEqual(r["summary"]["known_cost_usd"], 0.002)
        self.assertFalse(r["summary"]["canonical_acceptance"])
        self.assertEqual([x["case"] for x in r["trace"]], ["case-b", "case-a"])
        for case in r["cases"].values():
            self.assertEqual(case["inspection"]["status"], "no-op-in-isolated-copy")
            self.assertEqual(case["inspection"]["semantic_judgment"], "pending-human-review")
            self.assertEqual(case["inspection"]["recovery"]["status"], "not-exercised-no-change")
            self.assertEqual(case["authorization_parent_sha256"], r["protocol"]["sha256"])
        self.assertTrue(any(s["cases"]["case-b"]["trace"] and "response" in s["cases"]["case-b"]["trace"][0] and "inspection" not in s["cases"]["case-b"] for s in snapshots))

    def test_nonempty_mock_response_uses_its_own_baseline_state_and_recovery(self):
        candidate = copy.deepcopy(self.data["maintenance"]["consolidation"]["patch"])
        candidate["operations"] += [{"op": "retire", "id": key, "replacement": "retry-safety-current", "reason": "Mock source-preserving consolidation."} for key in ("retry-guidance", "database-writes", "notification-exception")]
        def send(endpoint, payload, token):
            count = len(json.loads(payload["messages"][1]["content"])["current_claims"])
            return self.response(candidate if count == 6 else None)
        with TemporaryDirectory() as directory:
            r, _, _ = self.run_in(directory, sender=Mock(side_effect=send))
        self.assertEqual(r["cases"]["case-b"]["inspection"]["before"]["active_claims"], 6)
        self.assertTrue(r["cases"]["case-b"]["inspection"]["recovery"]["material_recovered"])
        self.assertEqual(r["cases"]["case-a"]["inspection"]["status"], "no-op-in-isolated-copy")

    def test_unknown_first_accounting_stops_second_and_fresh_parent_cannot_resume(self):
        response = self.response(); response["usage"]["cost"] = None
        report, sender = copy.deepcopy(self.report), Mock(return_value=response)
        with TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ValueError, "no retry"):
                self.run_in(directory, sender=sender, report=report)
            self.assertEqual(report["status"], "stopped-contrast-no-retry")
            self.assertEqual(report["summary"]["planned_calls"], 2)
            self.assertEqual(report["summary"]["submitted_calls"], 1)
            self.assertEqual(report["summary"]["unknown_billing"], 1)
            self.assertEqual(report["cases"]["case-a"]["trace"], [])
            with self.assertRaisesRegex(ValueError, "already claimed"):
                self.run_in(directory, sender=sender)
            self.assertEqual(sender.call_count, 1)

    def test_accounted_invalid_first_output_is_not_replaced_second_is_still_scheduled(self):
        invalid = self.response(); invalid["choices"][0]["finish_reason"] = "length"
        with TemporaryDirectory() as directory:
            r, sender, _ = self.run_in(directory, sender=Mock(side_effect=[invalid, self.response()]))
        self.assertEqual(sender.call_count, 2)
        self.assertEqual(r["summary"]["cases"]["case-b"]["proposal_status"], "invalid-native-output-no-replacement")
        self.assertEqual(r["summary"]["cases"]["case-a"]["proposal_status"], "no-op-in-isolated-copy")

    def test_standalone_child_cannot_bypass_parent_stop_or_authorization(self):
        child = copy.deepcopy(self.frozen["trials"]["case-a"])
        with patch.object(trial.client, "Ledger", side_effect=AssertionError("no credential access")), self.assertRaisesRegex(ValueError, "parent coordinator"):
            trial.run(child, lambda: None, authorized_protocol_sha256=child["protocol"]["sha256"])
        with patch.object(trial.client.os, "environ", {}), TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ValueError, "missing OpenRouter"):
                trial.run_contrast(copy.deepcopy(self.report), lambda: None, authorized_protocol_sha256=self.report["protocol"]["sha256"], receipt_directory=directory)
            self.assertEqual(list(Path(directory).iterdir()), [])

    def test_changed_hash_schedule_and_evidence_are_rejected(self):
        r = copy.deepcopy(self.report)
        r["protocol"]["frozen"]["design"]["order"] = ["case-a", "case-a"]
        with self.assertRaises(ValueError):
            trial.check_contrast(r)
        trials = copy.deepcopy(self.frozen["trials"])
        trials["case-b"]["protocol"]["frozen"]["checkpoint"]["protocol"]["frozen"]["before"]["received"]["manual"]["text"] = "Different evidence."
        with self.assertRaisesRegex(ValueError, "changed evidence"):
            trial.contrast_invariants(trials)

    def test_cli_default_contrast_is_offline_and_no_clobber(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "contrast.json"
            with redirect_stdout(io.StringIO()):
                self.assertEqual(trial.main(["--contrast", "--output", str(path)]), 0)
            r = json.loads(path.read_text())
            self.assertEqual(r["status"], "prepared-contrast-awaiting-authorization")
            self.assertEqual(r["trace"], [])
            self.assertNotIn("cases", r)
            with self.assertRaises(ValueError):
                trial.main(["--contrast", "--output", str(path)])
