"""Frozen CUE contracts and bounded, stateless OpenRouter calls for experiments."""

import copy
import functools
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
import time

from scripts.jev_probe import is_number
from scripts.workbench_models import CHAT_ENDPOINT, transport


class CallFailure(ValueError):
    """Transport/accounting failure: stop the experiment, never retry automatically."""


class OutputFailure(ValueError):
    """Known-billed output is invalid: retain the failure, not a replacement sample."""


@functools.lru_cache(maxsize=512)
def validate_contract(schema, definition, encoded):
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory)
        (path / "contract.cue").write_text(schema)
        (path / "value.json").write_text(encoded)
        result = subprocess.run(
            ["cue", "vet", "-c", str(path / "contract.cue"), str(path / "value.json"), "-d", definition],
            capture_output=True, text=True,
        )
    if result.returncode:
        raise OutputFailure("stage contract rejected; content suppressed")


class Contracts:
    def __init__(self, path):
        self.schema = Path(path).read_text()
        self.definitions = {}

    def validate(self, definition, value):
        validate_contract(self.schema, definition, json.dumps(value, sort_keys=True, allow_nan=False))

    def describe(self, definition):
        if definition not in self.definitions:
            with tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / "contract.cue"
                path.write_text(self.schema)
                result = subprocess.run(["cue", "def", str(path), "-e", definition],
                                        check=True, capture_output=True, text=True)
            self.definitions[definition] = result.stdout
        return self.definitions[definition]


class Client:
    def __init__(self, plan, contracts, *, budget, max_calls, sender=transport, on_trace=None):
        if not is_number(budget) or budget <= 0 or type(max_calls) is not int or not 1 <= max_calls <= 60:
            raise ValueError("positive budget and 1..60 call limit required")
        self.token = os.environ.get("OPENROUTER_API_KEY", "").strip()
        if not self.token:
            raise ValueError("missing OpenRouter token")
        self.plan, self.contracts = copy.deepcopy(plan), contracts
        self.budget, self.max_calls, self.spent = budget, max_calls, 0.0
        self.sender, self.trace, self.halted = sender, [], False
        self.on_trace = on_trace or (lambda: None)

    def redact(self, value):
        return json.loads(json.dumps(value).replace(self.token, "[REDACTED]"))

    def call(self, role, definition, context, label):
        if self.halted or len(self.trace) >= self.max_calls:
            raise CallFailure("call limit or halted accounting")
        binding = self.plan["roles"][role]
        payload = {
            "model": binding["model"],
            "messages": [
                {"role": "system", "content": self.plan[role + "Instructions"] +
                 "\nReturn only a JSON object satisfying this CUE contract:\n" + self.contracts.describe(definition)},
                {"role": "user", "content": json.dumps(context, sort_keys=True)},
            ],
            "temperature": self.plan["temperature"], "max_tokens": self.plan["maxOutputTokens"],
            "response_format": {"type": "json_object"},
            "provider": {"only": [binding["provider"]], "allow_fallbacks": False, "data_collection": "deny",
                         "max_price": {"prompt": self.plan["maxPromptPricePerMillion"],
                                       "completion": self.plan["maxCompletionPricePerMillion"]}},
        }
        encoded = json.dumps(payload, sort_keys=True, allow_nan=False).encode()
        if len(encoded) > self.plan["maxRequestBytes"]:
            raise CallFailure("request byte limit exceeded")
        reserve = ((len(encoded) + 8192) * float(self.plan["maxPromptPricePerMillion"]) +
                   payload["max_tokens"] * float(self.plan["maxCompletionPricePerMillion"])) / 1_000_000
        if self.spent + reserve > self.budget:
            raise CallFailure("cannot reserve next call within local budget")
        self.spent += reserve
        record = {"role": role, "label": label, "status": "submitted", "reserved_usd": reserve,
                  "requested_model": binding["model"], "requested_provider": binding["provider"],
                  "request_sha256": hashlib.sha256(encoded).hexdigest(),
                  "system_sha256": hashlib.sha256(payload["messages"][0]["content"].encode()).hexdigest()}
        self.trace.append(record)
        self.on_trace()  # Persist submitted identity before a potentially billed call.
        started = time.monotonic()
        try:
            response = self.sender(CHAT_ENDPOINT, payload, self.token)
            usage = response.get("usage", {})
            cost = usage.get("cost")
            counts = [usage.get("input_tokens", usage.get("prompt_tokens")),
                      usage.get("output_tokens", usage.get("completion_tokens"))]
            if not is_number(cost) or usage.get("is_byok") or any(type(count) is not int or count < 0 for count in counts):
                raise ValueError("unknown or invalid billing")
            self.spent += cost - reserve
            record.update({"reported_cost_usd": cost, "input_tokens": counts[0], "output_tokens": counts[1],
                           "served_model": response.get("model"), "provider": response.get("provider"),
                           "latency_seconds": round(time.monotonic() - started, 3), "status": "received"})
            if self.spent > self.budget:
                raise ValueError("local budget exceeded; stop further calls")
        except (ValueError, TypeError, AttributeError, OSError):
            self.halted = True
            record["status"] = "failed-or-unaccounted"
            self.on_trace()
            raise CallFailure("transport or accounting failed; no automatic retry") from None
        self.on_trace()
        parsed = None
        try:
            served = response["model"]
            if not isinstance(served, str) or not (served == binding["model"] or served.startswith(binding["model"] + "-")):
                raise ValueError("unexpected model")
            choice = response["choices"][0]
            if choice["finish_reason"] != "stop" or not isinstance(choice["message"]["content"], str):
                raise ValueError("truncation, refusal, or non-text answer")
            parsed = json.loads(choice["message"]["content"])
            self.contracts.validate(definition, parsed)
            record["status"] = "validated"
            self.on_trace()
            return parsed
        except (ValueError, KeyError, TypeError, IndexError):
            record["status"] = "invalid-output"
            if parsed is not None:
                # Retain parsed rejected model data for diagnosis, not HTTP bodies.
                record["rejected_value"] = self.redact(parsed)
            self.on_trace()
            raise OutputFailure("invalid stage output; no replacement sample") from None
