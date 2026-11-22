"""Panel isolation, conditional scalar logic, and visible shared-failure controls."""

import copy
import io
import json
import os
from pathlib import Path
import tempfile
from unittest import TestCase, mock

from scripts import source_ir as ir, source_panel as panel


class PanelTests(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = panel.multi.export_cue(sorted(panel.DIRECTORY.glob("*.cue")))
        cls.template = panel.prepare(cls.data)
        cls.packets = {p["id"]: p for p in cls.template["protocol"]["frozen"]["packets"]}

    def prepared(self):
        return copy.deepcopy(self.template)

    def compiled_reference(self, name):
        packet = self.packets[name]
        return packet, ir.compile_ledger(panel.reference_ledger(packet), packet)

    def test_reference_states_are_conditional_consistency_not_semantic_gold(self):
        count = 0
        for packet in self.packets.values():
            compiled = ir.compile_ledger(panel.reference_ledger(packet), packet)
            self.assertFalse(compiled["rejected"])
            for q in packet["queries"]:
                self.assertEqual(ir.evaluate(compiled, q["binding"], q["value"])["state"], q["expected"])
                count += 1
        self.assertEqual(count, 17)

    def test_declared_finite_domain_can_exclude_the_only_other_value(self):
        compiled = {"constraints": [{"binding": "b0", "operator": "neq", "value": "forbidden", "witness": "w0"}], "domains": {"b0": ["permitted", "forbidden"]}}
        self.assertEqual(ir.evaluate(compiled, "b0", "permitted")["state"], "supported")
        self.assertEqual(ir.evaluate(compiled, "b0", "forbidden")["state"], "opposed")
        compiled["domains"] = {}
        self.assertEqual(ir.evaluate(compiled, "b0", "permitted")["state"], "unestablished")

    def test_unknown_and_other_date_exclusion_do_not_become_not_target_date(self):
        packet, compiled = self.compiled_reference("date-not-established")
        self.assertEqual(ir.evaluate(compiled, "b0", "2028-10-05")["state"], "unestablished")
        self.assertEqual(ir.evaluate(compiled, "b0", "2028-10-03")["state"], "opposed")
        self.assertTrue(any(r["atom"]["kind"] == "epistemic" for r in compiled["records"]))
        self.assertIn("epistemic", ir.render(compiled, packet, "interpreter"))

    def test_withdrawal_does_not_revoke_permission_or_retire_other_properties(self):
        _, compiled = self.compiled_reference("assurance-withdrawn")
        self.assertEqual(ir.evaluate(compiled, "b0", "permitted")["state"], "unestablished")
        self.assertEqual(ir.evaluate(compiled, "b1", "Juniper room")["state"], "supported")
        prior = [r for r in compiled["records"] if r["source"] == "d1"]
        self.assertEqual({r["atom"]["binding"]: r["current_effect"] for r in prior}, {"b0": False, "b1": True})
        self.assertEqual(len(compiled["records"]), 4)

    def test_permission_revocation_is_not_merely_lost_assurance(self):
        _, compiled = self.compiled_reference("permission-revoked")
        self.assertEqual(ir.evaluate(compiled, "b0", "permitted")["state"], "opposed")
        self.assertEqual(ir.evaluate(compiled, "b1", "Alder room")["state"], "supported")

    def test_conflict_and_property_scoped_replacement(self):
        _, conflict = self.compiled_reference("unresolved-conflict")
        self.assertEqual(ir.evaluate(conflict, "b0", "enabled")["state"], "contested")
        _, replacement = self.compiled_reference("property-scoped-replacement")
        self.assertEqual(ir.evaluate(replacement, "b0", "enabled")["state"], "opposed")
        self.assertEqual(ir.evaluate(replacement, "b1", "Ridge vault")["state"], "supported")

    def test_questions_directives_and_other_scopes_are_not_world_values(self):
        _, question = self.compiled_reference("question-and-directive")
        self.assertEqual(ir.evaluate(question, "b0", "2028-10-05")["state"], "unestablished")
        _, other = self.compiled_reference("different-environment")
        self.assertEqual(ir.evaluate(other, "b0", "enabled")["state"], "unestablished")
        self.assertEqual(ir.evaluate(other, "b1", "enabled")["state"], "supported")

    def test_grounding_modal_type_and_declared_scope_rejections_remain_visible(self):
        packet = self.packets["different-environment"]
        bad = panel.reference_ledger(packet)
        bad["ledger"][0]["atoms"][0]["binding"] = "b0"
        compiled = ir.compile_ledger(bad, packet)
        self.assertEqual(len(compiled["rejected"]), 1)
        self.assertIn("assertion scope", compiled["rejected"][0]["reason"])
        packet = self.packets["date-established"]
        bad = panel.reference_ledger(packet)
        date = next(a for a in bad["ledger"][0]["atoms"] if a["binding"] == "b0")
        date["value"] = "2028-10-03"  # Metadata timestamp exists, source literal does not.
        compiled = ir.compile_ledger(bad, packet)
        self.assertTrue(any("not grounded" in r["reason"] for r in compiled["rejected"]))
        date.update(kind="epistemic", operator="unknown")
        compiled = ir.compile_ledger(bad, packet)
        self.assertTrue(any("cannot carry a world value" in r["reason"] for r in compiled["rejected"]))

    def test_revision_crossing_authority_is_rejected_and_history_retained(self):
        packet = copy.deepcopy(self.packets["assurance-withdrawn"])
        packet["source_index"]["d2"]["authority"] = "unrelated-speaker"
        compiled = ir.compile_ledger(panel.reference_ledger(packet), packet)
        self.assertTrue(compiled["rejected"])
        self.assertEqual(ir.evaluate(compiled, "b0", "permitted")["state"], "supported")
        self.assertTrue(any(r["source"] == "d1" and r["current_effect"] for r in compiled["records"]))

    def test_cyclic_revision_proposals_do_not_pick_a_winner(self):
        packet = copy.deepcopy(self.packets["assurance-withdrawn"])
        packet["spans"]["d1-p0"]["text"] += " d2"
        ledger = {"ledger": [{"span": "d1-p0", "atoms": [{"kind": "supersedes", "binding": "b0", "operator": "none", "value": None, "target": "d2"}]},
                             {"span": "d2-p0", "atoms": [{"kind": "supersedes", "binding": "b0", "operator": "none", "value": None, "target": "d1"}]}]}
        with self.assertRaises(ValueError):
            ir.compile_ledger(ledger, packet)

    def test_extractor_inputs_are_blind_and_audit_never_sees_evaluation_labels(self):
        plan = self.template["protocol"]["frozen"]["plan"]
        packet = self.packets["date-not-established"]
        row = {"interpreter": {"status": "invalid", "value": "INTERPRETER_CANARY"}, "baseline": {"value": "BASELINE_CANARY"}}
        a = panel.operation(packet, row, "interpreter", plan)["payload"]
        b = panel.operation(packet, row, "verifier", plan)["payload"]
        self.assertEqual(a["messages"], b["messages"])
        for role in ("interpreter", "verifier", "auditor"):
            payload = json.dumps(panel.operation(packet, row, role, plan)["payload"])
            for secret in ("INTERPRETER_CANARY", "BASELINE_CANARY", "2028-10-05", '"expected"', '"reference"', '"queries"'):
                self.assertNotIn(secret, payload)
        self.assertNotIn("temperature", panel.operation(packet, row, "auditor", plan)["payload"])

    def sender(self, endpoint, payload, token):
        self.assertEqual(token, "SECRET_CANARY")
        state = payload.get("state") or json.loads(payload["messages"][1]["content"])
        packet = next(p for p in self.packets.values() if p["sources"] == state["sources"])
        response = {"model": payload["model"], "usage": {"cost": 0.001, "prompt_tokens": 100, "completion_tokens": 100}}
        if endpoint == panel.multi.split.DECISIONS:
            response["answers"] = {q["id"]: {"type": "choice", "choice": q["expected"]} for q in packet["queries"]}
        else:
            if "untrusted_interpretations" in state:
                value = {"checks": [{"span": span, "interpreter": "faithful", "verifier": "faithful", "issues": [], "rationale": "Recorded structural fixture."} for span in packet["spans"]], "limitations": []}
            else:
                value = panel.reference_ledger(packet)
            response["choices"] = [{"finish_reason": "stop", "message": {"content": json.dumps(value)}}]
        return response

    def test_shared_controls_are_frozen_admissible_and_not_exposed_as_mutations(self):
        plan = self.template["protocol"]["frozen"]["plan"]
        for packet in self.packets.values():
            control = packet["shared_control"]
            self.assertFalse(control["compiled"]["rejected"])
            self.assertFalse(panel.reference_match(ir.material(next(e for e in control["value"]["ledger"] if e["span"] == control["fault_span"])["atoms"]), packet, control["fault_span"]))
            payload = panel.operation(packet, {}, "audit_control", plan)["payload"]
            state = json.loads(payload["messages"][1]["content"])
            self.assertEqual(state["untrusted_interpretations"]["interpreter"], state["untrusted_interpretations"]["verifier"])
            for hidden in ('"controlFault"', '"fault_span"', '"queries"', "authored shared-error"):
                self.assertNotIn(hidden, json.dumps(payload))
            self.assertNotIn("temperature", payload)

    def test_recorded_panel_has_no_acceptance_vote_or_resampling(self):
        report = self.prepared()
        with mock.patch.dict(os.environ, {"OPENROUTER_API_KEY": "SECRET_CANARY"}):
            panel.run(report, lambda: None, sender=self.sender)
        self.assertEqual(report["status"], "completed")
        self.assertEqual(len(report["trace"]), 40)
        self.assertAlmostEqual(report["accounted_or_reserved_usd"], 0.040)
        self.assertEqual(report["summary"]["complete_trajectories"], 8)
        self.assertTrue(all(case["panel"] == "unchecked-agreement-not-acceptance" for case in report["summary"]["cases"].values()))
        self.assertNotIn("SECRET_CANARY", json.dumps(report))
        with self.assertRaises(ValueError):
            panel.run(report, lambda: None, sender=self.sender)

    def test_shared_semantic_error_can_pass_agreement_and_must_not_be_truth(self):
        report = self.prepared()
        def shared(endpoint, payload, token):
            response = self.sender(endpoint, payload, token)
            if payload["model"] in {"openai/gpt-4.1", "google/gemini-2.5-pro"}:
                value = json.loads(response["choices"][0]["message"]["content"])
                state = json.loads(payload["messages"][1]["content"])
                if "2028-10-05?" in state["sources"][0]["paragraphs"][0]:
                    value["ledger"][0]["atoms"].append({"kind": "world", "binding": "b0", "operator": "eq", "value": "2028-10-05", "target": None})
                    response["choices"][0]["message"]["content"] = json.dumps(value)
            return response
        with mock.patch.dict(os.environ, {"OPENROUTER_API_KEY": "SECRET_CANARY"}):
            panel.run(report, lambda: None, sender=shared)
        case = report["summary"]["cases"]["question-and-directive"]
        self.assertEqual(case["panel"], "unchecked-agreement-not-acceptance")
        self.assertEqual(case["states"]["interpreter"]["q0"], "supported")
        self.assertEqual(report["summary"]["audit"]["shared_discrepancy_spans"], 1)
        self.assertEqual(report["summary"]["audit"]["shared_discrepancies_both_challenged"], 0)

    def test_invalid_audit_stays_in_denominator_and_baseline_does_not_repair_it(self):
        report = self.prepared()
        def invalid(endpoint, payload, token):
            response = self.sender(endpoint, payload, token)
            if payload["model"] == "openai/o3":
                response["choices"][0]["message"]["content"] = "not JSON"
            return response
        with mock.patch.dict(os.environ, {"OPENROUTER_API_KEY": "SECRET_CANARY"}):
            panel.run(report, lambda: None, sender=invalid)
        self.assertEqual(len(report["trace"]), 40)
        self.assertEqual(report["summary"]["complete_trajectories"], 0)
        self.assertEqual(report["summary"]["audit"]["unassessed"], 24)

    def test_audit_error_needs_a_role_specific_original_source_anchor(self):
        packet = self.packets["date-established"]
        reference = panel.reference_ledger(packet)
        row = {role: {"status": "structurally-valid", "value": reference, "compiled": ir.compile_ledger(reference, packet)} for role in panel.EXTRACTORS}
        op = panel.operation(packet, row, "auditor", self.template["protocol"]["frozen"]["plan"])
        response = self.sender(op["endpoint"], op["payload"], "SECRET_CANARY")
        value = json.loads(response["choices"][0]["message"]["content"])
        value["checks"][0]["interpreter"] = "material-error"
        response["choices"][0]["message"]["content"] = json.dumps(value)
        with self.assertRaises(ValueError):
            panel.validate_response(response, op, packet)

    def test_unknown_billing_stops_without_retry(self):
        report = self.prepared()
        def failed(*args):
            raise OSError("recorded transport interruption")
        with mock.patch.dict(os.environ, {"OPENROUTER_API_KEY": "SECRET_CANARY"}), self.assertRaises(ValueError):
            panel.run(report, lambda: None, sender=failed)
        self.assertEqual(len(report["trace"]), 1)
        self.assertEqual(report["status"], "stopped-no-retry")
        self.assertGreater(report["accounted_or_reserved_usd"], 0)

    def test_protocol_limits_and_offline_new_only_cli(self):
        for budget, calls in ((5.01, 40), (5, 41), (5, 39)):
            with self.subTest(budget=budget, calls=calls), self.assertRaises(ValueError):
                panel.prepare(self.data, budget, calls)
        report = self.prepared()
        report["protocol"]["frozen"]["plan"]["version"] += " changed"
        with self.assertRaises(ValueError):
            panel.run(report, lambda: None)
        with tempfile.TemporaryDirectory() as directory, mock.patch("sys.stdout", new_callable=io.StringIO), mock.patch.object(panel, "run") as live:
            path = Path(directory) / "panel.json"
            self.assertEqual(panel.main(["--output", str(path)]), 0)
            before = path.read_bytes()
            self.assertEqual(panel.main(["--output", str(path)]), 2)
            self.assertEqual(before, path.read_bytes())
            live.assert_not_called()
