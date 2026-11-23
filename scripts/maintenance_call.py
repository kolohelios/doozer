"""Prepare offline; opt-in one-call proposer execution requires exact-hash consent."""

import argparse
import copy
import hashlib
import json
from pathlib import Path
import re

from scripts import calibration_pilot as pilot, deadline_transport, maintenance_proposer as proposer, split_judgment as client

ROOT = proposer.wb.ROOT


def hashes():
    paths = [*sorted((ROOT / "scripts").glob("*.py")), ROOT / "flake.lock", proposer.wb.CONTRACTS, ROOT / "experiments/workbench/proposer.cue"]
    return {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}


def validate_plan(plan):
    role = plan["roles"]["proposer"]
    if (type(plan["maxCalls"]) is not int or plan["maxCalls"] != 1 or plan["retries"] != 0
            or not client.is_number(plan["maxBudgetUSD"]) or not 0 < plan["maxBudgetUSD"] <= 0.15
            or role != {"model": "openai/gpt-4.1", "provider": "openai", "promptPrice": "3", "completionPrice": "9"}
            or any(type(plan[key]) is not int or not 0 < plan[key] <= maximum for key, maximum in
                   (("maxOutputTokens", 8000), ("maxRequestBytes", 131072), ("maxResponseBytes", 1048576), ("transportTimeoutSeconds", 120)))):
        raise ValueError("one-call proposed limits or role changed")


def operation(checkpoint, plan):
    validate_plan(plan)
    role = plan["roles"]["proposer"]
    return {"kind": "proposer", "sample": "retry-pre-consolidation", "endpoint": client.CHAT_ENDPOINT,
            "payload": {"model": role["model"], "provider": {**client.provider(role), "require_parameters": True},
                        "temperature": 0, "max_tokens": plan["maxOutputTokens"], "response_format": {"type": "json_object"},
                        "messages": proposer.proposer_messages(checkpoint)}}


def reservation(op, plan):
    encoded = json.dumps(op["payload"], allow_nan=False).encode()
    role = plan["roles"][op["kind"]]
    return ((len(encoded) + 8192) * float(role["promptPrice"]) + op["payload"]["max_tokens"] * float(role["completionPrice"])) / 1000000


def prepare():
    data, scenario = proposer.load()
    checkpoint = proposer.prepare(data, scenario)
    plan = copy.deepcopy(data["proposerCallPlan"])
    op = operation(checkpoint, plan)
    reserve = reservation(op, plan)
    if len(json.dumps(op["payload"]).encode()) > plan["maxRequestBytes"] or reserve > plan["maxBudgetUSD"]:
        raise ValueError("request cannot fit proposed local reservation")
    cached = ROOT / "experiments/judgment/metadata/scale-interpreter.json"
    frozen = {"plan": plan, "checkpoint": checkpoint, "operation": op,
              "limits": {"budget_usd": float(plan["maxBudgetUSD"]), "max_calls": 1, "retries": 0},
              "reservation_usd": reserve, "implementation_sha256": hashes(),
              "cached_public_endpoint_observation": json.loads(cached.read_text()),
              "metadata_boundary": "Historical public snapshot only; no refreshed availability or billing guarantee.",
              "authorization": "Proposed, not approved by preparation or PR merge. Exact-hash live opt-in and separate operator spending approval required."}
    return {"status": "prepared-awaiting-authorization", "protocol": {"sha256": proposer.digest(frozen), "frozen": frozen},
            "source_commit": pilot.source_commit(), "trace": [], "canonical_acceptance": False}


def check(report):
    frozen = report["protocol"]["frozen"]
    validate_plan(frozen["plan"])
    if (proposer.digest(frozen) != report["protocol"]["sha256"] or frozen["implementation_sha256"] != hashes()
            or frozen["operation"] != operation(frozen["checkpoint"], frozen["plan"])
            or frozen["limits"] != {"budget_usd": float(frozen["plan"]["maxBudgetUSD"]), "max_calls": 1, "retries": 0}
            or frozen["reservation_usd"] != reservation(frozen["operation"], frozen["plan"])):
        raise ValueError("changed request, protocol, implementation, or limits")
    return frozen


def summary(report):
    trace = report["trace"]
    return {"planned_calls": 1, "submitted_calls": len(trace),
            "known_cost_usd": sum(t.get("accounted_usd", 0) for t in trace),
            "unknown_billing": sum("accounted_usd" not in t for t in trace),
            "accounted_or_reserved_usd": report.get("accounted_or_reserved_usd", 0),
            "proposal_status": report.get("inspection", {}).get("status", report.get("output_status", "unavailable")),
            "semantic_judgment": report.get("inspection", {}).get("semantic_judgment", "not-evaluated"),
            "canonical_acceptance": False}


def run(report, checkpoint, *, authorized_protocol_sha256=None, sender=None, receipt_directory=None):
    frozen = check(report)
    if (authorized_protocol_sha256 != report["protocol"]["sha256"] or report["status"] != "prepared-awaiting-authorization"
            or report["trace"] or "inspection" in report):
        raise ValueError("exact-hash opt-in required; attempted reports cannot resume")
    if sender is None:
        sender = deadline_transport.ledger_sender(report, checkpoint, timeout=frozen["plan"]["transportTimeoutSeconds"],
                                                 maximum=frozen["plan"]["maxResponseBytes"], max_request_bytes=frozen["plan"]["maxRequestBytes"])
    ledger = client.Ledger(report, checkpoint, sender=sender)  # Credential check before consuming a local attempt receipt.
    directory = Path(receipt_directory) if receipt_directory is not None else ROOT / "runs/maintenance-proposer-attempts"
    directory.mkdir(parents=True, exist_ok=True)
    receipt = directory / (report["protocol"]["sha256"] + ".json")
    try:
        with receipt.open("x") as stream:
            json.dump({"protocol_sha256": report["protocol"]["sha256"], "phase": "claimed-before-submission-not-proof-of-billing"}, stream)
    except FileExistsError:
        raise ValueError("protocol already claimed locally; no resume or automatic retry") from None
    report.update(status="running", operator_opt_in_sha256=authorized_protocol_sha256, attempt_receipt=str(receipt))
    checkpoint()
    try:
        response = ledger.submit(frozen["operation"])
    except ValueError:
        report["status"] = "stopped-no-retry"
        report["summary"] = summary(report)
        checkpoint()
        raise
    # The complete native response is already checkpointed before interpretation.
    try:
        requested = frozen["operation"]["payload"]["model"]
        served = response.get("model", "")
        choices = response["choices"]
        if (not isinstance(served, str) or not (served == requested or re.fullmatch(re.escape(requested) + r"-\d{4}-\d{2}-\d{2}", served))
                or not isinstance(choices, list) or len(choices) != 1 or choices[0]["finish_reason"] != "stop"
                or not isinstance(choices[0]["message"]["content"], str) or choices[0]["message"].get("refusal")):
            raise ValueError("unexpected model, unfinished/refused output, or non-single response")
        raw = choices[0]["message"]["content"].encode("utf-8")
    except (ValueError, KeyError, TypeError, IndexError, UnicodeError):
        report.update(status="completed-one-call", output_status="invalid-native-output-no-replacement")
    else:
        try:
            report["inspection"] = proposer.inspect_proposal(frozen["checkpoint"], raw)
        except (ValueError, KeyError, TypeError, OSError, OverflowError, RecursionError):
            report["output_status"] = "inspection-failed-native-response-retained"
        report["status"] = "completed-one-call"
    report["summary"] = summary(report)
    checkpoint()
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True)
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--prepared")
    parser.add_argument("--protocol-sha256")
    args = parser.parse_args(argv)
    if args.live != bool(args.prepared) or args.live != bool(args.protocol_sha256):
        parser.error("live requires --prepared and --protocol-sha256; default mode only prepares")
    path = Path(args.output)
    if path.exists():
        raise ValueError("output exists; no overwrite")
    report = json.loads(Path(args.prepared).read_text()) if args.live else prepare()
    check(report)
    if args.live and (args.protocol_sha256 != report["protocol"]["sha256"] or report["status"] != "prepared-awaiting-authorization" or report["trace"]):
        raise ValueError("exact untouched prepared protocol required before creating output")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x") as stream:
        stream.write(json.dumps(report, indent=2, allow_nan=False) + "\n")
    code = 0
    if args.live:
        try:
            run(report, lambda: pilot.checkpoint(path, report), authorized_protocol_sha256=args.protocol_sha256)
        except (ValueError, OSError):
            report["status"] = "stopped-no-retry"
            report["summary"] = summary(report)
            pilot.checkpoint(path, report)
            code = 2
    print(json.dumps({"output": str(path), "status": report["status"], "protocol_sha256": report["protocol"]["sha256"],
                      "proposed_reservation_usd": report["protocol"]["frozen"]["reservation_usd"],
                      "proposed_limits": report["protocol"]["frozen"]["limits"],
                      "proposed_role": report["protocol"]["frozen"]["plan"]["roles"]["proposer"], "summary": report.get("summary")}, indent=2))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
