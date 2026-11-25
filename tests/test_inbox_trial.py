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
            self.assertEqual(overlap["status"], "complete")
            self.assertEqual(overlap["matching_pairs"], expected)
            self.assertEqual(snapshot, before)
            if append_only:
                self.assertEqual(snapshot, previous["checkpoint"]["snapshot"])
                self.assertEqual(context, json.loads(previous["operation"]["payload"]["messages"][1]["content"]))
                by_ref = prepared["claim_refs"]["existing"]
                self.assertEqual({by_ref[ref] for ref in overlap["pairs"][0]["claims"]},
                                 {"notification-exception", "retry-safety-scoped"})

    def test_rehashed_substitution_cannot_use_trial_route(self):
        with TemporaryDirectory() as directory:
            report = call.prepare_inbox(Path(directory) / "trial.sqlite")
        modified = copy.deepcopy(report)
        frozen = modified["protocol"]["frozen"]
        frozen["checkpoint"]["prepared"]["preparation"]["messages"][1]["content"] = "different evidence"
        modified["protocol"]["sha256"] = call.proposer.digest(frozen)
        with self.assertRaisesRegex(ValueError, "fixed synthetic checkpoint"):
            call.check(modified)
