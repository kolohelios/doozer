import gzip
import hashlib
import json
import unittest

from scripts import scale_panel as trial


class ScaleArchiveTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = trial.prior.multi.export_cue(sorted(trial.prior.DIRECTORY.glob("*.cue")))
        cls.observations = cls.data["scaleObservations"]
        cls.path = trial.prior.multi.ROOT / cls.observations["artifact"]["path"]
        cls.archive = cls.path.read_bytes()
        cls.raw = gzip.decompress(cls.archive)
        cls.report = json.loads(cls.raw)
        cls.frozen = cls.report["protocol"]["frozen"]
        cls.packets = {p["id"]: p for p in cls.frozen["packets"]}
        cls.rows = {r["id"]: r for r in cls.report["rows"]}

    def test_hashes_exact_bytes_manifest_and_source_commit(self):
        artifact = self.observations["artifact"]
        self.assertEqual((len(self.archive), hashlib.sha256(self.archive).hexdigest()), (artifact["bytes"], artifact["sha256"]))
        self.assertEqual((len(self.raw), hashlib.sha256(self.raw).hexdigest()), (artifact["rawBytes"], artifact["rawSHA256"]))
        self.assertEqual(trial.prior.multi.pilot.digest(self.frozen), artifact["protocolSHA256"])
        self.assertEqual(self.report["source_commit"], artifact["sourceCommit"])
        self.assertEqual(self.report["protocol"]["sha256"], artifact["protocolSHA256"])

    def test_every_planned_request_and_native_response_accounted_once(self):
        report = self.report
        self.assertEqual(report["status"], "completed")
        expected = [(p["id"], r) for p in self.frozen["packets"] for r in (*trial.ROLES, *(["control"] if "control" in p else []))]
        self.assertEqual([(o["sample"], o["kind"]) for o in report["requests"]], expected)
        self.assertEqual([(t["sample"], t["kind"]) for t in report["trace"]], expected)
        self.assertEqual(len(expected), 84)
        for record in report["trace"]:
            self.assertEqual(record["status"], "received")
            self.assertEqual(record["transport"]["attempts"], 1)
            self.assertEqual(record["transport"]["outcome"], "response-received")
            self.assertIn("choices", record["response"])
            self.assertIn("content", record["response"]["choices"][0]["message"])
            self.assertEqual(record["accounted_usd"], record["response"]["usage"]["cost"])
        self.assertAlmostEqual(sum(t["accounted_usd"] for t in report["trace"]), 2.527731)
        self.assertLess(report["accounted_or_reserved_usd"], 5)

    def test_original_summary_recomputes_without_rescoring(self):
        self.assertEqual(trial.summarize(self.report), self.report["summary"])
        summary = self.report["summary"]
        self.assertEqual((summary["complete_real_snapshots"], summary["snapshot_denominator"]), (20, 24))
        self.assertEqual((summary["roles"]["interpreter"]["profile_matches"], summary["roles"]["verifier"]["profile_matches"]), (38, 54))
        self.assertEqual((summary["roles"]["interpreter"]["query_matches"], summary["roles"]["verifier"]["query_matches"]), (62, 69))
        for arm, expected in (("single", (19, 9, 0, 38)), ("blind-check", (28, 0, 7, 31)), ("panel", (28, 0, 11, 27))):
            actual = summary["arms"][arm]
            self.assertEqual(tuple(actual[k] for k in ("discrepant_flagged", "discrepant_unflagged", "reference_matching_flagged", "reference_matching_eligible")), expected)
            self.assertEqual((actual["binding_units"], actual["unavailable_primary"]), (72, 6))
        self.assertEqual(summary["controls"]["faults_both_challenged"], 8)
        self.assertEqual(summary["controls"]["proposed_false_challenges"], 4)

    def test_composition_defect_and_authored_origin_cues_remain_visible(self):
        # Assert the actual historical defect, not a retrospectively fixed prompt.
        self.assertEqual(self.frozen["contract"]["version"], "reviewed-source-projection-v2")
        for op in self.report["requests"]:
            state = json.loads(op["payload"]["messages"][1]["content"])
            self.assertEqual(state["common_contract"], self.frozen["contract"])
            self.assertNotIn("rules", state["common_contract"])
            if op["kind"] == "control":
                self.assertIn("Authored development interpretation, not a model response or human gold.", json.dumps(state))
                self.assertNotIn("fault_bindings", state)
                self.assertNotIn("reference", state)
        for packet in self.frozen["packets"]:
            a = next(o for o in self.report["requests"] if o["sample"] == packet["id"] and o["kind"] == "interpreter")
            b = next(o for o in self.report["requests"] if o["sample"] == packet["id"] and o["kind"] == "verifier")
            self.assertEqual(a["payload"]["messages"], b["payload"]["messages"])

    def test_invalid_stages_are_not_repaired_or_promoted(self):
        invalid = {(r["id"], role) for r in self.report["rows"] for role in (*trial.ROLES, "control") if r.get(role, {}).get("status") == "invalid"}
        self.assertEqual(invalid, {("12-door-is-not-permission/w0", "interpreter"), ("06-independent-grant/w0", "interpreter"), ("11-unresolved-provisional/w1", "verifier"), ("04-note-date-gap/w1", "auditor")})
        for name, role in invalid:
            row = self.rows[name]
            record = next(t for t in self.report["trace"] if t["sample"] == name and t["kind"] == role)
            self.assertNotIn("value", row[role])
            response = record["response"]
            if role == "verifier":
                self.assertEqual(response["choices"][0]["finish_reason"], "length")
            else:
                value = json.loads(response["choices"][0]["message"]["content"])
                if role == "interpreter":
                    self.assertTrue(any(not limit["evidence"] for limit in value["extractionLimits"]))
                    with self.assertRaisesRegex(ValueError, "extractor limits"):
                        trial.compile_value(value, self.packets[name])
                else:
                    with self.assertRaisesRegex(ValueError, "duplicate evidence"):
                        trial.audit.validate(value, self.packets[name]["audit_schema"], {"interpreter": True, "verifier": True})

    def test_control_challenges_can_conflict_with_required_grant_constructor(self):
        for name in ("12-door-is-not-permission/w1", "05-assurance-withdrawal/w1"):
            packet, row = self.packets[name], self.rows[name]
            check = next(c for c in row["control"]["value"]["checks"] if c["binding"] == "b2")
            self.assertEqual((check["interpreter"], check["verifier"]), ("material-error", "material-error"))
            for role in trial.ROLES[:2]:
                compiled = packet["control"]["proposals"][role]["compiled"]
                grants = [r for r in compiled["core"]["records"] if r["atom"]["binding"] == "b2" and r["atom"]["kind"] == "grant"]
                self.assertEqual(len(grants), 1)
                self.assertIsNone(grants[0]["atom"]["value"])
                self.assertEqual(trial.core.evaluate(compiled["core"], "b2", "permitted")["state"], "supported")

    def test_no_additional_profile_detection_or_canonical_effects(self):
        for case in self.report["summary"]["cases"].values():
            for b in case["flags"]["panel"]:
                if case["flags"]["panel"][b] and not case["flags"]["blind-check"][b]:
                    self.assertTrue(case["fidelity"]["interpreter"][b])
        for row in self.report["rows"]:
            for role in trial.ROLES[:2]:
                for views in row.get(role, {}).get("reader_views", {}).values():
                    for view in views.values():
                        self.assertFalse(view["canonical_acceptance"])
        self.assertFalse(self.observations["canonicalAcceptance"])
        self.assertFalse(self.observations["retirement"])
