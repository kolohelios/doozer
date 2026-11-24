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
