import base64
import copy
from contextlib import redirect_stderr, redirect_stdout
import io
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import Mock, patch

from scripts import maintenance_call as trial


class MaintenanceCallTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with patch("urllib.request.urlopen", side_effect=AssertionError("offline preparation")):
            cls.report = trial.prepare()
        cls.frozen = cls.report["protocol"]["frozen"]
        cls.data, _ = trial.proposer.load()

    def response(self, value=None, **changes):
        if value is None:
            value = {"baseRevision": 5, "accounting": {}, "operations": [], "rationale": "Retain the current view."}
        response = {"model": "openai/gpt-4.1", "provider": "OpenAI", "choices": [{"finish_reason": "stop", "message": {"content": json.dumps(value)}}],
                    "usage": {"prompt_tokens": 2000, "completion_tokens": 500, "cost": 0.001}}
        response.update(changes)
        return response

    def run_in(self, directory, response=None, report=None, sender=None):
        report = copy.deepcopy(self.report) if report is None else report
        sender = sender if sender is not None else Mock(return_value=response if response is not None else self.response())
        snapshots = []
        with patch.dict(os.environ, {"OPENROUTER_API_KEY": "offline-test-token"}):
            trial.run(report, lambda: snapshots.append(copy.deepcopy(report)), authorized_protocol_sha256=report["protocol"]["sha256"],
                      sender=sender, receipt_directory=directory)
        return report, sender, snapshots

    def test_fixed_request_only_uses_blind_messages_and_pinned_single_role(self):
        f = self.frozen
        self.assertEqual(f["limits"], {"budget_usd": 0.15, "max_calls": 1, "retries": 0})
        payload = f["operation"]["payload"]
        self.assertEqual(payload["messages"], trial.proposer.proposer_messages(f["checkpoint"]))
        self.assertNotIn("retry-safety-current", json.dumps(payload))
        self.assertEqual(payload["model"], "openai/gpt-4.1")
        self.assertEqual(payload["provider"]["only"], ["openai"])
        self.assertFalse(payload["provider"]["allow_fallbacks"])
        self.assertTrue(payload["provider"]["require_parameters"])
        self.assertEqual(payload["max_tokens"], 8000)
        self.assertEqual(f["plan"]["transportTimeoutSeconds"], 120)
        self.assertEqual(trial.proposer.digest(f), self.report["protocol"]["sha256"])
        self.assertGreater(f["reservation_usd"], 0)
        self.assertLessEqual(f["reservation_usd"], 0.15)
        self.assertEqual(self.report["trace"], [])

    def test_exact_hash_required_before_credential_access_or_submission(self):
        sender = Mock()
        with self.assertRaisesRegex(ValueError, "exact-hash"), patch.object(trial.client, "Ledger", side_effect=AssertionError("no credential access")):
            trial.run(copy.deepcopy(self.report), lambda: None, sender=sender)
        sender.assert_not_called()

    def test_one_accounted_noop_native_response_saved_before_inspection(self):
        with TemporaryDirectory() as directory:
            report, sender, snapshots = self.run_in(directory)
        self.assertEqual(sender.call_count, 1)
        self.assertEqual(report["status"], "completed-one-call")
        self.assertEqual(report["summary"]["submitted_calls"], 1)
        self.assertEqual(report["summary"]["unknown_billing"], 0)
        self.assertAlmostEqual(report["summary"]["known_cost_usd"], 0.001)
        self.assertEqual(report["inspection"]["status"], "no-op-in-isolated-copy")
        self.assertEqual(report["inspection"]["semantic_judgment"], "pending-human-review")
        self.assertFalse(report["inspection"]["canonical_acceptance"])
        self.assertEqual(report["trace"][0]["reserved_usd"], self.frozen["reservation_usd"])
        self.assertTrue(any(s["trace"] and "response" in s["trace"][0] and "inspection" not in s for s in snapshots))

    def test_actual_mock_patch_exercises_recovery_without_semantic_acceptance(self):
        candidate = copy.deepcopy(self.data["maintenance"]["consolidation"]["patch"])
        candidate["operations"][0]["assertion"]["text"] = "All retry paths are safe."
        with TemporaryDirectory() as directory:
            report, sender, _ = self.run_in(directory, self.response(candidate))
        self.assertEqual(sender.call_count, 1)
        self.assertTrue(report["inspection"]["recovery"]["material_recovered"])
        self.assertEqual(report["inspection"]["proposal"], candidate)
        self.assertEqual(report["summary"]["semantic_judgment"], "pending-human-review")
        self.assertFalse(report["summary"]["canonical_acceptance"])

    def test_receipt_prevents_fresh_copy_or_new_output_from_repeating_protocol(self):
        with TemporaryDirectory() as directory:
            report, sender, _ = self.run_in(directory)
            receipt = Path(directory) / (report["protocol"]["sha256"] + ".json")
            self.assertTrue(receipt.exists())
            with self.assertRaisesRegex(ValueError, "cannot resume"):
                self.run_in(directory, report=report, sender=sender)
            with self.assertRaisesRegex(ValueError, "already claimed"):
                self.run_in(directory, report=copy.deepcopy(self.report), sender=sender)
            self.assertEqual(sender.call_count, 1)

    def test_unknown_billing_keeps_reservation_response_and_one_shot_receipt(self):
        response = self.response(); response["usage"]["cost"] = None
        report, sender = copy.deepcopy(self.report), Mock(return_value=response)
        with TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ValueError, "no retry"):
                self.run_in(directory, report=report, sender=sender)
            self.assertEqual(report["status"], "stopped-no-retry")
            self.assertEqual(report["summary"]["unknown_billing"], 1)
            self.assertEqual(report["summary"]["accounted_or_reserved_usd"], self.frozen["reservation_usd"])
            self.assertEqual(report["trace"][0]["response"], response)
            with self.assertRaisesRegex(ValueError, "already claimed"):
                self.run_in(directory, sender=sender)
            self.assertEqual(sender.call_count, 1)

    def test_reported_overrun_is_known_cost_not_unknown_or_permission_for_another_call(self):
        response = self.response(); response["usage"]["cost"] = 0.16
        report, sender = copy.deepcopy(self.report), Mock(return_value=response)
        with TemporaryDirectory() as directory, self.assertRaisesRegex(ValueError, "no retry"):
            self.run_in(directory, report=report, sender=sender)
        self.assertEqual(sender.call_count, 1)
        self.assertEqual(report["summary"]["known_cost_usd"], 0.16)
        self.assertEqual(report["summary"]["unknown_billing"], 0)
        self.assertEqual(report["status"], "stopped-no-retry")

    def test_deadline_and_http_error_adapter_retain_unknown_billing_diagnostics(self):
        for reason, body in (("deadline-expired", None), ("http-error", {"http_status": 402, "body_base64": base64.b64encode(b"Synthetic credit failure").decode(), "body_truncated": False})):
            report = copy.deepcopy(self.report)
            failure = trial.deadline_transport.TransportFailure(reason, {"elapsed_seconds": 120, "possibly_billed": True, "worker_reaped": True}, body, body is not None)
            with self.subTest(reason=reason), TemporaryDirectory() as directory, patch.dict(os.environ, {"OPENROUTER_API_KEY": "offline-test-token"}), patch.object(trial.deadline_transport, "request", side_effect=failure) as request:
                with self.assertRaisesRegex(ValueError, "no retry"):
                    trial.run(report, lambda: None, authorized_protocol_sha256=report["protocol"]["sha256"], receipt_directory=directory)
                self.assertEqual(request.call_count, 1)
                self.assertEqual(report["trace"][0]["transport"]["attempts"], 1)
                self.assertEqual(report["trace"][0]["transport"]["outcome"], reason)
                self.assertEqual(report["summary"]["unknown_billing"], 1)
                if body is not None:
                    self.assertEqual(report["trace"][0]["response"], body)

    def test_invalid_finish_model_or_multiple_choices_never_resampled(self):
        responses = []
        length = self.response(); length["choices"][0]["finish_reason"] = "length"; responses.append(length)
        refusal = self.response(); refusal["choices"][0]["message"]["content"] = None; responses.append(refusal)
        explicit = self.response(); explicit["choices"][0]["message"]["refusal"] = "Synthetic refusal"; responses.append(explicit)
        wrong = self.response(); wrong["model"] = "openai/gpt-4.1-mini"; responses.append(wrong)
        multiple = self.response(); multiple["choices"] *= 2; responses.append(multiple)
        for response in responses:
            with self.subTest(response=response), TemporaryDirectory() as directory:
                report, sender, _ = self.run_in(directory, response)
                self.assertEqual(sender.call_count, 1)
                self.assertEqual(report["summary"]["proposal_status"], "invalid-native-output-no-replacement")
                self.assertEqual(report["trace"][0]["response"], response)
                self.assertEqual(report["summary"]["unknown_billing"], 0)

    def test_invalid_patch_content_preserved_without_repair_and_dated_model_allowed(self):
        response = self.response(model="openai/gpt-4.1-2025-04-14")
        response["choices"][0]["message"]["content"] = '```json\n{"operations": []}\n```'
        with TemporaryDirectory() as directory:
            report, sender, _ = self.run_in(directory, response)
        self.assertEqual(sender.call_count, 1)
        self.assertEqual(report["inspection"]["status"], "invalid-json-not-applied")
        self.assertEqual(base64.b64decode(report["inspection"]["input"]["base64"]).decode(), response["choices"][0]["message"]["content"])

    def test_inspection_failure_does_not_lose_accounted_native_response(self):
        with TemporaryDirectory() as directory, patch.object(trial.proposer, "inspect_proposal", side_effect=ValueError("Synthetic inspector failure")):
            report, sender, _ = self.run_in(directory)
        self.assertEqual(sender.call_count, 1)
        self.assertEqual(report["output_status"], "inspection-failed-native-response-retained")
        self.assertIn("response", report["trace"][0])
        self.assertEqual(report["summary"]["known_cost_usd"], 0.001)

    def test_token_redacted_and_changed_request_or_limits_rejected(self):
        response = self.response(); response["debug"] = "offline-test-token"
        with TemporaryDirectory() as directory:
            report, _, _ = self.run_in(directory, response)
        self.assertNotIn("offline-test-token", json.dumps(report))
        changed = copy.deepcopy(self.report)
        changed["protocol"]["frozen"]["operation"]["payload"]["messages"].append({"role": "user", "content": "private labels"})
        with self.assertRaisesRegex(ValueError, "changed request"):
            trial.check(changed)
        plan = copy.deepcopy(self.frozen["plan"]); plan["maxBudgetUSD"] = 1
        with self.assertRaises(ValueError):
            trial.validate_plan(plan)

    def test_cli_prepares_without_credentials_no_clobber_or_unbound_live_output(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "prepared.json"
            with redirect_stdout(io.StringIO()):
                self.assertEqual(trial.main(["--output", str(path)]), 0)
            self.assertEqual(json.loads(path.read_text())["trace"], [])
            with self.assertRaises(ValueError):
                trial.main(["--output", str(path)])
            missing = Path(directory) / "not-created.json"
            with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
                trial.main(["--live", "--output", str(missing)])
            with self.assertRaisesRegex(ValueError, "exact untouched"):
                trial.main(["--live", "--prepared", str(path), "--protocol-sha256", "wrong", "--output", str(missing)])
            self.assertFalse(missing.exists())
