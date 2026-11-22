"""Jev adapter contract tests. Never call the network, even with a token set."""

import copy
import io
import json
from unittest import TestCase, mock

from scripts import jev_probe as probe


class JevProbeTests(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.corpus, cls.config = probe.load_inputs()

    def response(self):
        return {
            "model": "typesafe/jev-1.14-20261014",
            "answers": {"action": {"type": "choice", "choice": "analyze", "confidence": 0.8}},
            "usage": {"input_tokens": 123, "output_tokens": 0, "cost": 0.00001},
        }

    def test_all_case_references_and_request_limits(self):
        for case_id, case in self.config["cases"].items():
            with self.subTest(case=case_id):
                request = probe.build_request(self.corpus, self.config, case_id)
                self.assertIn(case["expected"], request["questions"]["action"]["criteria"])
                self.assertEqual(request["provider"]["only"], ["typesafe"])
                self.assertFalse(request["provider"]["allow_fallbacks"])

    def test_no_oracle_or_future_evidence_in_request(self):
        corpus, config = copy.deepcopy(self.corpus), copy.deepcopy(self.config)
        scenario = corpus["scenarios"]["retry-safety"]
        scenario["title"] = "ORACLE_CANARY"
        scenario["tags"] = ["ORACLE_CANARY"]
        for step in scenario["steps"]:
            step["expect"] = {"secret": "ORACLE_CANARY"}
        scenario["sources"]["handbook"]["text"] = "FUTURE_CANARY"
        config["cases"]["contextual-no"]["reason"] = "ORACLE_CANARY"
        request = probe.build_request(corpus, config, "contextual-no")
        encoded = json.dumps(request)
        self.assertNotIn("ORACLE_CANARY", encoded)
        self.assertNotIn("FUTURE_CANARY", encoded)
        self.assertNotIn("handbook", request["state"]["sources"])
        self.assertNotIn("contextual-no", encoded)

    def test_pending_is_not_already_processed(self):
        request = probe.build_request(self.corpus, self.config, "pending-incident")
        self.assertIn("incident", request["state"]["sources"])
        self.assertNotIn("incident", request["state"]["already_processed"])

    def test_duplicate_is_already_processed(self):
        request = probe.build_request(self.corpus, self.config, "duplicate-incident")
        self.assertIn("incident", request["state"]["already_processed"])

    def test_same_batch_reply_context_is_available(self):
        request = probe.build_request(self.corpus, self.config, "contextual-no")
        state = request["state"]
        self.assertEqual(state["sources"]["no"]["replyTo"], "proposal")
        self.assertIn("proposal", state["sources"])
        self.assertNotIn("proposal", state["already_processed"])

    def test_oversize_request_is_rejected(self):
        config = dict(self.config, maxRequestBytes=1)
        with self.assertRaisesRegex(ValueError, "byte limit"):
            probe.build_request(self.corpus, config, "contextual-no")

    def test_missing_step_is_rejected(self):
        config = copy.deepcopy(self.config)
        config["cases"]["contextual-no"]["step"] = "missing"
        with self.assertRaisesRegex(ValueError, "missing step"):
            probe.build_request(self.corpus, config, "contextual-no")

    def test_unavailable_incoming_is_rejected(self):
        config = copy.deepcopy(self.config)
        config["cases"]["contextual-no"]["incoming"] = ["handbook"]
        with self.assertRaisesRegex(ValueError, "unavailable incoming"):
            probe.build_request(self.corpus, config, "contextual-no")

    def test_unknown_action_is_rejected(self):
        response = self.response()
        response["answers"]["action"]["choice"] = "commit"
        with self.assertRaisesRegex(ValueError, "unknown action"):
            probe.summarize_response(response, self.config["model"])

    def test_refusal_is_rejected(self):
        response = self.response()
        response["answers"]["action"] = {"type": "refusal"}
        with self.assertRaisesRegex(ValueError, "refusal"):
            probe.summarize_response(response, self.config["model"])

    def test_missing_cost_is_explicitly_unknown(self):
        response = self.response()
        response["usage"].pop("cost")
        result = probe.summarize_response(response, self.config["model"])
        self.assertIsNone(result["reported_cost_usd"])

    def test_malformed_responses_fail_closed(self):
        variants = []
        for key, value in [("choice", []), ("confidence", float("nan")), ("confidence", True)]:
            response = self.response()
            response["answers"]["action"][key] = value
            variants.append(response)
        response = self.response()
        response["model"] = "typesafe/jev-router"
        variants.append(response)
        response = self.response()
        response["usage"]["input_tokens"] = -1
        variants.append(response)
        for response in variants:
            with self.subTest(response=response), self.assertRaises(ValueError):
                probe.summarize_response(response, self.config["model"])

    def test_preview_never_sends_even_with_a_token(self):
        with mock.patch.object(probe, "send_request") as send, \
                mock.patch.dict(probe.os.environ, {"OPENROUTER_API_KEY": "SECRET_CANARY"}), \
                mock.patch("sys.stdout", new_callable=io.StringIO) as output:
            self.assertEqual(probe.main(["contextual-no"]), 0)
            send.assert_not_called()
            self.assertNotIn("SECRET_CANARY", output.getvalue())
            self.assertEqual(json.loads(output.getvalue())["mode"], "preview")

    def test_live_is_one_call_and_reports_no_authorized_effects(self):
        with mock.patch.object(probe, "send_request", return_value=self.response()) as send, \
                mock.patch.dict(probe.os.environ, {"OPENROUTER_API_KEY": "SECRET_CANARY"}), \
                mock.patch("sys.stdout", new_callable=io.StringIO) as output:
            self.assertEqual(probe.main(["contextual-no", "--live"]), 0)
            send.assert_called_once()
            self.assertNotIn("SECRET_CANARY", output.getvalue())
            self.assertEqual(json.loads(output.getvalue())["authorized_effects"], "none")

    def test_http_error_does_not_echo_body_or_token(self):
        error = probe.urllib.error.HTTPError(
            probe.ENDPOINT, 401, "SECRET_CANARY", {}, io.BytesIO(b"SECRET_CANARY"),
        )
        opener = mock.Mock()
        opener.open.side_effect = error
        with mock.patch.object(probe.urllib.request, "build_opener", return_value=opener):
            with self.assertRaisesRegex(ValueError, "HTTP 401") as raised:
                probe.send_request({}, "SECRET_CANARY")
            opener.open.assert_called_once()
            self.assertNotIn("SECRET_CANARY", str(raised.exception))

    def test_redirect_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "redirect refused"):
            probe.NoRedirect().redirect_request(None, None, 302, "", {}, "https://example.com")
