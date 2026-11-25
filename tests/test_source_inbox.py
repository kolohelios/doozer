from concurrent.futures import ThreadPoolExecutor
from contextlib import redirect_stdout
import io
import json
from pathlib import Path
import sqlite3
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from scripts import source_inbox as inbox, workbench as wb


SOURCE = {"kind": "conversation", "text": "Count the lanterns twice.",
          "anchor": "fixture://lantern/thread/1", "scope": "inventory"}


def reconciliation(source_id="count-one", *, base_position=0, revision=0):
    claim = {"id": "claim-" + source_id, "text": SOURCE["text"], "scope": "inventory",
             "attribution": "expressed", "evidence": [{"source": source_id, "quote": SOURCE["text"]}]}
    return {"base_position": base_position, "batch": [source_id], "analysis": {"assertions": [claim]},
            "route": {"action": "analyze"}, "patch": {"baseRevision": revision, "rationale": "Record the instruction.",
            "operations": [{"op": "add", "assertion": claim}], "accounting": {
                source_id: {"mode": "represented", "claims": [claim["id"]], "reason": "Cited."}}}}


class SourceInboxTests(unittest.TestCase):
    def setUp(self):
        directory = TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.path = Path(directory.name) / "inbox.sqlite"

    def test_receipt_reopens_as_pending_and_redelivery_reuses_position(self):
        ack = inbox.receive(self.path, "count-one", SOURCE)
        self.assertEqual(ack, {"source_id": "count-one", "position": 1, "status": "received-pending"})
        self.assertEqual(inbox.receive(self.path, "count-one", dict(reversed(list(SOURCE.items())))), ack)
        state = inbox.snapshot(self.path)["state"]
        self.assertEqual(state["received"], {"count-one": SOURCE})
        self.assertEqual(wb.discover(state, "lanterns")["pending"], ["count-one"])
        self.assertEqual(state["processed"], [])
        self.assertEqual(state["journal"], [])
        self.assertEqual(state["revision"], 0)
        self.assertIn("unreconciled", wb.project(state)["handbook"])

    def test_discover_reads_committed_state_and_pending_coverage_without_refresh(self):
        inbox.receive(self.path, "count-one", SOURCE)
        inbox.refresh_projection(self.path)
        inbox.commit(self.path, "apply-one", **reconciliation())
        inbox.receive(self.path, "pending-note", {**SOURCE, "text": "Pending-only canary."})
        cached = inbox.projection(self.path)
        self.assertEqual(cached["status"], "behind")
        physical = self.path.read_bytes()
        with redirect_stdout(io.StringIO()) as output:
            self.assertEqual(inbox.main(["--db", str(self.path), "discover", "--query", "lanterns",
                                         "--scope", "inventory"]), 0)
        result = json.loads(output.getvalue())
        self.assertEqual(result["positions"], {"reconciliation": 1, "intake": 2})
        self.assertEqual(result["pending"], ["pending-note"])
        hit, = result["hits"]
        self.assertEqual(hit["claim"]["id"], "claim-count-one")
        self.assertEqual(hit["sources"], {"count-one": SOURCE["anchor"]})
        self.assertEqual(inbox.discover(self.path, "canary")["hits"], [])
        self.assertEqual(inbox.discover(self.path, "lanterns", find_scopes=True)["options"],
                         [{"scope": "inventory", "matched_claim_ids": ["claim-count-one"]}])
        self.assertEqual(inbox.discover(self.path, scope_history="inventory")["records"], [])
        self.assertEqual(inbox.projection(self.path), cached)
        self.assertEqual(self.path.read_bytes(), physical)

        inbox.restore(self.path, "undo-one", base_position=1,
                      request={"baseRevision": 1, "targetPosition": 0, "reason": "Restore before processing."})
        physical = self.path.read_bytes()
        with redirect_stdout(io.StringIO()) as output:
            self.assertEqual(inbox.main(["--db", str(self.path), "discover", "--scope-history", "inventory"]), 0)
        history = json.loads(output.getvalue())
        self.assertEqual(history["positions"], {"reconciliation": 2, "intake": 2})
        self.assertEqual(history["pending"], ["count-one", "pending-note"])
        record, = history["records"]
        self.assertEqual(record["historical"], hit["claim"])
        self.assertIsNone(record["current_reference"])
        self.assertEqual(inbox.discover(self.path, "lanterns", scope="inventory")["hits"], [])
        self.assertEqual(self.path.read_bytes(), physical)

    def test_conflicting_redelivery_never_overwrites(self):
        inbox.receive(self.path, "count-one", SOURCE)
        with self.assertRaisesRegex(ValueError, "different content"):
            inbox.receive(self.path, "count-one", {**SOURCE, "text": "Count once."})
        self.assertEqual(inbox.snapshot(self.path)["state"]["received"], {"count-one": SOURCE})
        self.assertEqual(inbox.receive(self.path, "count-two", SOURCE)["position"], 2)

    def test_process_exit_between_commit_and_ack_is_safe_to_redeliver(self):
        script = """
import json, os, sys
from scripts import source_inbox
source_inbox._sync_directory = lambda _: os._exit(91)
source_inbox.receive(sys.argv[1], 'count-one', json.loads(sys.argv[2]))
print('ack')
"""
        process = subprocess.run([sys.executable, "-c", script, str(self.path), json.dumps(SOURCE)],
                                 cwd=wb.ROOT, capture_output=True, timeout=15)
        self.assertEqual(process.returncode, 91, process.stderr.decode())
        self.assertEqual(process.stdout, b"")
        self.assertEqual(inbox.receive(self.path, "count-one", SOURCE)["position"], 1)
        self.assertEqual(inbox.snapshot(self.path)["state"]["received"], {"count-one": SOURCE})

    def test_commit_failure_returns_no_receipt_and_does_not_leave_a_row(self):
        inbox.receive(self.path, "count-one", SOURCE)
        connect = sqlite3.connect

        def fail_commit(*args, **kwargs):
            db = connect(*args, **kwargs)
            db.set_authorizer(lambda op, detail, *_: sqlite3.SQLITE_DENY
                              if op == sqlite3.SQLITE_TRANSACTION and detail == "COMMIT" else sqlite3.SQLITE_OK)
            return db

        with patch.object(sqlite3, "connect", side_effect=fail_commit), self.assertRaises(sqlite3.DatabaseError):
            inbox.receive(self.path, "count-two", SOURCE)
        self.assertEqual(inbox.snapshot(self.path)["state"]["received"], {"count-one": SOURCE})
        self.assertEqual(inbox.receive(self.path, "count-two", SOURCE)["position"], 2)

    def test_concurrent_local_redelivery_has_one_position(self):
        with ThreadPoolExecutor(max_workers=2) as pool:
            receipts = list(pool.map(lambda _: inbox.receive(self.path, "count-one", SOURCE), range(4)))
        self.assertEqual({r["position"] for r in receipts}, {1})
        self.assertEqual(inbox.snapshot(self.path)["state"]["received"], {"count-one": SOURCE})

    def test_invalid_input_creates_no_receipt(self):
        for key, value in (("Bad ID", SOURCE), ("count-one", {**SOURCE, "extra": "unknown"}),
                           ("count-one", {**SOURCE, "text": "x" * inbox.MAX_SOURCE_BYTES})):
            with self.assertRaises(ValueError):
                inbox.receive(self.path, key, value)
            self.assertFalse(self.path.exists())

    def test_reconciliation_persists_claims_and_pending_in_one_snapshot(self):
        received = inbox.receive(self.path, "count-one", SOURCE)
        inbox.receive(self.path, "count-two", SOURCE)
        request = reconciliation()
        ack = inbox.commit(self.path, "apply-one", **request)
        self.assertEqual(ack, {"operation_id": "apply-one", "position": 1, "revision": 1, "status": "committed-locally"})
        self.assertEqual(inbox.commit(self.path, "apply-one", **request), ack)
        self.assertEqual(inbox.receive(self.path, "count-one", SOURCE), received)
        saved = inbox.snapshot(self.path)
        state = saved["state"]
        self.assertEqual(saved["reconciliation_position"], 1)
        self.assertEqual(state["processed"], ["count-one"])
        self.assertEqual(len(state["journal"]), 1)
        self.assertEqual(state["history"], state["claims"])
        self.assertEqual(wb.discover(state, "lanterns")["pending"], ["count-two"])
        request["patch"]["rationale"] = "Changed request."
        with self.assertRaisesRegex(ValueError, "operation identity reused"):
            inbox.commit(self.path, "apply-one", **request)
        self.assertEqual(inbox.snapshot(self.path), saved)

    def test_guard_rejection_does_not_consume_operation_or_source(self):
        inbox.receive(self.path, "count-one", SOURCE)
        original = inbox.snapshot(self.path)
        invalid = reconciliation()
        invalid["patch"]["accounting"] = {}
        with self.assertRaisesRegex(ValueError, "unaccounted"):
            inbox.commit(self.path, "apply-one", **invalid)
        self.assertEqual(inbox.snapshot(self.path), original)
        self.assertEqual(inbox.commit(self.path, "apply-one", **reconciliation())["position"], 1)

    def test_failed_sql_commit_rolls_back_state_and_operation_receipt(self):
        inbox.receive(self.path, "count-one", SOURCE)
        original = inbox.snapshot(self.path)
        connect = sqlite3.connect

        def fail_commit(*args, **kwargs):
            db = connect(*args, **kwargs)
            db.set_authorizer(lambda op, detail, *_: sqlite3.SQLITE_DENY
                              if op == sqlite3.SQLITE_TRANSACTION and detail == "COMMIT" else sqlite3.SQLITE_OK)
            return db

        with patch.object(sqlite3, "connect", side_effect=fail_commit), self.assertRaises(sqlite3.DatabaseError):
            inbox.commit(self.path, "apply-one", **reconciliation())
        self.assertEqual(inbox.snapshot(self.path), original)
        self.assertEqual(inbox.commit(self.path, "apply-one", **reconciliation())["position"], 1)

    def test_process_exit_between_reconciliation_commit_and_ack_is_idempotent(self):
        inbox.receive(self.path, "count-one", SOURCE)
        request = reconciliation()
        script = """
import json, os, sys
from scripts import source_inbox
source_inbox._sync_directory = lambda _: os._exit(92)
source_inbox.commit(sys.argv[1], 'apply-one', **json.loads(sys.argv[2]))
print('ack')
"""
        process = subprocess.run([sys.executable, "-c", script, str(self.path), json.dumps(request)],
                                 cwd=wb.ROOT, capture_output=True, timeout=15)
        self.assertEqual(process.returncode, 92, process.stderr.decode())
        self.assertEqual(process.stdout, b"")
        self.assertEqual(inbox.commit(self.path, "apply-one", **request)["position"], 1)
        saved = inbox.snapshot(self.path)
        self.assertEqual(saved["state"]["processed"], ["count-one"])
        self.assertEqual(len(saved["state"]["journal"]), 1)

    def test_processing_only_commit_advances_position_and_fences_stale_work(self):
        for key in ("count-one", "count-two", "count-three"):
            inbox.receive(self.path, key, SOURCE)
        inbox.commit(self.path, "apply-one", **reconciliation())
        request = {"base_position": 1, "batch": ["count-two"], "analysis": {"assertions": [
            reconciliation()["analysis"]["assertions"][0]]}, "route": {"action": "analyze"},
            "patch": {"baseRevision": 1, "operations": [], "rationale": "Repeated evidence.", "accounting": {
                "count-two": {"mode": "dependent-no-op", "claims": ["claim-count-one"], "reason": "Already represented.",
                              "basis": [{"source": "count-one", "quote": SOURCE["text"]}]}}}}
        projected = inbox.refresh_projection(self.path)
        receipt = inbox.commit(self.path, "apply-two", **request)
        self.assertEqual((receipt["position"], receipt["revision"]), (2, 1))
        self.assertEqual(inbox.projection(self.path)["status"], "behind")
        refreshed = inbox.refresh_projection(self.path)
        self.assertEqual(refreshed["projection"]["revision"], projected["projection"]["revision"])
        self.assertEqual(refreshed["projected"], {"reconciliation": 2, "intake": 3})
        self.assertIn("2 of 3", refreshed["projection"]["handbook"])
        with self.assertRaisesRegex(ValueError, "stale reconciliation position"):
            inbox.commit(self.path, "apply-three", **reconciliation("count-three", base_position=1, revision=1))
        self.assertEqual(inbox.commit(self.path, "apply-one", **reconciliation())["position"], 1)
        self.assertEqual(inbox.snapshot(self.path)["state"]["processed"], ["count-one", "count-two"])

    def test_projection_catches_up_after_reopen_and_keeps_receipt_coverage(self):
        inbox.receive(self.path, "count-one", SOURCE)
        self.assertEqual(inbox.projection(self.path)["status"], "missing")
        initial = inbox.refresh_projection(self.path)
        self.assertEqual(initial["projected"], {"reconciliation": 0, "intake": 1})
        self.assertIn("0 of 1", initial["projection"]["handbook"])
        inbox.commit(self.path, "apply-one", **reconciliation())
        behind = inbox.projection(self.path)
        self.assertEqual(behind["status"], "behind")
        self.assertEqual(behind["available"], {"reconciliation": 1, "intake": 1})
        self.assertEqual(behind["projection"], initial["projection"])
        refreshed = inbox.refresh_projection(self.path)
        self.assertEqual(refreshed["status"], "caught-up")
        self.assertEqual(refreshed["projection"]["claims"], ["claim-count-one"])
        inbox.receive(self.path, "count-two", SOURCE)
        self.assertEqual(inbox.projection(self.path)["status"], "behind")
        again = inbox.refresh_projection(self.path)
        self.assertEqual(again["projected"], {"reconciliation": 1, "intake": 2})
        self.assertIn("1 of 2", again["projection"]["handbook"])
        self.assertIn("unreconciled", again["projection"]["handbook"])
        self.assertEqual(again["projection"]["revision"], 1)
        with patch.object(wb, "project", side_effect=AssertionError("must reuse caught-up projection")):
            self.assertEqual(inbox.refresh_projection(self.path), again)
        self.assertEqual(len(inbox.snapshot(self.path)["state"]["journal"]), 1)

    def test_failed_projection_transaction_preserves_previous_cache_and_cursor(self):
        inbox.receive(self.path, "count-one", SOURCE)
        old = inbox.refresh_projection(self.path)
        inbox.commit(self.path, "apply-one", **reconciliation())
        connect = sqlite3.connect

        def fail_commit(*args, **kwargs):
            db = connect(*args, **kwargs)
            db.set_authorizer(lambda op, detail, *_: sqlite3.SQLITE_DENY
                              if op == sqlite3.SQLITE_TRANSACTION and detail == "COMMIT" else sqlite3.SQLITE_OK)
            return db

        with patch.object(sqlite3, "connect", side_effect=fail_commit), self.assertRaises(sqlite3.DatabaseError):
            inbox.refresh_projection(self.path)
        behind = inbox.projection(self.path)
        self.assertEqual(behind["status"], "behind")
        self.assertEqual(behind["projected"], old["projected"])
        self.assertEqual(behind["projection"], old["projection"])
        self.assertEqual(inbox.refresh_projection(self.path)["status"], "caught-up")

    def test_durable_restore_keeps_history_and_rewinds_processing_not_receipt(self):
        inbox.receive(self.path, "count-one", SOURCE)
        inbox.commit(self.path, "apply-one", **reconciliation())
        inbox.receive(self.path, "count-two", SOURCE)
        before = inbox.snapshot(self.path)["state"]
        cached = inbox.refresh_projection(self.path)
        request = {"baseRevision": 1, "targetPosition": 0, "reason": "Undo the claim without losing its source."}
        receipt = inbox.restore(self.path, "undo-one", base_position=1, request=request)
        self.assertEqual(receipt, {"operation_id": "undo-one", "position": 2, "revision": 2, "status": "committed-locally"})
        self.assertEqual(inbox.restore(self.path, "undo-one", base_position=1, request=request), receipt)
        reopened = inbox.snapshot(self.path)
        state = reopened["state"]
        self.assertEqual(reopened["reconciliation_position"], 2)
        self.assertEqual(state["received"], before["received"])
        self.assertEqual(state["history"], before["history"])
        self.assertEqual(state["journal"][:-1], before["journal"])
        self.assertEqual(state["journal"][-1]["kind"], "restore")
        self.assertEqual(state["claims"], {})
        self.assertEqual(wb.discover(state, "lanterns")["pending"], ["count-one", "count-two"])
        self.assertEqual(inbox.projection(self.path)["status"], "behind")
        self.assertEqual(inbox.projection(self.path)["projection"], cached["projection"])
        refreshed = inbox.refresh_projection(self.path)
        self.assertEqual(refreshed["projected"], {"intake": 2, "reconciliation": 2})
        self.assertEqual(refreshed["projection"]["claims"], [])

    def test_restore_guards_leave_state_and_operation_identity_untouched(self):
        inbox.receive(self.path, "count-one", SOURCE)
        inbox.commit(self.path, "apply-one", **reconciliation())
        before = inbox.snapshot(self.path)
        request = {"baseRevision": 1, "targetPosition": 0, "reason": "Undo."}
        for base, operands, error in (
            (0, request, "stale reconciliation position"),
            (1, {**request, "baseRevision": 0}, "stale restore revision"),
            (1, {**request, "targetPosition": 2}, "invalid historical journal position"),
            (1, {**request, "targetPosition": 1}, "no state change"),
        ):
            with self.subTest(base=base, operands=operands), self.assertRaisesRegex(ValueError, error):
                inbox.restore(self.path, "undo-one", base_position=base, request=operands)
            self.assertEqual(inbox.snapshot(self.path), before)
        with self.assertRaisesRegex(ValueError, "operation identity reused"):
            inbox.restore(self.path, "apply-one", base_position=1, request=request)
        self.assertEqual(inbox.restore(self.path, "undo-one", base_position=1, request=request)["position"], 2)

    def test_restore_process_exit_before_ack_does_not_repeat_effect(self):
        inbox.receive(self.path, "count-one", SOURCE)
        inbox.commit(self.path, "apply-one", **reconciliation())
        envelope = {"base_position": 1, "request": {"baseRevision": 1, "targetPosition": 0, "reason": "Undo."}}
        script = """
import json, os, sys
from scripts import source_inbox
source_inbox._sync_directory = lambda _: os._exit(93)
source_inbox.restore(sys.argv[1], 'undo-one', **json.loads(sys.argv[2]))
print('ack')
"""
        process = subprocess.run([sys.executable, "-c", script, str(self.path), json.dumps(envelope)],
                                 cwd=wb.ROOT, capture_output=True, timeout=15)
        self.assertEqual(process.returncode, 93, process.stderr.decode())
        self.assertEqual(process.stdout, b"")
        request_path = self.path.with_name("restore.json")
        request_path.write_text(json.dumps(envelope))
        with redirect_stdout(io.StringIO()) as output:
            self.assertEqual(inbox.main(["--db", str(self.path), "restore", "--operation-id", "undo-one",
                                         "--request", str(request_path)]), 0)
        self.assertEqual(json.loads(output.getvalue())["position"], 2)
        self.assertEqual(len(inbox.snapshot(self.path)["state"]["journal"]), 2)

    def test_replay_after_restore_recovers_exact_material_and_invalidates_projection(self):
        inbox.receive(self.path, "count-one", SOURCE)
        original_receipt = inbox.commit(self.path, "apply-one", **reconciliation())
        original = inbox.snapshot(self.path)["state"]
        inbox.receive(self.path, "count-two", SOURCE)
        inbox.restore(self.path, "undo-one", base_position=1,
                      request={"baseRevision": 1, "targetPosition": 0, "reason": "Undo."})
        cached = inbox.refresh_projection(self.path)
        self.assertEqual(inbox.commit(self.path, "apply-one", **reconciliation()), original_receipt)
        self.assertEqual(inbox.snapshot(self.path)["state"]["processed"], [])
        envelope = {"base_position": 2, "journal_position": 0, "base_revision": 2}
        receipt = inbox.replay(self.path, "redo-one", **envelope)
        self.assertEqual(receipt, {"operation_id": "redo-one", "position": 3, "revision": 3, "status": "committed-locally"})
        self.assertEqual(inbox.replay(self.path, "redo-one", **envelope), receipt)
        state = inbox.snapshot(self.path)["state"]
        self.assertEqual(wb.material(state), wb.material(original))
        self.assertEqual(state["history"], original["history"])
        self.assertEqual(wb.discover(state, "lanterns")["pending"], ["count-two"])
        self.assertEqual(len(state["journal"]), 3)
        self.assertEqual(state["journal"][-1]["replayOf"], 0)
        self.assertEqual(inbox.projection(self.path)["status"], "behind")
        self.assertEqual(inbox.projection(self.path)["projection"], cached["projection"])
        self.assertEqual(inbox.refresh_projection(self.path)["projected"], {"intake": 2, "reconciliation": 3})

    def test_replay_guards_reject_stale_divergent_and_non_patch_targets(self):
        for key in ("count-one", "count-two"):
            inbox.receive(self.path, key, SOURCE)
        inbox.commit(self.path, "apply-one", **reconciliation())
        inbox.restore(self.path, "undo-one", base_position=1,
                      request={"baseRevision": 1, "targetPosition": 0, "reason": "Undo."})
        inbox.commit(self.path, "apply-two", **reconciliation("count-two", base_position=2, revision=2))
        divergent = inbox.snapshot(self.path)
        for base, target, revision, error in (
            (2, 0, 3, "stale reconciliation position"),
            (3, 0, 2, "stale replay revision"),
            (3, 1, 3, "not a restore event"),
            (3, 4, 3, "invalid historical journal position"),
            (3, 0, 3, "original material preconditions"),
        ):
            with self.subTest(target=target, error=error), self.assertRaisesRegex(ValueError, error):
                inbox.replay(self.path, "redo-one", base_position=base, journal_position=target, base_revision=revision)
            self.assertEqual(inbox.snapshot(self.path), divergent)
        inbox.restore(self.path, "undo-two", base_position=3,
                      request={"baseRevision": 3, "targetPosition": 0, "reason": "Return to the original prefix."})
        self.assertEqual(inbox.replay(self.path, "redo-one", base_position=4, journal_position=0, base_revision=4)["position"], 5)
        with self.assertRaisesRegex(ValueError, "operation identity reused"):
            inbox.replay(self.path, "redo-one", base_position=5, journal_position=0, base_revision=5)

    def test_replay_process_exit_before_ack_does_not_repeat_effect(self):
        inbox.receive(self.path, "count-one", SOURCE)
        inbox.commit(self.path, "apply-one", **reconciliation())
        inbox.restore(self.path, "undo-one", base_position=1,
                      request={"baseRevision": 1, "targetPosition": 0, "reason": "Undo."})
        envelope = {"base_position": 2, "journal_position": 0, "base_revision": 2}
        script = """
import json, os, sys
from scripts import source_inbox
source_inbox._sync_directory = lambda _: os._exit(94)
source_inbox.replay(sys.argv[1], 'redo-one', **json.loads(sys.argv[2]))
print('ack')
"""
        process = subprocess.run([sys.executable, "-c", script, str(self.path), json.dumps(envelope)],
                                 cwd=wb.ROOT, capture_output=True, timeout=15)
        self.assertEqual(process.returncode, 94, process.stderr.decode())
        self.assertEqual(process.stdout, b"")
        request_path = self.path.with_name("replay.json")
        request_path.write_text(json.dumps(envelope))
        with redirect_stdout(io.StringIO()) as output:
            self.assertEqual(inbox.main(["--db", str(self.path), "replay", "--operation-id", "redo-one",
                                         "--request", str(request_path)]), 0)
        self.assertEqual(json.loads(output.getvalue())["position"], 3)
        self.assertEqual(len(inbox.snapshot(self.path)["state"]["journal"]), 3)

    def test_durable_source_free_consolidation_preserves_history_and_replays(self):
        for key in ("count-one", "count-two", "count-three"):
            inbox.receive(self.path, key, SOURCE)
        inbox.commit(self.path, "apply-one", **reconciliation())
        inbox.commit(self.path, "apply-two", **reconciliation("count-two", base_position=1, revision=1))
        before = inbox.snapshot(self.path)["state"]
        inbox.refresh_projection(self.path)
        claim = {**before["claims"]["claim-count-one"], "id": "combined-count", "evidence": [
            c for old in before["claims"].values() for c in old["evidence"]]}
        patch_value = {"baseRevision": 2, "accounting": {}, "rationale": "Keep one scoped instruction.",
                       "operations": [{"op": "add", "assertion": claim}, *[
                           {"op": "retire", "id": key, "replacement": claim["id"], "reason": "Same scoped instruction."}
                           for key in before["claims"]]]}
        args = {"base_position": 2, "patch": patch_value, "analysis": {"assertions": [claim]}, "route": {"action": "analyze"}}
        receipt = inbox.maintain(self.path, "combine-counts", **args)
        self.assertEqual(inbox.maintain(self.path, "combine-counts", **args), receipt)
        after = inbox.snapshot(self.path)["state"]
        self.assertEqual(after["processed"], before["processed"])
        self.assertEqual(after["received"], before["received"])
        self.assertEqual(list(after["claims"]), ["combined-count"])
        for key, old in before["claims"].items():
            self.assertEqual(wb.resolve(after, key), claim)
            self.assertEqual(after["history"][key], old)
        self.assertEqual(inbox.explain(self.path, 3)["kind"], "maintenance")
        self.assertEqual(inbox.projection(self.path)["status"], "behind")
        inbox.restore(self.path, "undo-combine", base_position=3,
                      request={"baseRevision": 3, "targetPosition": 2, "reason": "Restore both earlier claims."})
        inbox.replay(self.path, "redo-combine", base_position=4, journal_position=2, base_revision=4)
        self.assertEqual(wb.material(inbox.snapshot(self.path)["state"]), wb.material(after))

    def test_source_free_no_change_and_pending_evidence_guard(self):
        inbox.receive(self.path, "count-one", SOURCE)
        inbox.commit(self.path, "apply-one", **reconciliation())
        inbox.receive(self.path, "count-two", SOURCE)
        before = inbox.snapshot(self.path)
        empty = {"base_position": 1, "patch": {"baseRevision": 1, "accounting": {}, "operations": [], "rationale": "Retain."},
                 "analysis": reconciliation()["analysis"], "route": {"action": "analyze"}}
        self.assertEqual(inbox.maintain(self.path, "maintenance-one", **empty)["status"], "no-change")
        self.assertEqual(inbox.snapshot(self.path), before)
        self.assertEqual(inbox.activity(self.path)["rejections"], [])
        invalid = reconciliation("count-two", base_position=1, revision=1)
        del invalid["batch"]
        invalid["patch"]["accounting"] = {}
        with self.assertRaisesRegex(ValueError, "unavailable source"):
            inbox.maintain(self.path, "maintenance-one", **invalid)
        self.assertEqual(inbox.snapshot(self.path), before)
        self.assertEqual(inbox.activity(self.path)["rejections"], [(1, "maintenance-one", 1)])
        pending = reconciliation("count-two", base_position=1, revision=1)
        self.assertEqual(inbox.commit(self.path, "maintenance-one", **pending)["position"], 2)

    def test_cli_snapshot_is_offline_and_exclusive(self):
        source_path = self.path.with_name("source.json")
        source_path.write_text(json.dumps(SOURCE))
        report_path = self.path.with_name("report.json")
        command = ["--db", str(self.path)]
        with patch("urllib.request.urlopen", side_effect=AssertionError("offline only")), redirect_stdout(io.StringIO()) as output:
            self.assertEqual(inbox.main([*command, "receive", "--source-id", "count-one", "--source", str(source_path)]), 0)
            self.assertEqual(json.loads(output.getvalue())["status"], "received-pending")
            request_path = self.path.with_name("request.json")
            request_path.write_text(json.dumps(reconciliation()))
            self.assertEqual(inbox.main([*command, "commit", "--operation-id", "apply-one", "--request", str(request_path)]), 0)
            self.assertEqual(inbox.main([*command, "snapshot", "--output", str(report_path)]), 0)
            with self.assertRaises(FileExistsError):
                inbox.main([*command, "snapshot", "--output", str(report_path)])
        self.assertEqual(json.loads(report_path.read_text()), inbox.snapshot(self.path))
