import base64
import gzip
import hashlib
import json
import unittest
from unittest.mock import patch

from scripts import maintenance_call as call


class ContrastArchiveTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        data, _ = call.proposer.load()
        cls.observation = data["contrastObservations"]
        cls.archive = (call.ROOT / cls.observation["artifact"]["path"]).read_bytes()
        cls.raw = gzip.decompress(cls.archive)
        cls.report = json.loads(cls.raw)
        cls.frozen = cls.report["protocol"]["frozen"]

    def test_exact_archive_and_parent_child_protocols_are_bound(self):
        artifact = self.observation["artifact"]
        self.assertEqual((len(self.archive), hashlib.sha256(self.archive).hexdigest()), (artifact["bytes"], artifact["sha256"]))
        self.assertEqual((len(self.raw), hashlib.sha256(self.raw).hexdigest()), (artifact["rawBytes"], artifact["rawSHA256"]))
        self.assertEqual(call.proposer.digest(self.frozen), artifact["protocolSHA256"])
        self.assertEqual(self.report["source_commit"], artifact["sourceCommit"])
        self.assertEqual(self.report["operator_opt_in_sha256"], artifact["protocolSHA256"])
        for name, child in self.report["cases"].items():
            self.assertEqual(call.proposer.digest(child["protocol"]["frozen"]), self.observation["cases"][name]["protocolSHA256"])
            self.assertEqual(child["authorization_parent_sha256"], artifact["protocolSHA256"])

    def test_two_complete_native_responses_and_original_accounting(self):
        self.assertEqual(self.report["status"], "completed-contrast")
        self.assertEqual([t["case"] for t in self.report["trace"]], ["case-b", "case-a"])
        self.assertEqual(call.contrast_summary(self.report), self.report["summary"])
        self.assertEqual(self.report["summary"]["submitted_calls"], 2)
        self.assertEqual(self.report["summary"]["unknown_billing"], 0)
        self.assertAlmostEqual(self.report["summary"]["known_cost_usd"], 0.011594)
        self.assertLess(self.report["summary"]["accounted_or_reserved_usd"], 0.30)
        for name, child in self.report["cases"].items():
            self.assertEqual(len(child["trace"]), 1)
            record = child["trace"][0]
            self.assertEqual(record["status"], "received")
            self.assertEqual(record["transport"]["attempts"], 1)
            self.assertEqual(record["transport"]["outcome"], "response-received")
            self.assertEqual(record["response"]["model"], "openai/gpt-4.1")
            self.assertEqual(record["response"]["provider"], "OpenAI")
            self.assertEqual(record["response"]["choices"][0]["finish_reason"], "stop")
            self.assertEqual(record["accounted_usd"], self.observation["cases"][name]["knownCostUSD"])
            self.assertEqual(record["response"]["usage"]["cost"], record["accounted_usd"])

    def test_same_evidence_and_actual_input_boundary(self):
        call.contrast_invariants(self.frozen["trials"])
        systems = []
        for name, child in self.report["cases"].items():
            frozen = child["protocol"]["frozen"]
            self.assertEqual(frozen, self.frozen["trials"][name]["protocol"]["frozen"])
            payload = frozen["operation"]["payload"]
            checkpoint = frozen["checkpoint"]["protocol"]["frozen"]
            self.assertEqual(payload["messages"], checkpoint["messages"])
            systems.append(payload["messages"][0])
            self.assertNotIn("retry-safety-current", json.dumps(payload))
            self.assertNotIn("payments", json.dumps(payload))
            self.assertNotIn("case-a", json.dumps(payload))
            self.assertNotIn("case-b", json.dumps(payload))
            self.assertEqual(payload["provider"]["only"], ["openai"])
            self.assertFalse(payload["provider"]["allow_fallbacks"])
        self.assertEqual(systems[0], systems[1])
        self.assertIn("Lack of new sources alone does not justify no-op", systems[0]["content"])

    def test_model_text_and_noop_rationales_are_not_repaired_or_rescored(self):
        for name, child in self.report["cases"].items():
            inspection = child["inspection"]
            content = child["trace"][0]["response"]["choices"][0]["message"]["content"]
            self.assertEqual(base64.b64decode(inspection["input"]["base64"]).decode(), content)
            self.assertEqual(json.loads(content), self.observation["cases"][name]["proposal"])
            self.assertEqual(inspection["proposal"], self.observation["cases"][name]["proposal"])
            self.assertEqual(inspection["proposal"]["operations"], [])
            self.assertIn("without additional evidence or a change in interpretive context", inspection["proposal"]["rationale"])
            self.assertEqual(inspection["semantic_judgment"], "pending-human-review")

    def test_each_view_is_unchanged_and_recovery_is_not_claimed_exercised(self):
        for name, child in self.report["cases"].items():
            before = child["protocol"]["frozen"]["checkpoint"]["protocol"]["frozen"]["before"]
            inspection = child["inspection"]
            self.assertEqual(inspection["status"], "no-op-in-isolated-copy")
            self.assertEqual(inspection["isolated_state"], before)
            self.assertEqual(inspection["before"], inspection["after"])
            self.assertEqual(len(before["claims"]), self.observation["cases"][name]["inputClaims"])
            self.assertEqual(inspection["recovery"], {"status": "not-exercised-no-change", "material_unchanged": True})
            self.assertFalse(inspection["canonical_acceptance"])
        self.assertFalse(self.observation["outcome"]["selectiveMaintenanceDemonstrated"])
        self.assertFalse(self.report["canonical_acceptance"])

    def test_historical_execution_cannot_be_resumed(self):
        # Code mismatch or completed status must reject before credential access.
        with patch.object(call.client.os, "environ", {}), self.assertRaises(ValueError):
            call.run_contrast(self.report, lambda: None, authorized_protocol_sha256=self.report["protocol"]["sha256"])
