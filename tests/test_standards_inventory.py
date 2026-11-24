"""Public-source inventory integrity, not standards interpretation or model evaluation."""

import re
import unittest
from urllib.parse import urlparse

from scripts import workbench as wb


class StandardsInventoryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.corpus = wb.export_cue(sorted((wb.ROOT / "corpus").glob("*.cue")))
        cls.inventory = wb.export_cue(sorted((wb.ROOT / "corpus/standards").glob("*.cue")))["publicStandardsPilot"]

    def test_full_development_lineage_has_pinned_official_representations(self):
        documents = self.inventory["documents"]
        self.assertEqual([d["id"] for d in documents], ["rfc7807", *[f"draft-{i:02d}" for i in range(8)], "rfc9457"])
        self.assertEqual(len({d["sha256"] for d in documents}), 10)
        for document in documents:
            self.assertRegex(document["sha256"], r"^[a-f0-9]{64}$")
            self.assertGreater(document["bytes"], 30000)
            self.assertIn(urlparse(document["url"]).hostname, {"www.rfc-editor.org", "www.ietf.org"})
            self.assertEqual(urlparse(document["url"]).scheme, "https")
            self.assertEqual(set(document), {"id", "kind", "url", "headerDate", "bytes", "sha256"})
        self.assertEqual(documents[0]["headerDate"], "March 2016")
        self.assertEqual(documents[-1]["headerDate"], "July 2023")

    def test_comments_are_locators_not_frozen_historical_bodies_or_adoption_labels(self):
        discovery = self.inventory["discussionDiscovery"]
        self.assertEqual(discovery["status"], "locators-only-not-captured-or-adjudicated")
        self.assertEqual(len(discovery["arcs"]), 3)
        self.assertIn("later edits", " ".join(discovery["cautions"]))
        for arc in discovery["arcs"]:
            self.assertEqual(set(arc), {"id", "issues", "pulls"})
            self.assertTrue(arc["issues"] and arc["pulls"])
            self.assertTrue(all(type(n) is int and n > 0 for n in arc["issues"] + arc["pulls"]))

    def test_no_redistribution_approval_rubric_model_calls_or_paid_budget_implied(self):
        self.assertEqual(self.inventory["status"], "external-inventory-not-yet-replay-corpus")
        self.assertEqual(self.inventory["licensing"]["status"], "redistribution-review-pending-no-third-party-text-vendored")
        self.assertEqual(self.inventory["evaluation"]["status"], "not-run-no-approved-rubric")
        self.assertEqual(self.inventory["evaluation"]["plannedModelCalls"], 0)
        self.assertEqual(self.inventory["evaluation"]["budgetUSD"], 0)
        self.assertIn("not a truth oracle", self.inventory["evaluation"]["boundary"])

    def test_existing_synthetic_scenarios_keep_separate_contract_and_real_dates_are_not_fabricated(self):
        self.assertEqual(len(self.corpus["scenarios"]), 5)
        for scenario in self.corpus["scenarios"].values():
            for source in scenario["sources"].values():
                self.assertTrue(source["anchor"].startswith("fixture://"))
                self.assertTrue(source["saidAt"].startswith("2026-"))
        for document in self.inventory["documents"]:
            self.assertFalse(re.search(r"2026", document["headerDate"]))
