"""Offline annotation integrity and support-proxy mechanics, not semantic gold tests."""

import copy
import hashlib
import io
import json
import os
from pathlib import Path
import tempfile
from unittest import TestCase, mock

from scripts import calibration as review


class CalibrationTests(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data, cls.artifact, cls.rows = review.load()

    def meaning(self, case, key):
        return next(item for item in self.data["meanings"][case] if item["id"] == key)

    def sources(self, case, *ids):
        return [doc for doc in self.rows[case, "full"]["context"] if doc["id"] in ids]

    def test_complete_draft_without_accuracy_or_approval(self):
        result = review.report(self.data, self.rows)
        self.assertEqual(len(result["rows"]), 9)
        self.assertEqual(len(result["calibration_samples"]), 12)
        self.assertEqual(sum(len(arm) for case in self.data["reviews"].values() for arm in case.values()), 51)
        self.assertEqual(result["meta"]["status"], "pending-user-review")
        self.assertFalse(result["meta"]["semanticScoringEnabled"])
        self.assertFalse(result["coverage_is_entailment_proof"])
        self.assertNotIn("accuracy", result)
        self.assertTrue(all(sample["split"] == "development" for sample in result["calibration_samples"]))

    def test_approval_cannot_be_inferred_or_enabled_by_this_tool(self):
        for changes in (dict(status="approved"), dict(semanticScoringEnabled=True)):
            data = copy.deepcopy(self.data)
            data["meta"].update(changes)
            with self.subTest(changes=changes), self.assertRaisesRegex(ValueError, "drafts only"):
                review.validate(data, self.artifact)

    def test_scheduler_meaning_can_use_direct_document_or_contextual_rejection(self):
        meaning = self.meaning("payout-recovery", "scheduler-boundary")
        direct, reply = meaning["sufficient"]
        document = self.sources("payout-recovery", "heldout/d-c8")
        contextual = self.sources("payout-recovery", "heldout/d-77", "heldout/d-b2")
        self.assertTrue(review.bundle_available(direct, document))
        self.assertTrue(review.bundle_available(reply, contextual))
        self.assertFalse(review.bundle_available(reply, self.sources("payout-recovery", "heldout/d-b2")))
        self.assertFalse(review.bundle_available(reply, self.sources("payout-recovery", "heldout/d-77")))

    def test_normal_access_needs_policy_and_time_scope(self):
        meaning = self.meaning("archive-access", "normal-catalog-access")
        direct = meaning["sufficient"][0]
        self.assertFalse(review.bundle_available(direct, self.sources("archive-access", "heldout/d-02")))
        self.assertFalse(review.bundle_available(direct, self.sources("archive-access", "heldout/d-34")))
        self.assertTrue(review.bundle_available(direct, self.sources("archive-access", "heldout/d-02", "heldout/d-34")))
        manuscript = self.meaning("archive-access", "manuscript-escort")["sufficient"][0]
        self.assertFalse(review.bundle_available(manuscript, self.sources("archive-access", "heldout/d-02", "heldout/d-8e")))

    def test_source_id_without_quoted_qualifier_does_not_satisfy_bundle(self):
        bundle = self.meaning("payout-recovery", "scheduler-boundary")["sufficient"][0]
        context = copy.deepcopy(self.sources("payout-recovery", "heldout/d-c8"))
        context[0]["text"] = "The Orchid recovery command --ledger-only bypasses email sending."
        self.assertFalse(review.bundle_available(bundle, context))

    def test_history_and_conditional_guards_do_not_inflate_answer_denominator(self):
        for case, arm in self.rows:
            support = review.draft_support(self.data["meanings"][case], self.rows[case, arm]["context"])
            expected = {meaning["id"] for meaning in self.data["meanings"][case] if meaning["applicability"] == "required"}
            self.assertEqual({item["meaning"] for item in support}, expected)
        self.assertEqual(self.data["reviews"]["archive-access"]["full"]["unresolved-intervention"]["label"], "not-assessed")

    def test_calibration_judge_inputs_exclude_labels_arms_and_draft_reasons(self):
        data = copy.deepcopy(self.data)
        for sample in data["samples"]:
            sample["expected"] = "EXPECTED_CANARY"
            sample["reason"] = "RATIONALE_CANARY"
        result = review.report(data, self.rows)
        for sample in result["calibration_samples"]:
            judge = sample["judge_input"]
            self.assertEqual(set(judge), {"question", "criterion", "target", "candidate", "authoritative_sources"})
            self.assertNotIn("EXPECTED_CANARY", json.dumps(judge))
            self.assertNotIn("RATIONALE_CANARY", json.dumps(judge))
            self.assertNotIn("arm", judge)

    def test_excerpt_and_omission_examples_are_distinct(self):
        result = review.report(self.data, self.rows)
        samples = {sample["id"]: sample for sample in result["calibration_samples"]}
        self.assertIsInstance(samples["missing-test-scope"]["judge_input"]["candidate"], dict)
        self.assertIsInstance(samples["scoped-manual-mitigation"]["judge_input"]["candidate"], list)
        claim = samples["echo-lineage-contract"]["judge_input"]["candidate"]
        self.assertEqual(len(claim["evidence"]), 2)
        self.assertIn("attribution", claim)
        self.assertIn("scope", claim)
        self.assertEqual({sample["draft_expected"] for sample in samples.values()}, {"pass", "fail", "uncertain"})

    def test_candidate_quotes_cannot_point_to_cited_source_text(self):
        answer = self.rows["payout-recovery", "full"]["understanding"]
        with self.assertRaisesRegex(ValueError, "answer text field"):
            review.resolve(answer, "/claims/0/evidence/0/quote")
        with self.assertRaisesRegex(ValueError, "does not resolve"):
            review.resolve(answer, "/claims/999/text")

    def test_misquoted_candidate_is_rejected(self):
        data = copy.deepcopy(self.data)
        data["reviews"]["payout-recovery"]["full"]["manual-bypass"]["spans"][0]["quote"] = "Invented answer text"
        with self.assertRaisesRegex(ValueError, "misquotes"):
            review.validate(data, self.artifact)

    def test_similar_other_case_source_cannot_support_a_domain_fact(self):
        data = copy.deepcopy(self.data)
        bundle = data["meanings"]["payout-recovery"][0]["sufficient"][0]
        bundle["allOf"] = [{"source": "heldout/d-69", "quote": "Gate the zone label by consumer revision."}]
        with self.assertRaisesRegex(ValueError, "authoritative"):
            review.validate(data, self.artifact)

    def test_contextual_bundle_without_reply_target_is_rejected(self):
        data = copy.deepcopy(self.data)
        meaning = next(m for m in data["meanings"]["payout-recovery"] if m["id"] == "scheduler-boundary")
        meaning["sufficient"][1]["allOf"] = [{"source": "heldout/d-b2", "quote": "No."}]
        with self.assertRaisesRegex(ValueError, "reply target"):
            review.validate(data, self.artifact)

    def test_review_coverage_cannot_silently_drop_a_meaning(self):
        data = copy.deepcopy(self.data)
        data["reviews"]["archive-access"]["vector"].pop("manuscript-escort")
        with self.assertRaisesRegex(ValueError, "omits or invents"):
            review.validate(data, self.artifact)

    def test_history_retention_cannot_be_passed_from_an_answer(self):
        data = copy.deepcopy(self.data)
        data["reviews"]["archive-access"]["full"]["unresolved-intervention"]["label"] = "pass"
        with self.assertRaisesRegex(ValueError, "history retention"):
            review.validate(data, self.artifact)

    def test_omission_calibration_cannot_claim_an_excerpt_without_spans(self):
        data = copy.deepcopy(self.data)
        sample = next(sample for sample in data["samples"] if sample["id"] == "missing-test-scope")
        sample["target"] = "excerpt"
        with self.assertRaisesRegex(ValueError, "excerpt"):
            review.validate(data, self.artifact)

    def test_zero_required_meanings_cannot_become_vacuous_coverage(self):
        data = copy.deepcopy(self.data)
        for meaning in data["meanings"]["payout-recovery"]:
            meaning["applicability"] = "if-mentioned"
        with self.assertRaisesRegex(ValueError, "no required"):
            review.validate(data, self.artifact)

    def test_whole_answer_pass_still_needs_a_real_supporting_span(self):
        data = copy.deepcopy(self.data)
        sample = next(sample for sample in data["samples"] if sample["id"] == "missing-test-scope")
        sample["expected"] = "pass"
        with self.assertRaisesRegex(ValueError, "pass requires"):
            review.validate(data, self.artifact)

    def test_conflicting_source_snapshots_are_rejected(self):
        artifact = copy.deepcopy(self.artifact)
        artifact["rows"][0]["context"][0]["text"] = "Different source version"
        with self.assertRaisesRegex(ValueError, "conflicting"):
            review.validate(self.data, artifact)

    def test_source_hash_mismatch_blocks_rebinding(self):
        data = copy.deepcopy(self.data)
        data["meta"]["artifactSHA256"] = "0" * 64
        with mock.patch.object(review, "export_cue", return_value=data), self.assertRaisesRegex(ValueError, "changed"):
            review.load()

    def test_cli_is_offline_and_never_modifies_original(self):
        original = review.ROOT / self.data["meta"]["artifact"]
        before = hashlib.sha256(original.read_bytes()).hexdigest()
        with tempfile.TemporaryDirectory() as directory, \
                mock.patch.dict(os.environ, {"OPENROUTER_API_KEY": "SECRET_CANARY"}), \
                mock.patch("urllib.request.build_opener") as network, \
                mock.patch("sys.stdout", new_callable=io.StringIO) as stdout:
            output, packet = Path(directory) / "report.json", Path(directory) / "packet.md"
            self.assertEqual(review.main(["--output", str(output), "--packet", str(packet)]), 0)
            network.assert_not_called()
            self.assertNotIn("SECRET_CANARY", output.read_text() + packet.read_text() + stdout.getvalue())
            self.assertIn("pending user approval", packet.read_text())
            self.assertEqual(review.main(["--output", str(output)]), 2)
            self.assertEqual(review.main(["--output", str(original)]), 2)
        self.assertEqual(before, hashlib.sha256(original.read_bytes()).hexdigest())

    def test_packet_and_report_cannot_collide(self):
        with tempfile.TemporaryDirectory() as directory, mock.patch("sys.stdout", new_callable=io.StringIO):
            path = Path(directory) / "same"
            self.assertEqual(review.main(["--output", str(path), "--packet", str(path)]), 2)
            self.assertFalse(path.exists())
