import copy
from contextlib import redirect_stderr
import io
import json
from pathlib import Path
import re
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from scripts import scale_contract as contract


class ScaleContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = contract.legacy.prior.multi.export_cue(sorted(contract.legacy.prior.DIRECTORY.glob("*.cue")))
        with patch("urllib.request.urlopen", side_effect=AssertionError("offline means no network")):
            cls.report = contract.prepare(cls.data)
        cls.frozen = cls.report["protocol"]["frozen"]
        cls.packets = {p["id"]: p for p in cls.frozen["packets"]}

    def packet(self, name="06-independent-grant", window="w1"):
        return copy.deepcopy(self.packets[name + "/" + window])

    def check_schema(self, value, packet):
        contract.legacy.meaning.validate_contract(packet["ledger_schema"]["cue"], "#Report", json.dumps(value, allow_nan=False))

    def test_offline_has_no_spending_authority_or_callable_live_path(self):
        self.assertEqual(self.report["status"], "offline-prospective-not-live")
        self.assertEqual((self.frozen["planned_calls"], self.frozen["plan"]["maxCalls"], self.frozen["plan"]["maxBudgetUSD"]), (0, 0, 0))
        self.assertEqual(self.frozen["limits"], {"budget_usd": 0.0, "max_calls": 0, "retries": 0})
        self.assertEqual(self.frozen["execution_authorization"]["status"], "none")
        self.assertEqual(self.report["trace"], [])
        self.assertEqual(len(self.report["request_previews"]), 84)
        with self.assertRaises(ValueError):
            contract.legacy.run(copy.deepcopy(self.report), lambda: None, lambda *args: self.fail("no submission"))

    def test_manifest_binds_previews_and_retains_historical_basis_not_approval(self):
        digest = contract.legacy.prior.multi.pilot.digest
        self.assertEqual(digest(self.frozen), self.report["protocol"]["sha256"])
        self.assertEqual(digest(self.report["request_previews"]), self.frozen["request_preview_sha256"])
        self.assertEqual(self.frozen["prospective_checks"]["priorProtocolSHA256"], self.data["scaleObservations"]["artifact"]["protocolSHA256"])
        self.assertFalse(self.frozen["prospective_checks"]["liveExecution"])
        self.assertFalse(self.frozen["prospective_checks"]["canonicalAcceptance"])
        self.assertIn("not independently reviewed gold", self.frozen["contract"]["basis"])

    def test_base_semantics_are_composed_without_active_legacy_holder_conflict(self):
        shared = self.frozen["contract"]
        self.assertEqual(shared["rules"][2:], self.data["reviewedContract"]["rules"][2:])
        self.assertEqual(len(shared["rules"]), 5)
        self.assertEqual(shared["projection"]["instructions"], self.data["meaningContract"]["instructions"])
        self.assertIn("holder=null", shared["rules"][0]["text"])
        self.assertIn("holder=source actor", shared["rules"][0]["text"])
        self.assertNotIn("Source uncertainty has the source speaker as holder", json.dumps(shared))
        self.assertNotIn(self.data["reviewedContract"]["wire"], json.dumps(shared))
        self.assertEqual(len(shared["constructors"]), 10)
        self.assertIn("null value is REQUIRED", shared["constructors"]["grant"])
        self.assertIn("without adding forbidden", shared["constructors"]["assurance-withdrawal"])

    def test_every_role_receives_identical_complete_contract_and_constructor_schema(self):
        for op in self.report["request_previews"]:
            packet = self.packets[op["sample"]]
            state = json.loads(op["payload"]["messages"][1]["content"])
            self.assertEqual(state["common_contract"], self.frozen["contract"])
            self.assertEqual(state["interpretation_schema"], packet["ledger_schema"]["json"])
            self.assertEqual(state["original_sources"], packet["context"]["sources"])
            if op["kind"] in contract.legacy.ROLES[:2]:
                self.assertEqual(state["interpretation_schema"], op["payload"]["response_format"]["json_schema"]["schema"])
            self.assertLess(len(json.dumps(op["payload"]).encode()), self.frozen["plan"]["maxRequestBytes"])
        for packet in self.frozen["packets"]:
            a, b = [next(o for o in self.report["request_previews"] if o["sample"] == packet["id"] and o["kind"] == r) for r in contract.legacy.ROLES[:2]]
            self.assertEqual(a["payload"]["messages"], b["payload"]["messages"])

    def test_grant_null_operands_have_explicit_shared_lowering_and_actual_consequence(self):
        packet = self.packet()
        branches = packet["ledger_schema"]["json"]["properties"]["ledger"]["items"]["properties"]["atoms"]["items"]["anyOf"]
        grant = next(b for b in branches if b["properties"]["kind"]["enum"] == ["grant"])
        self.assertEqual(grant["properties"]["value"], {"type": "null"})
        self.assertEqual(grant["properties"]["operator"]["enum"], ["none"])
        value = contract.legacy.reference(packet)
        compiled = contract.legacy.compile_value(value, packet)
        self.assertEqual(contract.legacy.core.evaluate(compiled["core"], "b0", "permitted")["state"], "supported")
        self.assertEqual(contract.legacy.core.evaluate(compiled["core"], "b2", "permitted")["state"], "supported")
        self.assertIn("lowers to a permitted constraint", self.frozen["contract"]["constructors"]["grant"])

    def test_control_packaging_has_no_explicit_authored_marker_and_preserves_meaning(self):
        historical = contract.legacy.prepare(self.data)["protocol"]["frozen"]
        originals = {p["id"]: p for p in historical["packets"]}
        for packet in self.frozen["packets"]:
            if "control" not in packet:
                continue
            for role in contract.legacy.ROLES[:2]:
                new = packet["control"]["proposals"][role]
                old = originals[packet["id"]]["control"]["proposals"][role]
                self.assertEqual(contract.legacy.profile(new["compiled"], packet["context"]), contract.legacy.profile(old["compiled"], packet["context"]))
                self.assertEqual(new["compiled"]["original_proposal"], new["value"])
                self.assertEqual(new["original_value"], old["value"])
                self.assertTrue(all(e["rationale"] == self.data["scaleContractChecks"]["auditRationale"] for e in new["value"]["ledger"]))
            op = contract.operation(packet, {}, "control", self.frozen)
            self.assertNotIn("Authored development interpretation", json.dumps(op["payload"]))
            self.assertNotIn("not a model response or human gold", json.dumps(op["payload"]))
            # Private authored references are preserved, not retrospectively rewritten.
            self.assertIn("Authored development interpretation", json.dumps(packet["reference"]))

    def test_private_labels_and_peer_canaries_never_enter_extractors_or_controls(self):
        packet = self.packet("04-note-date-gap", "w0")
        packet["reference"] = {"SECRET_REFERENCE_CANARY": True}
        packet["queries"] = [{"SECRET_QUERY_CANARY": True}]
        a = contract.operation(packet, {}, "interpreter", self.frozen)
        b = contract.operation(packet, {"interpreter": {"status": "valid", "value": "SECRET_PEER_CANARY"}}, "verifier", self.frozen)
        self.assertEqual(a["payload"]["messages"], b["payload"]["messages"])
        self.assertNotIn("SECRET_", json.dumps(b["payload"]))
        self.assertNotIn("2032-05-14", json.dumps(b["payload"]))
        packet = self.packet()
        packet["control"]["kind"] = "SECRET_KIND_CANARY"
        packet["control"]["fault_bindings"] = ["SECRET_LABEL_CANARY"]
        packet["control"]["specification"] = {"SECRET_MUTATION_CANARY": True}
        self.assertNotIn("SECRET_", json.dumps(contract.operation(packet, {}, "control", self.frozen)["payload"]))

    def test_original_prose_survives_while_both_audit_origins_use_same_projection(self):
        packet = self.packet()
        value = contract.legacy.reference(packet)
        value["ledger"][0]["rationale"] = "Real response rationale retained verbatim, not an authored-control normalization."
        row = {"interpreter": {"status": "valid", "value": value, "compiled": contract.legacy.compile_value(value, packet)}}
        before = copy.deepcopy(row)
        state = json.loads(contract.operation(packet, row, "auditor", self.frozen)["payload"]["messages"][1]["content"])
        self.assertEqual(row, before)
        projected = state["untrusted_proposals"]["interpreter"]["proposal"]
        expected = copy.deepcopy(value)
        for entry in expected["ledger"]:
            entry["rationale"] = self.data["scaleContractChecks"]["auditRationale"]
        self.assertEqual(projected, expected)
        controlled = json.loads(contract.operation(packet, {}, "control", self.frozen)["payload"]["messages"][1]["content"])
        self.assertEqual([e["rationale"] for e in projected["ledger"]], [e["rationale"] for e in controlled["untrusted_proposals"]["interpreter"]["proposal"]["ledger"]])
        self.assertIn("cannot assess rationale-only qualifications", state["common_contract"]["auditRationaleProjection"])

    def test_empty_limit_evidence_rejected_by_native_schema_and_validator(self):
        packet = self.packet("12-door-is-not-permission", "w0")
        value = contract.legacy.reference(packet)
        value["extractionLimits"] = [{"about": ["b1"], "evidence": [], "reason": "Bounded interpretation limit."}]
        with self.assertRaises(ValueError):
            self.check_schema(value, packet)
        with self.assertRaises(ValueError):
            contract.legacy.compile_value(value, packet)
        value["extractionLimits"][0]["evidence"] = ["m1"]
        self.check_schema(value, packet)
        contract.legacy.compile_value(value, packet)
        value["extractionLimits"][0]["evidence"] = ["absent-parent"]
        with self.assertRaises(ValueError):
            self.check_schema(value, packet)

    def test_nonblank_schema_matches_strip_including_unicode_whitespace(self):
        for point in [*range(256), 0x1680, *range(0x2000, 0x2031), 0x205f, 0x3000, 0x4e00, 0x1f600]:
            character = chr(point)
            self.assertEqual(bool(re.search(contract.NONBLANK, character)), bool(character.strip()), hex(point))
        packet = self.packet()
        for reason in ("", "  \n\t", "\u0085\u00a0\u2003\u3000"):
            value = contract.legacy.reference(packet)
            value["extractionLimits"] = [{"about": ["b0"], "evidence": ["m1"], "reason": reason}]
            with self.subTest(reason=reason), self.assertRaises(ValueError):
                self.check_schema(value, packet)
        value["extractionLimits"][0]["reason"] = "A scoped limitation with original-source pointers."
        self.check_schema(value, packet)

    def test_schema_cleanup_does_not_prove_hunch_or_scope_classification(self):
        for name in ("01-hunch-and-observation", "02-environment-coverage"):
            packet = self.packet(name)
            bad = packet["control"]["proposals"]["interpreter"]["value"]
            self.check_schema(bad, packet)
            compiled = contract.legacy.compile_value(bad, packet)
            self.assertFalse(compiled["core"]["rejected"] or compiled["rejected_annotations"])
            expected = contract.legacy.compile_value(contract.legacy.reference(packet), packet)
            self.assertNotEqual(contract.legacy.profile(compiled, packet["context"]), contract.legacy.profile(expected, packet["context"]))

    def test_preview_size_guard_rejects_oversized_sources(self):
        packet = self.packet()
        packet["context"]["sources"][0]["text"] += "x" * self.frozen["plan"]["maxRequestBytes"]
        for role in contract.legacy.ROLES:
            with self.subTest(role=role), self.assertRaisesRegex(ValueError, "byte bound"):
                contract.operation(packet, {}, role, self.frozen)

    def test_no_clobber_and_no_live_cli_option(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "keep.json"
            path.write_text("keep")
            with self.assertRaises(ValueError):
                contract.main(["--output", str(path)])
            with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
                contract.main(["--output", str(path), "--live"])
            self.assertEqual(path.read_text(), "keep")
