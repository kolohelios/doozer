import gzip
import hashlib
import json
import unittest

from scripts import reviewed_panel as trial


class ReviewedTransferArchiveTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = trial.multi.export_cue(sorted(trial.DIRECTORY.glob("*.cue")))
        cls.observed = cls.data["reviewedTransferObservations"]
        cls.encoded = (trial.multi.ROOT / cls.observed["artifact"]).read_bytes()
        cls.raw = gzip.decompress(cls.encoded)
        cls.report = json.loads(cls.raw)

    def test_archive_is_lossless_hash_bound_and_partial(self):
        o, r = self.observed, self.report
        self.assertEqual(hashlib.sha256(self.encoded).hexdigest(), o["archiveSHA256"])
        self.assertEqual(hashlib.sha256(self.raw).hexdigest(), o["uncompressedSHA256"])
        self.assertEqual((len(self.encoded), len(self.raw)), (o["archiveBytes"], o["uncompressedBytes"]))
        self.assertEqual(r["protocol"]["sha256"], o["protocolSHA256"])
        self.assertEqual(trial.multi.pilot.digest(r["protocol"]["frozen"]), o["protocolSHA256"])
        self.assertEqual(r["source_commit"], o["sourceCommit"])
        self.assertEqual(r["status"], "stopped-no-retry")
        self.assertEqual(r["protocol"]["frozen"]["planned_calls"], 49)
        self.assertEqual((len(r["requests"]), len(r["trace"])), (21, 21))

    def test_preparation_reproduces_frozen_protocol_without_network(self):
        replay = trial.prepare(self.data)
        self.assertEqual(replay["protocol"]["sha256"], self.report["protocol"]["sha256"])
        self.assertEqual(replay["trace"], [])
        for name, digest in self.report["protocol"]["frozen"]["implementation_sha256"].items():
            self.assertEqual(hashlib.sha256((trial.multi.ROOT / "scripts" / name).read_bytes()).hexdigest(), digest)

    def test_saved_requests_reproduce_without_reference_leakage_or_repairs(self):
        r = self.report
        packets = {p["id"]: p for p in r["protocol"]["frozen"]["packets"]}
        rows = {row["id"]: row for row in r["rows"]}
        for op in r["requests"]:
            actual = trial.operation(packets[op["sample"]], rows[op["sample"]], op["kind"], r["protocol"]["frozen"])
            self.assertEqual(actual, op)
            context = json.loads(op["payload"]["messages"][1]["content"])
            self.assertFalse({"reference", "queries", "control", "fault_bindings"} & context.keys())
            if op["kind"] in trial.ROLES[:2]:
                self.assertNotIn("untrusted_interpretations", context)
        pairs = [(op["sample"], op["kind"]) for op in r["requests"]]
        self.assertEqual(len(pairs), len(set(pairs)))

    def test_unknown_billing_is_not_zero_and_unused_budget_is_not_spent(self):
        r, o = self.report, self.observed
        known = [record for record in r["trace"] if "accounted_usd" in record]
        unknown = [record for record in r["trace"] if "accounted_usd" not in record]
        self.assertEqual((len(known), len(unknown)), (20, 1))
        self.assertAlmostEqual(sum(record["accounted_usd"] for record in known), o["knownReportedCostUSD"])
        self.assertEqual((unknown[0]["sample"], unknown[0]["kind"]), ("independent-grant-survives/w1", "control"))
        self.assertEqual(unknown[0]["status"], "failed-or-unaccounted")
        self.assertEqual(unknown[0]["response"]["error"]["code"], 504)
        self.assertEqual(unknown[0]["response"]["error"]["metadata"]["error_type"], "timeout")
        self.assertNotIn("usage", unknown[0]["response"])
        self.assertEqual(unknown[0]["reserved_usd"], o["unaccountedCallReservedUSD"])
        self.assertAlmostEqual(r["accounted_or_reserved_usd"], o["accountedOrReservedUSD"])
        self.assertEqual(r["protocol"]["frozen"]["planned_calls"] - len(r["trace"]), o["unattemptedCalls"])

    def test_separate_billing_lookup_preserves_404_without_guessing_zero(self):
        expected = self.observed["billingLookup"]
        raw = (trial.multi.ROOT / expected["artifact"]).read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(), expected["sha256"])
        lookup = json.loads(raw)
        self.assertEqual((lookup["method"], lookup["http_status"]), ("GET", 404))
        self.assertEqual(lookup["parent_protocol_sha256"], self.report["protocol"]["sha256"])
        self.assertEqual(lookup["generation_id"], self.report["trace"][-1]["response"]["id"])
        self.assertNotIn("total_cost", lookup)
        self.assertEqual(self.report["status"], "stopped-no-retry")

    def test_recomputed_full_denominators_and_stage_availability(self):
        r, o = self.report, self.observed
        self.assertEqual(trial.summarize(r), r["summary"])
        for role, expected in o["stages"].items():
            stages = [row.get(role, {}) for packet, row in zip(r["protocol"]["frozen"]["packets"], r["rows"]) if role != "control" or "control" in packet]
            self.assertEqual(len(stages), expected["planned"])
            for status in ("valid", "invalid"):
                self.assertEqual(sum(stage.get("status") == status for stage in stages), expected[status])
            self.assertEqual(sum(stage.get("status") == "call-failed" for stage in stages), expected["failed"])
            self.assertEqual(sum(not stage for stage in stages), expected["unattempted"])
        for counts in r["summary"]["arms"].values():
            self.assertEqual((counts["binding_units"], counts["unavailable_primary"]), (32, 16))
        for counts in r["summary"]["roles"].values():
            self.assertEqual((counts["state_cells"], counts["state_matches_proposed"]), (32, 16))
        self.assertEqual(r["summary"]["complete_snapshots"], 3)
        self.assertEqual(sum(all(trial.value_of(row, role) is not None for role in trial.ROLES) for row in r["rows"]), 4)

    def test_invalid_audits_remain_invalid_without_post_hoc_salvage(self):
        r = self.report
        packets = {p["id"]: p for p in r["protocol"]["frozen"]["packets"]}
        invalid = 0
        for op, trace in zip(r["requests"], r["trace"]):
            if op["kind"] != "auditor" or not op["sample"].startswith("regional-coverage/"):
                continue
            response = trace["response"]
            self.assertEqual(response["choices"][0]["finish_reason"], "stop")
            self.assertIsInstance(json.loads(response["choices"][0]["message"]["content"]), dict)
            with self.assertRaises(ValueError):
                trial.validate_response(response, op, packets[op["sample"]])
            invalid += 1
        self.assertEqual(invalid, 2)


if __name__ == "__main__":
    unittest.main()
