import base64
from contextlib import redirect_stdout
import io
import gzip
import hashlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from scripts import maintenance_proposer as proposer, workbench as wb


class RevisionArchiveTests(unittest.TestCase):
    def test_v3_archive_preserves_native_proposal_translation_and_recovery(self):
        archive = (wb.ROOT / "experiments/workbench/results/third-synthetic-revision.json.gz").read_bytes()
        self.assertEqual(hashlib.sha256(archive).hexdigest(), "d892103f5adb82abaf81d207c32758b84587d664b44725e58244cb603c471bf0")
        raw = gzip.decompress(archive)
        self.assertEqual(hashlib.sha256(raw).hexdigest(), "1bfd2bf50b753ae63b2b74a850f01da7e3a34db094419a61f4d7f2bbe05f944f")
        report = json.loads(raw)
        frozen = report["protocol"]["frozen"]
        expected = "48a1c94a529de5471207e827702514faee1a50755f254b3528f12a333caddbd4"
        self.assertEqual(proposer.digest(frozen), expected)
        self.assertEqual(report["operator_opt_in_sha256"], expected)
        record, = report["trace"]
        self.assertEqual(record["transport"]["attempts"], 1)
        self.assertEqual((record["input_tokens"], record["output_tokens"], record["accounted_usd"]), (1052, 330, 0.004744))
        self.assertEqual(report["summary"]["unknown_billing"], 0)
        inspection = report["inspection"]
        content = record["response"]["choices"][0]["message"]["content"]
        self.assertEqual(base64.b64decode(inspection["input"]["base64"]), content.encode())
        original = json.loads(content)
        self.assertEqual(inspection["proposal"], original)
        op, = original["operations"]
        self.assertEqual((op["op"], op["assertion"]["id"]), ("add", "new-1"))
        op["assertion"]["id"] = "claim-slot-1"
        original["accounting"]["guide-two"]["claims"] = ["claim-slot-1"]
        self.assertEqual(inspection["lowered_patch"], original)
        before = frozen["checkpoint"]["protocol"]["frozen"]["before"]
        state = inspection["state"]
        self.assertEqual(inspection["status"], "applied-in-isolated-copy")
        self.assertEqual(state["claims"]["marker-procedure"], before["claims"]["marker-procedure"])
        self.assertEqual(state["processed"], ["guide-one", "guide-two"])
        self.assertEqual(state["journal"][-1]["patch"], original)
        recovery = inspection["recovery"]
        self.assertEqual(recovery["status"], "exercised")
        self.assertTrue(recovery["material_recovered"])
        self.assertEqual(recovery["restored"]["processed"], 1)
        self.assertEqual(wb.material(recovery["state"]), wb.material(state))
        self.assertEqual(inspection["semantic_judgment"], "pending-human-review")
        self.assertFalse(inspection["canonical_acceptance"])

    def test_exact_scope_separates_guide_revisions_without_rewriting_the_archive(self):
        path = wb.ROOT / "experiments/workbench/results/third-synthetic-revision.json.gz"
        raw = gzip.decompress(path.read_bytes())
        state = json.loads(raw)["inspection"]["state"]
        scope = "Lantern Dispatch Guide, revision 2"
        selected = wb.project(state, scope=scope)
        self.assertEqual(selected["claims"], ["claim-slot-1"])
        for view in ("handbook", "agentContext"):
            self.assertIn("shared ledger", selected[view])
            self.assertIn("markers still do not change the dispatch deadline", selected[view])
            self.assertIn("fixture://lantern/guide-two", selected[view])
            self.assertNotIn("optional blue marker", selected[view])
            self.assertNotIn("fixture://lantern/guide-one", selected[view])
        old_scope = "Lantern Dispatch Guide, revision 1"
        old = wb.discover(state, "blue marker", scope=old_scope)
        self.assertEqual([hit["claim"]["id"] for hit in old["hits"]], ["marker-procedure"])
        self.assertEqual(len(wb.project(state)["claims"]), 2)
        self.assertEqual(wb.project(state, scope="Lantern Dispatch Guide, revision 3")["claims"], [])
        missing = wb.discover(state, "markers", scope="Lantern Dispatch Guide, revision 3")
        self.assertEqual(missing["status"], "no-matching-knowledge")
        self.assertEqual(missing["hits"], [])
        self.assertEqual(state, json.loads(raw)["inspection"]["state"])

        with TemporaryDirectory() as directory, redirect_stdout(io.StringIO()) as output:
            artifact = Path(directory) / "report.json"
            artifact.write_bytes(raw)
            self.assertEqual(wb.main(["--inspect", str(artifact), "--scope", scope,
                                      "--query", "ledger", "--reference", "marker-procedure"]), 0)
            result = json.loads(output.getvalue())
            self.assertEqual(result["projection"]["claims"], ["claim-slot-1"])
            self.assertEqual(result["discovery"]["coverage"]["exact_scope"], scope)
            self.assertEqual(result["historical"]["id"], "marker-procedure")
            self.assertIsNone(result["current"])
            self.assertEqual(artifact.read_bytes(), raw)

    def test_scope_options_nominate_both_revisions_but_do_not_choose_one(self):
        path = wb.ROOT / "experiments/workbench/results/third-synthetic-revision.json.gz"
        raw = gzip.decompress(path.read_bytes())
        state = json.loads(raw)["inspection"]["state"]
        result = wb.discover_scopes(state, "dispatch deadline")
        self.assertEqual(result["status"], "scope-options")
        self.assertEqual(result["options"], [
            {"scope": "Lantern Dispatch Guide, revision 1", "matched_claim_ids": ["marker-procedure"]},
            {"scope": "Lantern Dispatch Guide, revision 2", "matched_claim_ids": ["claim-slot-1"]},
        ])
        ledger = wb.discover_scopes(state, "ledger")
        self.assertEqual(ledger["options"], result["options"][1:])
        self.assertNotIn("projection", ledger)
        self.assertNotIn("selected", ledger)
        absent = wb.discover_scopes(state, "weather forecast")
        self.assertEqual((absent["status"], absent["options"]), ("no-matching-scopes", []))
        self.assertEqual(state, json.loads(raw)["inspection"]["state"])

        with TemporaryDirectory() as directory, redirect_stdout(io.StringIO()) as output:
            artifact = Path(directory) / "report.json"
            artifact.write_bytes(raw)
            self.assertEqual(wb.main(["--inspect", str(artifact), "--find-scopes", "--query", "dispatch deadline"]), 0)
            self.assertEqual(json.loads(output.getvalue()), result)
            self.assertEqual(artifact.read_bytes(), raw)

    def test_scope_options_exclude_historical_aliases_and_show_pending_sources(self):
        state = wb.new_state()
        state["claims"]["current-claim"] = {"id": "current-claim", "text": "Use the ledger.", "scope": "Ledger"}
        state["history"]["old-claim"] = {"id": "old-claim", "text": "Use the marker.", "scope": "Marker"}
        state["redirects"]["old-claim"] = "current-claim"
        state["received"]["pending-note"] = {"text": "Marker."}
        result = wb.discover_scopes(state, "marker")
        self.assertEqual(result["options"], [])
        self.assertEqual(result["pending"], ["pending-note"])

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
