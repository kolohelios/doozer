"""Prospective one-attempt transport with an absolute local deadline.

Worker termination does not cancel provider work or establish billing. No existing
runner is changed. Complete responses remain available on failures when captured.
"""

import base64
import datetime
import json
import math
import multiprocessing
from pathlib import Path
import tempfile
import time
import urllib.error
import urllib.request

from scripts.jev_probe import NoRedirect


class TransportFailure(ValueError):
    def __init__(self, reason, diagnostic, response=None, response_available=False):
        super().__init__(reason)  # Never put credentials, payload, or response in errors.
        self.diagnostic = {**diagnostic, "outcome": reason, "response_available": response_available}
        self.response = response


def _invalid_constant(value):
    raise ValueError("non-finite JSON number")


def _worker(path, endpoint, payload, token, timeout, maximum):
    request = urllib.request.Request(endpoint, data=json.dumps(payload, allow_nan=False).encode(), headers={"Authorization": "Bearer " + token, "Content-Type": "application/json"}, method="POST")
    try:
        failed_http = False
        try:
            response = urllib.request.build_opener(NoRedirect).open(request, timeout=timeout)
        except urllib.error.HTTPError as error:
            response, failed_http = error, True
        with response:
            raw = response.read(maximum + 1)
            status = response.status
        def captured(reason):
            bounded = raw[:maximum].replace(token.encode(), b"[REDACTED]")
            # Escaped credentials in a JSON error must not survive through base64.
            try:
                canonical = json.dumps(json.loads(raw[:maximum]), ensure_ascii=False, separators=(",", ":"))
                if token in canonical:
                    bounded = canonical.replace(token, "[REDACTED]").encode("utf-8", "backslashreplace")
            except (ValueError, RecursionError):
                pass
            return {"status": reason, "response": {"http_status": status, "body_base64": base64.b64encode(bounded).decode(), "body_truncated": len(raw) > maximum, "boundary": "Response bytes with credential redaction (escaped JSON may be canonicalized); not model output or known billing."}}
        if len(raw) > maximum:
            result = captured("response-limit")
        elif failed_http:
            result = captured("http-error")
        else:
            try:
                result = {"status": "received", "response": json.loads(raw, parse_constant=_invalid_constant)}
            except (ValueError, RecursionError):
                result = captured("invalid-json")
    except (ValueError, OSError, TypeError):
        result = {"status": "transport-failed"}
    encoded = json.dumps(result, ensure_ascii=False, allow_nan=False).encode()
    if len(encoded) > 2 * maximum + 4096:
        encoded = b'{"status":"response-limit"}'
    temporary = Path(path + ".partial")
    temporary.write_bytes(encoded)
    temporary.replace(path)  # The parent never promotes a partial write.


def _stop(process):
    if process.is_alive():
        process.terminate()
        process.join(0.1)
    if process.is_alive():
        process.kill()
        process.join(0.1)
    return not process.is_alive()


def _read(path, maximum):
    try:
        with Path(path).open("rb") as stream:
            encoded = stream.read(2 * maximum + 4097)
        if len(encoded) > 2 * maximum + 4096:
            return {"status": "response-limit"}
        result = json.loads(encoded)
        return result if isinstance(result, dict) else {"status": "invalid-worker-result"}
    except (OSError, ValueError):
        return {"status": "response-unavailable"}


def ledger_sender(report, checkpoint, timeout=120, maximum=1048576, max_request_bytes=131072, *, worker=None):
    """Opt-in adapter for the existing reservation ledger; not installed in old runners."""
    def send(endpoint, payload, token):
        if not report["trace"] or report["trace"][-1]["status"] != "submitted":
            raise ValueError("deadline sender requires a reserved submitted attempt")
        record = report["trace"][-1]
        started = time.monotonic()
        record["transport"] = {"started_at": datetime.datetime.now(datetime.timezone.utc).isoformat(), "deadline_seconds": timeout, "attempts": 1, "outcome": "started", "possibly_billed": True}
        checkpoint()
        try:
            response = request(endpoint, payload, token, timeout, maximum, max_request_bytes, worker=worker)
        except TransportFailure as failure:
            record["transport"].update(failure.diagnostic)
            if failure.diagnostic["response_available"]:
                record["response"] = json.loads(json.dumps(failure.response, allow_nan=False).replace(token, "[REDACTED]"))
            checkpoint()
            raise
        record["transport"].update(outcome="response-received", elapsed_seconds=time.monotonic() - started, response_available=True)
        checkpoint()
        return response
    return send


def request(endpoint, payload, token, timeout=120, maximum=1048576, max_request_bytes=131072, *, worker=None):
    """Return one native response or raise with safe diagnostics and any complete body.

    timeout includes worker startup, connect, read, and response capture. Bounded
    termination/reaping follows the deadline; this is not a real-time OS guarantee.
    A future caller must preserve failure.response and reserve unknown billing.
    worker is a spawn-compatible offline test seam, never fallback or retry.
    """
    if type(timeout) not in (int, float) or not math.isfinite(timeout) or timeout <= 0 or type(maximum) is not int or maximum <= 0 or type(max_request_bytes) is not int or max_request_bytes <= 0:
        raise ValueError("invalid transport limits")
    if not isinstance(endpoint, str) or not endpoint or not isinstance(token, str) or not token:
        raise ValueError("missing endpoint or credential")
    if len(json.dumps(payload, allow_nan=False).encode()) > max_request_bytes:
        raise ValueError("request limit; no attempt submitted")
    context = multiprocessing.get_context("spawn")
    started = time.monotonic()
    deadline = started + timeout
    with tempfile.TemporaryDirectory(prefix="doozer-deadline-") as directory:
        path = str(Path(directory) / "result.json")
        process = context.Process(target=worker or _worker, args=(path, endpoint, payload, token, timeout, maximum), daemon=True)
        attempted = False
        try:
            process.start()
            attempted = True
            process.join(max(0, deadline - time.monotonic()))
            expired = process.is_alive() or time.monotonic() >= deadline
            stopped = _stop(process)
            result = _read(path, maximum)
            diagnostic = {"deadline_seconds": timeout, "elapsed_seconds": time.monotonic() - started,
                          "possibly_billed": attempted, "worker_reaped": stopped}
            body_available = "response" in result
            reason = "deadline-expired" if expired or time.monotonic() >= deadline else "worker-failed" if process.exitcode != 0 else "invalid-worker-result" if result.get("status") == "received" and not body_available else result.get("status", "invalid-worker-result")
            if reason != "received":
                raise TransportFailure(reason, diagnostic, result.get("response"), body_available)
            return result["response"]
        finally:
            if process.pid is not None:
                _stop(process)
                if not process.is_alive():
                    process.close()
