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

    def test_cli_snapshot_is_offline_and_exclusive(self):
        source_path = self.path.with_name("source.json")
        source_path.write_text(json.dumps(SOURCE))
        report_path = self.path.with_name("report.json")
        command = ["--db", str(self.path)]
        with patch("urllib.request.urlopen", side_effect=AssertionError("offline only")), redirect_stdout(io.StringIO()) as output:
            self.assertEqual(inbox.main([*command, "receive", "--source-id", "count-one", "--source", str(source_path)]), 0)
            self.assertEqual(json.loads(output.getvalue())["status"], "received-pending")
            self.assertEqual(inbox.main([*command, "snapshot", "--output", str(report_path)]), 0)
            with self.assertRaises(FileExistsError):
                inbox.main([*command, "snapshot", "--output", str(report_path)])
        self.assertEqual(json.loads(report_path.read_text()), inbox.snapshot(self.path))
