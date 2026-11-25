import copy
import gzip
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import Mock, patch

from scripts import maintenance_call as call, maintenance_handoff as handoff, source_inbox as inbox
from scripts import maintenance_proposer as proposer, workbench as wb


class InboxTrialTests(unittest.TestCase):
    def test_durable_seed_and_mock_response_leave_database_unchanged(self):
        with TemporaryDirectory() as directory:
            db = Path(directory) / "trial.sqlite"
            with patch("urllib.request.urlopen", side_effect=AssertionError("offline only")):
                report = call.prepare_inbox(db)
            before = inbox.snapshot(db)
            frozen = report["protocol"]["frozen"]
            self.assertEqual(len(before["state"]["claims"]), 6)
            self.assertEqual(frozen["checkpoint"]["snapshot"]["state"], before["state"])
            self.assertEqual(frozen["limits"], {"budget_usd": 0.10, "max_calls": 1, "retries": 0})
            payload = frozen["operation"]["payload"]
            self.assertEqual(payload["messages"], frozen["checkpoint"]["prepared"]["preparation"]["messages"])
            context = json.loads(payload["messages"][1]["content"])
            self.assertEqual(context["pending_count"], 0)
            self.assertTrue(context["sources"])
            self.assertTrue(all(source["anchor"].startswith("fixture://") for source in context["sources"].values()))
            self.assertNotIn("claim_refs", json.dumps(payload))
            self.assertNotIn("journal", context)
            self.assertNotIn("accounting", payload["messages"][0]["content"])
            patched = {"baseRevision": before["state"]["revision"],
                       "operations": [], "rationale": "Synthetic no-op response."}
            sender = Mock(return_value={"model": "openai/gpt-4.1", "provider": "OpenAI",
                                       "choices": [{"finish_reason": "stop", "message": {"content": json.dumps(patched)}}],
                                       "usage": {"cost": 0.001, "prompt_tokens": 900, "completion_tokens": 100}})
            with patch.dict("os.environ", {"OPENROUTER_API_KEY": "offline-test-token"}):
                call.run(report, lambda: None, authorized_protocol_sha256=report["protocol"]["sha256"],
                         sender=sender, receipt_directory=directory)
            self.assertEqual(sender.call_count, 1)
            self.assertEqual(report["inspection"]["status"], "no-change-in-isolated-copy")
            inspection = report["inspection"]["inspection"]
            self.assertEqual(inspection["scope_impact"]["lost_active_scopes"], [])
            self.assertEqual(inspection["scope_impact"]["added_active_scopes"], [])
            self.assertEqual(inspection["recovery"], {"status": "not-exercised-no-change"})
            self.assertEqual(inspection["proposal"], patched)
            self.assertEqual(inspection["request"]["patch"], {**patched, "accounting": {}})
            self.assertEqual(inbox.snapshot(db), before)
            self.assertFalse(report["canonical_acceptance"])

    def test_overlap_adds_only_comparison_metadata_to_the_same_checkpoint(self):
        archive = wb.ROOT / "experiments/workbench/results/second-inbox-maintenance.json.gz"
        previous = json.loads(gzip.decompress(archive.read_bytes()))["protocol"]["frozen"]
        for append_only, expected in ((False, 1), (True, 7)):
            state = proposer.prepare(append_only=append_only)["protocol"]["frozen"]["before"]
            snapshot = {"state": state, "reconciliation_position": len(state["journal"])}
            before = copy.deepcopy(snapshot)
            prepared = handoff.prepare_snapshot(snapshot)["preparation"]
            context = json.loads(prepared["messages"][1]["content"])
            overlap = context.pop("evidence_overlap")
            reply_context = context.pop("reply_context")
            self.assertEqual(overlap["status"], "complete")
            self.assertEqual(overlap["matching_pairs"], expected)
            self.assertEqual(snapshot, before)
            if append_only:
                self.assertEqual(snapshot, previous["checkpoint"]["snapshot"])
                self.assertEqual(context, json.loads(previous["operation"]["payload"]["messages"][1]["content"]))
                self.assertTrue(reply_context.keys().isdisjoint(context["sources"]))
                self.assertIn("proposal", context["sources"])
                by_ref = prepared["claim_refs"]["existing"]
                self.assertEqual({by_ref[ref] for ref in overlap["pairs"][0]["claims"]},
                                 {"notification-exception", "retry-safety-scoped"})

    def test_closure_case_keeps_authored_control_outside_the_frozen_request(self):
        with TemporaryDirectory() as directory:
            db = Path(directory) / "closure.sqlite"
            with patch("urllib.request.urlopen", side_effect=AssertionError("offline only")):
                report = call.prepare_inbox(db, "closure")
            frozen = call.check(report)
            self.assertEqual(frozen["operation"]["sample"], "synthetic-inbox-closure")
            prepared = frozen["checkpoint"]["prepared"]["preparation"]
            payload = frozen["operation"]["payload"]
            self.assertEqual(payload["messages"], prepared["messages"])
            context = json.loads(payload["messages"][1]["content"])
            self.assertEqual(len(context["current_claims"]), 3)
            self.assertEqual(set(context["sources"]), {"note", "west"})
            self.assertEqual(context["evidence_overlap"]["matching_pairs"], 1)
            refs = {key: ref for ref, key in prepared["claim_refs"]["existing"].items()}
            merged = {**context["current_claims"][0], "id": "new-1",
                      "text": "At evening closure, latch the vent and leave the circulation fan running."}
            proposal = {"baseRevision": context["current_revision"], "rationale": "Authored comparison only.",
                        "operations": [{"op": "add", "assertion": merged}, *[
                            {"op": "retire", "id": refs[key], "replacement": "new-1", "reason": "Combine the east instructions."}
                            for key in ("east-fan", "east-vent")]]}
            self.assertNotIn(merged["text"], json.dumps(payload))
            before = inbox.snapshot(db)["state"]
            physical = db.read_bytes()
            inspected = call.inbox_trial.inspect(frozen["checkpoint"], json.dumps(proposal).encode())
            self.assertEqual(inspected["status"], "applicable-in-isolated-copy")
            self.assertEqual(inspected["inspection"]["scope_impact"]["lost_active_scopes"], [])
            recovery = {"status": "exercised-in-isolated-copy", "target_prefix": 1, "replayed_position": 2}
            self.assertEqual(inspected["inspection"]["recovery"], recovery)
            inverted = copy.deepcopy(proposal)
            inverted["operations"][0]["assertion"]["text"] = "At evening closure, latch the vent and turn the circulation fan off."
            counterexample = call.inbox_trial.inspect(frozen["checkpoint"], json.dumps(inverted).encode())
            self.assertEqual(counterexample["inspection"]["recovery"], recovery)
            self.assertEqual(counterexample["semantic_judgment"], "not-evaluated")
            self.assertEqual(db.read_bytes(), physical)
            handoff.apply(db, "authored-control", inspected, inspection_sha256=inspected["inspection_sha256"])
            after = inbox.snapshot(db)["state"]
            self.assertEqual(after["claims"]["west-fan"], before["claims"]["west-fan"])
            east = inbox.discover(db, "vent fan", scope="east greenhouse evening closure")["hits"]
            self.assertEqual([hit["claim"]["text"] for hit in east], [merged["text"]])
            for key in ("east-fan", "east-vent"):
                self.assertEqual(wb.resolve(after, key)["text"], merged["text"])
                self.assertEqual(after["history"][key], before["claims"][key])
            self.assertEqual(after["received"], before["received"])
            receipt = inbox.restore(db, "undo-control", base_position=2,
                                    request={"targetPosition": 1, "baseRevision": after["revision"], "reason": "Exercise recovery."})
            self.assertEqual(wb.material(inbox.snapshot(db)["state"]), wb.material(before))
            inbox.replay(db, "redo-control", base_position=3, journal_position=1, base_revision=receipt["revision"])
            self.assertEqual(wb.material(inbox.snapshot(db)["state"]), wb.material(after))
            with self.assertRaisesRegex(ValueError, "fixed synthetic checkpoint"):
                call.operation(frozen["checkpoint"], call.inbox_plan("retry"))

    def test_rehashed_substitution_cannot_use_trial_route(self):
        with TemporaryDirectory() as directory:
            report = call.prepare_inbox(Path(directory) / "trial.sqlite")
        modified = copy.deepcopy(report)
        frozen = modified["protocol"]["frozen"]
        frozen["checkpoint"]["prepared"]["preparation"]["messages"][1]["content"] = "different evidence"
        modified["protocol"]["sha256"] = call.proposer.digest(frozen)
        with self.assertRaisesRegex(ValueError, "fixed synthetic checkpoint"):
            call.check(modified)
