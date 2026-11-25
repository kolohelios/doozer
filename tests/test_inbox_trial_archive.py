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
