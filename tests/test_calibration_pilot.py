"""Offline safety, freezing, accounting, and contract tests; not semantic proof."""

import copy
import io
import json
import os
from pathlib import Path
import tempfile
from unittest import TestCase, mock

from scripts import calibration, calibration_pilot as pilot
from scripts.evaluation_client import Client, Contracts, OutputFailure


class PilotTests(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data, _, _ = calibration.load()
        cls.contracts = Contracts(pilot.CONTRACT)

    def prepared(self):
        return pilot.prepare(self.data, self.contracts, 0.10, 10)

    def judgment(self, context):
        source = context["authoritative_sources"][0]
        return {"result": "uncertain", "rationale": "Recorded structural fixture, not semantic gold.",
                "answerQuotes": [], "citations": [{"source": source["id"], "quote": source["text"]}]}

    def sender(self, endpoint, payload, token):
        self.assertEqual(token, "SECRET_CANARY")
        self.assertEqual(payload["model"], "openai/gpt-4.1-mini")
        self.assertEqual(payload["provider"]["only"], ["openai"])
        self.assertFalse(payload["provider"]["allow_fallbacks"])
        self.assertNotIn("inputSHA256", payload["messages"][0]["content"])
        context = json.loads(payload["messages"][1]["content"])
        self.assertEqual(set(context), {"question", "criterion", "target", "candidate", "authoritative_sources"})
        return {"model": "openai/gpt-4.1-mini", "provider": "OpenAI", "usage": {"cost": 0.001, "prompt_tokens": 100, "completion_tokens": 100},
                "choices": [{"finish_reason": "stop", "message": {"content": json.dumps(self.judgment(context))}}]}

    def test_prepare_is_offline_deterministic_and_bound_to_ten_approved_pairs(self):
        report = self.prepared()
        self.assertEqual(report, self.prepared())
        self.assertEqual(len(report["rows"]), 10)
        self.assertEqual(pilot.digest(report["protocol"]["frozen"]), report["protocol"]["sha256"])
        self.assertEqual(sum(row["reference"] == "pass" for row in report["rows"]), 3)
        self.assertEqual(report["trace"], [])

    def test_approved_payload_or_label_changes_require_new_approval(self):
        for mutation in ("candidate", "reference", "source", "membership"):
            data = copy.deepcopy(self.data)
            group = data["threadContrasts"][0]
            if mutation == "candidate":
                group["candidates"][0]["candidate"] += " changed"
            elif mutation == "reference":
                group["candidates"][0]["expected"] = "fail"
            elif mutation == "source":
                data["threads"][0]["messages"][0]["text"] += " changed"
            else:
                group["candidates"].pop()
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                pilot.prepare(data, self.contracts, 0.10, 10)

    def test_limits_cannot_exceed_user_authorization(self):
        for budget, calls in ((0.11, 10), (0.10, 11), (float("nan"), 10), (0, 10), (0.10, True)):
            with self.subTest(budget=budget, calls=calls), self.assertRaises(ValueError):
                pilot.prepare(self.data, self.contracts, budget, calls)

    def test_quote_checks_are_separate_from_semantic_labels(self):
        context = self.prepared()["protocol"]["frozen"]["samples"][0]["judge_input"]
        value = self.judgment(context)
        self.contracts.validate("#PilotJudgment", value)
        pilot.validate_judgment(value, context)
        for mutation in ("pass", "answer", "source", "quote"):
            bad = copy.deepcopy(value)
            if mutation == "pass":
                bad["result"] = "pass"
            elif mutation == "answer":
                bad["answerQuotes"] = ["invented text"]
            elif mutation == "source":
                bad["citations"][0]["source"] = "unknown"
            else:
                bad["citations"][0]["quote"] = "invented quote"
            with self.subTest(mutation=mutation), self.assertRaises(OutputFailure):
                pilot.validate_judgment(bad, context)

    def test_recorded_calls_preserve_denominators_and_do_not_send_references(self):
        report = self.prepared()
        with mock.patch.dict(os.environ, {"OPENROUTER_API_KEY": "SECRET_CANARY"}):
            client = Client(self.data["pilotPlan"], self.contracts, budget=0.10, max_calls=10, sender=self.sender)
            pilot.run(report, client, lambda: None)
        self.assertEqual(report["status"], "completed")
        self.assertEqual(len(report["trace"]), 10)
        self.assertAlmostEqual(report["accounted_or_reserved_usd"], 0.01)
        self.assertEqual(report["summary"]["primary"]["planned"], 7)
        self.assertEqual(report["summary"]["robustness"]["planned"], 3)
        self.assertEqual(sum(group["judged"] for group in report["summary"].values()), 10)
        self.assertNotIn("SECRET_CANARY", json.dumps(report))
        with self.assertRaises(ValueError):
            pilot.run(report, client, lambda: None)

    def test_invalid_outputs_are_not_replaced_and_accounting_failure_stops(self):
        for failure in ("output", "billing"):
            report = self.prepared()
            def sender(endpoint, payload, token):
                response = self.sender(endpoint, payload, token)
                if failure == "output":
                    response["choices"][0]["message"]["content"] = "not JSON"
                else:
                    response["usage"].pop("cost")
                return response
            with mock.patch.dict(os.environ, {"OPENROUTER_API_KEY": "SECRET_CANARY"}):
                client = Client(self.data["pilotPlan"], self.contracts, budget=0.10, max_calls=10, sender=sender)
                pilot.run(report, client, lambda: None)
            if failure == "output":
                self.assertEqual(len(report["trace"]), 10)
                self.assertEqual(sum(group["invalid"] for group in report["summary"].values()), 10)
            else:
                self.assertEqual(len(report["trace"]), 1)
                self.assertEqual(report["status"], "stopped-no-retry")
                self.assertEqual(sum(group["not_attempted"] for group in report["summary"].values()), 9)

    def test_protocol_or_row_tampering_prevents_calls(self):
        for mutation in ("protocol", "rows"):
            report = self.prepared()
            if mutation == "protocol":
                report["protocol"]["frozen"]["plan"]["temperature"] = 1
            else:
                report["rows"].pop()
            client = mock.Mock()
            with self.assertRaises(ValueError):
                pilot.run(report, client, lambda: None)
            client.call.assert_not_called()

    def test_default_cli_never_constructs_a_live_client_or_overwrites_output(self):
        with tempfile.TemporaryDirectory() as directory, mock.patch.object(pilot, "Client") as client, mock.patch("sys.stdout", new_callable=io.StringIO):
            path = Path(directory) / "prepared.json"
            self.assertEqual(pilot.main(["--output", str(path)]), 0)
            before = path.read_bytes()
            self.assertEqual(pilot.main(["--output", str(path)]), 2)
            self.assertEqual(before, path.read_bytes())
            client.assert_not_called()

    def test_capture_preserves_malformed_text_without_retry_or_secret(self):
        def malformed(endpoint, payload, token):
            response = self.sender(endpoint, payload, token)
            response["choices"][0]["message"]["content"] = "not JSON SECRET_CANARY"
            return response
        with tempfile.TemporaryDirectory() as directory, mock.patch.dict(os.environ, {"OPENROUTER_API_KEY": "SECRET_CANARY"}), mock.patch.object(pilot, "transport", side_effect=malformed), mock.patch("sys.stdout", new_callable=io.StringIO):
            path = Path(directory) / "live-recorded.json"
            self.assertEqual(pilot.main(["--live", "--output", str(path)]), 0)
            result = json.loads(path.read_text())
            self.assertTrue(all(row["response_choices"][0]["message"]["content"] == "not JSON [REDACTED]" for row in result["rows"]))
            self.assertEqual(sum(group["invalid"] for group in result["summary"].values()), 10)
            self.assertNotIn("SECRET_CANARY", path.read_text())
