import base64
import io
import json
import os
from pathlib import Path
import time
import unittest
import urllib.error
from unittest.mock import patch

from scripts import deadline_transport as transport
from scripts.split_judgment import Ledger


# Spawn-compatible workers: no sockets, credentials, or provider calls in tests.
def success(path, endpoint, payload, token, timeout, maximum):
    Path(path).write_text(json.dumps({"status": "received", "response": {"echo": payload, "usage": {"cost": 0.001}}}))


def dribble(path, endpoint, payload, token, timeout, maximum):
    # Simulate endless activity which would reset a socket-operation timeout.
    with Path(path + ".partial").open("w") as stream:
        while True:
            stream.write(" ")
            stream.flush()
            time.sleep(0.01)


def completed_body_but_stuck(path, endpoint, payload, token, timeout, maximum):
    Path(path).write_text(json.dumps({"status": "received", "response": {"error": {"code": 504, "message": token}, "id": "synthetic-id"}}))
    time.sleep(20)


def oversized(path, endpoint, payload, token, timeout, maximum):
    Path(path).write_bytes(b"x" * (2 * maximum + 4097))


def broken(path, endpoint, payload, token, timeout, maximum):
    Path(path).write_text('{"status":')


def api_error(path, endpoint, payload, token, timeout, maximum):
    Path(path).write_text(json.dumps({"status": "received", "response": {"error": {"code": 504, "message": "timeout"}, "id": "synthetic-id"}}))


class DeadlineTransportTests(unittest.TestCase):
    def test_one_success_returns_native_body_without_repair(self):
        response = transport.request("offline", {"input": "synthetic"}, "test-secret", timeout=3, worker=success)
        self.assertEqual(response, {"echo": {"input": "synthetic"}, "usage": {"cost": 0.001}})

    def test_dribbling_cannot_extend_absolute_deadline_or_promote_partial_body(self):
        started = time.monotonic()
        with self.assertRaises(transport.TransportFailure) as caught:
            transport.request("offline", {}, "test-secret", timeout=0.5, worker=dribble)
        failure = caught.exception
        self.assertEqual(str(failure), "deadline-expired")
        self.assertLess(time.monotonic() - started, 3)
        self.assertTrue(failure.diagnostic["worker_reaped"])
        self.assertTrue(failure.diagnostic["possibly_billed"])
        self.assertFalse(failure.diagnostic["response_available"])
        self.assertNotIn("test-secret", str(failure))

    def test_complete_body_is_preserved_even_when_worker_times_out(self):
        with self.assertRaises(transport.TransportFailure) as caught:
            transport.request("offline", {}, "test-secret", timeout=1, worker=completed_body_but_stuck)
        failure = caught.exception
        self.assertEqual(str(failure), "deadline-expired")
        self.assertTrue(failure.diagnostic["response_available"])
        self.assertEqual(failure.response["id"], "synthetic-id")
        self.assertEqual(failure.response["error"]["code"], 504)
        self.assertTrue(failure.diagnostic["worker_reaped"])

    def test_api_error_body_is_not_retried_or_rewritten_as_an_empty_success(self):
        response = transport.request("offline", {}, "test-secret", timeout=3, worker=api_error)
        self.assertEqual(response["error"]["code"], 504)
        self.assertNotIn("usage", response)  # Billing remains the caller's unresolved concern.

    def test_response_bound_and_missing_result_fail_closed(self):
        for worker, expected in ((oversized, "response-limit"), (broken, "response-unavailable")):
            with self.subTest(worker=worker), self.assertRaises(transport.TransportFailure) as caught:
                transport.request("offline", {}, "test-secret", timeout=3, maximum=32, worker=worker)
            self.assertEqual(str(caught.exception), expected)
            self.assertTrue(caught.exception.diagnostic["possibly_billed"])

    def test_reservation_ledger_preserves_deadline_body_unknown_billing_and_no_retry(self):
        report = {"protocol": {"frozen": {"limits": {"max_calls": 2, "budget_usd": 1.0}, "plan": {"maxRequestBytes": 131072, "roles": {"interpreter": {"promptPrice": "3", "completionPrice": "9"}}}}}, "trace": []}
        sender = transport.ledger_sender(report, lambda: None, timeout=1, worker=completed_body_but_stuck)
        operation = {"kind": "interpreter", "sample": "offline-fixture", "endpoint": "offline", "payload": {"max_tokens": 4}}
        with patch.dict(os.environ, {"OPENROUTER_API_KEY": "offline-test-token"}):
            ledger = Ledger(report, lambda: None, sender=sender)
            with self.assertRaises(ValueError):
                ledger.submit(operation)
            with self.assertRaises(ValueError):
                ledger.submit(operation)
        self.assertEqual(len(report["trace"]), 1)
        record = report["trace"][0]
        self.assertEqual(record["status"], "failed-or-unaccounted")
        self.assertEqual(record["transport"]["outcome"], "deadline-expired")
        self.assertEqual(record["transport"]["attempts"], 1)
        self.assertTrue(record["transport"]["possibly_billed"])
        self.assertEqual(record["response"]["id"], "synthetic-id")
        self.assertEqual(record["response"]["error"]["message"], "[REDACTED]")
        self.assertNotIn("accounted_usd", record)
        self.assertGreater(record["reserved_usd"], 0)
        self.assertEqual(report["accounted_or_reserved_usd"], record["reserved_usd"])

    def test_http_error_body_is_captured_once_with_escaped_credential_redaction(self):
        from tempfile import TemporaryDirectory
        raw = b'{"error":{"message":"\\u0074est-secret"}}'
        error = urllib.error.HTTPError("https://example.invalid", 504, "timeout", {}, io.BytesIO(raw))
        with TemporaryDirectory() as directory, patch.object(transport.urllib.request, "build_opener") as opener:
            opener.return_value.open.side_effect = error
            path = str(Path(directory) / "response.json")
            transport._worker(path, "https://example.invalid", {}, "test-secret", 1, 1024)
            result = transport._read(path, 1024)
        self.assertEqual(result["status"], "http-error")
        self.assertEqual(result["response"]["http_status"], 504)
        body = base64.b64decode(result["response"]["body_base64"])
        self.assertEqual(json.loads(body)["error"]["message"], "[REDACTED]")
        self.assertFalse(result["response"]["body_truncated"])
        opener.return_value.open.assert_called_once()

    def test_invalid_json_and_oversized_response_keep_bounded_redacted_bytes(self):
        from tempfile import TemporaryDirectory
        class Response(io.BytesIO):
            status = 200
        for raw, maximum, expected in ((b"not JSON test-secret", 1024, "invalid-json"), (b"x" * 100, 32, "response-limit"), (b'{"number":NaN}', 1024, "invalid-json")):
            with self.subTest(expected=expected), TemporaryDirectory() as directory, patch.object(transport.urllib.request, "build_opener") as opener:
                opener.return_value.open.return_value = Response(raw)
                path = str(Path(directory) / "response.json")
                transport._worker(path, "https://example.invalid", {}, "test-secret", 1, maximum)
                result = transport._read(path, maximum)
                self.assertEqual(result["status"], expected)
                self.assertNotIn(b"test-secret", base64.b64decode(result["response"]["body_base64"]))
                self.assertEqual(result["response"]["body_truncated"], len(raw) > maximum)
                opener.return_value.open.assert_called_once()

    def test_invalid_limits_and_large_requests_are_rejected_before_submission(self):
        for timeout in (0, -1, float("nan"), float("inf"), True):
            with self.subTest(timeout=timeout), self.assertRaises(ValueError):
                transport.request("offline", {}, "test-secret", timeout=timeout, worker=success)
        with self.assertRaisesRegex(ValueError, "no attempt"):
            transport.request("offline", {"input": "x" * 100}, "test-secret", max_request_bytes=16, worker=success)


if __name__ == "__main__":
    unittest.main()
