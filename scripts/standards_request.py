"""Freeze one standards request for local review. This module has no sender."""

import argparse
import hashlib
import json
from pathlib import Path

from scripts import maintenance_call, maintenance_proposer as proposer, standards_maintenance as loop
from scripts.split_judgment import CHAT_ENDPOINT, provider


ROLE = {"model": "openai/gpt-4.1", "provider": "openai", "promptPrice": "3", "completionPrice": "9"}
MAX_REQUEST_BYTES = 131072
INPUT_ALLOWANCE = 73728  # Serialized-body bytes plus padding; not provider token accounting.
OUTPUT_LIMIT = 4096
BUDGET_USD = 0.26


def preview(state):
    if state["processed"] != ["draft-04"] or not state["claims"]:
        raise ValueError("expected a nonempty local draft-04 view before draft-05 processing")
    batch = loop.prepare("checkpoint-06", state=state, source_id="draft-05")
    payload = {"model": ROLE["model"], "provider": {**provider(ROLE), "require_parameters": True},
               "temperature": 0, "max_tokens": OUTPUT_LIMIT, "response_format": {"type": "json_object"},
               "messages": loop.model_messages(batch)}
    raw = json.dumps(payload, allow_nan=False).encode()
    input_proxy = len(raw) + 8192
    reservation = maintenance_call.reservation({"payload": payload, "kind": "proposer"}, {"roles": {"proposer": ROLE}})
    if len(raw) > MAX_REQUEST_BYTES or input_proxy > INPUT_ALLOWANCE or reservation > BUDGET_USD:
        raise ValueError("whole request exceeds proposed local limits; no truncation or fallback")
    frozen = {"version": "standards-draft-update-preview-v1", "batch_sha256": batch["protocol"]["sha256"],
              "implementation_sha256": maintenance_call.hashes(), "endpoint": CHAT_ENDPOINT, "payload": payload,
              "request_bytes": len(raw), "request_sha256": hashlib.sha256(raw).hexdigest(),
              "proposed_limits": {"calls": 1, "retries": 0, "request_bytes": MAX_REQUEST_BYTES,
                                  "response_bytes": 1048576, "timeout_seconds": 120, "output_tokens": OUTPUT_LIMIT,
                                  "input_reservation_units": INPUT_ALLOWANCE, "local_budget_usd": BUDGET_USD},
              "input_reservation_units": input_proxy, "reservation_usd": reservation,
              "reservation_basis": "Serialized body bytes plus 8192, not a measured input token count or provider cap.",
              "transmission_review": "pending; excerpt reuse does not approve provider transmission",
              "spending_approval": "none", "baseline": "Operator supplied local draft-04 view; no semantic endorsement."}
    return {"status": "offline-preview-not-executable", "planned_calls": 0, "network_calls": 0,
            "canonical_acceptance": False, "protocol": {"sha256": proposer.digest(frozen), "frozen": frozen},
            "private_batch": batch}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state", required=True, help="Local draft-04 inspection artifact")
    parser.add_argument("--output", required=True, help="New private preview; never submit the report")
    args = parser.parse_args(argv)
    path = Path(args.output)
    if path.exists():
        raise ValueError("output exists; no overwrite")
    result = preview(loop.read_json(args.state)["state"])
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x") as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
        stream.write("\n")
    frozen = result["protocol"]["frozen"]
    print(json.dumps({"status": result["status"], "protocol_sha256": result["protocol"]["sha256"],
                      "request_bytes": frozen["request_bytes"], "reservation_usd": frozen["reservation_usd"],
                      "network_calls": 0}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
