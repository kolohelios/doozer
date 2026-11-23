import copy
from contextlib import redirect_stdout
import io
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from scripts import reviewed_ir as ir, reviewed_panel as trial


class ReviewedPanelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = trial.prepare(trial.multi.export_cue(sorted(trial.DIRECTORY.glob("*.cue"))))
        cls.frozen = cls.report["protocol"]["frozen"]
        cls.packets = {p["id"]: p for p in cls.frozen["packets"]}

    def packet(self, thread, window="w1"):
        return copy.deepcopy(self.packets[thread + "/" + window])

    def compile(self, packet):
        return ir.compile_ledger(trial.reference_ledger(packet), packet)

    def ledger_entry(self, ledger, span):
        return next(e for e in ledger["ledger"] if e["span"] == span)

    def audit(self, packet, roles=None, fault=False):
        return {"checks": [{"binding": binding,
                            **{role: ("unavailable" if roles and roles[role]["proposal"] is None else "material-error" if fault and binding in packet["control"]["fault_bindings"] else "faithful") for role in trial.ROLES[:2]},
                            "issues": [{"affects": "both", "evidence": ["m1", "m7"], "detail": "Authored omitted or extra interpretation."}] if fault and binding in packet["control"]["fault_bindings"] else [],
                            "rationale": "Scripted test, not a semantic judge."} for binding in packet["binding_index"]], "limitations": []}

    def response(self, value, model, finish="stop", cost=0.001):
        return {"model": model, "choices": [{"finish_reason": finish, "message": {"content": json.dumps(value)}}],
                "usage": {"prompt_tokens": 1200, "completion_tokens": 300, "cost": cost}}

    def sender(self, fail_first=None):
        queue = [(packet, role) for packet in self.frozen["packets"] for role in (*trial.ROLES, *(["control"] if "control" in packet else []))]
        calls = []
        def send(endpoint, payload, token):
            packet, role = queue[len(calls)]
            calls.append(payload)
            state = json.loads(payload["messages"][1]["content"])
            if role in trial.ROLES[:2]:
                value = trial.reference_ledger(packet)
            else:
                value = self.audit(packet, state["untrusted_interpretations"], fault=role == "control")
            result = self.response(value, payload["model"])
            if len(calls) == 1 and fail_first:
                fail_first(result)
            return result
        return send, calls

    def test_preparation_is_fixed_and_offline(self):
        self.assertEqual(len(self.frozen["packets"]), 14)
        self.assertEqual(self.frozen["planned_calls"], 49)
        self.assertEqual(sum(len(p["queries"]) for p in self.frozen["packets"]), 32)
        self.assertEqual(self.report["trace"], [])
        self.assertEqual(self.frozen["review"]["decisions"]["interpretationApprovals"]["sharedPolicyApproval"], "not-separately-approved")

    def test_extractors_blind_to_peers_labels_and_future(self):
        packet = self.packet("drill-date-resolution", "w0")
        a = trial.operation(packet, {}, "interpreter", self.frozen)
        b = trial.operation(packet, {"interpreter": {"status": "valid", "value": {"canary": True}}}, "verifier", self.frozen)
        self.assertEqual(a["payload"]["messages"], b["payload"]["messages"])
        content = json.loads(a["payload"]["messages"][1]["content"])
        self.assertEqual(set(content), {"shared_semantic_contract", "current_window", "bindings", "original_sources", "unavailable_reference_ids", "boundary"})
        self.assertEqual([s["id"] for s in content["original_sources"]], ["m1", "m2", "m3", "m4"])
        self.assertNotIn("m7", json.dumps(a["payload"]))
        self.assertNotIn("canary", json.dumps(b["payload"]))
        self.assertFalse(a["payload"]["provider"]["allow_fallbacks"])
        self.assertNotEqual(a["payload"]["model"], b["payload"]["model"])

    def test_auditor_shares_contract_not_labels_or_control_identity(self):
        packet = self.packet("withdraw-only-assurance")
        op = trial.operation(packet, {}, "control", self.frozen)
        state = json.loads(op["payload"]["messages"][1]["content"])
        self.assertEqual(state["shared_semantic_contract"], trial.context(packet, self.frozen["shared_contract"])["shared_semantic_contract"])
        self.assertNotIn("fault_bindings", json.dumps(state))
        self.assertNotIn("reference", state)
        self.assertNotIn("temperature", op["payload"])
        self.assertTrue(all(p["proposal"] for p in state["untrusted_interpretations"].values()))

    def test_controls_include_equivalences_and_admissible_shared_faults(self):
        clean = faulty = 0
        for packet in self.frozen["packets"]:
            if "control" not in packet:
                continue
            case = packet["control"]
            a, b = (case["proposals"][r] for r in trial.ROLES[:2])
            self.assertFalse(a["compiled"]["rejected"] or b["compiled"]["rejected"])
            self.assertEqual(ir.material(a["compiled"], packet), ir.material(b["compiled"], packet))
            if case["kind"] == "equivalent":
                clean += 1
                self.assertNotEqual(a["value"], b["value"])
                self.assertEqual(ir.material(a["compiled"], packet), ir.material(self.compile(packet), packet))
            else:
                faulty += 1
                self.assertEqual(a["value"], b["value"])
                self.assertEqual(len(case["fault_bindings"]), 1)
        self.assertEqual((clean, faulty), (3, 4))

    def test_question_and_directive_do_not_assign_dates(self):
        packet = self.packet("drill-date-resolution", "w0")
        compiled = self.compile(packet)
        self.assertEqual(ir.evaluate(compiled, "b0", "2031-06-12")["state"], "unestablished")
        self.assertEqual(ir.evaluate(compiled, "b0", "2031-06-10")["state"], "opposed")
        self.assertTrue(any(r["atom"]["kind"] == "question" for r in compiled["records"]))
        self.assertTrue(any(r["atom"]["kind"] == "directive" for r in compiled["records"]))

    def test_unknown_owner_is_historical_not_current_fog(self):
        packet = self.packet("drill-date-resolution")
        compiled = self.compile(packet)
        view = ir.views(compiled, packet)["b0"]
        self.assertEqual(ir.evaluate(compiled, "b0", "2031-06-12")["state"], "supported")
        self.assertFalse(view["qualifications"])
        self.assertEqual(len(view["historical_source_conditions"]), 1)
        record = next(r for r in compiled["records"] if r["id"] in view["historical_source_conditions"])
        self.assertEqual((record["atom"]["holder"], record["frame"]), ("Rin", "w0"))

    def test_source_uncertainty_cannot_be_owned_by_extractor(self):
        packet = self.packet("drill-date-resolution", "w0")
        value = trial.reference_ledger(packet)
        self.ledger_entry(value, "m1")["atoms"][1]["holder"] = "extractor"
        compiled = ir.compile_ledger(value, packet)
        flags = ir.gates(packet, compiled)
        self.assertFalse(flags["b0"]["candidate_eligible"])
        self.assertTrue(flags["b1"]["candidate_eligible"])

    def test_coverage_is_bounded_not_a_source_ignorance_claim(self):
        packet = self.packet("regional-coverage", "w0")
        compiled = self.compile(packet)
        self.assertEqual(ir.evaluate(compiled, "b0", "enabled")["state"], "unestablished")
        self.assertEqual(ir.views(compiled, packet)["b0"]["coverage"]["sources"], ["m1", "m2", "m3", "m4"])
        self.assertFalse(any(r["atom"]["kind"] == "source-uncertainty" for r in compiled["records"]))

    def test_missing_parent_is_visible_coverage_not_source_ignorance(self):
        initial = self.packet("regional-coverage", "w0")
        final = self.packet("regional-coverage")
        self.assertEqual(initial["unavailable_reference_ids"], [])
        self.assertEqual(final["unavailable_reference_ids"], ["m0"])
        self.assertNotIn("m0", final["source_index"])
        compiled = self.compile(final)
        self.assertEqual(ir.views(compiled, final)["b0"]["coverage"]["unavailable_reference_ids"], ["m0"])
        self.assertFalse(any(r["atom"]["kind"] == "source-uncertainty" for r in compiled["records"]))
        value = trial.reference_ledger(final)
        guess = copy.deepcopy(self.ledger_entry(value, "m7")["atoms"][0])
        guess["value"] = "enabled"
        self.ledger_entry(value, "m5")["atoms"] = [guess]
        guessed = ir.compile_ledger(value, final)
        self.assertFalse(guessed["rejected"])  # Mechanics cannot resolve the missing parent.
        self.assertNotEqual(ir.material(guessed, final)["b0"], ir.material(compiled, final)["b0"])

    def test_provisional_qualifier_preserves_exactly_one_unknown_alternative(self):
        packet = self.packet("unresolved-qualifier")
        compiled = self.compile(packet)
        self.assertEqual(ir.evaluate(compiled, "b0", "2031-08-14")["state"], "supported")
        self.assertTrue(ir.views(compiled, packet)["b0"]["qualifications"])
        self.assertFalse(ir.views(compiled, packet)["b2"]["qualifications"])
        qualifiers = [r["atom"] for r in compiled["records"] if r["atom"]["kind"] == "qualifier"]
        self.assertTrue(all(a["operator"] == "one-provisional" and a["alternatives"] == ["b0", "b1"] for a in qualifiers))

    def test_assurance_withdrawal_does_not_imply_prohibition(self):
        packet = self.packet("withdraw-only-assurance")
        compiled = self.compile(packet)
        self.assertEqual(ir.evaluate(compiled, "b0", "permitted")["state"], "unestablished")
        self.assertEqual(ir.evaluate(compiled, "b0", "forbidden")["state"], "unestablished")
        self.assertEqual(ir.evaluate(compiled, "b1", "Copper hall")["state"], "supported")
        self.assertFalse(next(r for r in compiled["records"] if r["atom"]["kind"] == "assurance")["not_explicitly_retired"])

    def test_independent_grant_survives(self):
        packet = self.packet("independent-grant-survives")
        compiled = self.compile(packet)
        self.assertEqual(ir.evaluate(compiled, "b0", "permitted")["state"], "supported")
        self.assertTrue(next(r for r in compiled["records"] if r["atom"]["kind"] == "grant")["not_explicitly_retired"])
        self.assertFalse(next(r for r in compiled["records"] if r["atom"]["kind"] == "assurance")["not_explicitly_retired"])

    def test_revocation_is_scoped_normative_not_physical(self):
        packet = self.packet("actual-grant-revoked")
        compiled = self.compile(packet)
        self.assertEqual(ir.evaluate(compiled, "b0", "permitted")["state"], "opposed")
        self.assertEqual(packet["binding_index"]["b0"]["subject"], "booked visitors under grant m1")
        self.assertEqual(ir.evaluate(compiled, "b1", "Bronze hall")["state"], "supported")
        self.assertEqual(len(compiled["source_ids"]), 8)

    def test_conflict_does_not_hide_venue_or_resolve_by_repetition(self):
        packet = self.packet("equal-authority-date-conflict")
        compiled = self.compile(packet)
        self.assertEqual(ir.evaluate(compiled, "b0", "2031-10-11")["state"], "contested")
        self.assertEqual(ir.evaluate(compiled, "b1", "Maple hall")["state"], "supported")
        self.assertTrue(all(g["candidate_eligible"] for g in ir.gates(packet, compiled).values()))

    def test_mechanics_cannot_prove_entailment_even_when_states_match(self):
        packet = self.packet("regional-coverage")
        value = trial.reference_ledger(packet)
        added = copy.deepcopy(self.ledger_entry(value, "m7")["atoms"][0])
        self.ledger_entry(value, "m3")["atoms"].append(added)  # East observation wrongly transferred west.
        compiled = ir.compile_ledger(value, packet)
        self.assertFalse(compiled["rejected"])
        reference = self.compile(packet)
        self.assertEqual(ir.evaluate(compiled, "b0", "enabled")["state"], ir.evaluate(reference, "b0", "enabled")["state"])
        self.assertNotEqual(ir.material(compiled, packet)["b0"], ir.material(reference, packet)["b0"])

    def test_agreement_with_shared_fault_is_not_truth(self):
        packet = self.packet("withdraw-only-assurance")
        bad = packet["control"]["proposals"]["interpreter"]["compiled"]
        flags = ir.gates(packet, bad, bad, self.audit(packet), panel=True)
        self.assertTrue(flags["b0"]["candidate_eligible"])
        self.assertIn("never canonical acceptance", flags["b0"]["warning"])
        self.assertNotEqual(ir.material(bad, packet), ir.material(self.compile(packet), packet))

    def test_panel_flags_are_binding_local_and_never_replace_primary(self):
        packet = self.packet("withdraw-only-assurance")
        good = self.compile(packet)
        bad = packet["control"]["proposals"]["verifier"]["compiled"]
        row = {"interpreter": {"status": "valid", "value": trial.reference_ledger(packet), "compiled": good}, "verifier": packet["control"]["proposals"]["verifier"], "auditor": {"status": "valid", "value": self.audit(packet)}}
        masks = trial.assessments(packet, row)
        self.assertTrue(masks["single"]["b0"]["candidate_eligible"])
        self.assertFalse(masks["blind-check"]["b0"]["candidate_eligible"])
        self.assertFalse(masks["panel"]["b0"]["candidate_eligible"])
        self.assertTrue(masks["panel"]["b1"]["candidate_eligible"])
        self.assertEqual(ir.evaluate(good, "b0", "permitted")["state"], "unestablished")
        self.assertEqual(ir.evaluate(bad, "b0", "permitted")["state"], "opposed")

    def test_missing_primary_is_visible_not_a_verifier_fallback(self):
        packet = self.packet("actual-grant-revoked")
        row = {"verifier": {"compiled": self.compile(packet)}}
        masks = trial.assessments(packet, row)
        self.assertTrue(all(not flag["candidate_eligible"] for flags in masks.values() for flag in flags.values()))
        self.assertIn("primary-unavailable", masks["single"]["b0"]["reasons"])

    def test_grounding_and_target_checks_hold_only_affected_binding(self):
        packet = self.packet("actual-grant-revoked")
        value = trial.reference_ledger(packet)
        self.ledger_entry(value, "m1")["atoms"] = [a for a in self.ledger_entry(value, "m1")["atoms"] if a["kind"] != "grant"]
        compiled = ir.compile_ledger(value, packet)
        self.assertTrue(compiled["rejected"])
        flags = ir.gates(packet, compiled)
        self.assertFalse(flags["b0"]["candidate_eligible"])
        self.assertTrue(flags["b1"]["candidate_eligible"])

    def test_world_facts_cannot_be_hidden_in_conditions(self):
        packet = self.packet("regional-coverage")
        value = trial.reference_ledger(packet)
        entry = self.ledger_entry(value, "m2")
        entry["conditions"], entry["atoms"] = entry["atoms"], []
        self.assertIn("smuggle", ir.compile_ledger(value, packet)["rejected"][0]["reason"])

    def test_binary_complement_is_equivalent_not_open_domain_guess(self):
        packet = self.packet("regional-coverage")
        value = trial.reference_ledger(packet)
        atom = self.ledger_entry(value, "m7")["atoms"][0]
        # Test the algebra with an explicit complementary literal, not a hidden repair.
        packet["sources"][-2]["text"] += " It is not enabled."
        atom["operator"], atom["value"] = "neq", "enabled"
        actual = ir.compile_ledger(value, packet)
        self.assertEqual(ir.material(actual, packet), ir.material(self.compile(packet), packet))
        self.assertEqual(ir.evaluate(actual, "b0", "enabled")["state"], "opposed")
        unknown = self.compile(self.packet("drill-date-resolution", "w0"))
        self.assertEqual(ir.evaluate(unknown, "b0", "2031-06-12")["state"], "unestablished")

    def test_audit_verdict_issue_consistency_and_source_anchors(self):
        packet = self.packet("actual-grant-revoked")
        row = {role: {"status": "valid", "value": trial.reference_ledger(packet)} for role in trial.ROLES[:2]}
        op = trial.operation(packet, row, "auditor", self.frozen)
        value = self.audit(packet)
        value["checks"][0]["issues"] = [{"affects": "interpreter", "evidence": ["m1"], "detail": "Contradictory verdict."}]
        with self.assertRaises(ValueError):
            trial.validate_response(self.response(value, op["payload"]["model"]), op, packet)
        value["checks"][0]["interpreter"] = "material-error"
        self.assertEqual(trial.validate_response(self.response(value, op["payload"]["model"]), op, packet), value)
        value["checks"][0]["issues"][0]["evidence"] = ["m99"]
        with self.assertRaises(ValueError):
            trial.validate_response(self.response(value, op["payload"]["model"]), op, packet)

    def test_complete_mock_run_has_all_denominators_and_no_repairs(self):
        report = copy.deepcopy(self.report)
        sender, calls = self.sender()
        with patch.dict(os.environ, {"OPENROUTER_API_KEY": "offline-test-token"}):
            trial.run(report, lambda: None, sender)
        self.assertEqual((report["status"], len(calls)), ("completed", 49))
        self.assertEqual(report["summary"]["complete_snapshots"], 14)
        for counts in report["summary"]["arms"].values():
            self.assertEqual(counts["binding_units"], 32)
            self.assertEqual(counts["reference_faithful_eligible"], 32)
            self.assertEqual(counts["primary_reference_discrepancies"], 0)
        for counts in report["summary"]["roles"].values():
            self.assertEqual((counts["state_cells"], counts["state_matches_proposed"]), (32, 32))
        self.assertEqual(report["summary"]["controls"]["faults_both_challenged"], 4)
        self.assertEqual(report["summary"]["controls"]["false_challenges"], 0)
        self.assertAlmostEqual(report["accounted_or_reserved_usd"], 0.049)
        self.assertEqual(len(report["requests"]), 49)
        self.assertAlmostEqual(report["summary"]["costs"]["paired_arms_known_usd"]["single"], 0.014)
        self.assertAlmostEqual(report["summary"]["costs"]["paired_arms_known_usd"]["panel"], 0.042)
        for counts in report["summary"]["transitions"].values():
            self.assertEqual(counts["paired_bindings"], 16)
            self.assertEqual(counts["unaffected_material_bindings"], 9)
            self.assertEqual(counts["unaffected_faithful_eligible"], 9)
            self.assertEqual(counts["changed_state_queries"], 4)
            self.assertEqual(counts["changed_state_final_faithful_eligible"], 4)
            self.assertEqual(counts["stable_supported_queries"], 11)
            self.assertEqual(counts["stable_supported_final_faithful_eligible"], 11)

    def test_refusal_preserved_and_not_resampled(self):
        report = copy.deepcopy(self.report)
        def refuse(response):
            response["choices"][0]["finish_reason"] = "content_filter"
        sender, calls = self.sender(refuse)
        with patch.dict(os.environ, {"OPENROUTER_API_KEY": "offline-test-token"}):
            trial.run(report, lambda: None, sender)
        self.assertEqual(len(calls), 49)
        self.assertEqual(report["rows"][0]["interpreter"]["status"], "invalid")
        self.assertGreater(report["summary"]["arms"]["panel"]["unavailable_primary"], 0)
        self.assertEqual(report["trace"][0]["response"]["choices"][0]["finish_reason"], "content_filter")
        self.assertEqual(report["summary"]["arms"]["single"]["binding_units"], 32)

    def test_unknown_cost_stops_without_retry_or_dropped_denominators(self):
        report = copy.deepcopy(self.report)
        def unknown(response):
            response["usage"]["cost"] = None
        sender, calls = self.sender(unknown)
        with patch.dict(os.environ, {"OPENROUTER_API_KEY": "offline-test-token"}), self.assertRaises(ValueError):
            trial.run(report, lambda: None, sender)
        self.assertEqual((len(calls), report["status"]), (1, "stopped-no-retry"))
        self.assertEqual(report["trace"][0]["status"], "failed-or-unaccounted")
        self.assertIn("response", report["trace"][0])
        self.assertEqual(report["summary"]["arms"]["single"]["unavailable_primary"], 32)

    def test_declared_authority_cannot_be_borrowed_from_other_source(self):
        packet = self.packet("actual-grant-revoked")
        packet["source_index"]["m7"]["authority"] = "participant"
        compiled = self.compile(packet)
        self.assertIn("authority", compiled["rejected"][0]["reason"])
        self.assertEqual(ir.evaluate(compiled, "b0", "permitted")["state"], "supported")

    def test_withdrawal_cannot_borrow_another_actors_endorsement(self):
        packet = self.packet("withdraw-only-assurance")
        packet["source_index"]["m7"]["actor"] = "another coordinator"
        compiled = self.compile(packet)
        self.assertTrue(any("ownership" in r["reason"] for r in compiled["rejected"]))
        self.assertTrue(next(r for r in compiled["records"] if r["atom"]["kind"] == "assurance")["not_explicitly_retired"])

    def test_ambiguous_prior_assurance_is_held_not_mass_retired(self):
        packet = self.packet("withdraw-only-assurance")
        value = trial.reference_ledger(packet)
        entry = self.ledger_entry(value, "m1")
        opposite = copy.deepcopy(entry["atoms"][0])
        opposite["operator"] = "neq"
        entry["atoms"].append(opposite)
        compiled = ir.compile_ledger(value, packet)
        self.assertTrue(any("ambiguous" in r["reason"] for r in compiled["rejected"]))
        self.assertTrue(all(r["not_explicitly_retired"] for r in compiled["records"] if r["atom"]["kind"] == "assurance"))

    def test_partial_revision_cannot_erase_a_multi_binding_qualifier(self):
        packet = self.packet("unresolved-qualifier")
        value = trial.reference_ledger(packet)
        revision = copy.deepcopy(value["ledger"][0]["atoms"][0])
        revision.update(kind="supersession", binding="b0", operator="none", value=None, targetSource="m1", targetKind="qualifier")
        self.ledger_entry(value, "m7")["atoms"].append(revision)
        compiled = ir.compile_ledger(value, packet)
        self.assertTrue(compiled["rejected"])
        self.assertTrue(all(r["not_explicitly_retired"] for r in compiled["records"] if r["atom"]["kind"] == "qualifier"))
        self.assertTrue(ir.views(compiled, packet)["b1"]["qualifications"])

    def test_projection_exposes_acts_and_extractor_limits_without_world_effect(self):
        packet = self.packet("drill-date-resolution", "w0")
        value = trial.reference_ledger(packet)
        value["extractionLimits"] = [{"about": ["b0"], "evidence": ["m2"], "reason": "No claim of confirmation can be recovered from the question."}]
        compiled = ir.compile_ledger(value, packet)
        view = ir.views(compiled, packet)["b0"]
        kinds = {r["atom"]["kind"] for r in compiled["records"] if r["id"] in view["source_acts"]}
        self.assertEqual(kinds, {"question", "directive"})
        self.assertEqual(view["extractor_limits"][0]["origin"], "extractor-interpretation")
        self.assertFalse(ir.views(compiled, packet)["b1"]["extractor_limits"])
        self.assertEqual(ir.evaluate(compiled, "b0", "2031-06-12")["state"], "unestablished")
        self.assertEqual(ir.material(compiled, packet), ir.material(self.compile(packet), packet))

    def test_live_cli_requires_exact_prepared_hash_before_any_call_or_write(self):
        with TemporaryDirectory() as folder, patch.object(trial, "run", side_effect=AssertionError("network called")), redirect_stdout(io.StringIO()):
            path = Path(folder) / "attempt.json"
            result = trial.main(["--live", "--protocol-sha256", "wrong-hash", "--output", str(path)])
            self.assertEqual(result, 2)
            self.assertFalse(path.exists())
            result = trial.main(["--live", "--output", str(path)])
            self.assertEqual(result, 2)
            self.assertFalse(path.exists())

    def test_frozen_content_cannot_change_before_execution(self):
        report = copy.deepcopy(self.report)
        report["protocol"]["frozen"]["packets"][0]["sources"][0]["text"] += " mutated"
        with self.assertRaises(ValueError):
            trial.run(report, lambda: None, lambda *args: self.fail("network called"))
        self.assertFalse(report["trace"])

    def test_replay_is_not_resume(self):
        report = copy.deepcopy(self.report)
        report["trace"].append({"status": "failed-or-unaccounted"})
        with self.assertRaises(ValueError):
            trial.run(report, lambda: None, lambda *args: self.fail("network called"))


if __name__ == "__main__":
    unittest.main()
