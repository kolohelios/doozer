"""Review integrity is not approval, semantic entailment, or a model experiment."""

import copy
import io
import json
import os
from pathlib import Path
import socket
import tempfile
from unittest import TestCase, mock

from scripts import interpretation_review as review


class InterpretationReviewTests(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = review.load()

    def draft(self):
        return copy.deepcopy(self.data)

    def test_original_proposal_snapshot_and_projection_are_reproducible(self):
        data = review.validate(self.draft())
        self.assertEqual(len(data["contractExamples"]), 8)
        self.assertEqual(data["interpretationReview"]["status"], "pending-user-review")
        self.assertEqual(review.render(data), review.PROJECTION.read_text())
        self.assertEqual(len(review.fingerprints(data)["examples"]), 8)

    def test_all_eight_explicit_decisions_bind_to_reviewed_content_only(self):
        status = review.approval_status(self.data)
        self.assertEqual(status["status"], "example-review-complete")
        self.assertEqual(status["approved_examples"], sorted(self.data["contractExamples"]))
        self.assertEqual(status["shared_policy_approval"], "not-separately-approved")
        changed = self.draft()
        changed["contractExamples"]["08-local-conflict"]["decision"] += " Changed."
        with self.assertRaises(ValueError):
            review.approval_status(changed)

    def test_decision_records_cannot_silently_change_example_or_approval_scope(self):
        record = json.loads(review.subprocess.run(["cue", "export", str(review.APPROVALS)], check=True, capture_output=True, text=True).stdout)["interpretationApprovals"]
        for field in ("exampleSHA256", "status"):
            bad = copy.deepcopy(record)
            bad["examples"]["08-local-conflict"][field] = "invalid"
            with self.subTest(field=field), self.assertRaises(ValueError):
                review.approval_status(self.data, bad)
        bad = copy.deepcopy(record)
        bad["sharedPolicyApproval"] = "blanket-approval"
        with self.assertRaises(ValueError):
            review.approval_status(self.data, bad)
        with tempfile.TemporaryDirectory() as directory, mock.patch.object(review, "APPROVALS", Path(directory) / "absent.cue"):
            self.assertEqual(review.approval_status(self.data)["approved_examples"], [])

    def test_hashes_bind_policy_and_individual_input_interpretation_pairs(self):
        original = review.fingerprints(self.data)
        data = self.draft()
        data["interpretationReview"]["policies"][0]["proposal"] += " A revised proposal."
        changed = review.fingerprints(data)
        self.assertNotEqual(original["policy_sha256"], changed["policy_sha256"])
        self.assertNotEqual(original["packet_sha256"], changed["packet_sha256"])
        self.assertEqual(original["examples"], changed["examples"])
        data = self.draft()
        data["contractExamples"]["01-source-uncertainty"]["sources"][0]["text"] += " An extra statement."
        changed = review.fingerprints(data)
        self.assertEqual(original["policy_sha256"], changed["policy_sha256"])
        self.assertNotEqual(original["packet_sha256"], changed["packet_sha256"])
        self.assertNotEqual(original["examples"]["01-source-uncertainty"], changed["examples"]["01-source-uncertainty"])
        self.assertEqual(original["examples"]["02-window-coverage"], changed["examples"]["02-window-coverage"])

    def test_operational_approval_text_is_not_part_of_meaning_digest(self):
        data = self.draft()
        data["interpretationReview"]["approval"] += " Operational note."
        self.assertEqual(review.fingerprints(data), review.fingerprints(self.data))
        data["interpretationReview"]["status"] = "user-approved"
        with self.assertRaises(ValueError):
            review.validate(data)

    def test_bad_anchors_and_future_sources_are_rejected(self):
        data = self.draft()
        data["contractExamples"]["01-source-uncertainty"]["meanings"][0]["anchors"][0]["quote"] = "The drill ... Pine annex."
        with self.assertRaises(ValueError):
            review.validate(data)
        data = self.draft()
        date = next(m for m in data["contractExamples"]["07-resolved-uncertainty"]["meanings"] if m["id"] == "new-date")
        date["window"] = "w1"
        with self.assertRaises(ValueError):
            review.validate(data)

    def test_source_and_extractor_channels_cannot_silently_trade_owners(self):
        data = self.draft()
        example = data["contractExamples"]["03-extractor-limitation"]
        unit = next(m for m in example["meanings"] if m["id"] == "interpretation-limit")
        unit["origin"] = "source"
        with self.assertRaises(ValueError):
            review.validate(data)
        data = self.draft()
        unit = next(m for m in data["contractExamples"]["01-source-uncertainty"]["meanings"] if m["kind"] == "source-uncertainty")
        unit["holder"] = "nobody"
        with self.assertRaises(ValueError):
            review.validate(data)

    def test_directive_topic_is_not_a_world_effect_and_retains_action_arguments(self):
        data = self.draft()
        example = data["contractExamples"]["04-question-and-directive"]
        request = next(m for m in example["meanings"] if m["kind"] == "directive")
        self.assertEqual(request["about"], ["date"])
        self.assertEqual(request["affects"], [])
        self.assertEqual(request["action"], {"verb": "check", "object": "calendar", "condition": "before making travel plans"})
        request["affects"] = ["date"]
        with self.assertRaises(ValueError):
            review.validate(data)
        request["affects"] = []
        del request["action"]
        with self.assertRaises(ValueError):
            review.validate(data)

    def test_withdrawal_and_revocation_have_different_target_kinds(self):
        for key, kind in (("05-assurance-withdrawal", "assurance-withdrawal"), ("06-permission-revocation", "revocation")):
            with self.subTest(key=key):
                data = self.draft()
                unit = next(m for m in data["contractExamples"][key]["meanings"] if m["kind"] == kind)
                unit["target"] = "venue"
                with self.assertRaises(ValueError):
                    review.validate(data)

    def test_equivalent_declared_encodings_need_not_have_identical_unit_sets(self):
        data = self.draft()
        example = data["contractExamples"]["04-question-and-directive"]
        self.assertNotEqual(example["representations"][0]["retains"], example["representations"][1]["retains"])
        review.validate(data)
        example["representations"][0]["retains"].remove("question")
        with self.assertRaises(ValueError):
            review.validate(data)

    def test_later_establishment_keeps_prior_source_limit_in_its_own_frame(self):
        example = self.data["contractExamples"]["07-resolved-uncertainty"]
        units = {m["id"]: m for m in example["meanings"]}
        self.assertEqual(units["earlier-limit"]["window"], "w1")
        self.assertEqual(units["new-date"]["window"], "w2")
        self.assertEqual(example["currentWindow"], "w2")
        self.assertIn("2030-02-14", example["projection"]["current"])
        self.assertIn("history", example["representations"][1]["id"])

    def test_unknown_references_duplicate_ids_and_frames_are_rejected(self):
        data = self.draft()
        example = data["contractExamples"]["02-window-coverage"]
        example["windows"]["w1"].append("absent")
        with self.assertRaises(ValueError):
            review.validate(data)
        data = self.draft()
        example = data["contractExamples"]["02-window-coverage"]
        example["meanings"][0]["about"] = ["absent"]
        with self.assertRaises(ValueError):
            review.validate(data)
        data = self.draft()
        example = data["contractExamples"]["02-window-coverage"]
        example["meanings"].append(copy.deepcopy(example["meanings"][0]))
        with self.assertRaises(ValueError):
            review.validate(data)

    def test_mechanical_validation_does_not_pretend_to_judge_natural_language(self):
        data = self.draft()
        data["contractExamples"]["01-source-uncertainty"]["meanings"][0]["content"] = "An unsupported venue interpretation requiring human review."
        review.validate(data)  # Valid pointers/types are not a semantic pass.
        self.assertEqual(data["interpretationReview"]["status"], "pending-user-review")
        self.assertNotEqual(review.fingerprints(data), review.fingerprints(self.data))

    def test_cli_without_credentials_cannot_connect_or_approve_or_overwrite(self):
        with mock.patch.dict(os.environ, {key: value for key, value in os.environ.items() if key != "OPENROUTER_API_KEY"}, clear=True), mock.patch.object(socket.socket, "connect", side_effect=AssertionError("network forbidden")), mock.patch("sys.stdout", new_callable=io.StringIO) as out:
            self.assertEqual(review.main(["--check"]), 0)
            report = json.loads(out.getvalue())
            self.assertEqual(report["paid_calls"], 0)
            self.assertFalse(report["validation_grants_approval"])
            self.assertEqual(report["status"], "example-review-complete")
            self.assertEqual(len(report["approved_examples"]), 8)
        with tempfile.TemporaryDirectory() as directory, mock.patch("sys.stdout", new_callable=io.StringIO):
            path = Path(directory) / "review.md"
            self.assertEqual(review.main(["--output", str(path)]), 0)
            before = path.read_bytes()
            self.assertEqual(review.main(["--output", str(path)]), 2)
            self.assertEqual(path.read_bytes(), before)
            with mock.patch.object(review, "PROJECTION", path):
                path.write_text("stale review")
                self.assertEqual(review.main(["--check"]), 2)
                self.assertEqual(path.read_text(), "stale review")
