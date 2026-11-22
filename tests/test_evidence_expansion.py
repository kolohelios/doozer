"""Conditional proof algebra and bounded visibility, not semantic gold grading."""

import copy
import gzip
import hashlib
import io
import json
import os
import subprocess
from pathlib import Path
import tempfile
from unittest import TestCase, mock

from scripts import evidence_expansion as expansion, evidence_graph as graph


class EvidenceGraphTests(TestCase):
    def test_no_witness_does_not_create_a_negative_fact(self):
        self.assertEqual(graph.evidence_state([], []), "unestablished")
        self.assertEqual(graph.evidence_state(["a"], []), "supported")
        self.assertEqual(graph.evidence_state([], ["b"]), "opposed")
        self.assertEqual(graph.evidence_state(["a"], ["b"]), "contested")

    def test_provenance_requires_resolved_roots_not_document_count(self):
        hypothesis = {"guard": "origins", "subjects": ["d1", "d2"]}
        initial = [{"id": "d1", "origin": "a"}, {"id": "d2", "originFrom": "d3"}]
        self.assertEqual(graph.origin_guard(hypothesis, initial)["state"], "unestablished")
        self.assertEqual(graph.origin_guard(hypothesis, initial + [{"id": "d3", "origin": "a"}])["state"], "opposed")
        self.assertEqual(graph.origin_guard(hypothesis, initial + [{"id": "d3", "origin": "b"}])["state"], "supported")
        with self.assertRaises(ValueError):
            graph.origin_guard(hypothesis, initial + [{"id": "d3", "originFrom": "d2"}])

    def test_scope_and_supersession_filter_proofs_without_erasing_history(self):
        sources = [{"id": "d1", "scope": "west", "text": "P."}, {"id": "d2", "scope": "east", "text": "P."},
                   {"id": "d3", "scope": "west", "text": "Not P.", "supersedes": ["d1", "d2"]}]
        packet = graph.view(sources)
        self.assertEqual(packet["retired_source_ids"], ["d1"])
        self.assertEqual(len(packet["sources"]), 3)
        self.assertEqual(packet["ignored_supersessions"], [["d3", "d2"]])
        proof = graph.compile_proof({"scope": "west", "guard": "none"}, {"positive": ["d1-s0", "d2-s0"], "negative": ["d3-s0"]}, packet)
        self.assertEqual(proof["raw_proposed_state"], "contested")
        self.assertEqual(proof["guarded_state"], "opposed")
        self.assertEqual({entry["reason"] for entry in proof["rejected"]}, {"historical", "different-scope"})
        sources[0]["supersedes"] = ["d3"]
        with self.assertRaises(ValueError):
            graph.view(sources)

    def test_expansion_is_bounded_reference_closure_not_an_oracle_search(self):
        initial = [{"id": "d1", "references": ["d2"], "scope": "x", "text": "Initial."}]
        catalog = [{"id": "d2", "references": ["d3"], "scope": "x", "text": "Second."},
                   {"id": "d3", "scope": "x", "text": "Third."}, {"id": "d9", "scope": "x", "text": "Unlinked."}]
        visible, log = graph.expand(initial, catalog, {"maxDocuments": 2, "maxHops": 2, "maxBytes": 1000})
        self.assertEqual({source["id"] for source in visible}, {"d1", "d2", "d3"})
        self.assertEqual(log["documents_added"], 2)
        for key, value, status in (("maxDocuments", 0, "document-limit"), ("maxHops", 0, "hop-limit"), ("maxBytes", 0, "byte-limit")):
            limits = {"maxDocuments": 2, "maxHops": 2, "maxBytes": 1000, key: value}
            visible, log = graph.expand(initial, catalog, limits)
            self.assertEqual(len(visible), 1)
            self.assertEqual(log["requests"][0]["status"], status)
        _, log = graph.expand(initial, [], {"maxDocuments": 2, "maxHops": 2, "maxBytes": 1000})
        self.assertEqual(log["requests"][0]["status"], "unavailable")


class ExpansionTests(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = expansion.multi.export_cue(sorted(expansion.DIRECTORY.glob("*.cue")))

    def prepared(self):
        return expansion.prepare(self.data)

    def sender(self, endpoint, payload, token):
        self.assertEqual(token, "SECRET_CANARY")
        self.assertNotIn("UNRETRIEVED_CATALOG_CANARY", json.dumps(payload))
        result = {"model": payload["model"], "usage": {"cost": 0.001, "input_tokens": 100, "output_tokens": 100}}
        if endpoint == expansion.multi.split.DECISIONS:
            result["answers"] = {key: {"type": "choice", "choice": "justified" if key == "warrant" else "unestablished", "confidence": 0.7} for key in payload["questions"]}
        else:
            state = json.loads(payload["messages"][1]["content"])
            hypotheses = state["hypotheses_not_premises"]
            if "proposal_summary" in state:
                self.assertNotIn("untrusted_previous_proposal", state)
                value = {"rationale": "Recorded structural fixture.", "narrativeIssues": [], "ledgers": [
                    {"id": item["id"], "spans": [{"id": key, "relation": "neither", "rationale": "Recorded structural fixture."} for key in state["visible_packet"]["spans"]]} for item in hypotheses]}
            else:
                value = {"summary": "Visible evidence is limited; no canonical claim is made.", "uncertainties": ["Recorded structural fixture."], "changes": [],
                         "proofs": [{"id": item["id"], "positive": [], "negative": [], "rationale": "Recorded structural fixture."} for item in hypotheses]}
            result["choices"] = [{"finish_reason": "stop", "message": {"content": json.dumps(value)}}]
        return result

    def test_frozen_artifacts_and_summaries_are_lossless_not_semantic_gold(self):
        from scripts import evidence_direction
        observations = self.data["expansionObservations"]
        for spec, module in ((observations, expansion), (observations["directionControl"], evidence_direction)):
            compressed = (expansion.ROOT / spec["artifact"]).read_bytes()
            raw = gzip.decompress(compressed)
            self.assertEqual(hashlib.sha256(compressed).hexdigest(), spec["archiveSHA256"])
            self.assertEqual(hashlib.sha256(raw).hexdigest(), spec["uncompressedSHA256"])
            report = json.loads(raw)
            self.assertEqual(expansion.multi.pilot.digest(report["protocol"]["frozen"]), spec["protocolSHA256"])
            self.assertEqual(report["summary"], module.summarize(report))
            self.assertEqual(report["source_commit"], spec["sourceCommit"])
            self.assertEqual(len(report["trace"]), spec["calls"])
            self.assertAlmostEqual(report["accounted_or_reserved_usd"], spec["reportedCostUSD"])

    def test_forks_share_one_initial_state_and_hide_future_catalog(self):
        report = self.prepared()
        frozen = report["protocol"]["frozen"]
        self.assertEqual(frozen["planned_calls"], 68)
        self.assertEqual(sum(len(f["branches"]) for f in frozen["families"]), 12)
        for family in frozen["families"]:
            op = expansion.operation(family, None, {}, None, "initial", frozen["plan"])
            encoded = json.dumps(op["payload"])
            self.assertNotIn("UNRETRIEVED_CATALOG_CANARY", encoded)
            self.assertNotIn("reference_reason", encoded)
            self.assertNotIn("initialExpected", encoded)
            visible = json.loads(op["payload"]["messages"][1]["content"])["visible_packet"]
            self.assertEqual(visible, family["before"])
            self.assertNotIn("d3", {source["id"] for source in visible["sources"]})
            for branch in family["branches"]:
                self.assertNotIn("d9", {source["id"] for source in branch["after"]["sources"]})

    def test_constructive_countermodels_keep_epistemic_and_version_acts_separate(self):
        controls = self.data["proofControls"]
        self.assertEqual(controls["dateCountermodel"]["world"]["exception"]["effectiveDate"], "2027-05-16")
        self.assertFalse(controls["dateCountermodel"]["epistemic"]["exception"]["effectiveDateEstablishedHere"])
        self.assertTrue(controls["withdrawalCountermodel"]["world"]["meadow-april-10"]["normalCatalogAvailable"])
        self.assertTrue(controls["withdrawalCountermodel"]["sourceActs"]["meadow-april-10"]["priorAssuranceWithdrawn"])
        for name, value in (("otherScopeAllowsP", True), ("otherScopeAllowsNotP", False)):
            self.assertEqual(controls[name]["world"]["production-west"]["readsQuietMail"], value)
            self.assertTrue(controls[name]["world"]["production-east"]["readsQuietMail"])
        source = expansion.DIRECTORY / "proof-controls.cue"
        for left, right in (("accessTarget", "accessOpposition"), ("dateTarget", "dateAlternative")):
            result = subprocess.run(["cue", "eval", str(source), "-e", f"proofControls.{left} & proofControls.{right}"], capture_output=True, text=True, check=False)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("conflicting values", result.stderr)

    def test_partial_parent_keeps_known_location_without_inventing_date(self):
        family = next(f for f in self.prepared()["protocol"]["frozen"]["families"] if f["id"] == "parent-recovery")
        branch = next(b for b in family["branches"] if b["variant"] == "v2")
        self.assertEqual(branch["expected"], {"p0": "supported", "p1": "unestablished"})
        self.assertEqual(branch["retrieval"]["documents_added"], 1)
        self.assertNotIn("d3", branch["after"]["unread_reference_ids"])

    def test_recorded_dag_preserves_all_states_and_never_retries(self):
        report = self.prepared()
        with mock.patch.dict(os.environ, {"OPENROUTER_API_KEY": "SECRET_CANARY"}):
            expansion.run(report, lambda: None, sender=self.sender)
        self.assertEqual(report["status"], "completed")
        self.assertEqual(len(report["trace"]), 68)
        self.assertAlmostEqual(report["accounted_or_reserved_usd"], 0.068)
        self.assertEqual(report["summary"]["complete_trajectories"], 12)
        for root in report["families"]:
            self.assertEqual(len({row["shared_initial_parent"]["proposal_sha256"] for row in root["branches"]}), 1)
        self.assertNotIn("SECRET_CANARY", json.dumps(report))
        with self.assertRaises(ValueError):
            expansion.run(report, lambda: None, sender=self.sender)

    def test_invalid_audit_is_not_replaced_or_hidden_by_later_valid_steps(self):
        report = self.prepared()
        def bad(endpoint, payload, token):
            response = self.sender(endpoint, payload, token)
            if payload["model"] == "google/gemini-2.5-pro":
                response["choices"][0]["message"]["content"] = "not JSON"
            return response
        with mock.patch.dict(os.environ, {"OPENROUTER_API_KEY": "SECRET_CANARY"}):
            expansion.run(report, lambda: None, sender=bad)
        self.assertEqual(len(report["trace"]), 68)
        self.assertEqual(report["summary"]["complete_trajectories"], 0)
        self.assertTrue(all(row["audit"]["status"] == "invalid" for root in report["families"] for row in root["branches"]))

    def test_limits_protocol_and_existing_paths_are_guarded(self):
        for budget, calls in ((5.01, 80), (5, 81), (5, 67)):
            with self.subTest(budget=budget, calls=calls), self.assertRaises(ValueError):
                expansion.prepare(self.data, budget, calls)
        report = self.prepared()
        report["protocol"]["frozen"]["families"][0]["question"] += " changed"
        sender = mock.Mock()
        with self.assertRaises(ValueError):
            expansion.run(report, lambda: None, sender=sender)
        sender.assert_not_called()
        with tempfile.TemporaryDirectory() as directory, mock.patch("sys.stdout", new_callable=io.StringIO):
            path = Path(directory) / "plan.json"
            self.assertEqual(expansion.main(["--output", str(path)]), 0)
            before = path.read_bytes()
            self.assertEqual(expansion.main(["--output", str(path)]), 2)
            self.assertEqual(before, path.read_bytes())
