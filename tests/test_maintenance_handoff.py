import copy
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

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
        self.local_patch = copy.deepcopy(self.patch)
        del self.local_patch["accounting"]
        self.local_patch["operations"][0]["assertion"]["id"] = "new-1"
        self.local_patch["operations"][1].update(id="existing-1", replacement="new-1")
        self.local_raw = json.dumps(self.local_patch, indent=2).encode()

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

    def test_preparation_exposes_only_active_claims_and_cited_processed_sources(self):
        inbox.receive(self.path, "count-two", {**SOURCE, "text": "pending-canary"})
        physical = self.path.read_bytes()
        with patch("urllib.request.urlopen", side_effect=AssertionError("offline only")):
            prepared = handoff.prepare(self.path)
            self.assertEqual(prepared, handoff.prepare(self.path))
        self.assertEqual(prepared["planned_calls"], 0)
        messages = prepared["preparation"]["messages"]
        context = json.loads(messages[1]["content"])
        self.assertEqual(set(context["sources"]), {"count-one"})
        self.assertEqual(context["pending_count"], 1)
        self.assertEqual([claim["id"] for claim in context["current_claims"]], ["existing-1"])
        self.assertEqual(context["new_claim_slots"], ["new-1", "new-2", "new-3", "new-4"])
        self.assertNotIn("claim-count-one", json.dumps(messages))
        self.assertNotIn("pending-canary", json.dumps(prepared))
        self.assertEqual(self.path.read_bytes(), physical)
        report = handoff.inspect(self.path, self.local_raw, prepared=prepared)
        self.assertEqual(report["inspection"]["preparation_sha256"], prepared["preparation_sha256"])
        self.assertEqual(report["inspection"]["proposal"], self.local_patch)
        lowered = copy.deepcopy(self.patch)
        lowered["operations"][0]["assertion"]["id"] = "claim-slot-1"
        lowered["operations"][1]["replacement"] = "claim-slot-1"
        self.assertEqual(report["inspection"]["request"]["patch"], lowered)
        self.assertEqual(handoff.apply(self.path, "apply-prepared", report,
                                      inspection_sha256=report["inspection_sha256"])["position"], 2)
        state = inbox.snapshot(self.path)["state"]
        self.assertEqual(state["journal"][-1]["patch"], lowered)
        self.assertEqual(wb.resolve(state, "claim-count-one")["id"], "claim-slot-1")

    def test_preparation_rejects_context_changes_and_never_trims(self):
        prepared = handoff.prepare(self.path)
        altered = copy.deepcopy(prepared)
        altered["preparation"]["messages"][0]["content"] += " tampering"
        with self.assertRaisesRegex(ValueError, "preparation no longer matches"):
            handoff.inspect(self.path, self.raw, prepared=altered)
        with patch.object(handoff, "MAX_CONTEXT_BYTES", 1), self.assertRaisesRegex(ValueError, "no evidence was trimmed"):
            handoff.prepare(self.path)
        inbox.receive(self.path, "count-two", SOURCE)
        with self.assertRaisesRegex(ValueError, "preparation no longer matches"):
            handoff.inspect(self.path, self.raw, prepared=prepared)

    def test_prepared_response_cannot_cite_unshown_processed_evidence(self):
        inbox.receive(self.path, "count-two", SOURCE)
        disposition = {"mode": "dependent-no-op", "claims": ["claim-count-one"], "reason": "Same instruction.",
                       "basis": [{"source": "count-one", "quote": SOURCE["text"]}]}
        inbox.commit(self.path, "apply-two", base_position=1, batch=["count-two"],
                     patch={"baseRevision": 1, "operations": [], "rationale": "Duplicate wording.", "accounting": {"count-two": disposition}},
                     analysis=reconciliation()["analysis"], route={"action": "analyze"})
        prepared = handoff.prepare(self.path)
        self.assertEqual(prepared["preparation"]["shown_sources"], ["count-one"])
        candidate = copy.deepcopy(self.local_patch)
        candidate["operations"][0]["assertion"]["evidence"].append({"source": "count-two", "quote": SOURCE["text"]})
        with self.assertRaisesRegex(ValueError, "outside the prepared context"):
            handoff.inspect(self.path, json.dumps(candidate).encode(), prepared=prepared)

    def test_processed_reply_parent_is_context_only(self):
        reply = {**SOURCE, "text": "No.", "replyTo": "question"}
        inbox.receive(self.path, "reply", reply)
        request = reconciliation("reply", base_position=1, revision=1)
        claim, = request["analysis"]["assertions"]
        claim.update(text="A negative reply was recorded.", evidence=[{"source": "reply", "quote": "No."}])
        inbox.commit(self.path, "apply-reply", **request)

        def prepare():
            prepared = handoff.prepare(self.path)
            return prepared, json.loads(prepared["preparation"]["messages"][1]["content"])

        self.assertEqual(prepare()[1]["reply_context"], {"question": {"status": "missing"}})
        question = {**SOURCE, "text": "Count them a third time?"}
        inbox.receive(self.path, "question", question)
        pending = prepare()[1]
        self.assertEqual(pending["reply_context"], {"question": {"status": "pending"}})
        self.assertNotIn(question["text"], json.dumps(pending))
        disposition = {"mode": "dependent-no-op", "claims": ["claim-count-one"], "reason": "Context only.",
                       "basis": [{"source": "count-one", "quote": SOURCE["text"]}]}
        inbox.commit(self.path, "apply-question", base_position=2, batch=["question"],
                     patch={"baseRevision": 2, "operations": [], "rationale": "Record coverage without adding a claim.",
                            "accounting": {"question": disposition}},
                     analysis=reconciliation()["analysis"], route={"action": "analyze"})
        physical = self.path.read_bytes()
        prepared, context = prepare()
        self.assertEqual(context["reply_context"], {"question": {"status": "processed", "anchor": question["anchor"],
                                                                  "passages": [question["text"]]}})
        self.assertNotIn("question", context["sources"])
        candidate = copy.deepcopy(self.local_patch)
        candidate["baseRevision"] = context["current_revision"]
        candidate["operations"][0]["assertion"]["evidence"].append({"source": "question", "quote": question["text"]})
        with self.assertRaisesRegex(ValueError, "outside the prepared context"):
            handoff.inspect(self.path, json.dumps(candidate).encode(), prepared=prepared)
        self.assertEqual(self.path.read_bytes(), physical)

    def test_prepared_inspection_rejects_persistent_ids_and_unused_slots(self):
        prepared = handoff.prepare(self.path)
        before = inbox.snapshot(self.path)
        persistent = {key: value for key, value in self.patch.items() if key != "accounting"}
        with self.assertRaisesRegex(ValueError, "listed new slot"):
            handoff.inspect(self.path, json.dumps(persistent).encode(), prepared=prepared)
        candidate = copy.deepcopy(self.local_patch)
        candidate["operations"][1]["replacement"] = "new-2"
        with self.assertRaisesRegex(ValueError, "declared replacement reference"):
            handoff.inspect(self.path, json.dumps(candidate).encode(), prepared=prepared)
        self.assertEqual(inbox.snapshot(self.path), before)

    def test_overlap_nominates_distinct_meanings_without_a_merge_instruction(self):
        quote = "Venue is Oak hall. Date is Friday."
        claims = [{"id": "existing-1", "text": "Venue is Oak hall.", "scope": "venue",
                   "evidence": [{"source": "note", "quote": quote}]},
                  {"id": "existing-2", "text": "Date is Friday.", "scope": "date",
                   "evidence": [{"source": "note", "quote": quote}]}]
        before = copy.deepcopy(claims)
        self.assertEqual(handoff._evidence_overlap(claims), {"status": "complete", "matching_pairs": 1,
                         "pairs": [{"claims": ["existing-1", "existing-2"],
                                    "shared_source_count": 1, "shared_quote_count": 1}]})
        self.assertEqual(claims, before)
        claims[1]["evidence"][0]["source"] = "other"
        self.assertEqual(handoff._evidence_overlap(claims)["pairs"], [])
        instructions = handoff.prepare(self.path)["preparation"]["messages"][0]["content"]
        self.assertIn("do not prove equivalent claims or independent support", instructions)

    def test_overlap_bounds_only_limit_comparison_metadata(self):
        claims = [{"id": f"existing-{i}", "evidence": [{"source": "note", "quote": "Same quote."}]}
                  for i in range(1, 34)]
        limited = handoff._evidence_overlap(claims[:5])
        self.assertEqual(limited["status"], "truncated")
        self.assertEqual(limited["matching_pairs"], 10)
        self.assertEqual(len(limited["pairs"]), 8)
        self.assertEqual(handoff._evidence_overlap(claims), {"status": "skipped-claim-limit", "pairs": []})
        with patch.object(handoff, "MAX_OVERLAP_CLAIMS", 0):
            prepared = handoff.prepare(self.path)["preparation"]
        context = json.loads(prepared["messages"][1]["content"])
        self.assertEqual(context["evidence_overlap"]["status"], "skipped-claim-limit")
        self.assertEqual(len(context["current_claims"]), 1)
        self.assertEqual(set(context["sources"]), {"count-one"})

    def test_accounting_is_owned_by_the_workbench_only_for_prepared_proposals(self):
        prepared = handoff.prepare(self.path)
        before = inbox.snapshot(self.path)
        for accounting in ({}, {"count-one": {"mode": "represented"}}):
            candidate = {**self.local_patch, "accounting": accounting}
            with self.assertRaisesRegex(ValueError, "#MaintenanceProposal"):
                handoff.inspect(self.path, json.dumps(candidate).encode(), prepared=prepared)
        canonical = {key: value for key, value in self.patch.items() if key != "accounting"}
        with self.assertRaises((ValueError, KeyError)):
            handoff.inspect(self.path, json.dumps(canonical).encode())
        self.assertEqual(inbox.snapshot(self.path), before)

    def test_new_receipt_without_revision_change_also_invalidates_inspection(self):
        report = handoff.inspect(self.path, self.raw)
        inbox.receive(self.path, "count-two", SOURCE)
        before = inbox.snapshot(self.path)
        with self.assertRaisesRegex(ValueError, "state changed since inspection"):
            handoff.apply(self.path, "maintain-one", report, inspection_sha256=report["inspection_sha256"])
        self.assertEqual(inbox.snapshot(self.path), before)
        self.assertEqual(inbox.activity(self.path)["rejections"], [])
