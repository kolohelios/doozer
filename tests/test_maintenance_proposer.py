import base64
import copy
from contextlib import redirect_stderr, redirect_stdout
import io
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from scripts import maintenance_proposer as trial, workbench as wb


class MaintenanceProposerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data, cls.scenario = trial.load()
        with patch("urllib.request.urlopen", side_effect=AssertionError("offline only")):
            cls.prepared = trial.prepare(cls.data, cls.scenario)
        cls.frozen = cls.prepared["protocol"]["frozen"]

    def candidate(self):
        # Authored test input only, never part of the actual proposer prompt.
        return copy.deepcopy(self.data["maintenance"]["consolidation"]["patch"])

    def inspect(self, candidate):
        return trial.inspect_proposal(self.prepared, json.dumps(candidate).encode())

    def test_preparation_has_one_checkpoint_no_model_no_calls_or_budget(self):
        self.assertEqual(self.prepared["status"], "prepared-offline")
        self.assertEqual((self.frozen["planned_calls"], self.frozen["budget_usd"]), (0, 0.0))
        self.assertIsNone(self.frozen["model"])
        self.assertIsNone(self.frozen["provider"])
        self.assertEqual(self.frozen["before"]["revision"], 5)
        self.assertEqual(len(self.frozen["before"]["claims"]), 3)
        self.assertNotIn("retry-safety-current", self.frozen["before"]["history"])
        self.assertEqual(trial.digest(self.frozen), self.prepared["protocol"]["sha256"])

    def test_prompt_contains_only_allowlisted_context_and_exact_contract(self):
        messages = trial.proposer_messages(self.prepared)
        self.assertEqual(messages, self.frozen["messages"])
        state = json.loads(messages[1]["content"])
        self.assertEqual(set(state), {"current_revision", "current_claims", "sources", "reserved_claim_ids", "existing_aliases"})
        self.assertEqual(state["current_claims"], list(self.frozen["before"]["claims"].values()))
        self.assertEqual(set(state["sources"]), set(self.frozen["before"]["processed"]))
        self.assertIn(self.frozen["output_contract"], messages[0]["content"])
        self.assertIn("operations=[]", messages[0]["content"])
        self.assertNotIn("retry-safety-current", json.dumps(messages))
        self.assertNotIn(self.candidate()["rationale"], json.dumps(messages))
        self.assertLess(len(json.dumps(messages).encode()), self.frozen["plan"]["maxPromptBytes"])
        messages[0]["content"] = "caller mutation"
        self.assertNotEqual(messages, self.frozen["messages"])

    def test_target_rubrics_future_sources_and_journal_canaries_stay_private(self):
        data, scenario = copy.deepcopy(self.data), copy.deepcopy(self.scenario)
        data["maintenance"]["consolidation"] = {"secret": "SECRET_TARGET_CANARY"}
        data["maintenance"]["expected"] = {"secret": "SECRET_COUNT_CANARY"}
        data["proposerCheckpoint"]["readerQueries"] = ["SECRET_READER_CANARY"]
        data["proposerCheckpoint"]["references"] = ["SECRET_REFERENCE_CANARY"]
        data["recorded"]["echo-and-projection"]["patch"]["rationale"] = "SECRET_JOURNAL_CANARY"
        scenario["title"] = "SECRET_TITLE_CANARY"
        for step in scenario["steps"]:
            step["expect"]["must"][0]["meaning"] = "SECRET_RUBRIC_CANARY"
        scenario["sources"]["future"] = {**scenario["sources"]["manual"], "text": "SECRET_FUTURE_CANARY"}
        scenario["steps"].append({"id": "future-checkpoint", "receive": ["future"], "reconcile": [], "expect": {}})
        prepared = trial.prepare(data, scenario)
        self.assertNotIn("SECRET_", json.dumps(prepared["protocol"]["frozen"]["messages"]))
        self.assertIn("SECRET_RUBRIC_CANARY", json.dumps(prepared["protocol"]["frozen"]["evaluation"]))
        self.assertNotIn("future", prepared["protocol"]["frozen"]["before"]["received"])

    def test_saved_candidate_applies_only_to_copy_and_recovery_uses_actual_patch(self):
        before = copy.deepcopy(self.prepared)
        candidate = self.candidate()
        result = self.inspect(candidate)
        self.assertEqual(result["status"], "applied-in-isolated-copy")
        self.assertEqual(result["proposal"], candidate)
        self.assertEqual(len(result["isolated_state"]["claims"]), 2)
        self.assertEqual(self.prepared, before)
        self.assertFalse(result["canonical_acceptance"])
        self.assertEqual(result["semantic_judgment"], "pending-human-review")
        self.assertTrue(result["recovery"]["material_recovered"])
        self.assertEqual(result["recovery"]["restored"]["active_claims"], 3)
        self.assertGreater(result["recovery"]["replayed"]["revision"], result["after"]["revision"])
        self.assertEqual(wb.material(result["recovery"]["state"]), wb.material(result["isolated_state"]))
        self.assertEqual(result["derived_analysis"]["assertions"], [candidate["operations"][0]["assertion"]])

    def test_noop_is_available_without_forced_merge_or_automatic_semantic_pass(self):
        noop = {"baseRevision": 5, "accounting": {}, "operations": [], "rationale": "Retain the current layout; no justified change proposed."}
        result = self.inspect(noop)
        self.assertEqual(result["status"], "no-op-in-isolated-copy")
        self.assertEqual(result["isolated_state"], self.frozen["before"])
        self.assertEqual(result["recovery"]["status"], "not-exercised-no-change")
        self.assertEqual(result["semantic_judgment"], "pending-human-review")
        self.assertEqual(result["derived_analysis"]["assertions"], list(self.frozen["before"]["claims"].values()))

    def test_candidate_need_not_equal_authored_target(self):
        candidate = self.candidate()
        candidate["operations"][0]["assertion"]["id"] = "alternative-current-view"
        for op in candidate["operations"][1:]:
            op["replacement"] = "alternative-current-view"
        result = self.inspect(candidate)
        self.assertEqual(result["status"], "applied-in-isolated-copy")
        self.assertIn("alternative-current-view", result["isolated_state"]["claims"])
        self.assertNotIn("retry-safety-current", result["isolated_state"]["claims"])

    def test_false_conclusion_can_pass_application_and_recovery_not_meaning_review(self):
        candidate = self.candidate()
        candidate["operations"][0]["assertion"]["text"] = "All retry paths are safe."
        result = self.inspect(candidate)
        self.assertEqual(result["status"], "applied-in-isolated-copy")
        self.assertTrue(result["recovery"]["material_recovered"])
        self.assertFalse(result["canonical_acceptance"])
        self.assertEqual(result["semantic_judgment"], "pending-human-review")
        self.assertEqual(result["proposal"]["operations"][0]["assertion"]["text"], "All retry paths are safe.")

    def test_contract_preconditions_reject_without_repair_or_partial_application(self):
        candidates = []
        stale = self.candidate(); stale["baseRevision"] = 0; candidates.append(stale)
        fabricated = self.candidate(); fabricated["operations"][0]["assertion"]["evidence"][0]["quote"] = "Not in the fixture."; candidates.append(fabricated)
        dropped = self.candidate(); dropped["operations"][0]["assertion"]["evidence"] = dropped["operations"][0]["assertion"]["evidence"][:-1]; candidates.append(dropped)
        reused = self.candidate(); reused["operations"][0]["assertion"]["id"] = "retry-guidance"; candidates.append(reused)
        intake = self.candidate(); intake["accounting"] = {"manual": {"mode": "represented", "claims": ["retry-safety-current"], "reason": "False intake."}}; candidates.append(intake)
        for candidate in candidates:
            with self.subTest(candidate=candidate):
                result = self.inspect(candidate)
                self.assertEqual(result["status"], "rejected-not-applied")
                self.assertEqual(result["proposal"], candidate)
                self.assertNotIn("isolated_state", result)
                self.assertFalse(result["canonical_acceptance"])
        self.assertEqual(self.frozen["before"]["revision"], 5)

    def test_invalid_json_duplicate_members_and_nonfinite_numbers_retained_exactly(self):
        nested = b"[" * 70 + b"0" + b"]" * 70
        for raw in (b"not json", b"\xff", b'{"operations":[],"operations":[]}', b'{"value":NaN}', b'{"value":1e999}', b'```json\n{}\n```', nested):
            with self.subTest(raw=raw):
                result = trial.inspect_proposal(self.prepared, raw)
                self.assertEqual(result["status"], "invalid-json-not-applied")
                self.assertEqual(base64.b64decode(result["input"]["base64"]), raw)
                self.assertTrue(result["input"]["complete"])
                self.assertNotIn("proposal", result)

    def test_oversized_input_has_explicit_bounded_capture_not_false_complete_output(self):
        bound = self.frozen["plan"]["maxProposalBytes"]
        result = trial.inspect_proposal(self.prepared, b"x" * (bound + 1))
        self.assertEqual(result["status"], "oversized-not-applied")
        self.assertFalse(result["input"]["complete"])
        self.assertEqual(result["input"]["captured_bytes"], bound)
        self.assertNotIn("proposal", result)

    def test_changed_protocol_or_implementation_refuses_inspection(self):
        changed = copy.deepcopy(self.prepared)
        changed["protocol"]["frozen"]["before"]["revision"] = 9
        with self.assertRaisesRegex(ValueError, "changed protocol"):
            trial.inspect_proposal(changed, b"{}")
        with patch.object(trial, "implementation", return_value={"different-code": "different-hash"}), self.assertRaisesRegex(ValueError, "changed protocol"):
            trial.inspect_proposal(self.prepared, b"{}")

    def test_reader_views_and_reference_pairs_present_without_semantic_scores(self):
        result = self.inspect(self.candidate())
        self.assertEqual(set(result["before"]["reader_probes"]), set(self.frozen["plan"]["readerQueries"]))
        self.assertEqual(set(result["after"]["reader_probes"]), set(self.frozen["plan"]["readerQueries"]))
        for ref, pair in result["after"]["references"].items():
            self.assertIsNotNone(pair["historical"], ref)
            self.assertIsNotNone(pair["current"], ref)
        self.assertIn("manual-replay", result["after"]["projection"]["handbook"])
        self.assertIn("automatic retries", result["after"]["projection"]["agentContext"])
        self.assertEqual(result["network_calls"], 0)

    def test_cli_prepare_inspect_no_overwrite_no_live_and_original_input_unchanged(self):
        with TemporaryDirectory() as directory:
            prepared, proposal, output = (Path(directory) / name for name in ("prepared.json", "proposal.json", "output.json"))
            with redirect_stdout(io.StringIO()):
                self.assertEqual(trial.main(["--output", str(prepared)]), 0)
            raw = json.dumps(self.candidate()).encode(); proposal.write_bytes(raw)
            with redirect_stdout(io.StringIO()):
                self.assertEqual(trial.main(["--prepared", str(prepared), "--proposal", str(proposal), "--output", str(output)]), 0)
            self.assertEqual(proposal.read_bytes(), raw)
            self.assertEqual(json.loads(output.read_text())["status"], "applied-in-isolated-copy")
            with self.assertRaises(ValueError):
                trial.main(["--output", str(output)])
            for arguments in (["--live"], ["--proposal", str(proposal)]):
                with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
                    trial.main(["--output", str(Path(directory) / "not-created.json"), *arguments])
            self.assertFalse((Path(directory) / "not-created.json").exists())
