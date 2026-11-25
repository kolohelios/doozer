import gzip
import hashlib
import json
import unittest

from scripts import maintenance_proposer as proposer, workbench as wb


class InboxTrialArchiveTests(unittest.TestCase):
    def test_original_response_and_rejected_inspection_are_preserved(self):
        archive = (wb.ROOT / "experiments/workbench/results/first-inbox-maintenance.json.gz").read_bytes()
        self.assertEqual(hashlib.sha256(archive).hexdigest(), "a89dbb51fa56d2fbb5f28c91107475e9d003135e4e695a84ac52f46f7bf0e167")
        raw = gzip.decompress(archive)
        self.assertEqual(hashlib.sha256(raw).hexdigest(), "87190bc1ded6d9b5d62f64652b3e6a64c2b707f4db2fd011fc5653d8bec7b5a0")
        report = json.loads(raw)
        frozen = report["protocol"]["frozen"]
        expected = "331d934b2b05255bcc197bd7b23dc86634a9172191442b0ec1d3742fcb6fcac2"
        self.assertEqual(proposer.digest(frozen), expected)
        self.assertEqual(report["operator_opt_in_sha256"], expected)
        self.assertEqual(frozen["limits"], {"budget_usd": 0.10, "max_calls": 1, "retries": 0})
        record, = report["trace"]
        self.assertEqual(record["transport"]["attempts"], 1)
        self.assertEqual((record["input_tokens"], record["output_tokens"], record["accounted_usd"]), (1920, 67, 0.004376))
        self.assertEqual(report["summary"]["unknown_billing"], 0)
        proposal = json.loads(record["response"]["choices"][0]["message"]["content"])
        self.assertEqual(proposal["operations"], [])
        self.assertNotIn("accounting", proposal)
        self.assertEqual(report["inspection"], {"status": "rejected-not-applied", "failure": "'accounting'",
                                               "semantic_judgment": "not-evaluated"})
        self.assertFalse(report["canonical_acceptance"])

    def test_revised_trial_preserves_mechanically_valid_no_op(self):
        results = wb.ROOT / "experiments/workbench/results"
        archive = (results / "second-inbox-maintenance.json.gz").read_bytes()
        self.assertEqual(hashlib.sha256(archive).hexdigest(), "207a49ea3a14895cac66900b396d905cda2cb07e365c6e0bc7c08fbdf3c79faa")
        raw = gzip.decompress(archive)
        self.assertEqual(hashlib.sha256(raw).hexdigest(), "515ec627126f254d93134ac253b237a6f337ab89d6105e363fef61aa473add97")
        report = json.loads(raw)
        frozen = report["protocol"]["frozen"]
        expected = "5dd0d9d5b7d409dd9ae6a4e0218fbf42fd642e5a41afe1531f4c54caeead5542"
        self.assertEqual(proposer.digest(frozen), expected)
        self.assertEqual(report["operator_opt_in_sha256"], expected)
        previous = json.loads(gzip.decompress((results / "first-inbox-maintenance.json.gz").read_bytes()))["protocol"]["frozen"]
        self.assertEqual(frozen["checkpoint"]["snapshot"], previous["checkpoint"]["snapshot"])
        self.assertEqual(frozen["operation"]["payload"]["messages"][1], previous["operation"]["payload"]["messages"][1])
        record, = report["trace"]
        self.assertEqual(record["transport"]["attempts"], 1)
        self.assertEqual((record["input_tokens"], record["output_tokens"], record["accounted_usd"]), (1811, 59, 0.004094))
        self.assertEqual(report["summary"]["unknown_billing"], 0)
        result = report["inspection"]
        self.assertEqual(result["status"], "no-change-in-isolated-copy")
        self.assertEqual(result["semantic_judgment"], "not-evaluated")
        inspected = result["inspection"]
        proposal = json.loads(record["response"]["choices"][0]["message"]["content"])
        self.assertEqual(proposal["operations"], [])
        self.assertNotIn("accounting", proposal)
        self.assertEqual(inspected["proposal"], proposal)
        self.assertEqual(inspected["request"]["patch"], {**proposal, "accounting": {}})
        self.assertEqual(inspected["before"], inspected["after"])
        self.assertFalse(inspected["changed"])
        self.assertFalse(report["canonical_acceptance"])

    def test_overlap_trial_preserves_named_comparison_and_unchanged_view(self):
        results = wb.ROOT / "experiments/workbench/results"
        archive = (results / "third-inbox-maintenance.json.gz").read_bytes()
        self.assertEqual(hashlib.sha256(archive).hexdigest(), "679fb468ccd601002ab14bbbb042780289753e329cb608406345b687ac0dd9bf")
        raw = gzip.decompress(archive)
        self.assertEqual(hashlib.sha256(raw).hexdigest(), "e6dec29228524852e169d7f6e480f1ace538880ff1322881a7e13278331cffaf")
        report = json.loads(raw)
        frozen = report["protocol"]["frozen"]
        expected = "3996ece7538e4152bc88c5fe5ad3ea4694d24b22d80af5fe6a67f3b5c5d72825"
        self.assertEqual(proposer.digest(frozen), expected)
        self.assertEqual(report["operator_opt_in_sha256"], expected)
        previous = json.loads(gzip.decompress((results / "second-inbox-maintenance.json.gz").read_bytes()))["protocol"]["frozen"]
        self.assertEqual(frozen["checkpoint"]["snapshot"], previous["checkpoint"]["snapshot"])
        context = json.loads(frozen["operation"]["payload"]["messages"][1]["content"])
        overlap = context.pop("evidence_overlap")
        self.assertEqual(context, json.loads(previous["operation"]["payload"]["messages"][1]["content"]))
        self.assertEqual(len(overlap["pairs"]), 7)
        self.assertEqual(set(overlap["pairs"][0]["claims"]), {"existing-4", "existing-6"})
        record, = report["trace"]
        self.assertEqual(record["transport"]["attempts"], 1)
        self.assertEqual((record["input_tokens"], record["output_tokens"], record["accounted_usd"]), (2095, 163, 0.005494))
        self.assertEqual(report["summary"]["unknown_billing"], 0)
        result = report["inspection"]
        self.assertEqual(result["status"], "no-change-in-isolated-copy")
        self.assertEqual(result["semantic_judgment"], "not-evaluated")
        inspected = result["inspection"]
        proposal = json.loads(record["response"]["choices"][0]["message"]["content"])
        self.assertEqual(proposal["operations"], [])
        for ref in overlap["pairs"][0]["claims"]:
            self.assertIn(ref, proposal["rationale"])
        self.assertEqual(inspected["proposal"], proposal)
        self.assertEqual(inspected["before"], inspected["after"])
        self.assertFalse(inspected["changed"])
        self.assertFalse(report["canonical_acceptance"])
