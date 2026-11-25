import copy
import gzip
import hashlib
import json
from contextlib import redirect_stdout
import io
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import Mock, patch

from scripts import maintenance_call as call, maintenance_handoff as handoff, source_inbox as inbox
from scripts import maintenance_proposer as proposer, watch_workbench as watch, workbench as wb


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
            east_scope = merged["scope"]
            comparison_query = "circulation fan"
            counterexample = handoff.inspect(db, json.dumps(inverted).encode(), prepared=frozen["checkpoint"]["prepared"],
                                             query=comparison_query, scope=east_scope)
            self.assertEqual(counterexample["inspection"]["recovery"], recovery)
            self.assertEqual(counterexample["semantic_judgment"], "not-evaluated")
            comparison = counterexample["inspection"]["reader_comparison"]
            self.assertEqual(comparison["exact_scope"], east_scope)
            self.assertEqual([hit["claim"]["id"] for hit in comparison["before"]["hits"]], ["east-fan"])
            bad_hit, = comparison["after"]["hits"]
            self.assertIn("fan off", bad_hit["claim"]["text"])
            self.assertEqual(bad_hit["sources"], {"note": context["sources"]["note"]["anchor"]})
            self.assertIn("leave the circulation fan running", bad_hit["claim"]["evidence"][0]["quote"])
            self.assertNotIn(json.dumps(comparison_query), payload["messages"][1]["content"])
            self.assertEqual(db.read_bytes(), physical)
            handoff.apply(db, "authored-control", inspected, inspection_sha256=inspected["inspection_sha256"])
            after = inbox.snapshot(db)["state"]
            self.assertEqual(after["claims"]["west-fan"], before["claims"]["west-fan"])
            with redirect_stdout(io.StringIO()) as output:
                self.assertEqual(inbox.main(["--db", str(db), "source-usage", "--source-id", "note"]), 0)
            usage = json.loads(output.getvalue())
            self.assertEqual(usage["status"], "processed")
            self.assertEqual(usage["anchor"], context["sources"]["note"]["anchor"])
            self.assertEqual([row["id"] for row in usage["active"]], ["claim-slot-1"])
            self.assertEqual([row["id"] for row in usage["historical"]], ["east-fan", "east-vent"])
            earlier = inbox.source_usage(db, "note", at_position=1)
            self.assertEqual([row["id"] for row in earlier["active"]], ["east-fan", "east-vent"])
            self.assertEqual(earlier["historical"], [])
            east = inbox.discover(db, "vent fan", scope="east greenhouse evening closure")["hits"]
            self.assertEqual([hit["claim"]["text"] for hit in east], [merged["text"]])
            west = inbox.discover(db, "circulation fan", scope="west greenhouse evening closure")["hits"]
            self.assertEqual([hit["claim"]["id"] for hit in west], ["west-fan"])
            self.assertIn("turn the circulation fan off", west[0]["claim"]["evidence"][0]["quote"])
            self.assertEqual(inbox.evidence(db, east[0]["claim"]["id"])["citations"][0]["quote"],
                             context["sources"]["note"]["text"])
            for key in ("east-fan", "east-vent"):
                self.assertEqual(wb.resolve(after, key)["text"], merged["text"])
                self.assertEqual(after["history"][key], before["claims"][key])
            self.assertEqual(after["received"], before["received"])
            receipt = inbox.restore(db, "undo-control", base_position=2,
                                    request={"targetPosition": 1, "baseRevision": after["revision"], "reason": "Exercise recovery."})
            self.assertEqual(wb.material(inbox.snapshot(db)["state"]), wb.material(before))
            inbox.replay(db, "redo-control", base_position=3, journal_position=1, base_revision=receipt["revision"])
            self.assertEqual(wb.material(inbox.snapshot(db)["state"]), wb.material(after))
            events = []
            watch.poll(db, emit=events.append)
            for label, position, operation in (("Maintained", 2, "authored-control"), ("Restored", 3, "undo-control"),
                                               ("Replayed", 4, "redo-control")):
                self.assertTrue(any(line.startswith(label) and f"reconciliation {position}," in line and line.endswith(operation)
                                    for line in events))
            with self.assertRaisesRegex(ValueError, "fixed synthetic checkpoint"):
                call.operation(frozen["checkpoint"], call.inbox_plan("retry"))

    def test_browse_closure_scopes_without_a_query(self):
        with TemporaryDirectory() as directory:
            db = Path(directory) / "closure.sqlite"
            call.inbox_trial.seed(db, "closure")
            inbox.receive(db, "pending", {"kind": "conversation", "text": "Pending canary.",
                                          "anchor": "fixture://greenhouse/pending", "scope": "east greenhouse evening closure"})
            physical = db.read_bytes()
            east = "east greenhouse evening closure"
            with redirect_stdout(io.StringIO()) as output:
                self.assertEqual(inbox.main(["--db", str(db), "browse", "--scope", east]), 0)
            view = json.loads(output.getvalue())
            self.assertEqual([claim["id"] for claim in view["claims"]], ["east-fan", "east-vent"])
            self.assertEqual(view["source_anchors"], {"note": "fixture://greenhouse/closing-note"})
            self.assertEqual(view["pending"], ["pending"])
            self.assertNotIn("Pending canary.", output.getvalue())
            west = inbox.browse(db, "west greenhouse evening closure")
            self.assertEqual([claim["id"] for claim in west["claims"]], ["west-fan"])
            self.assertEqual(inbox.browse(db, "greenhouse")["status"], "no-matching-knowledge")
            self.assertEqual(inbox.browse(db, east, at_position=0)["claims"], [])
            self.assertIsNone(inbox.browse(db, east, at_position=1)["pending"])
            self.assertEqual(db.read_bytes(), physical)

    def test_saved_closure_response_reproduces_no_change_offline(self):
        artifact = wb.ROOT / "experiments/workbench/results/first-inbox-closure.json"
        raw = artifact.read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(),
                         "81988c901545993d9a20fd5f2a5ed851a5a51d80b7d55d40a51a268034bd66cb")
        result = json.loads(raw)
        self.assertEqual((result["attempts"], result["known_cost_usd"], result["unknown_billing"]), (1, 0.003128, 0))
        checkpoint = call.inbox_trial.checkpoint(call.inbox_trial.reference_snapshot("closure"))
        inspected = call.inbox_trial.inspect(checkpoint, result["response_content"].encode())
        self.assertEqual(inspected["status"], result["proposal_status"])
        self.assertEqual(inspected["semantic_judgment"], "not-evaluated")
        self.assertEqual(inspected["inspection"]["before"], inspected["inspection"]["after"])
        self.assertFalse(inspected["inspection"]["changed"])

    def test_rehashed_substitution_cannot_use_trial_route(self):
        with TemporaryDirectory() as directory:
            report = call.prepare_inbox(Path(directory) / "trial.sqlite")
        modified = copy.deepcopy(report)
        frozen = modified["protocol"]["frozen"]
        frozen["checkpoint"]["prepared"]["preparation"]["messages"][1]["content"] = "different evidence"
        modified["protocol"]["sha256"] = call.proposer.digest(frozen)
        with self.assertRaisesRegex(ValueError, "fixed synthetic checkpoint"):
            call.check(modified)
