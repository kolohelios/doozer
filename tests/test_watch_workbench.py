from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from scripts import source_inbox as inbox, watch_workbench as watch


class WatchWorkbenchTests(unittest.TestCase):
    def test_playback_shows_real_receipts_commits_and_projection_diffs(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "watch.sqlite"
            lines, pauses = [], []
            with patch("urllib.request.urlopen", side_effect=AssertionError("offline only")):
                status = watch.play(path, emit=lines.append, pause=lambda: pauses.append(len(lines)))
            snapshot = inbox.snapshot(path)
            projection = inbox.projection(path)
        self.assertEqual(status, 0)
        self.assertEqual(len(pauses), 7)
        commits = [line.strip() for line in lines if line.startswith("  Committed")]
        self.assertEqual(len(commits), len(snapshot["state"]["journal"]))
        for position, (line, record) in enumerate(zip(commits, snapshot["state"]["journal"]), 1):
            self.assertEqual(line, f"Committed · position {position}, revision {record['revision']}")
        self.assertTrue(any(line.startswith("  Received · no #") and line.endswith('"No."') for line in lines))
        self.assertIn("  Pending   · incident", lines)
        self.assertIn("  No commit · receipt only", lines)
        self.assertIn("  No commit · batch already processed", lines)
        self.assertTrue(any(line.startswith("  Redelivery · incident #") for line in lines))
        self.assertTrue(any(line.startswith("    +") and "automatic-retr" in line for line in lines))
        self.assertTrue(any(line.startswith("    -") and "fixture://" in line for line in lines))
        self.assertEqual(projection["status"], "caught-up")

    def test_rejected_commit_is_not_reported_as_applied(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "watch.sqlite"
            lines = []
            with patch.object(inbox, "commit", side_effect=ValueError("test rejection")):
                self.assertEqual(watch.play(path, emit=lines.append), 2)
            snapshot = inbox.snapshot(path)
        self.assertTrue(any(line.startswith("  Proposed") for line in lines))
        self.assertIn("  Rejected  · test rejection", lines)
        self.assertFalse(any(line.startswith(("  Committed", "  Refreshed", "\nComplete")) for line in lines))
        self.assertEqual(set(snapshot["state"]["received"]), {"guide", "retry"})
        self.assertEqual(snapshot["reconciliation_position"], 0)
