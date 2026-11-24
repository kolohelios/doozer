import copy
import json
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import Mock, patch

from scripts import maintenance_call as call, workbench as wb


class RevisionUpdateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with patch("urllib.request.urlopen", side_effect=AssertionError("offline only")):
            cls.prepared = call.prepare_revision()
        cls.frozen = cls.prepared["protocol"]["frozen"]

    def test_only_synthetic_evidence_is_sent_and_limits_are_fixed(self):
        payload = self.frozen["operation"]["payload"]
        context = json.loads(payload["messages"][1]["content"])
        self.assertEqual(set(context["sources"]), {"guide-one", "guide-two"})
        self.assertEqual(context["incoming"], ["guide-two"])
        self.assertEqual(self.frozen["limits"], {"budget_usd": 0.10, "max_calls": 1, "retries": 0})
        self.assertEqual(payload["max_tokens"], 4096)
        self.assertTrue(all(s["anchor"].startswith("fixture://") for s in context["sources"].values()))
        self.assertNotIn("Where can I recover", json.dumps(payload))
        self.assertLess(self.frozen["reservation_usd"], 0.10)

    def test_rehashed_checkpoint_cannot_substitute_evidence(self):
        report = copy.deepcopy(self.prepared)
        frozen = report["protocol"]["frozen"]
        checkpoint = frozen["checkpoint"]["protocol"]
        checkpoint["frozen"]["messages"][1]["content"] = "substitution"
        checkpoint["sha256"] = call.proposer.digest(checkpoint["frozen"])
        report["protocol"]["sha256"] = call.proposer.digest(frozen)
        with self.assertRaisesRegex(ValueError, "fixed fixture"):
            call.check(report)

    def test_existing_runner_applies_mock_native_patch_and_recovers(self):
        report = copy.deepcopy(self.prepared)
        claim = {"id": "ledger-procedure", "text": "Record completed counts in the shared ledger.",
                 "scope": "Revision 2", "attribution": "expressed",
                 "evidence": [{"source": "guide-two", "quote": "Dispatchers record completed inventory counts in the shared ledger."}]}
        proposal = {"baseRevision": 1, "accounting": {"guide-two": {"mode": "represented", "claims": [claim["id"]], "reason": "Cited."}},
                    "operations": [{"op": "add", "assertion": claim}], "rationale": "Mock response; not a semantic verdict."}
        sender = Mock(return_value={"model": "openai/gpt-4.1", "provider": "OpenAI", "choices": [{"finish_reason": "stop", "message": {"content": json.dumps(proposal)}}],
                                    "usage": {"cost": 0.001, "prompt_tokens": 800, "completion_tokens": 200}})
        with TemporaryDirectory() as directory, patch.dict("os.environ", {"OPENROUTER_API_KEY": "offline-test-token"}):
            call.run(report, lambda: None, sender=sender, receipt_directory=directory, authorized_protocol_sha256=report["protocol"]["sha256"])
        self.assertEqual(sender.call_count, 1)
        result = report["inspection"]
        self.assertEqual(result["proposal"], proposal)
        self.assertEqual(result["state"]["processed"], ["guide-one", "guide-two"])
        self.assertIsNotNone(wb.resolve(result["state"], "marker-procedure"))
        self.assertEqual(result["recovery"]["status"], "exercised")
        self.assertFalse(result["canonical_acceptance"])
        self.assertEqual(result["semantic_judgment"], "pending-human-review")
