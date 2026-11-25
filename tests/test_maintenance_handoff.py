import copy
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from scripts import maintenance_handoff as handoff, source_inbox as inbox, workbench as wb
from tests.test_source_inbox import SOURCE, reconciliation


class MaintenanceHandoffTests(unittest.TestCase):
    def setUp(self):
        directory = TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.path = Path(directory.name) / "inbox.sqlite"
        inbox.receive(self.path, "count-one", SOURCE)
        inbox.commit(self.path, "apply-one", **reconciliation())
        old = inbox.snapshot(self.path)["state"]["claims"]["claim-count-one"]
        claim = {**old, "id": "scoped-count"}
        self.patch = {"baseRevision": 1, "accounting": {}, "rationale": "Make a new scoped revision.",
                      "operations": [{"op": "add", "assertion": claim},
                                     {"op": "retire", "id": old["id"], "replacement": claim["id"], "reason": "Keep source access."}]}
        self.raw = json.dumps(self.patch, indent=2).encode()

    def test_inspect_is_read_only_and_exact_apply_is_idempotent(self):
        physical = self.path.read_bytes()
        report = handoff.inspect(self.path, self.raw)
        self.assertEqual(self.path.read_bytes(), physical)
        self.assertEqual(report["inspection"]["before"]["claims"], ["claim-count-one"])
        self.assertEqual(report["inspection"]["after"]["claims"], ["scoped-count"])
        self.assertEqual(report["semantic_judgment"], "not-evaluated")
        digest = report["inspection_sha256"]
        receipt = handoff.apply(self.path, "maintain-one", report, inspection_sha256=digest)
        self.assertEqual(handoff.apply(self.path, "maintain-one", report, inspection_sha256=digest), receipt)
        saved = inbox.snapshot(self.path)["state"]
        self.assertEqual(saved["journal"][-1]["patch"], self.patch)
        self.assertEqual(wb.resolve(saved, "claim-count-one")["id"], "scoped-count")

    def test_modified_inspection_and_intervening_commit_rejected(self):
        report = handoff.inspect(self.path, self.raw)
        altered = copy.deepcopy(report)
        altered["inspection"]["request"]["patch"]["rationale"] = "Changed."
        digest = report["inspection_sha256"]
        with self.assertRaisesRegex(ValueError, "exact inspection hash"):
            handoff.apply(self.path, "maintain-one", altered, inspection_sha256=digest)
        inbox.receive(self.path, "count-two", SOURCE)
        inbox.commit(self.path, "apply-two", **reconciliation("count-two", base_position=1, revision=1))
        before = inbox.snapshot(self.path)
        with self.assertRaisesRegex(ValueError, "stale reconciliation position"):
            handoff.apply(self.path, "maintain-one", report, inspection_sha256=digest)
        self.assertEqual(inbox.snapshot(self.path), before)

    def test_new_receipt_without_revision_change_also_invalidates_inspection(self):
        report = handoff.inspect(self.path, self.raw)
        inbox.receive(self.path, "count-two", SOURCE)
        before = inbox.snapshot(self.path)
        with self.assertRaisesRegex(ValueError, "state changed since inspection"):
            handoff.apply(self.path, "maintain-one", report, inspection_sha256=report["inspection_sha256"])
        self.assertEqual(inbox.snapshot(self.path), before)
        self.assertEqual(inbox.activity(self.path)["rejections"], [])
