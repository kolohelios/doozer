"""Replaceable model-role backends; deterministic CI only uses recorded responses."""

import copy
import hashlib
import json
import os
import subprocess
import time
import urllib.error
import urllib.request

from scripts.jev_probe import ENDPOINT, NoRedirect, export_cue, is_number, summarize_response
from scripts.workbench import CONTRACTS, ROOT, validate


CHAT_ENDPOINT = "https://openrouter.ai/api/v1/chat/completions"


def transport(endpoint, payload, token):
    request = urllib.request.Request(
        endpoint, data=json.dumps(payload).encode(), method="POST",
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
    )
    try:
        with urllib.request.build_opener(NoRedirect).open(request, timeout=30) as response:
            raw = response.read(1024 * 1024 + 1)
    except (urllib.error.URLError, TimeoutError, OSError):
        raise ValueError("OpenRouter transport failed; body suppressed, no retry") from None
    if len(raw) > 1024 * 1024:
        raise ValueError("oversized response")
    try:
        return json.loads(raw)
    except (ValueError, UnicodeError):
        raise ValueError("invalid response JSON; body suppressed") from None


class RecordedBackend:
    def __init__(self):
        self.responses = export_cue(sorted((ROOT / "experiments/workbench").glob("*.cue")))["recorded"]
        self.trace = []
        self.contexts = []

    def _stage(self, stage, step, context):
        self.contexts.append((stage, copy.deepcopy(context)))
        self.trace.append({"mode": "recorded", "stage": stage, "step": step, "network": False})
        field = "patch" if stage == "reasoning" else stage
        return copy.deepcopy(self.responses[step][field])

    def route(self, step, context):
        return self._stage("route", step, context)

    def analyze(self, step, context):
        return self._stage("analysis", step, context)

    def reason(self, step, context):
        return self._stage("reasoning", step, context)


class LiveBackend:
    def __init__(self, args, *, sender=transport):
        if not args.analysis_model or not args.reasoning_model:
            raise ValueError("live runs require explicit analysis and reasoning model IDs")
        if not is_number(args.budget_usd) or args.budget_usd <= 0:
            raise ValueError("live runs require a positive budget")
        if type(args.max_calls) is not int or not 1 <= args.max_calls <= 18:
            raise ValueError("max calls must be between 1 and 18")
        self.token = os.environ.get("OPENROUTER_API_KEY", "").strip()
        if not self.token:
            raise ValueError("missing OpenRouter token")
        self.plan = export_cue([ROOT / "experiments/workbench/plan.cue"])["plan"]
        self.question = export_cue([ROOT / "experiments/jev/probes.cue"])["question"]
        self.router = getattr(args, "router", "rules")
        self.models = {"analysis": args.analysis_model, "reasoning": args.reasoning_model}
        self.budget, self.max_calls, self.spent = args.budget_usd, args.max_calls, 0.0
        self.sender, self.trace = sender, []
        self.contract_text = {}
        for stage, definition in (("analysis", "#Analysis"), ("reasoning", "#Patch")):
            result = subprocess.run(
                ["cue", "def", str(CONTRACTS), "-e", definition],
                check=True, capture_output=True, text=True,
            )
            self.contract_text[stage] = result.stdout

    def _call(self, endpoint, payload, stage, step, max_output):
        encoded = json.dumps(payload, sort_keys=True, allow_nan=False).encode()
        if len(encoded) > self.plan["maxRequestBytes"]:
            raise ValueError("request byte limit exceeded")
        if sum(item["network"] for item in self.trace) >= self.max_calls:
            raise ValueError("model call limit exhausted")
        rates = payload["provider"]["max_price"]
        # Conservative local reservation, not a provider-enforced token/spend cap.
        reservation = (
            (len(encoded) + 8192) * float(rates["prompt"]) + max_output * float(rates["completion"])
        ) / 1_000_000
        if self.spent + reservation > self.budget:
            raise ValueError("insufficient remaining run budget")
        self.spent += reservation
        record = {
            "mode": "live", "stage": stage, "step": step, "network": True,
            "requested_model": payload["model"], "prompt_revision": self.plan["promptRevision"],
            "request_sha256": hashlib.sha256(encoded).hexdigest(), "status": "submitted",
            "reserved_usd": reservation,
        }
        self.trace.append(record)
        started = time.monotonic()
        try:
            response = self.sender(endpoint, payload, self.token)
            record["latency_seconds"] = round(time.monotonic() - started, 3)
            if not isinstance(response, dict) or not isinstance(response.get("usage"), dict):
                raise ValueError("missing usage accounting")
            usage = response["usage"]
            if not is_number(usage.get("cost")):
                raise ValueError("unknown billed cost; stop instead of assuming zero")
            if any(type(usage.get(key)) is not int or usage[key] < 0 for key in ("input_tokens", "output_tokens")):
                raise ValueError("invalid token usage")
            if usage.get("is_byok"):
                raise ValueError("BYOK cost excludes provider charges; cannot account for this run")
            self.spent += usage["cost"] - reservation
            record.update({
                "reported_cost_usd": usage["cost"], "served_model": response.get("model"),
                "input_tokens": usage.get("input_tokens"), "output_tokens": usage.get("output_tokens"),
                "status": "received",
            })
            if self.spent > self.budget:
                raise ValueError("reported billing exceeded the local budget; stop all further calls")
            return response
        except (ValueError, OSError):
            record["status"] = "failed-or-unaccounted"
            raise ValueError("model call failed or could not be accounted for; no automatic retry") from None

    def route(self, step, context):
        if self.router == "rules":
            self.trace.append({"mode": "rules", "stage": "route", "step": step, "network": False})
            duplicate = set(context["incoming"]) <= set(context["already_processed"])
            return {"action": "no-op" if duplicate else "analyze"}
        payload = {
            "model": self.plan["routerModel"], "state": context,
            "questions": {"action": self.question},
            "provider": {"only": ["typesafe"], "allow_fallbacks": False, "data_collection": "deny",
                         "max_price": {"prompt": "0.05", "completion": "0"}},
        }
        response = self._call(ENDPOINT, payload, "route", step, 0)
        result = {"action": summarize_response(response, payload["model"])["action"]}
        validate("#Route", result)
        return result

    def _chat(self, stage, step, context, definition):
        instructions = self.plan[stage + "Instructions"]
        payload = {
            "model": self.models[stage],
            "messages": [
                {"role": "system", "content": instructions + "\nReturn only a JSON object satisfying this CUE contract:\n" + self.contract_text[stage]},
                {"role": "user", "content": json.dumps(context, sort_keys=True)},
            ],
            "response_format": {"type": "json_object"},
            "max_tokens": self.plan["maxOutputTokens"],
            "provider": {"allow_fallbacks": False, "data_collection": "deny",
                         "max_price": {"prompt": self.plan["chatPromptPricePerMillion"],
                                       "completion": self.plan["chatCompletionPricePerMillion"]}},
        }
        response = self._call(CHAT_ENDPOINT, payload, stage, step, payload["max_tokens"])
        try:
            served = response["model"]
            if not isinstance(served, str) or not (
                served == payload["model"] or served.startswith(payload["model"] + "-")
            ):
                raise ValueError("unexpected served model")
            choice = response["choices"][0]
            if choice["finish_reason"] != "stop":
                raise ValueError("truncated or refused completion")
            content = choice["message"]["content"]
            if not isinstance(content, str):
                raise ValueError("non-text completion")
            result = json.loads(content)
            validate(definition, result)
            return result
        except (KeyError, IndexError, TypeError, ValueError):
            self.trace[-1]["status"] = "invalid-output"
            raise ValueError("model output failed its stage contract; content suppressed") from None

    def analyze(self, step, context):
        return self._chat("analysis", step, context, "#Analysis")

    def reason(self, step, context):
        return self._chat("reasoning", step, context, "#Patch")
