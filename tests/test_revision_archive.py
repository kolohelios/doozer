import base64
import gzip
import hashlib
import json
import unittest

from scripts import maintenance_proposer as proposer, workbench as wb


class RevisionArchiveTests(unittest.TestCase):
    def test_v2_archive_preserves_schema_valid_collision_and_atomic_rejection(self):
        archive = (wb.ROOT / "experiments/workbench/results/second-synthetic-revision.json.gz").read_bytes()
        self.assertEqual(hashlib.sha256(archive).hexdigest(), "1071746009a8c55a5d7c6da2d724ae8e919429e3fcd4f90670ee47cee1bd10a3")
        raw = gzip.decompress(archive)
        self.assertEqual(hashlib.sha256(raw).hexdigest(), "1b976291eef10b207a20ed0466fcd8991f81915efe2c293c8161a4c72e08bd99")
        report = json.loads(raw)
        frozen = report["protocol"]["frozen"]
        expected = "9dd2e54d8a2f1dd07d0ea6e800de7249bfdfece986f8dc55b618f10f864e4678"
        self.assertEqual(proposer.digest(frozen), expected)
        self.assertEqual(report["operator_opt_in_sha256"], expected)
        self.assertEqual(frozen["plan"]["retries"], 0)
        record, = report["trace"]
        self.assertEqual(record["transport"]["attempts"], 1)
        self.assertEqual((record["input_tokens"], record["output_tokens"], record["accounted_usd"]), (963, 364, 0.004838))
        self.assertEqual(report["summary"]["unknown_billing"], 0)
        inspection = report["inspection"]
        content = record["response"]["choices"][0]["message"]["content"]
        self.assertEqual(base64.b64decode(inspection["input"]["base64"]), content.encode())
        self.assertEqual(inspection["proposal"], json.loads(content))
        wb.validate("#Patch", inspection["proposal"])
        self.assertEqual(set(inspection["proposal"]["accounting"]), {"guide-two"})
        self.assertEqual(inspection["status"], "rejected-not-applied")
        self.assertIn("claim identity already exists", inspection["failure"]["detail"])
        self.assertEqual(inspection["state"], frozen["checkpoint"]["protocol"]["frozen"]["before"])
        self.assertNotIn("ledger-procedure", inspection["state"]["history"])
        self.assertEqual(inspection["state"]["processed"], ["guide-one"])
        self.assertNotIn("recovery", inspection)
        self.assertEqual(inspection["semantic_judgment"], "not-evaluated")
        self.assertFalse(inspection["canonical_acceptance"])

    def test_original_rejected_trial_preserves_output_accounting_and_state(self):
        archive = (wb.ROOT / "experiments/workbench/results/first-synthetic-revision.json.gz").read_bytes()
        self.assertEqual(hashlib.sha256(archive).hexdigest(), "2c76594d43032acc88bc0e8f50569b9cdc5657d8908a56a7709611ffa7583de2")
        raw = gzip.decompress(archive)
        self.assertEqual(hashlib.sha256(raw).hexdigest(), "6087911eca0a8ded2512d5d3a72970fe6e2e080ac3ad8a257345e8f01e298cdb")
        report = json.loads(raw)
        frozen = report["protocol"]["frozen"]
        expected = "5f51e85e8bc551505e1b0952f8997b5175cb26bba39444b0ef840e53224bab1c"
        self.assertEqual(proposer.digest(frozen), expected)
        self.assertEqual(report["operator_opt_in_sha256"], expected)
        self.assertEqual(frozen["plan"]["retries"], 0)
        record, = report["trace"]
        self.assertEqual(record["transport"]["attempts"], 1)
        self.assertEqual((record["input_tokens"], record["output_tokens"], record["accounted_usd"]), (766, 296, 0.0039))
        self.assertEqual(report["summary"]["unknown_billing"], 0)
        inspection = report["inspection"]
        content = record["response"]["choices"][0]["message"]["content"]
        self.assertEqual(base64.b64decode(inspection["input"]["base64"]), content.encode())
        self.assertEqual(inspection["proposal"], json.loads(content))
        self.assertEqual(inspection["proposal"]["operations"][0]["replacement"], "")
        self.assertEqual(inspection["status"], "rejected-not-applied")
        self.assertEqual(inspection["state"], frozen["checkpoint"]["protocol"]["frozen"]["before"])
        self.assertEqual(inspection["state"]["processed"], ["guide-one"])
        self.assertNotIn("recovery", inspection)
        self.assertEqual(inspection["semantic_judgment"], "not-evaluated")
        self.assertFalse(inspection["canonical_acceptance"])
