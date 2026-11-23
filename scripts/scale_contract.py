"""Offline prospective prompt/ABI checks; no live execution or inherited budget."""

import argparse
import copy
import hashlib
import json
from pathlib import Path

from scripts import cue_contract, scale_panel as legacy

# The whitespace set used by Python str.strip, including its C0 separators.
# Literal codepoints reach both JSON Schema and CUE's regexp matcher via JSON.
NONBLANK = "[^\t-\r\x1c-\x20\u0085\u00a0\u1680\u2000-\u200a\u2028\u2029\u202f\u205f\u3000]"


def schema_for(packet):
    schema = copy.deepcopy(packet["ledger_schema"]["json"])
    limits = schema["properties"]["extractionLimits"]["items"]["properties"]
    limits["evidence"]["minItems"] = 1
    limits["reason"].update(minLength=1, pattern=NONBLANK)
    schema["properties"]["ledger"]["items"]["properties"]["rationale"].update(minLength=1, pattern=NONBLANK)
    return {"json": schema, "cue": cue_contract.compile_schema(json.dumps(schema, sort_keys=True))}


def neutral_controls(packet, rationale):
    """Change only authored control packaging; never rewrite real model output."""
    for proposal in packet.get("control", {}).get("proposals", {}).values():
        before = legacy.profile(proposal["compiled"], packet["context"])
        proposal["original_value"] = copy.deepcopy(proposal["value"])
        value = copy.deepcopy(proposal["value"])
        for entry in value["ledger"]:
            entry["rationale"] = rationale
        compiled = legacy.compile_value(value, packet)
        if legacy.profile(compiled, packet["context"]) != before or compiled["core"]["rejected"] or compiled["rejected_annotations"]:
            raise ValueError("control packaging changed its operational meaning")
        proposal.update(value=value, compiled=compiled)


def operation(packet, row, role, frozen):
    op = legacy.operation(packet, row, role, frozen)
    state = json.loads(op["payload"]["messages"][1]["content"])
    # Auditor sees exactly the schema enforced for both extractors, rather than
    # guessing constructor operands from untrusted proposals or old wire prose.
    state["interpretation_schema"] = copy.deepcopy(packet["ledger_schema"]["json"])
    if role in {"auditor", "control"}:
        for proposed in state["untrusted_proposals"].values():
            if proposed["proposal"] is not None:
                for entry in proposed["proposal"]["ledger"]:
                    entry["rationale"] = frozen["prospective_checks"]["auditRationale"]
    op["payload"]["messages"][1]["content"] = json.dumps(state, sort_keys=True)
    if len(json.dumps(op["payload"]).encode()) > frozen["plan"]["maxRequestBytes"]:
        raise ValueError("prospective request exceeds the existing byte bound")
    return op


def prepare(data):
    # Reuse fixture construction/checks, not the previous execution authority.
    report = legacy.prepare(data)
    frozen = report["protocol"]["frozen"]
    settings = copy.deepcopy(data["scaleContractChecks"])
    frozen["contract"] = copy.deepcopy(data["scaleContract"])
    frozen["prospective_checks"] = settings
    frozen["plan"].update(version=settings["version"], maxCalls=0, maxBudgetUSD=0,
                          policy="Offline request inspection over reused development fixtures only. No live execution, spending, repair, or canonical effects.")
    frozen["planned_calls"] = 0
    frozen["limits"] = {"budget_usd": 0.0, "max_calls": 0, "retries": 0}
    frozen["execution_authorization"] = {"status": "none", "scope": "Offline construction only; the original 84-call approval does not transfer to this prospective protocol."}
    frozen["provider_snapshot_scope"] = "Copied historical public metadata, not refreshed availability or authorization for calls."
    for packet in frozen["packets"]:
        packet["ledger_schema"] = schema_for(packet)
        legacy.compile_value(legacy.reference(packet), packet)
        neutral_controls(packet, settings["auditRationale"])
    previews = [operation(packet, {}, role, frozen) for packet in frozen["packets"] for role in (*legacy.ROLES, *(["control"] if "control" in packet else []))]
    frozen["request_previews"] = len(previews)
    frozen["request_preview_sha256"] = legacy.prior.multi.pilot.digest(previews)
    # Explicitly bind this prospective module too; no old protocol is rewritten.
    frozen["implementation_sha256"][Path(__file__).name] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    report.update(status="offline-prospective-not-live", request_previews=previews)
    report["protocol"]["sha256"] = legacy.prior.multi.pilot.digest(frozen)
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True)
    args = parser.parse_args(argv)
    path = Path(args.output)
    if path.exists():
        raise ValueError("output exists; no overwrite")
    data = legacy.prior.multi.export_cue(sorted(legacy.prior.DIRECTORY.glob("*.cue")))
    report = prepare(data)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x") as stream:
        stream.write(json.dumps(report, indent=2, allow_nan=False) + "\n")
    print(json.dumps({"output": str(path), "status": report["status"], "request_previews": len(report["request_previews"]), "planned_calls": 0, "protocol_sha256": report["protocol"]["sha256"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
