"""One bounded, opt-in Decisions API call; no engine actions or raw response logs."""

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import time
import urllib.error
import urllib.request


ROOT = Path(__file__).resolve().parents[1]
ENDPOINT = "https://openrouter.ai/api/alpha/decisions"
ACTIONS = {"analyze", "no-op", "retain-ambiguity"}


def export_cue(files):
    result = subprocess.run(
        ["cue", "export", *map(str, files)], check=True, capture_output=True, text=True,
    )
    return json.loads(result.stdout)


def load_inputs():
    return (
        export_cue(sorted((ROOT / "corpus").glob("*.cue"))),
        export_cue([ROOT / "experiments/jev/probes.cue"]),
    )


def build_request(corpus, config, case_id):
    """Allowlist inputs: never send rubrics, titles, future sources, or case IDs."""
    case = config["cases"][case_id]
    scenario = corpus["scenarios"][case["scenario"]]
    received, processed = set(), set()
    for step in scenario["steps"]:
        received.update(step["receive"])
        if step["id"] == case["step"]:
            break
        processed.update(step["reconcile"])
    else:
        raise ValueError("probe references a missing step")
    incoming = case["incoming"]
    if not set(incoming) <= received:
        raise ValueError("probe references unavailable incoming sources")
    # Same-batch context can resolve a reply, but is not already reconciled.
    sources = {}
    for source_id in sorted(received):
        source = scenario["sources"][source_id]
        sources[source_id] = {
            key: source[key] for key in
            ("kind", "text", "anchor", "saidAt", "scope", "replyTo", "derivedFrom")
            if key in source
        }
        references = set(source.get("derivedFrom", []))
        if "replyTo" in source:
            references.add(source["replyTo"])
        if not references <= received:
            raise ValueError("probe context has future source references")
    request = {
        "model": config["model"],
        "state": {
            "sources": sources,
            "already_processed": sorted(processed),
            "incoming": incoming,
        },
        "questions": {"action": config["question"]},
        "provider": {
            "only": ["typesafe"],
            "allow_fallbacks": False,
            "data_collection": "deny",
            "max_price": {
                "prompt": config["maxPromptPricePerMillion"],
                "completion": config["maxCompletionPricePerMillion"],
            },
        },
    }
    if len(json.dumps(request).encode()) > config["maxRequestBytes"]:
        raise ValueError("request exceeds the configured byte limit")
    return request


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ValueError("redirect refused; credentials are restricted to OpenRouter")


def send_request(payload, token):
    request = urllib.request.Request(
        ENDPOINT,
        data=json.dumps(payload).encode(),
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        method="POST",
    )
    opener = urllib.request.build_opener(NoRedirect)
    # No retries: timeouts can still be billed, so never automatically replay.
    try:
        with opener.open(request, timeout=30) as response:
            raw = response.read(1024 * 1024 + 1)
    except urllib.error.HTTPError as error:
        raise ValueError(f"OpenRouter HTTP {error.code}; response body suppressed") from None
    except (urllib.error.URLError, TimeoutError, OSError):
        raise ValueError("OpenRouter network failure; no automatic retry") from None
    if len(raw) > 1024 * 1024:
        raise ValueError("response exceeds the byte limit")
    try:
        return json.loads(raw)
    except (ValueError, UnicodeError):
        raise ValueError("OpenRouter returned invalid JSON; response suppressed") from None


def summarize_response(response, requested_model):
    """Reject refusals/unknown choices; confidence is diagnostic, not calibrated."""
    if not isinstance(response, dict):
        raise ValueError("invalid response object")
    model = response.get("model")
    if not isinstance(model, str) or not (
        model == requested_model or model.startswith(requested_model + "-")
    ):
        raise ValueError("unexpected response model")
    answers = response.get("answers")
    if not isinstance(answers, dict) or set(answers) != {"action"}:
        raise ValueError("missing or unexpected answers")
    answer = answers["action"]
    if not isinstance(answer, dict) or answer.get("type") != "choice":
        raise ValueError("refusal or non-choice answer; no action authorized")
    choice = answer.get("choice")
    if not isinstance(choice, str) or choice not in ACTIONS:
        raise ValueError("unknown action; no action authorized")
    confidence = answer.get("confidence")
    if confidence is not None and not is_number(confidence, maximum=1):
        raise ValueError("invalid confidence")
    usage = response.get("usage")
    if not isinstance(usage, dict):
        raise ValueError("missing usage")
    for field in ("input_tokens", "output_tokens"):
        if type(usage.get(field)) is not int or usage[field] < 0:
            raise ValueError("invalid token usage")
    cost = usage.get("cost")
    if cost is not None and not is_number(cost):
        raise ValueError("invalid cost")
    return {
        "served_model": model,
        "action": choice,
        "confidence": confidence,
        "input_tokens": usage["input_tokens"],
        "output_tokens": usage["output_tokens"],
        "reported_cost_usd": cost,
        "is_byok": usage.get("is_byok"),
    }


def is_number(value, maximum=math.inf):
    return type(value) in (int, float) and math.isfinite(value) and 0 <= value <= maximum


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("case", help="case ID from experiments/jev/probes.cue")
    parser.add_argument("--live", action="store_true", help="make ONE paid request, with no retries")
    args = parser.parse_args(argv)
    try:
        corpus, config = load_inputs()
        if args.case not in config["cases"]:
            raise ValueError("unknown case; see experiments/jev/probes.cue")
        payload = build_request(corpus, config, args.case)
        if not args.live:
            print(json.dumps({"mode": "preview", "request": payload}, indent=2))
            return 0
        token = os.environ.get("OPENROUTER_API_KEY", "").strip()
        if not token:
            raise ValueError("export OPENROUTER_API_KEY before live runs")
        started = time.monotonic()
        response = send_request(payload, token)
        result = summarize_response(response, payload["model"])
        case = config["cases"][args.case]
        result.update({
            "case": args.case,
            "prompt_revision": config["promptRevision"],
            "request_sha256": hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest(),
            "latency_seconds": round(time.monotonic() - started, 3),
            "expected": case["expected"],
            "matches_provisional_label": result["action"] == case["expected"],
            "authorized_effects": "none",
        })
        print(json.dumps(result, indent=2))
        return 0 if result["matches_provisional_label"] else 1
    except (ValueError, subprocess.CalledProcessError):
        # Never print response bodies, source content, environment, or exceptions
        # from external commands. These can echo credentials or provider inputs.
        print("Probe failed validation or transport; no engine action taken. Check inputs, credentials, and provider availability.", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
