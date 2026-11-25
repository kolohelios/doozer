from contextlib import redirect_stdout
import io
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from scripts import recorded_dispatch as driver, source_inbox as inbox, workbench as wb
from scripts.workbench_models import RecordedBackend


class RecordedDispatchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        corpus = wb.export_cue(sorted((wb.ROOT / "corpus").glob("*.cue")))
        cls.fixture = wb.run(corpus["scenarios"]["retry-safety"], RecordedBackend())["state"]

    def setUp(self):
        directory = TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.path = Path(directory.name) / "inbox.sqlite"

    def receive(self, key):
        inbox.receive(self.path, key, self.fixture["received"][key])

    def test_wait_for_missing_sources_without_advancing(self):
        self.receive("retry")
        before = inbox.snapshot(self.path)
        result = driver.advance(self.path)
        self.assertEqual(result, {"status": "waiting-for-sources", "position": 0, "missing": ["guide"], "network_calls": 0})
        self.assertEqual(inbox.snapshot(self.path), before)
        self.receive("guide")
        self.assertEqual(driver.advance(self.path)["receipt"]["position"], 1)
        self.assertEqual(driver.advance(self.path)["status"], "waiting-for-sources")

    def test_one_step_per_call_and_full_prefix_matches_after_reopen(self):
        for key in reversed(list(self.fixture["received"])):
            self.receive(key)
        inbox.refresh_projection(self.path)
        with patch("urllib.request.urlopen", side_effect=AssertionError("offline only")):
            for position in range(1, len(self.fixture["journal"]) + 1):
                self.assertEqual(driver.advance(self.path)["receipt"]["position"], position)
                self.assertEqual(inbox.snapshot(self.path)["state"]["journal"], self.fixture["journal"][:position])
            self.assertEqual(driver.advance(self.path)["status"], "complete")
        self.assertEqual(inbox.snapshot(self.path)["state"], self.fixture)
        self.assertEqual(inbox.projection(self.path)["status"], "behind")
        self.assertEqual(inbox.refresh_projection(self.path)["status"], "caught-up")

    def test_drain_stops_at_missing_evidence_and_streams_committed_positions(self):
        for key in ("retry", "guide"):
            self.receive(key)
        with redirect_stdout(io.StringIO()) as stdout:
            self.assertEqual(driver.main(["--db", str(self.path), "--max-steps", "3"]), 0)
        receipt, summary = map(json.loads, stdout.getvalue().splitlines())
        self.assertEqual(receipt["receipt"]["position"], 1)
        self.assertEqual(summary["status"], "waiting-for-sources")
        self.assertEqual(summary["committed_steps"], 1)
        self.assertTrue(summary["missing"])
        self.assertEqual(inbox.snapshot(self.path)["reconciliation_position"], 1)

    def test_bounded_drain_recovers_if_reporting_stops_after_commit(self):
        for key in reversed(list(self.fixture["received"])):
            self.receive(key)
        with self.assertRaisesRegex(ValueError, "positive integer"):
            driver.drain(self.path, max_steps=True)
        result = driver.drain(self.path, max_steps=1)
        self.assertEqual(result, {"status": "step-limit", "position": 1, "committed_steps": 1, "network_calls": 0})

        def interrupted(receipt):
            self.assertEqual(inbox.snapshot(self.path)["reconciliation_position"], receipt["position"])
            raise OSError("reporting sink stopped")

        with self.assertRaisesRegex(OSError, "reporting sink stopped"):
            driver.drain(self.path, max_steps=6, on_commit=interrupted)
        self.assertEqual(inbox.snapshot(self.path)["reconciliation_position"], 2)
        reported = []
        with patch("urllib.request.urlopen", side_effect=AssertionError("offline only")):
            result = driver.drain(self.path, max_steps=6, on_commit=reported.append)
        last = len(self.fixture["journal"])
        self.assertEqual(result, {"status": "complete", "position": last, "committed_steps": last - 2, "network_calls": 0})
        self.assertEqual([row["position"] for row in reported], list(range(3, last + 1)))
        self.assertEqual(inbox.snapshot(self.path)["state"], self.fixture)
        self.assertEqual(driver.drain(self.path, max_steps=1)["committed_steps"], 0)

    def test_projection_catches_up_after_drain_finished_but_refresh_failed(self):
        for key in self.fixture["received"]:
            self.receive(key)
        inbox.refresh_projection(self.path)
        last = len(self.fixture["journal"])
        with patch.object(inbox, "refresh_projection", side_effect=OSError("projection unavailable")):
            with self.assertRaisesRegex(OSError, "projection unavailable"):
                driver.drain(self.path, max_steps=last, refresh_projection=True)
        committed = inbox.snapshot(self.path)
        self.assertEqual(committed["state"], self.fixture)
        self.assertEqual(inbox.projection(self.path)["status"], "behind")
        with redirect_stdout(io.StringIO()) as output:
            driver.main(["--db", str(self.path), "--max-steps", "1", "--refresh-projection"])
        summary = json.loads(output.getvalue())
        self.assertEqual(summary["committed_steps"], 0)
        self.assertEqual(summary["status"], "complete")
        heads = {"reconciliation": last, "intake": len(self.fixture["received"])}
        self.assertEqual(summary["projection"], {"status": "caught-up", "available": heads, "projected": heads})
        self.assertEqual(inbox.snapshot(self.path), committed)
        self.assertEqual(inbox.projection(self.path)["projection"], wb.project(committed["state"]))

    def test_rejects_changed_evidence_and_divergent_journal(self):
        source = self.fixture["received"]["guide"]
        inbox.receive(self.path, "guide", {**source, "text": "Different synthetic statement."})
        before = inbox.snapshot(self.path)
        with self.assertRaisesRegex(ValueError, "outside the recorded synthetic fixture"):
            driver.advance(self.path)
        self.assertEqual(inbox.snapshot(self.path), before)

        self.path = self.path.with_name("divergent.sqlite")
        self.receive("guide")
        self.receive("retry")
        driver.advance(self.path)
        inbox.restore(self.path, "undo-first", base_position=1,
                      request={"baseRevision": 1, "targetPosition": 0, "reason": "Undo the recorded step."})
        restored = inbox.snapshot(self.path)
        with self.assertRaisesRegex(ValueError, "not an exact recorded fixture prefix"):
            driver.advance(self.path)
        self.assertEqual(inbox.snapshot(self.path), restored)
