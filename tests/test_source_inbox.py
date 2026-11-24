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
