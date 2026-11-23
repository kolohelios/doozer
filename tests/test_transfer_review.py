import copy
from contextlib import redirect_stderr, redirect_stdout
import io
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from scripts import interpretation_review as original, transfer_review as review


class TransferReviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw = review.load()
        cls.data = review.validate(cls.raw)
        cls.decisions = review.load_decisions()

    def test_pending_examples_are_distinct_from_earlier_approvals(self):
        self.assertEqual(self.data["interpretationReview"]["status"], "pending-user-review")
        self.assertEqual(len(self.data["contractExamples"]), 2)
        earlier = original.validate(original.load())
        self.assertEqual(original.fingerprints(earlier)["packet_sha256"], "710a4ddce7cc5f4c07a3f009cec0130c347867550a0f0f8cea68aae7525aaaf2")
        self.assertEqual(len(original.approval_status(earlier)["approved_examples"]), 8)
        self.assertEqual(original.approval_status(earlier)["shared_policy_approval"], "not-separately-approved")

    def test_only_the_explicitly_reviewed_example_is_approved(self):
        status = review.approval_status(self.data, self.decisions)
        self.assertEqual(status["approved_examples"], ["01-coverage-frame"])
        self.assertEqual(status["pending_examples"], ["02-invitation-directive"])
        self.assertEqual(status["shared_policy_approval"], "not-separately-approved")
        self.assertEqual(status["decision_sha256"], original.digest(self.decisions))
        self.assertEqual(original.fingerprints(self.data)["packet_sha256"], "fcbaebd37bc47fa9789b879b54450344d6c9b8cbf2994d246e4236078ab20468")
        self.assertEqual(original.fingerprints(self.data)["examples"]["01-coverage-frame"], "e2c6dc4386fedeacfbeb500d4724f3f4d02123ff7b8a34557b2848553b8a203c")

    def test_hunch_clarification_is_separate_from_unchanged_proposal(self):
        decision = self.decisions["examples"]["01-coverage-frame"]
        self.assertEqual(decision["clarification"]["quote"], "folks can speculate, but that isn't evidence, it's a hunch.")
        self.assertIn("yes... folks can speculate", decision["basis"])
        self.assertIn("not as a supporting or opposing witness", decision["clarification"]["interpretation"])
        self.assertIn("No approval of example 02", decision["scope"])
        self.assertIn("Merging PR 18 is not", decision["scope"])

    def test_changed_content_or_policy_cannot_reuse_the_decision(self):
        for field in ("meaning", "policy"):
            changed = copy.deepcopy(self.data)
            if field == "meaning":
                changed["contractExamples"]["01-coverage-frame"]["projection"]["current"] += " Changed."
            else:
                changed["interpretationReview"]["policies"][0]["proposal"] += " Changed."
            with self.subTest(field=field), self.assertRaises(ValueError):
                review.approval_status(changed, self.decisions)

    def test_decision_cannot_imply_full_review_or_blanket_policy_approval(self):
        for field, value in (("status", "example-review-complete"), ("sharedPolicyApproval", "approved"), ("contextPacketSHA256", "changed")):
            record = copy.deepcopy(self.decisions)
            record[field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                review.approval_status(self.data, record)
        for field in ("exampleSHA256", "status", "basis", "scope"):
            record = copy.deepcopy(self.decisions)
            record["examples"]["01-coverage-frame"][field] = ""
            with self.subTest(field=field), self.assertRaises(ValueError):
                review.approval_status(self.data, record)

    def test_check_never_writes_decisions_or_approves_the_next_example(self):
        before = review.APPROVALS.read_bytes()
        with redirect_stdout(io.StringIO()):
            self.assertEqual(review.main(["--check"]), 0)
        self.assertEqual(review.APPROVALS.read_bytes(), before)
        self.assertEqual(review.approval_status(self.data)["pending_examples"], ["02-invitation-directive"])

    def test_cli_rejects_mismatched_decisions_before_render_or_output(self):
        record = copy.deepcopy(self.decisions)
        record["examples"]["01-coverage-frame"]["exampleSHA256"] = "changed"
        with patch.object(review, "load_decisions", return_value=record), TemporaryDirectory() as folder, redirect_stdout(io.StringIO()):
            path = Path(folder) / "proposal.md"
            self.assertEqual(review.main(["--output", str(path)]), 2)
            self.assertFalse(path.exists())
            self.assertEqual(review.main(["--render"]), 2)

    def test_projection_is_exact_and_all_meaning_fields_and_anchors_visible(self):
        rendered = review.render(self.data)
        self.assertEqual(review.PROJECTION.read_text(), rendered)
        for example in self.data["contractExamples"].values():
            for source in example["sources"]:
                self.assertIn(source["text"], rendered)
            for meaning in example["meanings"]:
                self.assertIn(meaning["content"], rendered)
                for anchor in meaning["anchors"]:
                    self.assertIn(anchor["quote"], rendered)
        self.assertIn('"affects": ["oak-permission"]', rendered)
        self.assertIn('"holder": null', rendered)
        self.assertIn('"target": "assurance"', rendered)

    def test_single_example_view_does_not_imply_approval_of_the_other(self):
        text = review.render(self.data, "01-coverage-frame")
        self.assertIn("## 01-coverage-frame", text)
        self.assertNotIn("## 02-invitation-directive", text)
        self.assertIn("No decision for one example applies to the other", text)

    def test_hash_changes_when_meaning_or_recovery_changes(self):
        changed = copy.deepcopy(self.data)
        changed["contractExamples"]["01-coverage-frame"]["projection"]["current"] += " Changed proposal."
        before, after = original.fingerprints(self.data), original.fingerprints(changed)
        self.assertNotEqual(before["packet_sha256"], after["packet_sha256"])
        self.assertNotEqual(before["examples"]["01-coverage-frame"], after["examples"]["01-coverage-frame"])
        self.assertEqual(before["examples"]["02-invitation-directive"], after["examples"]["02-invitation-directive"])

    def test_sources_metadata_and_context_cannot_drift_from_archive(self):
        for field, value in (("text", "Changed source"), ("actor", "Someone else"), ("derivedFrom", ["m99"]), ("authority", "other-authority")):
            raw = copy.deepcopy(self.raw)
            raw["transferExamples"]["01-coverage-frame"]["sources"][0][field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                review.validate(raw)
        raw = copy.deepcopy(self.raw)
        raw["transferReviewArchive"]["sha256"] = "changed"
        with self.assertRaises(ValueError):
            review.validate(raw)

    def test_no_missing_or_future_historical_context(self):
        raw = copy.deepcopy(self.raw)
        raw["transferExamples"]["02-invitation-directive"]["windows"]["w0"].append("m7")
        with self.assertRaises(ValueError):
            review.validate(raw)
        raw = copy.deepcopy(self.raw)
        raw["transferExamples"]["01-coverage-frame"]["sources"].pop()
        with self.assertRaises(ValueError):
            review.validate(raw)

    def test_review_does_not_import_peer_model_opinions(self):
        raw = copy.deepcopy(self.raw)
        raw["transferExamples"]["01-coverage-frame"]["extractorReports"] = [{"id": "opinion", "actor": "model", "window": "w0", "text": "All models agree."}]
        with self.assertRaises(ValueError):
            review.validate(raw)

    def test_coverage_cannot_invent_a_personal_knowledge_holder(self):
        raw = copy.deepcopy(self.raw)
        meaning = next(m for m in raw["transferExamples"]["01-coverage-frame"]["meanings"] if m["id"] == "report-limit")
        meaning["holder"] = "Tess"
        with self.assertRaises(ValueError):
            review.validate(raw)

    def test_directive_retains_action_and_has_no_world_assignment(self):
        example = self.data["contractExamples"]["02-invitation-directive"]
        warning = next(m for m in example["meanings"] if m["id"] == "warning")
        self.assertEqual(warning["affects"], [])
        self.assertEqual(warning["action"]["object"], "catering meeting invitation")
        raw = copy.deepcopy(self.raw)
        next(m for m in raw["transferExamples"]["02-invitation-directive"]["meanings"] if m["id"] == "warning")["affects"] = ["permission-evidence-use"]
        with self.assertRaises(ValueError):
            review.validate(raw)

    def test_declared_recovery_and_exact_quotes_not_entailment_are_checked(self):
        raw = copy.deepcopy(self.raw)
        raw["transferExamples"]["01-coverage-frame"]["meanings"][0]["anchors"][0]["quote"] = "Invented quotation"
        with self.assertRaises(ValueError):
            review.validate(raw)
        raw = copy.deepcopy(self.raw)
        raw["transferExamples"]["02-invitation-directive"]["representations"][0]["retains"].remove("warning")
        with self.assertRaises(ValueError):
            review.validate(raw)
        raw = copy.deepcopy(self.raw)
        raw["transferExamples"]["01-coverage-frame"]["meanings"][0]["content"] = "An unsupported assertion that this mechanical checker cannot adjudicate."
        self.assertEqual(review.validate(raw)["interpretationReview"]["status"], "pending-user-review")

    def test_check_is_offline_and_cannot_write_approvals_or_overwrite_outputs(self):
        out = io.StringIO()
        with patch("urllib.request.OpenerDirector.open", side_effect=AssertionError("network called")), redirect_stdout(out):
            self.assertEqual(review.main(["--check"]), 0)
        summary = json.loads(out.getvalue())
        self.assertEqual(summary["approved_examples"], ["01-coverage-frame"])
        self.assertEqual(summary["pending_examples"], ["02-invitation-directive"])
        self.assertEqual(summary["status"], "partial-user-review")
        self.assertEqual(summary["proposal_snapshot_status"], "pending-user-review")
        self.assertEqual(summary["paid_calls"], 0)
        self.assertFalse(summary["validation_grants_approval"])
        with TemporaryDirectory() as folder, redirect_stdout(io.StringIO()):
            path = Path(folder) / "review.md"
            self.assertEqual(review.main(["--output", str(path)]), 0)
            original_bytes = path.read_bytes()
            self.assertEqual(review.main(["--output", str(path)]), 2)
            self.assertEqual(path.read_bytes(), original_bytes)
        with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            review.main(["--approve"])
        raw = copy.deepcopy(self.raw)
        raw["transferReview"]["status"] = "approved"
        with self.assertRaises(ValueError):
            review.validate(raw)


if __name__ == "__main__":
    unittest.main()
