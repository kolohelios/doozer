"""Schema-language control safety; no model performance is assumed."""

import copy
import gzip
import io
import json
import os
from pathlib import Path
import tempfile
from unittest import TestCase, mock

from scripts import evidence_direction as direction


class DirectionTests(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = direction.expansion.multi.export_cue(sorted(direction.expansion.DIRECTORY.glob("*.cue")))

    def test_control_preserves_all_user_contexts_models_and_sources(self):
        report = direction.prepare(self.data)
        original = json.loads(gzip.decompress(direction.BASELINE.read_bytes()))
        requests = {op["sample"]: op for op in original["requests"] if op["kind"] == "reconciled"}
        self.assertEqual(len(report["rows"]), 12)
        for item in report["protocol"]["frozen"]["items"]:
            old, new = requests[item["id"]]["payload"], item["operation"]["payload"]
            self.assertEqual(old["messages"][1], new["messages"][1])
            for key in ("model", "provider", "temperature", "max_tokens"):
                self.assertEqual(old[key], new[key])
            old_fields = old["response_format"]["json_schema"]["schema"]["properties"]["proofs"]["items"]["properties"]
            new_fields = new["response_format"]["json_schema"]["schema"]["properties"]["proofs"]["items"]["properties"]
            mapping = {"positive": "supports_hypothesis", "negative": "incompatible_fact_spans"}
            self.assertEqual([mapping.get(key, key) for key in old_fields], list(new_fields))
        self.assertLessEqual(report["protocol"]["frozen"]["baseline_calls"] + len(report["rows"]), 80)

    def test_recorded_outputs_keep_new_slots_and_only_map_names(self):
        report = direction.prepare(self.data)
        def sender(endpoint, payload, token):
            self.assertEqual(token, "SECRET_CANARY")
            state = json.loads(payload["messages"][1]["content"])
            value = {"summary": "Recorded structural fixture.", "uncertainties": [], "changes": [],
                     "proofs": [{"id": item["id"], "supports_hypothesis": [], "incompatible_fact_spans": [], "rationale": "Recorded structural fixture."} for item in state["hypotheses_not_premises"]]}
            return {"model": payload["model"], "usage": {"cost": 0.001, "prompt_tokens": 100, "completion_tokens": 100},
                    "choices": [{"finish_reason": "stop", "message": {"content": json.dumps(value)}}]}
        with mock.patch.dict(os.environ, {"OPENROUTER_API_KEY": "SECRET_CANARY"}):
            direction.run(report, lambda: None, sender=sender)
        self.assertEqual(len(report["trace"]), 12)
        self.assertEqual(report["status"], "completed")
        for row in report["rows"]:
            self.assertIn("supports_hypothesis", row["raw_new_schema_output"]["proofs"][0])
            self.assertIn("positive", row["slot_mapping_only"]["proofs"][0])
        with self.assertRaises(ValueError):
            direction.run(report, lambda: None, sender=sender)

    def test_limits_and_baseline_changes_are_rejected_before_calls(self):
        for budget, calls in ((0.51, 12), (0.5, 13), (0.5, 11)):
            with self.subTest(budget=budget, calls=calls), self.assertRaises(ValueError):
                direction.prepare(self.data, budget, calls)
        data = copy.deepcopy(self.data)
        data["directionPlan"]["baselineArchiveSHA256"] = "0" * 64
        with self.assertRaises(ValueError):
            direction.prepare(data)

    def test_cli_is_offline_by_default_and_output_is_new_only(self):
        with tempfile.TemporaryDirectory() as directory, mock.patch.object(direction, "run") as live, mock.patch("sys.stdout", new_callable=io.StringIO):
            path = Path(directory) / "control.json"
            self.assertEqual(direction.main(["--output", str(path)]), 0)
            before = path.read_bytes()
            self.assertEqual(direction.main(["--output", str(path)]), 2)
            self.assertEqual(before, path.read_bytes())
            live.assert_not_called()
