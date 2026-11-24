import copy
import json
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import Mock, patch

from scripts import maintenance_call as call, standards_maintenance as batch, workbench as wb


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
        self.assertEqual(context["new_claim_slots"], ["new-1", "new-2", "new-3", "new-4"])
        self.assertEqual([claim["id"] for claim in context["current_claims"]], ["existing-1"])
        for private in ("marker-procedure", "claim-slot-", "claim_refs"):
            self.assertNotIn(private, json.dumps(payload))
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

    def test_plain_language_rules_are_in_the_system_message_only(self):
        system, user = self.frozen["operation"]["payload"]["messages"]
        for phrase in ("not claim IDs", "claim that survives", "not the incoming source", "every source cited", "add-only patch is allowed"):
            self.assertIn(phrase, system["content"])
        self.assertNotIn("Patch rules", user["content"])
        self.assertNotIn("No prescribed graph layout", system["content"])

    def candidate(self):
        claim = {"id": "new-1", "text": "Record completed counts in the shared ledger.",
                 "scope": "Revision 2", "attribution": "expressed",
                 "evidence": [{"source": "guide-two", "quote": "Dispatchers record completed inventory counts in the shared ledger."}]}
        return {"baseRevision": 1, "accounting": {"guide-two": {"mode": "represented", "claims": [claim["id"]], "reason": "Cited."}},
                "operations": [{"op": "add", "assertion": claim}], "rationale": "Mock response; not a semantic verdict."}

    def test_plain_language_rules_match_existing_patch_gate(self):
        checkpoint = self.frozen["checkpoint"]
        def inspect(value):
            return call.batch.inspect_proposal(checkpoint, json.dumps(value).encode())

        patch_value = self.candidate()
        self.assertEqual(inspect(patch_value)["status"], "applied-in-isolated-copy")
        retired = {"op": "retire", "id": "existing-1", "replacement": "new-1", "reason": "Test source paths."}
        for defect, expected in (("claim-key", "incoming source"), ("empty-claims", "#Patch contract"),
                                 ("incoming-basis", "unavailable source"), ("empty-replacement", "#Patch contract"),
                                 ("lost-source", "source discovery paths")):
            with self.subTest(defect=defect):
                bad = copy.deepcopy(patch_value)
                account = bad["accounting"]["guide-two"]
                if defect == "claim-key":
                    bad["accounting"] = {"ledger-procedure": account}
                elif defect == "empty-claims":
                    account["claims"] = []
                elif defect == "incoming-basis":
                    account.update(mode="dependent-no-op", basis=bad["operations"][0]["assertion"]["evidence"])
                else:
                    bad["operations"].append({**retired, "replacement": ""} if defect == "empty-replacement" else retired)
                result = inspect(bad)
                self.assertEqual(result["status"], "rejected-not-applied")
                self.assertIn(expected, result["failure"]["detail"])
                self.assertEqual(result["state"], checkpoint["protocol"]["frozen"]["before"])
        replacement = patch_value["operations"][0]["assertion"]
        replacement["evidence"].extend(checkpoint["protocol"]["frozen"]["before"]["claims"]["marker-procedure"]["evidence"])
        patch_value["operations"].append(retired)
        result = inspect(patch_value)
        self.assertEqual(result["status"], "applied-in-isolated-copy")
        self.assertEqual(wb.resolve(result["state"], "marker-procedure")["id"], "claim-slot-1")
        self.assertEqual(result["lowered_patch"]["operations"][1]["replacement"], "claim-slot-1")
        self.assertEqual(result["state"]["history"]["marker-procedure"],
                         checkpoint["protocol"]["frozen"]["before"]["history"]["marker-procedure"])
        self.assertEqual(result["semantic_judgment"], "pending-human-review")

    def test_allocation_skips_active_historical_and_redirect_ids(self):
        state = {"claims": {"claim-slot-1": {}}, "history": {"claim-slot-2": {}},
                 "redirects": {"claim-slot-3": "claim-slot-4"}}
        original = copy.deepcopy(state)
        expected = {"existing": {"existing-1": "claim-slot-1"},
                    "new": {"new-1": "claim-slot-5", "new-2": "claim-slot-6"}}
        self.assertEqual(batch.claim_references(state, slots=2), expected)
        self.assertEqual(state, original)

    def test_invalid_reference_operands_reject_without_lowering_or_state_change(self):
        checkpoint = self.frozen["checkpoint"]
        before = checkpoint["protocol"]["frozen"]["before"]
        for defect in ("existing-add", "persistent-add", "duplicate", "unused-accounting", "unused-replacement", "new-retirement"):
            with self.subTest(defect=defect):
                candidate = self.candidate()
                op, = candidate["operations"]
                if defect in ("existing-add", "persistent-add"):
                    op["assertion"]["id"] = "existing-1" if defect == "existing-add" else "claim-slot-1"
                elif defect == "duplicate":
                    candidate["operations"].append(copy.deepcopy(op))
                elif defect == "unused-accounting":
                    candidate["accounting"]["guide-two"]["claims"] = ["new-2"]
                else:
                    candidate["operations"].append({"op": "retire", "id": "existing-1" if defect == "unused-replacement" else "new-1",
                                                    "replacement": "new-2" if defect == "unused-replacement" else "existing-1", "reason": "Invalid operand."})
                raw = json.dumps(candidate).encode()
                result = batch.inspect_proposal(checkpoint, raw)
                self.assertEqual(result["status"], "rejected-not-applied")
                self.assertEqual(result["proposal"], candidate)
                self.assertEqual(result["state"], before)
                self.assertNotIn("lowered_patch", result)

    def test_existing_runner_applies_mock_native_patch_and_recovers(self):
        report = copy.deepcopy(self.prepared)
        proposal = self.candidate()
        sender = Mock(return_value={"model": "openai/gpt-4.1", "provider": "OpenAI", "choices": [{"finish_reason": "stop", "message": {"content": json.dumps(proposal)}}],
                                    "usage": {"cost": 0.001, "prompt_tokens": 800, "completion_tokens": 200}})
        with TemporaryDirectory() as directory, patch.dict("os.environ", {"OPENROUTER_API_KEY": "offline-test-token"}):
            call.run(report, lambda: None, sender=sender, receipt_directory=directory, authorized_protocol_sha256=report["protocol"]["sha256"])
        self.assertEqual(sender.call_count, 1)
        result = report["inspection"]
        self.assertEqual(result["proposal"], proposal)
        expected = copy.deepcopy(proposal)
        expected["operations"][0]["assertion"]["id"] = "claim-slot-1"
        expected["accounting"]["guide-two"]["claims"] = ["claim-slot-1"]
        self.assertEqual(result["lowered_patch"], expected)
        self.assertEqual(result["state"]["journal"][-1]["patch"], expected)
        self.assertEqual(result["state"]["processed"], ["guide-one", "guide-two"])
        self.assertIsNotNone(wb.resolve(result["state"], "marker-procedure"))
        self.assertEqual(result["recovery"]["status"], "exercised")
        self.assertFalse(result["canonical_acceptance"])
        self.assertEqual(result["semantic_judgment"], "pending-human-review")
