import base64
import gzip
import hashlib
import json
import unittest
from unittest.mock import patch

from scripts import maintenance_call as call, maintenance_proposer as proposer


class ProposerArchiveTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        data, _ = proposer.load()
        cls.observation = data["proposerObservations"]
        cls.archive = (call.ROOT / cls.observation["artifact"]["path"]).read_bytes()
        cls.raw = gzip.decompress(cls.archive)
        cls.report = json.loads(cls.raw)
        cls.frozen = cls.report["protocol"]["frozen"]

    def test_exact_archive_bytes_and_frozen_protocol_are_bound(self):
        artifact = self.observation["artifact"]
        self.assertEqual((len(self.archive), hashlib.sha256(self.archive).hexdigest()), (artifact["bytes"], artifact["sha256"]))
        self.assertEqual((len(self.raw), hashlib.sha256(self.raw).hexdigest()), (artifact["rawBytes"], artifact["rawSHA256"]))
        self.assertEqual(proposer.digest(self.frozen), artifact["protocolSHA256"])
        self.assertEqual(self.report["operator_opt_in_sha256"], artifact["protocolSHA256"])
        self.assertEqual(self.report["source_commit"], artifact["preparationSourceCommit"])
        self.assertEqual(self.frozen["checkpoint"]["protocol"]["sha256"], artifact["checkpointSHA256"])

    def test_one_native_response_fully_accounted_under_original_bounds(self):
        r = self.report
        self.assertEqual(r["status"], "completed-one-call")
        self.assertEqual(len(r["trace"]), 1)
        record = r["trace"][0]
        self.assertEqual(record["status"], "received")
        self.assertEqual(record["transport"]["attempts"], 1)
        self.assertEqual(record["transport"]["outcome"], "response-received")
        self.assertEqual(record["transport"]["deadline_seconds"], 120)
        self.assertEqual(record["response"]["model"], self.observation["servedModel"])
        self.assertEqual(record["response"]["provider"], self.observation["provider"])
        self.assertEqual(record["response"]["choices"][0]["finish_reason"], "stop")
        self.assertEqual(record["accounted_usd"], self.observation["knownCostUSD"])
        self.assertEqual(record["response"]["usage"]["prompt_tokens"], 2035)
        self.assertEqual(record["response"]["usage"]["completion_tokens"], 92)
        self.assertEqual(record["reserved_usd"], 0.123036)
        self.assertLess(r["accounted_or_reserved_usd"], 0.15)
        self.assertEqual(call.summary(r), r["summary"])
        self.assertEqual(r["summary"]["unknown_billing"], 0)

    def test_actual_noop_and_raw_model_text_are_preserved_without_repair(self):
        inspection = self.report["inspection"]
        content = self.report["trace"][0]["response"]["choices"][0]["message"]["content"]
        self.assertEqual(base64.b64decode(inspection["input"]["base64"]).decode(), content)
        self.assertTrue(inspection["input"]["complete"])
        self.assertEqual(json.loads(content), self.observation["proposal"])
        self.assertEqual(inspection["proposal"], self.observation["proposal"])
        self.assertEqual(inspection["proposal"]["operations"], [])
        self.assertEqual(inspection["proposal"]["accounting"], {})
        self.assertEqual(inspection["proposal"]["baseRevision"], 5)

    def test_no_state_churn_no_recovery_success_claim_or_semantic_acceptance(self):
        inspection = self.report["inspection"]
        original = self.frozen["checkpoint"]["protocol"]["frozen"]["before"]
        self.assertEqual(inspection["isolated_state"], original)
        self.assertEqual(inspection["before"], inspection["after"])
        self.assertEqual(len(original["claims"]), 3)
        self.assertEqual(inspection["recovery"], {"status": "not-exercised-no-change", "material_unchanged": True})
        self.assertEqual(inspection["semantic_judgment"], "pending-human-review")
        self.assertFalse(inspection["canonical_acceptance"])
        self.assertFalse(self.report["canonical_acceptance"])
        self.assertFalse(self.observation["outcome"]["canonicalAcceptance"])

    def test_only_frozen_blind_messages_were_transmitted(self):
        payload = self.frozen["operation"]["payload"]
        checkpoint = self.frozen["checkpoint"]["protocol"]["frozen"]
        self.assertEqual(payload["messages"], checkpoint["messages"])
        context = json.loads(payload["messages"][1]["content"])
        self.assertEqual(set(context), {"current_revision", "current_claims", "sources", "reserved_claim_ids", "existing_aliases"})
        self.assertNotIn("retry-safety-current", json.dumps(payload))
        self.assertNotIn("payments", json.dumps(payload))
        self.assertNotIn(checkpoint["before"]["journal"][-1]["patch"]["rationale"], json.dumps(payload))
        self.assertEqual(payload["provider"]["only"], ["openai"])
        self.assertFalse(payload["provider"]["allow_fallbacks"])

    def test_archive_is_never_a_resumable_execution_input(self):
        # Do not require current code hashes to match a historical artifact.
        # Either historical-code mismatch or completed status must stop before keys.
        with patch.object(call.client, "Ledger", side_effect=AssertionError("no credential access")), self.assertRaises(ValueError):
            call.run(self.report, lambda: None, authorized_protocol_sha256=self.report["protocol"]["sha256"])
