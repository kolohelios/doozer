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

    def thread(self, key, data=None):
        return next(item for item in (data or self.data)["threads"] if item["id"] == key)

    def test_accepted_policy_does_not_approve_fixture_or_sample_labels(self):
        result = review.report(self.data, self.rows)
        self.assertEqual(result["accepted_interpretation_policy"]["status"], "accepted")
        self.assertEqual(result["accepted_interpretation_policy"]["labelApproval"], "pending-user-review")
        self.assertTrue(all(item["status"] == "pending-user-review" for item in result["thread_fixtures"] + result["calibration_samples"]))
        self.assertFalse(result["meta"]["semanticScoringEnabled"])

    def test_primary_threads_have_rich_corrections_and_nonadjacent_reply_targets(self):
        primary = [thread for thread in self.data["threads"] if thread["cohort"] == "primary"]
        self.assertEqual(len(primary), 2)
        for thread in primary:
            messages = thread["messages"]
            chain, missing = review.reply_chain(messages, thread["correction"])
            self.assertIsNone(missing)
            self.assertEqual(chain[1], thread["expectedReferent"])
            offset = next(index for index, message in enumerate(messages) if message["id"] == thread["correction"])
            self.assertNotEqual(messages[offset - 1]["id"], thread["expectedReferent"])
            self.assertGreater(len(messages[offset]["text"].split()), 15)

    def test_missing_context_preserves_partial_chain_without_guessing_a_parent(self):
        thread = self.thread("missing-reply-context")
        chain, missing = review.reply_chain(thread["messages"], thread["correction"])
        self.assertEqual(chain, [thread["correction"]])
        self.assertEqual(missing, "m-unavailable")
        self.assertNotIn("expectedReferent", thread)
        self.assertTrue(thread["expected"]["known"])
        self.assertTrue(thread["expected"]["unresolved"])
        self.assertEqual(thread["cohort"], "robustness")

    def test_primary_thread_cannot_silently_lose_its_reply_target(self):
        data = copy.deepcopy(self.data)
        thread = self.thread("recovery-path-correction", data)
        thread["messages"] = [message for message in thread["messages"] if message["id"] != thread["expectedReferent"]]
        with self.assertRaisesRegex(ValueError, "unavailable reply target"):
            review.validate(data, self.artifact)

    def test_adjacency_cannot_replace_the_explicit_reply_link(self):
        data = copy.deepcopy(self.data)
        thread = self.thread("recovery-path-correction", data)
        thread["expectedReferent"] = "m-e3"
        with self.assertRaisesRegex(ValueError, "actual reply link"):
            review.validate(data, self.artifact)

    def test_thread_cycles_and_temporally_impossible_replies_are_rejected(self):
        for mutation, error in (("cycle", "cyclic"), ("date", "predates")):
            data = copy.deepcopy(self.data)
            thread = self.thread("recovery-path-correction", data)
            if mutation == "cycle":
                thread["messages"][0]["replyTo"] = thread["correction"]
            else:
                thread["messages"][1]["saidAt"] = "2026-08-01T09:00:00Z"
            with self.subTest(mutation=mutation), self.assertRaisesRegex(ValueError, error):
                review.validate(data, self.artifact)

    def test_thread_support_cannot_borrow_evidence_from_a_different_thread(self):
        data = copy.deepcopy(self.data)
        self.thread("recovery-path-correction", data)["expected"]["known"][0]["support"][0]["message"] = "m-r8"
        with self.assertRaisesRegex(ValueError, "unavailable evidence"):
            review.validate(data, self.artifact)

    def test_missing_context_cannot_be_declared_resolved(self):
        data = copy.deepcopy(self.data)
        self.thread("missing-reply-context", data)["expectedReferent"] = "invented-target"
        with self.assertRaisesRegex(ValueError, "without inventing"):
            review.validate(data, self.artifact)

    def test_new_thread_model_inputs_exclude_expected_outcomes_and_case_metadata(self):
        data = copy.deepcopy(self.data)
        for index, thread in enumerate(data["threads"]):
            old_id = thread["id"]
            thread["id"] = f"PROVENANCE_CANARY-{index}"
            for group in data["threadContrasts"]:
                if group["thread"] == old_id:
                    group["thread"] = thread["id"]
            thread["expected"]["known"][0]["meaning"] = "OUTCOME_CANARY"
            thread["expected"]["forbidden"].append("FORBIDDEN_CANARY")
        for thread in review.report(data, self.rows)["thread_fixtures"]:
            payload = thread["model_input"]
            self.assertEqual(set(payload), {"question", "messages"})
            for canary in ("PROVENANCE_CANARY", "OUTCOME_CANARY", "FORBIDDEN_CANARY"):
                self.assertNotIn(canary, json.dumps(payload))
            self.assertNotIn("expectedReferent", payload)
            self.assertNotIn("topology", payload)

    def test_detached_stop_probe_is_retained_as_robustness_not_primary(self):
        result = review.report(self.data, self.rows)
        sample = next(item for item in result["calibration_samples"] if item["id"] == "unrelated-span-false-pass")
        self.assertEqual(sample["cohort"], "robustness")
        self.assertEqual(sample["draft_expected"], "fail")
        packet = review.packet(self.data, self.rows, result)
        self.assertLess(packet.index("## Primary thread-shaped fixtures"), packet.index("## Saved-answer review"))
        self.assertGreater(packet.index("### unrelated-span-false-pass"), packet.index("## Robustness probes"))

    def test_authored_contrasts_cover_threads_with_shared_blind_criteria_and_sources(self):
        result = review.report(self.data, self.rows)
        samples = result["thread_calibration_samples"]
        self.assertEqual(len(samples), 10)
        self.assertEqual(sum(sample["cohort"] == "primary" for sample in samples), 7)
        for thread in self.data["threads"]:
            group = [sample for sample in samples if sample["provenance"]["thread"] == thread["id"]]
            self.assertEqual({sample["draft_expected"] for sample in group}, {"pass", "fail"})
            for sample in group:
                self.assertEqual(sample["judge_input"]["criterion"], group[0]["judge_input"]["criterion"])
                self.assertEqual(sample["judge_input"]["authoritative_sources"], thread["messages"])
                self.assertEqual(sample["provenance"]["origin"], "authored-contrast")
                self.assertEqual(sample["status"], "user-approved-development-reference")

    def test_contrast_labels_and_rationales_do_not_leak_or_change_input_hashes(self):
        data = copy.deepcopy(self.data)
        before = review.contrast_samples(data)
        for group in data["threadContrasts"]:
            for candidate in group["candidates"]:
                candidate["expected"] = "LABEL_CANARY"
                candidate["reason"] = "REASON_CANARY"
                candidate["id"] = "IDENTITY_CANARY"
                candidate["spans"] = ["SPAN_CANARY"]
        after = review.contrast_samples(data)
        for old, new in zip(before, after):
            self.assertEqual(set(new["judge_input"]), {"question", "criterion", "target", "candidate", "authoritative_sources"})
            self.assertEqual(old["judge_input"], new["judge_input"])
            self.assertEqual(old["input_sha256"], new["input_sha256"])
            self.assertNotIn("CANARY", json.dumps(new["judge_input"]))

    def test_contrast_candidate_and_evidence_changes_change_input_hash(self):
        baseline = review.contrast_samples(self.data)[0]["input_sha256"]
        for change in ("candidate", "source", "criterion"):
            data = copy.deepcopy(self.data)
            if change == "candidate":
                data["threadContrasts"][0]["candidates"][0]["candidate"] += " Changed."
            elif change == "source":
                data["threads"][0]["messages"][0]["text"] += " Changed."
            else:
                data["threadContrasts"][0]["criterion"] += " Changed."
            with self.subTest(change=change):
                self.assertNotEqual(baseline, review.contrast_samples(data)[0]["input_sha256"])

    def test_contrast_reference_quote_and_identity_integrity(self):
        mutations = (
            ("thread", "unknown or duplicate"),
            ("duplicate", "duplicate contrast candidate"),
            ("candidate-quote", "misquotes its candidate"),
            ("pass-no-span", "pass needs"),
            ("cross-thread", "thread-local evidence"),
            ("source-quote", "thread-local evidence"),
        )
        for mutation, error in mutations:
            data = copy.deepcopy(self.data)
            group = data["threadContrasts"][0]
            candidate = group["candidates"][0]
            if mutation == "thread":
                group["thread"] = "unknown-thread"
            elif mutation == "duplicate":
                candidate["id"] = data["samples"][0]["id"]
            elif mutation == "candidate-quote":
                candidate["spans"] = ["Invented answer quote"]
            elif mutation == "pass-no-span":
                candidate["spans"] = []
            elif mutation == "cross-thread":
                candidate["evidence"][0]["message"] = "m-r8"
            else:
                candidate["evidence"][0]["quote"] = "Invented source quote"
            with self.subTest(mutation=mutation), self.assertRaisesRegex(ValueError, error):
                review.validate(data, self.artifact)

    def test_contrast_groups_cannot_silently_drop_a_thread_or_all_negatives(self):
        for mutation, error in (("coverage", "every thread"), ("labels", "positive and negative")):
            data = copy.deepcopy(self.data)
            if mutation == "coverage":
                data["threadContrasts"].pop()
            else:
                for candidate in data["threadContrasts"][0]["candidates"]:
                    candidate["expected"] = "pass"
            with self.subTest(mutation=mutation), self.assertRaisesRegex(ValueError, error):
                review.validate(data, self.artifact)

    def test_omission_contrast_uses_whole_answer_without_a_fabricated_span(self):
        sample = next(item for item in review.contrast_samples(self.data) if item["id"] == "maple-manuscript-omission")
        self.assertEqual(sample["candidate_spans"], [])
        self.assertEqual(sample["judge_input"]["target"], "whole-answer")
        self.assertEqual(sample["draft_expected"], "fail")

    def test_packet_separates_primary_and_robustness_authored_contrasts(self):
        result = review.report(self.data, self.rows)
        packet = review.packet(self.data, self.rows, result)
        self.assertLess(packet.index("### harbor-bounded-answer"), packet.index("## Saved-answer review"))
        self.assertGreater(packet.index("### partial-context-invented-target"), packet.index("## Robustness probes"))

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
