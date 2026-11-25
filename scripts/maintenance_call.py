"""Prepare offline; opt-in one-call proposer execution requires exact-hash consent."""

import argparse
import copy
import hashlib
import json
from pathlib import Path
import re

from scripts import calibration_pilot as pilot, deadline_transport, maintenance_proposer as proposer, revision_update, split_judgment as client
from scripts import inbox_trial, standards_maintenance as batch

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
    synthetic_update = plan["version"] == revision_update.VERSION
    if synthetic_update and (checkpoint != revision_update.prepare() or plan != revision_plan()):
        raise ValueError("synthetic update must match the fixed fixture and limits")
    if plan["version"] == inbox_trial.VERSION:
        if plan != inbox_plan():
            raise ValueError("inbox trial limits changed")
        messages, sample = inbox_trial.messages(checkpoint), "synthetic-inbox-maintenance"
    elif synthetic_update:
        messages, sample = batch.model_messages(checkpoint), "synthetic-guide-update"
    else:
        messages, sample = proposer.proposer_messages(checkpoint), "retry-pre-consolidation"
    return {"kind": "proposer", "sample": sample, "endpoint": client.CHAT_ENDPOINT,
            "payload": {"model": role["model"], "provider": {**client.provider(role), "require_parameters": True},
                        "temperature": 0, "max_tokens": plan["maxOutputTokens"], "response_format": {"type": "json_object"},
                        "messages": messages}}


def reservation(op, plan):
    encoded = json.dumps(op["payload"], allow_nan=False).encode()
    role = plan["roles"][op["kind"]]
    return ((len(encoded) + 8192) * float(role["promptPrice"]) + op["payload"]["max_tokens"] * float(role["completionPrice"])) / 1000000


def prepare():
    data, scenario = proposer.load()
    checkpoint = proposer.prepare(data, scenario)
    return from_checkpoint(checkpoint, data["proposerCallPlan"])


def revision_plan():
    data = proposer.wb.export_cue([ROOT / "experiments/workbench/proposer.cue"])
    return {**data["proposerCallPlan"], "version": revision_update.VERSION, "maxBudgetUSD": 0.10, "maxOutputTokens": 4096}


def prepare_revision():
    return from_checkpoint(revision_update.prepare(), revision_plan())


def inbox_plan():
    return {**revision_plan(), "version": inbox_trial.VERSION}


def prepare_inbox(path):
    return from_checkpoint(inbox_trial.seed(path), inbox_plan())


def from_checkpoint(checkpoint, proposed_plan):
    """Reuse the one-call envelope for an explicitly constructed offline view."""
    plan = copy.deepcopy(proposed_plan)
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
    if frozen["plan"]["version"] in (revision_update.VERSION, inbox_trial.VERSION):
        if (len(json.dumps(frozen["operation"]["payload"], allow_nan=False).encode()) > frozen["plan"]["maxRequestBytes"]
                or frozen["reservation_usd"] > frozen["plan"]["maxBudgetUSD"]):
            raise ValueError("synthetic request exceeds local bounds")
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


def run(report, checkpoint, *, authorized_protocol_sha256=None, sender=None, receipt_directory=None, _contrast_parent_sha256=None):
    frozen = check(report)
    if (authorized_protocol_sha256 != report["protocol"]["sha256"] or report["status"] != "prepared-awaiting-authorization"
            or report["trace"] or "inspection" in report):
        raise ValueError("exact-hash opt-in required; attempted reports cannot resume")
    if frozen.get("execution_scope") == "contrast-child" and not _contrast_parent_sha256:
        raise ValueError("contrast child requires its parent coordinator; no standalone continuation")
    if sender is None:
        sender = deadline_transport.ledger_sender(report, checkpoint, timeout=frozen["plan"]["transportTimeoutSeconds"],
                                                 maximum=frozen["plan"]["maxResponseBytes"], max_request_bytes=frozen["plan"]["maxRequestBytes"])
    ledger = client.Ledger(report, checkpoint, sender=sender)  # Credential check before consuming a local attempt receipt.
    receipt = claim_receipt(report, receipt_directory)
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
            inspectors = {revision_update.VERSION: batch.inspect_proposal, inbox_trial.VERSION: inbox_trial.inspect}
            inspector = inspectors.get(frozen["plan"]["version"], proposer.inspect_proposal)
            report["inspection"] = inspector(frozen["checkpoint"], raw)
        except (ValueError, KeyError, TypeError, OSError, OverflowError, RecursionError):
            report["output_status"] = "inspection-failed-native-response-retained"
        report["status"] = "completed-one-call"
    report["summary"] = summary(report)
    checkpoint()
    return report


def claim_receipt(report, receipt_directory):
    directory = Path(receipt_directory) if receipt_directory is not None else ROOT / "runs/maintenance-proposer-attempts"
    directory.mkdir(parents=True, exist_ok=True)
    receipt = directory / (report["protocol"]["sha256"] + ".json")
    try:
        with receipt.open("x") as stream:
            json.dump({"protocol_sha256": report["protocol"]["sha256"], "phase": "claimed-before-submission-not-proof-of-billing"}, stream)
    except FileExistsError:
        raise ValueError("protocol already claimed locally; no resume or automatic retry") from None
    return receipt


def prepare_contrast(data=None, scenario=None):
    if data is None and scenario is None:
        data, scenario = proposer.load()
    if data is None or scenario is None:
        raise ValueError("supply both fixture data and scenario")
    design = copy.deepcopy(data["proposerContrast"])
    if design["proposedCalls"] != 2 or design["proposedBudgetUSD"] != 0.30 or design["retries"] != 0 or set(design["order"]) != {"case-a", "case-b"} or len(design["order"]) != 2:
        raise ValueError("invalid fixed contrast envelope")
    adjusted = copy.deepcopy(data)
    adjusted["proposerCheckpoint"].update(version=design["version"], instructions=design["sharedInstructions"], boundary=design["sharedBoundary"])
    trials = {}
    for name, append_only in (("case-a", False), ("case-b", True)):
        native = proposer.prepare(adjusted, scenario, append_only=append_only)
        trials[name] = from_checkpoint(native, data["proposerCallPlan"])
        trials[name]["protocol"]["frozen"]["execution_scope"] = "contrast-child"
        trials[name]["protocol"]["sha256"] = proposer.digest(trials[name]["protocol"]["frozen"])
    contrast_invariants(trials)
    frozen = {"design": design, "trials": trials, "limits": {"max_calls": 2, "budget_usd": 0.30, "retries": 0},
              "implementation_sha256": hashes(), "authorization": "Proposed only; separate exact-parent-hash spending approval required."}
    return {"status": "prepared-contrast-awaiting-authorization", "protocol": {"sha256": proposer.digest(frozen), "frozen": frozen},
            "source_commit": pilot.source_commit(), "trace": [], "canonical_acceptance": False}


def contrast_invariants(trials):
    checkpoints = [trials[key]["protocol"]["frozen"]["checkpoint"]["protocol"]["frozen"] for key in ("case-a", "case-b")]
    a, b = [c["before"] for c in checkpoints]
    if (any(a[key] != b[key] for key in ("received", "processed", "history", "revision"))
            or len(a["received"]) != 11 or set(a["processed"]) != set(a["received"]) or a["revision"] != 5 or len(a["history"]) != 6
            or (len(a["claims"]), len(b["claims"])) != (3, 6)
            or not a["claims"].keys() <= b["claims"].keys()
            or any(a["claims"][key] != b["claims"][key] for key in a["claims"])):
        raise ValueError("contrast changed evidence/history/revision or input membership")
    if checkpoints[0]["messages"][0] != checkpoints[1]["messages"][0]:
        raise ValueError("contrast instructions differ")
    contexts = [json.loads(c["messages"][1]["content"]) for c in checkpoints]
    for c, context in zip(checkpoints, contexts):
        state = c["before"]
        expected = {"current_revision": state["revision"], "current_claims": list(state["claims"].values()),
                    "sources": {key: state["received"][key] for key in state["processed"]},
                    "reserved_claim_ids": sorted(state["history"]), "existing_aliases": state["redirects"]}
        if context != expected:
            raise ValueError("prompt and private working view differ")
    if any(contexts[0][key] != contexts[1][key] for key in ("sources", "current_revision", "reserved_claim_ids")):
        raise ValueError("non-representation public inputs differ")


def check_contrast(report):
    frozen = report["protocol"]["frozen"]
    if (proposer.digest(frozen) != report["protocol"]["sha256"] or frozen["implementation_sha256"] != hashes()
            or frozen["limits"] != {"max_calls": 2, "budget_usd": 0.30, "retries": 0}
            or frozen["design"]["proposedCalls"] != 2 or frozen["design"]["proposedBudgetUSD"] != 0.30 or frozen["design"]["retries"] != 0
            or len(frozen["design"]["order"]) != 2 or set(frozen["design"]["order"]) != {"case-a", "case-b"}
            or set(frozen["trials"]) != {"case-a", "case-b"}):
        raise ValueError("changed contrast protocol, implementation, or schedule")
    for child in frozen["trials"].values():
        check(child)
        if child["status"] != "prepared-awaiting-authorization" or child["trace"] or child["protocol"]["frozen"].get("execution_scope") != "contrast-child":
            raise ValueError("contrast embeds an attempted child")
    contrast_invariants(frozen["trials"])
    if sum(child["protocol"]["frozen"]["limits"]["budget_usd"] for child in frozen["trials"].values()) > 0.30:
        raise ValueError("child limits exceed contrast budget")
    return frozen


def contrast_summary(report):
    cases = {key: summary(child) for key, child in report.get("cases", {}).items()}
    return {"planned_calls": 2, "submitted_calls": sum(c["submitted_calls"] for c in cases.values()),
            "known_cost_usd": sum(c["known_cost_usd"] for c in cases.values()),
            "unknown_billing": sum(c["unknown_billing"] for c in cases.values()),
            "accounted_or_reserved_usd": sum(c["accounted_or_reserved_usd"] for c in cases.values()),
            "cases": cases, "canonical_acceptance": False}


def run_contrast(report, checkpoint, *, authorized_protocol_sha256=None, sender=None, receipt_directory=None):
    frozen = check_contrast(report)
    if authorized_protocol_sha256 != report["protocol"]["sha256"] or report["status"] != "prepared-contrast-awaiting-authorization" or report["trace"] or "cases" in report:
        raise ValueError("exact contrast hash required; no resume")
    if not client.os.environ.get("OPENROUTER_API_KEY", "").strip():
        raise ValueError("missing OpenRouter token")
    receipt = claim_receipt(report, receipt_directory)
    report.update(status="running-contrast", attempt_receipt=str(receipt), operator_opt_in_sha256=authorized_protocol_sha256, cases=copy.deepcopy(frozen["trials"]))
    def capture():
        report["trace"] = [{"case": name, "status": t["status"]} for name in frozen["design"]["order"] for t in report["cases"][name]["trace"]]
        report["summary"] = contrast_summary(report)
        checkpoint()
    capture()
    try:
        for name in frozen["design"]["order"]:
            child = report["cases"][name]
            child["authorization_parent_sha256"] = report["protocol"]["sha256"]
            run(child, capture, authorized_protocol_sha256=child["protocol"]["sha256"], sender=sender, receipt_directory=receipt_directory, _contrast_parent_sha256=report["protocol"]["sha256"])
    except (ValueError, OSError):
        report["status"] = "stopped-contrast-no-retry"
        capture()
        raise
    report["status"] = "completed-contrast"
    capture()
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True)
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--contrast", action="store_true", help="Prepare or explicitly execute the fixed two-view contrast")
    parser.add_argument("--revision-update", action="store_true", help="Prepare the fixed synthetic guide update only")
    parser.add_argument("--inbox-trial", metavar="NEW_DB", help="Seed a new synthetic inbox and prepare its maintenance trial")
    parser.add_argument("--prepared")
    parser.add_argument("--protocol-sha256")
    args = parser.parse_args(argv)
    if args.live != bool(args.prepared) or args.live != bool(args.protocol_sha256):
        parser.error("live requires --prepared and --protocol-sha256; default mode only prepares")
    if (args.revision_update or args.inbox_trial) and (args.live or args.contrast or (args.revision_update and args.inbox_trial)):
        parser.error("synthetic preparation modes cannot be combined with each other, --contrast, or --live")
    path = Path(args.output)
    if path.exists():
        raise ValueError("output exists; no overwrite")
    if args.live:
        report = json.loads(Path(args.prepared).read_text())
    elif args.inbox_trial:
        report = prepare_inbox(args.inbox_trial)
    else:
        report = prepare_contrast() if args.contrast else prepare_revision() if args.revision_update else prepare()
    (check_contrast if args.contrast else check)(report)
    expected_status = "prepared-contrast-awaiting-authorization" if args.contrast else "prepared-awaiting-authorization"
    if args.live and (args.protocol_sha256 != report["protocol"]["sha256"] or report["status"] != expected_status or report["trace"]):
        raise ValueError("exact untouched prepared protocol required before creating output")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x") as stream:
        stream.write(json.dumps(report, indent=2, allow_nan=False) + "\n")
    code = 0
    if args.live:
        try:
            (run_contrast if args.contrast else run)(report, lambda: pilot.checkpoint(path, report), authorized_protocol_sha256=args.protocol_sha256)
        except (ValueError, OSError):
            report["status"] = "stopped-contrast-no-retry" if args.contrast else "stopped-no-retry"
            report["summary"] = (contrast_summary if args.contrast else summary)(report)
            pilot.checkpoint(path, report)
            code = 2
    frozen = report["protocol"]["frozen"]
    children = frozen["trials"] if args.contrast else {"single": report}
    reservations = {key: child["protocol"]["frozen"]["reservation_usd"] for key, child in children.items()}
    role = next(iter(children.values()))["protocol"]["frozen"]["plan"]["roles"]["proposer"]
    print(json.dumps({"output": str(path), "status": report["status"], "protocol_sha256": report["protocol"]["sha256"],
                      "proposed_limits": frozen["limits"], "proposed_role": role,
                      "proposed_reservation_usd": sum(reservations.values()), "case_reservations_usd": reservations,
                      "summary": report.get("summary")}, indent=2))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
