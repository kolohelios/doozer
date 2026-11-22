"""End-to-end recorded plumbing and fail-closed gate tests; no live model scoring."""

import copy
import io
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
from unittest import TestCase, mock

from scripts import workbench as wb
from scripts import workbench_models as models


class WorkbenchTests(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.corpus = wb.export_cue(sorted((wb.ROOT / "corpus").glob("*.cue")))
        cls.scenario = cls.corpus["scenarios"]["retry-safety"]
        cls.backend = models.RecordedBackend()
        cls.result = wb.run(cls.scenario, cls.backend)

    def first_state(self):
        return wb.run(self.scenario, models.RecordedBackend(), through="expressed-guidance")["state"]

    def next_patch(self):
        backend = models.RecordedBackend()
        return copy.deepcopy(backend.responses["narrow-code-evidence"])

    def commit_next(self, state, response):
        return wb.commit(state, response["patch"], ["code"], response["analysis"], response["route"])

    def test_all_checkpoints_run_without_network(self):
        self.assertEqual(len(self.result["snapshots"]), 8)
        self.assertEqual(self.result["state"]["revision"], 5)
        self.assertEqual(len(self.backend.trace), 18)
        self.assertFalse(any(item["network"] for item in self.backend.trace))

    def test_recorded_projection_keeps_authored_scope_and_citations(self):
        projection = wb.project(self.result["state"])
        self.assertIn("manual-replay path", projection["handbook"])
        self.assertIn("automatic retries", projection["handbook"])
        self.assertIn("unknown-referent", projection["handbook"])
        for claim in self.result["state"]["claims"].values():
            self.assertIn(claim["text"], projection["handbook"])
            self.assertIn(claim["text"], projection["agentContext"])
        self.assertIn("fixture://retry/incident/7", projection["handbook"])

    def test_retired_references_still_resolve_and_history_is_recoverable(self):
        state = self.result["state"]
        self.assertEqual(wb.resolve(state, "retry-guidance")["id"], "retry-safety-scoped")
        self.assertIn("express broad retry safety", state["history"]["retry-guidance"]["text"])
        self.assertTrue(all(record["patch"]["rationale"] for record in state["journal"]))

    def test_replay_has_no_model_stages_or_revision_churn(self):
        snapshots = {item["step"]: item for item in self.result["snapshots"]}
        previous, replay = snapshots["scoped-mitigation"], snapshots["duplicate-delivery"]
        self.assertEqual(previous["projection"], replay["projection"])
        self.assertEqual(replay["disposition"], "exact-replay")
        self.assertNotIn("duplicate-delivery", [item["step"] for item in self.backend.trace])

    def test_received_not_processed_is_visible_in_discovery(self):
        snapshot = self.result["snapshots"][2]
        self.assertEqual(snapshot["pending"], ["incident"])
        self.assertEqual(snapshot["discovery"]["pending"], ["incident"])
        self.assertNotIn("fixture://retry/incident/7", snapshot["projection"]["handbook"])
        self.assertEqual(wb.discover(self.result["state"], "payments")["status"], "no-matching-knowledge")

    def test_review_is_explicitly_not_semantic_grading(self):
        review = wb.review(self.scenario, self.result["snapshots"])
        self.assertTrue(all(item["semantic_judgment"] == "pending-human-review" for item in review))
        self.assertTrue(all(all(item["structural"].values()) for item in review))
        self.assertTrue(all(item["required"] and item["forbidden"] for item in review))

    def test_oracle_and_future_sources_never_reach_model_contexts(self):
        scenario = copy.deepcopy(self.scenario)
        scenario["title"] = "ORACLE_CANARY"
        scenario["tags"] = ["ORACLE_CANARY"]
        for step in scenario["steps"]:
            step["expect"] = {"secret": "ORACLE_CANARY"}
        backend = models.RecordedBackend()
        wb.run(scenario, backend, through="scoped-mitigation")
        encoded = json.dumps(backend.contexts)
        self.assertNotIn("ORACLE_CANARY", encoded)
        for _, context in backend.contexts:
            self.assertNotIn("handbook", context["sources"])
            self.assertNotIn("no", context["sources"])
        self.assertNotIn("expressed-guidance", encoded)

    def test_retrieval_cannot_hide_active_claims_from_reasoning(self):
        for stage, context in self.backend.contexts:
            if stage == "reasoning":
                protected = {item["id"] for item in context["retrieval"]["protected"]}
                self.assertEqual(protected, {item["id"] for item in context["current"]})

    def test_stale_patch_rejected_without_partial_changes(self):
        state, response = self.first_state(), self.next_patch()
        wb.receive(state, "code", self.scenario["sources"]["code"])
        response["patch"]["baseRevision"] = 0
        before = copy.deepcopy(state)
        with self.assertRaisesRegex(ValueError, "stale"):
            self.commit_next(state, response)
        self.assertEqual(state, before)

    def test_fabricated_quote_rejected_atomically(self):
        state, response = self.first_state(), self.next_patch()
        wb.receive(state, "code", self.scenario["sources"]["code"])
        response["patch"]["operations"][0]["assertion"]["evidence"][0]["quote"] = "Guaranteed safe everywhere."
        before = copy.deepcopy(state)
        with self.assertRaisesRegex(ValueError, "fabricated"):
            self.commit_next(state, response)
        self.assertEqual(state, before)

    def test_pending_evidence_cannot_support_a_committed_claim(self):
        state, response = self.first_state(), self.next_patch()
        wb.receive(state, "code", self.scenario["sources"]["code"])
        wb.receive(state, "manual", self.scenario["sources"]["manual"])
        response["patch"]["operations"][0]["assertion"]["evidence"].append(
            {"source": "manual", "quote": "Manual replay suppresses outbound notifications."}
        )
        with self.assertRaisesRegex(ValueError, "unavailable"):
            self.commit_next(state, response)

    def test_replacement_cannot_drop_old_source_paths(self):
        state, response = self.first_state(), self.next_patch()
        wb.receive(state, "code", self.scenario["sources"]["code"])
        response["patch"]["operations"][0]["assertion"]["evidence"] = [
            {"source": "code", "quote": "We deduplicate database writes by event ID."}
        ]
        with self.assertRaisesRegex(ValueError, "drops source"):
            self.commit_next(state, response)

    def test_replacement_must_survive(self):
        state, response = self.first_state(), self.next_patch()
        wb.receive(state, "code", self.scenario["sources"]["code"])
        response["patch"]["operations"][1]["replacement"] = "missing"
        with self.assertRaisesRegex(ValueError, "surviving replacement"):
            self.commit_next(state, response)

    def test_historical_claim_identity_cannot_be_reused(self):
        state, response = self.first_state(), self.next_patch()
        wb.receive(state, "code", self.scenario["sources"]["code"])
        response["patch"]["operations"][0]["assertion"]["id"] = "retry-guidance"
        with self.assertRaisesRegex(ValueError, "identity already exists"):
            self.commit_next(state, response)

    def test_captured_live_v1_response_is_rejected_by_current_contract(self):
        observations = wb.export_cue([wb.ROOT / "experiments/workbench/observations.cue"])["observations"]
        with self.assertRaises(ValueError):
            wb.validate("#Patch", observations["v1"]["lastPatch"])
        self.assertNotIn("manual", [citation["source"]
            for operation in observations["v1"]["lastPatch"]["operations"] if operation["op"] == "add"
            for citation in operation["assertion"]["evidence"]])

    def test_new_source_cannot_be_marked_processed_without_accounting(self):
        state, response = self.first_state(), self.next_patch()
        wb.receive(state, "code", self.scenario["sources"]["code"])
        response["patch"]["accounting"] = {}
        before = copy.deepcopy(state)
        with self.assertRaisesRegex(ValueError, "unaccounted"):
            self.commit_next(state, response)
        self.assertEqual(state, before)

    def test_claimed_representation_requires_a_citation_to_new_source(self):
        state, response = self.first_state(), self.next_patch()
        wb.receive(state, "code", self.scenario["sources"]["code"])
        evidence = response["patch"]["operations"][0]["assertion"]["evidence"]
        response["patch"]["operations"][0]["assertion"]["evidence"] = [c for c in evidence if c["source"] != "code"]
        with self.assertRaisesRegex(ValueError, "not represented"):
            self.commit_next(state, response)

    def test_noop_cannot_use_unprocessed_source_as_its_own_basis(self):
        state, response = self.first_state(), self.next_patch()
        wb.receive(state, "code", self.scenario["sources"]["code"])
        response["patch"]["accounting"]["code"] = {
            "mode": "dependent-no-op", "claims": ["database-writes"], "reason": "circular processing claim",
            "basis": [{"source": "code", "quote": "We deduplicate database writes by event ID."}],
        }
        with self.assertRaisesRegex(ValueError, "unavailable"):
            self.commit_next(state, response)

    def test_projection_cannot_become_canonical_support(self):
        state = wb.run(self.scenario, models.RecordedBackend(), through="contextual-no")["state"]
        wb.receive(state, "handbook", self.scenario["sources"]["handbook"])
        patch = {"accounting": {"handbook": {"mode": "represented", "claims": ["bad-feedback"], "reason": "bad feedback"}},
                 "baseRevision": state["revision"], "rationale": "bad feedback", "operations": [{
            "op": "add", "assertion": {"id": "bad-feedback", "text": "A new proof.", "scope": "all", "attribution": "inferred",
            "evidence": [{"source": "handbook", "quote": "Database writes are deduplicated."}]},
        }]}
        record = state["journal"][-1]
        with self.assertRaisesRegex(ValueError, "projections"):
            wb.commit(state, patch, ["handbook"], record["analysis"], record["route"])

    def test_direct_commit_cannot_reprocess_an_old_source(self):
        state, response = self.first_state(), self.next_patch()
        response["patch"]["accounting"] = {"guide": {"mode": "represented", "claims": ["retry-guidance"], "reason": "replay"}}
        with self.assertRaisesRegex(ValueError, "not-yet-processed"):
            wb.commit(state, response["patch"], ["guide"], response["analysis"], response["route"])

    def test_source_identity_reuse_is_rejected(self):
        state = self.first_state()
        with self.assertRaisesRegex(ValueError, "identity reused"):
            wb.receive(state, "guide", dict(self.scenario["sources"]["guide"], text="Different."))

    def test_router_noop_cannot_silently_discard_new_evidence(self):
        backend = models.RecordedBackend()
        backend.route = lambda step, context: {"action": "no-op"}
        result = wb.run(self.scenario, backend)
        self.assertEqual(result["state"]["claims"], self.result["state"]["claims"])
        self.assertEqual(result["snapshots"][0]["disposition"], "analyze")

    def test_stage_contracts_reject_unknown_fields_and_invalid_operations(self):
        cases = [
            ("#Route", {"action": "commit"}),
            ("#Analysis", {"assertions": []}),
            ("#Patch", {"baseRevision": 0, "rationale": "why", "operations": [{"op": "erase"}]}),
            ("#Projection", {"revision": 0, "handbook": "x", "agentContext": "x", "claims": [], "extra": 1}),
        ]
        for definition, value in cases:
            with self.subTest(definition=definition), self.assertRaises(ValueError):
                wb.validate(definition, value)

    def test_cli_offline_artifact_and_no_overwrite(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "run.json"
            with mock.patch("sys.stdout", new_callable=io.StringIO):
                self.assertEqual(wb.main(["--output", str(output)]), 0)
            artifact = json.loads(output.read_text())
            self.assertEqual(len(artifact["evaluation"]), 8)
            with mock.patch("sys.stderr", new_callable=io.StringIO), self.assertRaises(SystemExit):
                wb.main(["--output", str(output)])
            with mock.patch("sys.stdout", new_callable=io.StringIO) as stdout, \
                    mock.patch.object(models, "transport") as transport:
                self.assertEqual(wb.main(["--inspect", str(output), "--query", "payments", "--reference", "retry-guidance"]), 0)
                inspection = json.loads(stdout.getvalue())
                self.assertEqual(inspection["discovery"]["status"], "no-matching-knowledge")
                self.assertEqual(inspection["current"]["id"], "retry-safety-scoped")
                transport.assert_not_called()


class LiveWorkbenchTests(TestCase):
    def args(self, **changes):
        return SimpleNamespace(**{
            **dict(router="jev", analysis_model="test/analysis", reasoning_model="test/reasoning", budget_usd=1.0, max_calls=18),
            **changes,
        })

    def backend(self, sender, **changes):
        with mock.patch.dict(models.os.environ, {"OPENROUTER_API_KEY": "SECRET_CANARY"}):
            return models.LiveBackend(self.args(**changes), sender=sender)

    def routed_response(self):
        return {
            "model": "typesafe/jev-1.14", "answers": {"action": {"type": "choice", "choice": "analyze"}},
            "usage": {"input_tokens": 10, "output_tokens": 1, "cost": 0.000001},
        }

    def test_no_live_configuration_without_explicit_role_models_and_budget(self):
        for changes in [dict(analysis_model=None), dict(reasoning_model=None), dict(budget_usd=None),
                        dict(budget_usd=float("nan")), dict(max_calls=19)]:
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                self.backend(mock.Mock(), **changes)

    def test_rules_router_is_a_network_free_baseline(self):
        sender = mock.Mock()
        backend = self.backend(sender, router="rules")
        self.assertEqual(backend.route("s", {"incoming": ["new"], "already_processed": []}), {"action": "analyze"})
        self.assertEqual(backend.route("s", {"incoming": ["old"], "already_processed": ["old"]}), {"action": "no-op"})
        sender.assert_not_called()
        self.assertTrue(all(not item["network"] for item in backend.trace))

    def test_call_limit_and_budget_stop_before_transport(self):
        sender = mock.Mock(return_value=self.routed_response())
        backend = self.backend(sender, max_calls=1)
        backend.route("s", {})
        with self.assertRaisesRegex(ValueError, "call limit"):
            backend.route("s", {})
        sender.assert_called_once()
        sender.reset_mock()
        backend = self.backend(sender, budget_usd=0.00000001)
        with self.assertRaisesRegex(ValueError, "budget"):
            backend.route("s", {})
        sender.assert_not_called()

    def test_full_mocked_live_loop_keeps_model_roles_separate(self):
        recorded = models.RecordedBackend().responses
        corpus = wb.export_cue(sorted((wb.ROOT / "corpus").glob("*.cue")))
        steps = [step["id"] for step in corpus["scenarios"]["retry-safety"]["steps"]
                 if step["id"] in recorded]
        calls = []

        def sender(endpoint, payload, token):
            index = len(calls)
            calls.append(copy.deepcopy(payload))
            response = {"model": payload["model"], "usage": {"cost": 0.00001, "input_tokens": 10, "output_tokens": 10}}
            step = steps[index // 3]
            if endpoint == models.ENDPOINT:
                response["answers"] = {"action": {"type": "choice", "choice": recorded[step]["route"]["action"]}}
            else:
                field = "analysis" if payload["model"] == "test/analysis" else "patch"
                response["choices"] = [{"finish_reason": "stop", "message": {"content": json.dumps(recorded[step][field])}}]
            return response

        backend = self.backend(sender)
        result = wb.run(corpus["scenarios"]["retry-safety"], backend)
        self.assertEqual(len(calls), 18)
        self.assertEqual(result["state"]["revision"], 5)
        self.assertEqual([call["model"] for call in calls[:3]], ["typesafe/jev-1.14", "test/analysis", "test/reasoning"])
        self.assertNotIn("SECRET_CANARY", json.dumps(backend.trace))
        self.assertTrue(all(item["reported_cost_usd"] == 0.00001 for item in backend.trace))

    def test_unknown_cost_stops_without_retry(self):
        response = self.routed_response()
        response["usage"].pop("cost")
        sender = mock.Mock(return_value=response)
        backend = self.backend(sender)
        with self.assertRaisesRegex(ValueError, "could not be accounted"):
            backend.route("s", {})
        sender.assert_called_once()
        self.assertEqual(backend.trace[-1]["status"], "failed-or-unaccounted")
        self.assertNotIn("SECRET_CANARY", json.dumps(backend.trace))

    def test_truncated_chat_response_is_rejected(self):
        sender = mock.Mock(return_value={
            "model": "test/analysis", "usage": {"cost": 0, "input_tokens": 10, "output_tokens": 10},
            "choices": [{"finish_reason": "length", "message": {"content": "SECRET_CANARY"}}],
        })
        backend = self.backend(sender)
        with self.assertRaisesRegex(ValueError, "stage contract"):
            backend.analyze("s", {})
        self.assertNotIn("SECRET_CANARY", json.dumps(backend.trace))

    def test_failed_stage_checkpoint_retains_sources_but_no_partial_patch(self):
        corpus = wb.export_cue(sorted((wb.ROOT / "corpus").glob("*.cue")))
        sender = mock.Mock(return_value=self.routed_response())
        backend = self.backend(sender, max_calls=1)
        checkpoints = []
        with self.assertRaisesRegex(ValueError, "call limit"):
            wb.run(corpus["scenarios"]["retry-safety"], backend,
                   checkpoint=lambda state, snapshots, trace: checkpoints.append(copy.deepcopy((state, snapshots, trace))))
        state, snapshots, trace = checkpoints[-1]
        self.assertEqual(set(state["received"]), {"guide", "retry"})
        self.assertEqual(state["revision"], 0)
        self.assertEqual(state["claims"], {})
        self.assertEqual(state["processed"], [])
        self.assertEqual(snapshots, [])
        self.assertEqual(len(trace), 1)
        sender.assert_called_once()
