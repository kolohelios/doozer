import copy
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from scripts import scale_panel as trial


class ScalePanelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = trial.prior.multi.export_cue(sorted(trial.prior.DIRECTORY.glob("*.cue")))
        with patch("urllib.request.urlopen", side_effect=AssertionError("offline preparation")):
            cls.report = trial.prepare(cls.data)
        cls.frozen = cls.report["protocol"]["frozen"]
        cls.packets = {p["id"]: p for p in cls.frozen["packets"]}

    def packet(self, name, window="w1"):
        return copy.deepcopy(self.packets[name + "/" + window])

    def proposal(self, packet):
        value = trial.reference(packet)
        return {"status": "valid", "value": value, "compiled": trial.compile_value(value, packet)}

    def judge(self, packet, availability=None, controlled=False):
        return {"checks": [{"binding": b,
                            **{r: "unavailable" if availability and not availability[r] else "material-error" if controlled and b in packet["control"]["fault_bindings"] else "faithful" for r in trial.ROLES[:2]},
                            "issues": [{"severity": "material", "affects": "both", "evidence": [packet["control"]["specification"]["span"]], "detail": "Scripted authored-fault observation; not a semantic judge."}] if controlled and b in packet["control"]["fault_bindings"] else [],
                            "rationale": "Offline scripted report."} for b in packet["context"]["binding_index"]], "limitations": []}

    def sender(self, mutate=None):
        queue = [(p, r) for p in self.frozen["packets"] for r in (*trial.ROLES, *(["control"] if "control" in p else []))]
        calls = []
        def send(endpoint, payload, token):
            packet, role = queue[len(calls)]
            calls.append(payload)
            if role in trial.ROLES[:2]:
                value = trial.reference(packet)
            else:
                context = json.loads(payload["messages"][1]["content"])
                available = {r: p["availability"] for r, p in context["untrusted_proposals"].items()}
                value = self.judge(packet, available, role == "control")
            response = {"model": payload["model"], "choices": [{"finish_reason": "stop", "message": {"content": json.dumps(value)}}], "usage": {"prompt_tokens": 1200, "completion_tokens": 300, "cost": 0.001}}
            if mutate:
                mutate(response, len(calls))
            return response
        return send, calls

    def test_exact_offline_schedule_and_all_denominators(self):
        self.assertEqual((len(self.frozen["packets"]), self.frozen["planned_calls"]), (24, 84))
        self.assertEqual(sum(len(p["queries"]) for p in self.frozen["packets"]), 72)
        self.assertEqual(self.report["trace"], [])
        self.assertEqual(self.frozen["limits"], {"budget_usd": 5.0, "max_calls": 84, "retries": 0})
        self.assertEqual(self.frozen["plan"]["transportTimeoutSeconds"], 300)
        self.assertEqual(set(self.frozen["metadata"]), set(trial.ROLES))
        summary = trial.summarize(self.report)
        self.assertEqual(summary["controls"]["planned"], 12)
        self.assertEqual(summary["controls"]["fault_bindings_planned"], 8)
        for role in summary["roles"].values():
            self.assertEqual((role["binding_units"], role["unavailable_binding_units"], role["query_cells"]), (72, 72, 72))
        for arm in summary["arms"].values():
            self.assertEqual((arm["binding_units"], arm["unavailable_primary"]), (72, 72))

    def test_blind_inputs_include_contract_not_peers_labels_or_future(self):
        packet = self.packet("04-note-date-gap", "w0")
        a = trial.operation(packet, {}, "interpreter", self.frozen)
        b = trial.operation(packet, {"interpreter": {"status": "valid", "value": {"canary": "peer-output"}}}, "verifier", self.frozen)
        self.assertEqual(a["payload"]["messages"], b["payload"]["messages"])
        state = json.loads(a["payload"]["messages"][1]["content"])
        self.assertEqual(len(state["original_sources"]), 8)
        self.assertNotIn("2032-05-14", json.dumps(a["payload"]))
        self.assertNotIn("peer-output", json.dumps(b["payload"]))
        self.assertNotIn("queries", state)
        self.assertNotIn("reference", state)
        self.assertEqual(state["unavailable_reference_ids"], ["absent-parent"])
        self.assertEqual(state["common_contract"], self.frozen["contract"])
        self.assertFalse(a["payload"]["provider"]["allow_fallbacks"])

    def test_auditor_cannot_see_control_labels_or_query_hypotheses(self):
        packet = self.packet("06-independent-grant")
        state = json.loads(trial.operation(packet, {}, "control", self.frozen)["payload"]["messages"][1]["content"])
        self.assertEqual(state["common_contract"], self.frozen["contract"])
        self.assertEqual(state["audit_reporting_contract"], self.frozen["audit_contract"]["instructions"])
        self.assertNotIn("control", state)
        self.assertNotIn("fault_bindings", json.dumps(state))
        self.assertNotIn("queries", state)
        self.assertTrue(all(p["availability"] for p in state["untrusted_proposals"].values()))

    def test_controls_are_admissible_and_expected_equivalences_or_shared_faults(self):
        clean = faulty = 0
        for packet in self.frozen["packets"]:
            if "control" not in packet:
                continue
            case = packet["control"]
            a, b = (case["proposals"][r] for r in trial.ROLES[:2])
            self.assertFalse(a["compiled"]["core"]["rejected"] or b["compiled"]["rejected_annotations"])
            expected = trial.profile(trial.compile_value(trial.reference(packet), packet), packet["context"])
            actual = [trial.profile(p["compiled"], packet["context"]) for p in (a, b)]
            if case["kind"] == "equivalent":
                clean += 1
                self.assertNotEqual(a["value"], b["value"])
                self.assertEqual(actual, [expected, expected])
            else:
                faulty += 1
                self.assertEqual(a["value"], b["value"])
                self.assertEqual(actual[0], actual[1])
                self.assertEqual({k for k in expected if actual[0][k] != expected[k]}, {"b0"})
        self.assertEqual((clean, faulty), (4, 8))

    def test_hunch_and_scope_faults_can_survive_literal_checks(self):
        for name in ("01-hunch-and-observation", "02-environment-coverage"):
            packet = self.packet(name)
            bad = packet["control"]["proposals"]["interpreter"]["compiled"]
            self.assertFalse(bad["core"]["rejected"] or bad["rejected_annotations"])
            self.assertNotEqual(trial.profile(bad, packet["context"]), trial.profile(trial.compile_value(trial.reference(packet), packet), packet["context"]))
        packet = self.packet("02-environment-coverage")
        self.assertEqual(trial.core.evaluate(packet["control"]["proposals"]["interpreter"]["compiled"]["core"], "b0", "enabled")["state"], "opposed")
        # Correct filtered state does not erase the extra wrong-scope witness.
        packet = self.packet("01-hunch-and-observation")
        self.assertEqual(trial.core.evaluate(packet["control"]["proposals"]["interpreter"]["compiled"]["core"], "b0", "enabled")["state"], "contested")

    def test_optional_notes_are_separately_reportable_not_personal_ignorance(self):
        packet = self.packet("04-note-date-gap")
        a, b = (packet["control"]["proposals"][r]["compiled"] for r in trial.ROLES[:2])
        self.assertEqual(trial.profile(a, packet["context"]), trial.profile(b, packet["context"]))
        self.assertNotEqual(trial.note_profile(a), trial.note_profile(b))
        packet = self.packet("03-personal-unknown")
        value = trial.reference(packet)
        next(e for e in value["ledger"] if e["span"] == "m3")["annotations"] = []
        self.assertNotEqual(trial.profile(trial.compile_value(value, packet), packet["context"]), trial.profile(trial.compile_value(trial.reference(packet), packet), packet["context"]))

    def test_nonmaterial_audit_cannot_clear_mechanical_flags_or_other_checks(self):
        packet = self.packet("07-grant-revocation")
        row = {r: self.proposal(packet) for r in trial.ROLES[:2]}
        value = row["interpreter"]["value"]
        next(e for e in value["ledger"] if e["span"] == "m13")["atoms"][0]["targetSource"] = "m5"
        row["interpreter"]["compiled"] = trial.compile_value(value, packet)
        judged = self.judge(packet)
        judged["checks"][0]["issues"] = [{"severity": "non-material", "affects": "both", "evidence": ["m1"], "detail": "Harmless formatting observation."}]
        row["auditor"] = {"status": "valid", "value": judged}
        flags = trial.masks(packet, row)
        self.assertTrue(flags["single"]["b0"])
        self.assertTrue(flags["panel"]["b0"])
        self.assertFalse(flags["panel"]["b1"])

    def test_full_mock_run_reuses_primary_and_reports_costs_and_transitions(self):
        report = copy.deepcopy(self.report)
        sender, calls = self.sender()
        with patch.dict(os.environ, {"OPENROUTER_API_KEY": "offline-test-token"}):
            trial.run(report, lambda: None, sender)
        self.assertEqual((report["status"], len(calls), len(report["trace"])), ("completed", 84, 84))
        summary = report["summary"]
        self.assertEqual((summary["complete_real_snapshots"], summary["complete_evaluations"]), (24, 24))
        self.assertEqual(summary["controls"]["faults_both_challenged"], 8)
        self.assertEqual(summary["controls"]["proposed_false_challenges"], 0)
        for arm in summary["arms"].values():
            self.assertEqual((arm["binding_units"], arm["reference_matching_eligible"]), (72, 72))
        for role in summary["roles"].values():
            self.assertEqual((role["query_cells"], role["query_matches"], role["profile_matches"]), (72, 72, 72))
        for counts in summary["transitions"].values():
            self.assertEqual(counts["paired_bindings"], 36)
            self.assertEqual(counts["unchanged_matching_eligible"], counts["unchanged_profiles"])
            self.assertEqual(counts["state_pair_matches"], counts["state_changes"])
        self.assertAlmostEqual(report["accounted_or_reserved_usd"], 0.084)
        self.assertAlmostEqual(summary["costs"]["known_arms_usd"]["single"], 0.024)
        self.assertAlmostEqual(summary["costs"]["known_arms_usd"]["panel"], 0.072)
        for packet, row in zip(self.frozen["packets"], report["rows"]):
            for role in trial.ROLES[:2]:
                self.assertEqual(row[role]["value"], trial.reference(packet))
                self.assertFalse(any(v["canonical_acceptance"] for views in row[role]["reader_views"].values() for v in views.values()))
        with self.assertRaises(ValueError):
            trial.run(report, lambda: None, sender)
        self.assertEqual(len(calls), 84)

    def test_unknown_billing_stops_without_retry_and_keeps_all_denominators(self):
        report = copy.deepcopy(self.report)
        sender, calls = self.sender(lambda response, n: response["usage"].update(cost=None))
        with patch.dict(os.environ, {"OPENROUTER_API_KEY": "offline-test-token"}), self.assertRaises(ValueError):
            trial.run(report, lambda: None, sender)
        self.assertEqual((len(calls), report["status"]), (1, "stopped-no-retry"))
        self.assertTrue(report["trace"][0]["reserved_usd"] > 0)
        self.assertEqual(report["rows"][0]["interpreter"]["status"], "call-failed")
        self.assertEqual(report["summary"]["arms"]["single"]["unavailable_primary"], 72)
        self.assertEqual(report["summary"]["controls"]["planned"], 12)

    def test_invalid_but_accounted_output_is_preserved_not_resampled(self):
        report = copy.deepcopy(self.report)
        def refuse(response, number):
            if number == 1:
                response["choices"][0]["finish_reason"] = "content_filter"
        sender, calls = self.sender(refuse)
        with patch.dict(os.environ, {"OPENROUTER_API_KEY": "offline-test-token"}):
            trial.run(report, lambda: None, sender)
        self.assertEqual((len(calls), report["rows"][0]["interpreter"]["status"]), (84, "invalid"))
        self.assertEqual(report["trace"][0]["response"]["choices"][0]["finish_reason"], "content_filter")
        self.assertEqual(report["summary"]["arms"]["single"]["unavailable_primary"], 3)
        self.assertEqual(report["summary"]["arms"]["single"]["binding_units"], 72)

    def test_changed_protocol_and_limits_are_rejected(self):
        report = copy.deepcopy(self.report)
        report["protocol"]["frozen"]["limits"]["budget_usd"] = 6.0
        with self.assertRaises(ValueError):
            trial.run(report, lambda: None, lambda *args: self.fail("no submission"))
        for budget, calls in ((6, 84), (0, 84), (True, 84), (float("nan"), 84), (5, 83)):
            with self.subTest(budget=budget, calls=calls), self.assertRaises(ValueError):
                trial.prepare(self.data, budget, calls)

    def test_authored_request_sizes_and_no_clobber_cli(self):
        sizes = []
        for packet in self.frozen["packets"]:
            row = {r: self.proposal(packet) for r in trial.ROLES[:2]}
            for role in (*trial.ROLES, *(["control"] if "control" in packet else [])):
                op = trial.operation(packet, row, role, self.frozen)
                sizes.append(len(json.dumps(op["payload"]).encode()))
        self.assertLess(max(sizes), self.frozen["plan"]["maxRequestBytes"])
        with TemporaryDirectory() as directory:
            path = Path(directory) / "existing.json"
            path.write_text("keep")
            with patch("builtins.print"):
                self.assertEqual(trial.main(["--output", str(path)]), 2)
            self.assertEqual(path.read_text(), "keep")
