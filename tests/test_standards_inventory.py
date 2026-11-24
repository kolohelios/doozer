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

    def test_inventory_distinguishes_captured_arc_from_remaining_locators(self):
        discovery = self.inventory["discussionDiscovery"]
        self.assertEqual(discovery["status"], "http-field-excerpts-captured-other-arcs-locators-only")
        self.assertEqual(len(discovery["arcs"]), 3)
        self.assertIn("later edits", " ".join(discovery["cautions"]))
        for arc in discovery["arcs"]:
            self.assertEqual(set(arc), {"id", "issues", "pulls"})
            self.assertTrue(arc["issues"] and arc["pulls"])
            self.assertTrue(all(type(n) is int and n > 0 for n in arc["issues"] + arc["pulls"]))

    def test_no_blanket_reuse_approval_rubric_model_calls_or_paid_budget_implied(self):
        self.assertEqual(self.inventory["status"], "external-inventory-with-one-curated-development-arc")
        self.assertEqual(self.inventory["licensing"]["status"], "http-field-scoped-excerpt-review-other-reuse-pending")
        self.assertEqual(self.inventory["evaluation"]["status"], "not-run-no-approved-rubric")
        self.assertEqual(self.inventory["evaluation"]["plannedModelCalls"], 0)
        self.assertEqual(self.inventory["evaluation"]["budgetUSD"], 0)
        self.assertIn("not a truth oracle", self.inventory["evaluation"]["boundary"])

    def test_design_versions_companion_and_prior_snapshots_are_synchronized(self):
        prd = (wb.ROOT / "docs/PRD.md").read_text()
        edd = (wb.ROOT / "docs/EDD.md").read_text()
        readme = (wb.ROOT / "README.md").read_text()
        for document in (prd, edd):
            self.assertIn("**Version:** 0.7", document)
            self.assertIn("**Date:** November 24, 2026", document)
            self.assertIn("535c06d11377db5079b6055e1781d644cc363702", document)
            self.assertIn("19860b5cac12b93fa51cc0e3877000c3bf6615e3", document)
            self.assertIn("16ba8f2dc806203d80dace8928b21972e0306bbe", document)
        self.assertIn("[Doozers PRD v0.7](PRD.md)", edd)
        self.assertIn("design documents are v0.7", readme)
        self.assertIn("**Evidence at v0.7:**", prd)
        self.assertIn("Evidence level at v0.7", edd)

    def test_current_design_does_not_relabel_the_frozen_contrast_contract(self):
        workbench = wb.export_cue(sorted((wb.ROOT / "experiments/workbench").glob("*.cue")))
        self.assertEqual(workbench["proposerContrast"]["designVersion"], "0.5")
        for path in ("docs/PRD.md", "docs/EDD.md"):
            document = (wb.ROOT / path).read_text()
            self.assertIn("truth oracle", document)
            self.assertIn("later edits", document)
        self.assertEqual(self.inventory["evaluation"]["status"], "not-run-no-approved-rubric")

    def test_existing_synthetic_scenarios_keep_separate_contract_and_real_dates_are_not_fabricated(self):
        self.assertEqual(len(self.corpus["scenarios"]), 5)
        for scenario in self.corpus["scenarios"].values():
            for source in scenario["sources"].values():
                self.assertTrue(source["anchor"].startswith("fixture://"))
                self.assertTrue(source["saidAt"].startswith("2026-"))
        for document in self.inventory["documents"]:
            self.assertFalse(re.search(r"2026", document["headerDate"]))
