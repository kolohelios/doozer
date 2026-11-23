"""Frozen paired comparison on fresh staged threads under reviewed meanings."""

import argparse
import copy
import hashlib
import json
from pathlib import Path
import subprocess

from scripts import interpretation_review as review, jev_multipass as multi, reviewed_ir as ir
from scripts.evaluation_client import OutputFailure, validate_contract

ROLES = ("interpreter", "verifier", "auditor")
DIRECTORY = multi.DIRECTORY


def schema_for(base, packet, audit=False):
    schema = copy.deepcopy(base)
    fields = schema["properties"]["checks" if audit else "ledger"]["items"]["properties"]
    if audit:
        fields["binding"]["enum"] = list(packet["binding_index"])
        fields["issues"]["items"]["properties"]["evidence"]["items"]["enum"] = list(packet["source_index"])
    else:
        fields["span"]["enum"] = list(packet["source_index"])
        for placement in ("atoms", "conditions"):
            atom = fields[placement]["items"]["properties"]
            atom["binding"]["enum"] = [None, *packet["binding_index"]]
            atom["holder"]["enum"] = [None, *sorted({s["actor"] for s in packet["sources"]})]
            atom["targetSource"]["enum"] = [None, *packet["source_index"]]
            atom["alternatives"]["items"]["enum"] = list(packet["binding_index"])
        limits = schema["properties"]["extractionLimits"]["items"]["properties"]
        limits["about"]["items"]["enum"] = list(packet["binding_index"])
        limits["evidence"]["items"]["enum"] = list(packet["source_index"])
    return {"json": schema, "cue": multi.compile_schema(json.dumps(schema, sort_keys=True))}


def reference_ledger(packet):
    return {"ledger": [{"span": key, "atoms": copy.deepcopy(packet["reference"][key]), "conditions": [], "rationale": "Interpretation of this original message."} for key in packet["source_index"]], "extractionLimits": []}


def control(packet, specification):
    a = reference_ledger(packet)
    b = copy.deepcopy(a)
    target = next(e for e in b["ledger"] if e["span"] == specification["span"])
    if specification["mode"] == "layout":
        moved = [atom for atom in target["atoms"] if atom["kind"] in ir.CONDITIONS]
        if moved:
            target["atoms"] = [atom for atom in target["atoms"] if atom["kind"] not in ir.CONDITIONS]
            target["conditions"] = moved + copy.deepcopy(moved)  # Duplicate meaning is not extra evidence.
        else:
            target["atoms"] += copy.deepcopy(target["atoms"])
    elif specification["mode"] == "add":
        target["atoms"].append(copy.deepcopy(specification["atom"]))
        a = copy.deepcopy(b)
    else:
        kinds = {atom["kind"] for atom in target["atoms"] if specification["binding"] in ir.affected(atom, packet)}
        origin = packet["source_index"][specification["span"]]["origin"]
        for entry in b["ledger"]:
            if packet["source_index"][entry["span"]]["origin"] == origin:
                entry["atoms"] = [atom for atom in entry["atoms"] if not (atom["kind"] in kinds and specification["binding"] in ir.affected(atom, packet))]
        a = copy.deepcopy(b)
    proposals = {role: {"status": "valid", "value": value, "compiled": ir.compile_ledger(value, packet)} for role, value in (("interpreter", a), ("verifier", b))}
    expected = ir.material(ir.compile_ledger(reference_ledger(packet), packet), packet)
    if any(stage["compiled"]["rejected"] for stage in proposals.values()):
        raise ValueError("control is not mechanically admissible")
    bad = {binding for binding in packet["binding_index"] if any(ir.material(stage["compiled"], packet)[binding] != expected[binding] for stage in proposals.values())}
    if (specification["kind"] == "equivalent" and bad) or (specification["kind"] == "fault" and bad != {specification["binding"]}):
        raise ValueError("control does not match predeclared semantic mutation/equivalence")
    return {"kind": specification["kind"], "fault_bindings": sorted(bad), "proposals": proposals,
            "origin": "Authored diagnostic candidates, not actual model outputs; no repair."}


def prepare(data, budget=5.0, calls=49):
    plan = copy.deepcopy(data["reviewedPanelPlan"])
    approved_data = review.validate(review.load())
    approved = review.approval_status(approved_data)
    if len(approved["approved_examples"]) != 8:
        raise ValueError("required example review incomplete")
    if not multi.is_number(budget) or not 0 < budget <= plan["maxBudgetUSD"] or type(calls) is not int or not 1 <= calls <= plan["maxCalls"] or plan["retries"] != 0:
        raise ValueError("invalid paired-trial limits")
    contract = copy.deepcopy(data["reviewedContract"])
    if any(not set(rule["supports"]) <= set(approved["approved_examples"]) or not rule["supports"] for rule in contract["rules"]):
        raise ValueError("contract claims unsupported review backing")
    packets = []
    for key, thread in sorted(data["reviewedThreads"].items()):
        if len(thread["sources"]) != 8 or {s["id"] for s in thread["sources"]} != set(thread["reference"]) or len({s["id"] for s in thread["sources"]}) != 8:
            raise ValueError("thread identity/reference mismatch")
        for length, window in ((4, "w0"), (8, "w1")):
            sources = copy.deepcopy(thread["sources"][:length])
            for index, source in enumerate(sources):
                source["frame"] = "w0" if index < 4 else "w1"
            packet = {"id": key + "/" + window, "thread": key, "window": window, "sources": sources,
                      "bindings": copy.deepcopy(thread["bindings"]), "queries": copy.deepcopy(thread["queries"]),
                      "reference": {s["id"]: copy.deepcopy(thread["reference"][s["id"]]) for s in sources}}
            for definition in packet["bindings"]:
                definition["authority"] = thread["authority"]
            packet["source_index"] = {s["id"]: s for s in sources}
            packet["binding_index"] = {b["id"]: b for b in packet["bindings"]}
            if len(packet["binding_index"]) != len(packet["bindings"]) or len({q["id"] for q in packet["queries"]}) != len(packet["queries"]):
                raise ValueError("duplicate binding or query")
            referenced = {ref for s in sources for ref in ([s["replyTo"]] if s["replyTo"] else []) + s["derivedFrom"]}
            packet["unavailable_reference_ids"] = sorted(referenced - packet["source_index"].keys())
            if not set(packet["unavailable_reference_ids"]) <= set(thread["unavailableParents"]):
                raise ValueError("undeclared missing parent/provenance")
            packet["ledger_schema"] = schema_for(data["transferLedgerSchema"], packet)
            packet["audit_schema"] = schema_for(data["transferAuditSchema"], packet, audit=True)
            compiled = ir.compile_ledger(reference_ledger(packet), packet)
            if compiled["rejected"] or any(q["binding"] not in packet["binding_index"] or ir.evaluate(compiled, q["binding"], q["value"])["state"] != q["expected"][window] for q in packet["queries"]):
                raise ValueError("provisional reference disagrees with conditional scalar rules")
            if window == "w1":
                packet["control"] = control(packet, thread["control"])
            packets.append(packet)
    # Keep prefix/full order inside each independently randomized thread.
    packets.sort(key=lambda p: (multi.pilot.digest([plan["orderSeed"], p["thread"]]), p["window"]))
    planned = len(packets) * len(ROLES) + sum("control" in p for p in packets)
    if planned > calls:
        raise ValueError("cannot accommodate fixed schedule")
    names = ("reviewed_panel.py", "reviewed_ir.py", "interpretation_review.py", "jev_multipass.py", "split_judgment.py", "evaluation_client.py", "calibration_pilot.py", "calibration.py", "jev_probe.py", "workbench_models.py")
    frozen = {"plan": plan, "shared_contract": contract, "packets": packets, "planned_calls": planned,
              "limits": {"budget_usd": float(budget), "max_calls": calls, "retries": 0},
              "review": {"decisions": json.loads(subprocess.run(["cue", "export", str(review.APPROVALS)], check=True, capture_output=True, text=True).stdout), "hashes": review.fingerprints(approved_data), "scope": "Example interpretations only; broader policy prose is not separately approved."},
              "implementation_sha256": {name: hashlib.sha256((multi.ROOT / "scripts" / name).read_bytes()).hexdigest() for name in names},
              "metadata": {name: json.loads((DIRECTORY / "metadata" / name).read_text()) for name in ("analyst.json", "expansion-auditor.json", "panel-auditor.json")},
              "flake_lock_sha256": hashlib.sha256((multi.ROOT / "flake.lock").read_bytes()).hexdigest()}
    return {"protocol": {"sha256": multi.pilot.digest(frozen), "frozen": frozen}, "source_commit": multi.pilot.source_commit(),
            "status": "prepared", "trace": [], "requests": [], "rows": [{"id": p["id"]} for p in packets],
            "warning": "Fresh transfer probes, provisional new labels; not human-reviewed held-out gold. Diagnostic eligibility never accepts canonical knowledge."}


def context(packet, contract):
    return {"shared_semantic_contract": contract, "current_window": packet["window"], "bindings": packet["bindings"], "original_sources": packet["sources"], "unavailable_reference_ids": packet["unavailable_reference_ids"],
            "boundary": "Only these supplied sources are visible. No global coverage, durable acknowledgement, or independent-model corroboration is implied."}


def value_of(row, role):
    stage = row.get(role, {})
    return stage.get("value") if stage.get("status") == "valid" else None


def operation(packet, row, role, frozen):
    plan = frozen["plan"]
    state = context(packet, frozen["shared_contract"])
    audit = role in {"auditor", "control"}
    if audit:
        proposals = packet["control"]["proposals"] if role == "control" else row
        state["untrusted_interpretations"] = {name: {"status": proposals.get(name, {}).get("status", "unavailable"), "proposal": value_of(proposals, name), "mechanical_checks": proposals.get(name, {}).get("compiled")} for name in ROLES[:2]}
    binding = plan["roles"][role]
    payload = {"model": binding["model"], "max_tokens": plan["maxOutputTokens"], "provider": multi.split.provider(binding),
               "response_format": {"type": "json_schema", "json_schema": {"name": "reviewed_transfer", "strict": True, "schema": packet["audit_schema" if audit else "ledger_schema"]["json"]}},
               "messages": [{"role": "system", "content": plan["audit" if audit else "extract"]}, {"role": "user", "content": json.dumps(state, sort_keys=True)}]}
    if not audit:
        payload["temperature"] = 0
    if role == "verifier":
        payload["reasoning"] = {"max_tokens": 2048, "exclude": True}
    elif audit:
        payload["reasoning"] = {"effort": "medium", "exclude": True}
    return {"kind": role, "sample": packet["id"], "endpoint": multi.split.CHAT_ENDPOINT, "payload": payload}


def validate_response(response, op, packet):
    requested, served = op["payload"]["model"], response.get("model", "")
    if not isinstance(served, str) or not (served == requested or served.startswith(requested + "-")):
        raise OutputFailure("unexpected served model")
    choice = response["choices"][0]
    if choice["finish_reason"] != "stop":
        raise OutputFailure("incomplete/refused output")
    value = json.loads(choice["message"]["content"])
    audit = op["kind"] in {"auditor", "control"}
    validate_contract(packet["audit_schema" if audit else "ledger_schema"]["cue"], "#Report", json.dumps(value, sort_keys=True))
    entries = value["checks" if audit else "ledger"]
    field = "binding" if audit else "span"
    expected = set(packet["binding_index"] if audit else packet["source_index"])
    if len(entries) != len(expected) or {e[field] for e in entries} != expected or any(not e["rationale"].strip() for e in entries):
        raise OutputFailure("omitted/duplicated unit or empty rationale")
    if audit:
        proposals = json.loads(op["payload"]["messages"][1]["content"])["untrusted_interpretations"]
        for entry in entries:
            for issue in entry["issues"]:
                if not issue["evidence"] or not issue["detail"].strip():
                    raise OutputFailure("unanchored issue")
            for role in ROLES[:2]:
                relevant = [issue for issue in entry["issues"] if issue["affects"] in {role, "both"}]
                if proposals[role]["proposal"] is None and entry[role] != "unavailable":
                    raise OutputFailure("claims to assess absent proposal")
                if (entry[role] == "faithful" and relevant) or (entry[role] == "material-error" and not relevant):
                    raise OutputFailure("audit verdict/issue contradiction")
    elif any(not limit["evidence"] or not limit["reason"].strip() for limit in value["extractionLimits"]):
        raise OutputFailure("unanchored extraction limit")
    return value


def assessments(packet, row):
    primary = row.get("interpreter", {}).get("compiled")
    verifier = row.get("verifier", {}).get("compiled")
    return {"single": ir.gates(packet, primary), "blind-check": ir.gates(packet, primary, verifier, panel=True, audit_required=False), "panel": ir.gates(packet, primary, verifier, value_of(row, "auditor"), panel=True)}


def summarize(report):
    result = {"reference_status": report["protocol"]["frozen"]["plan"]["referenceStatus"], "planned_calls": report["protocol"]["frozen"]["planned_calls"], "submitted_calls": len(report["trace"]), "complete_snapshots": 0,
              "arms": {arm: {"binding_units": 0, "primary_reference_discrepancies": 0, "discrepancies_flagged": 0, "discrepancies_unflagged": 0, "reference_faithful_flagged": 0, "reference_faithful_eligible": 0, "unavailable_primary": 0} for arm in ("single", "blind-check", "panel")},
              "roles": {role: {"valid": 0, "compiled": 0, "state_cells": 0, "state_matches_proposed": 0, "unsupported_support_cells": 0, "missing_support_cells": 0, "spurious_opposition_cells": 0, "missing_opposition_cells": 0, "mechanically_rejected_atoms": 0, "reference_binding_matches": 0, "reference_binding_units": 0, "reference_signature_memberships": 0, "missing_signature_memberships": 0, "extra_signature_memberships": 0, "unavailable_signature_memberships": 0} for role in ROLES[:2]},
              "audit": {"reference_discrepancy_role_bindings": 0, "coincident_material_challenges": 0, "reference_faithful_role_bindings": 0, "false_challenges_proposed": 0, "unavailable_reference_role_bindings": 0, "unclear_or_unavailable_assessments": 0},
              "controls": {"planned": 0, "valid": 0, "fault_bindings": 0, "faults_both_challenged": 0, "faults_not_both_challenged": 0, "faithful_role_bindings": 0, "false_challenges": 0, "unassessed_role_bindings": 0}, "cases": {}}
    for packet, row in zip(report["protocol"]["frozen"]["packets"], report["rows"]):
        reference = ir.compile_ledger(reference_ledger(packet), packet)
        reference_meanings = ir.material(reference, packet)
        fidelity, states = {}, {}
        for role in ROLES[:2]:
            compiled = row.get(role, {}).get("compiled")
            counts = result["roles"][role]
            counts["valid"] += value_of(row, role) is not None
            counts["compiled"] += compiled is not None
            counts["mechanically_rejected_atoms"] += len(compiled["rejected"]) if compiled else 0
            actual = ir.material(compiled, packet) if compiled else None
            fidelity[role] = {binding: actual[binding] == meanings if actual is not None else None for binding, meanings in reference_meanings.items()}
            for binding, expected in reference_meanings.items():
                counts["reference_signature_memberships"] += len(expected)
                if actual is None:
                    counts["unavailable_signature_memberships"] += len(expected)
                else:
                    counts["missing_signature_memberships"] += len(expected - actual[binding])
                    counts["extra_signature_memberships"] += len(actual[binding] - expected)
            counts["reference_binding_units"] += len(fidelity[role])
            counts["reference_binding_matches"] += sum(v is True for v in fidelity[role].values())
            states[role] = {}
            for q in packet["queries"]:
                state = ir.evaluate(compiled, q["binding"], q["value"])["state"] if compiled else "unavailable"
                states[role][q["id"]] = state
                counts["state_cells"] += 1
                expected = q["expected"][packet["window"]]
                counts["state_matches_proposed"] += state == expected
                if compiled:
                    has_support, needs_support = state in {"supported", "contested"}, expected in {"supported", "contested"}
                    has_opposition, needs_opposition = state in {"opposed", "contested"}, expected in {"opposed", "contested"}
                    counts["unsupported_support_cells"] += has_support and not needs_support
                    counts["missing_support_cells"] += needs_support and not has_support
                    counts["spurious_opposition_cells"] += has_opposition and not needs_opposition
                    counts["missing_opposition_cells"] += needs_opposition and not has_opposition
        masks = assessments(packet, row)
        for arm, flags in masks.items():
            counts = result["arms"][arm]
            for binding, flag in flags.items():
                counts["binding_units"] += 1
                faithful = fidelity["interpreter"][binding]
                held = not flag["candidate_eligible"]
                if faithful is None:
                    counts["unavailable_primary"] += 1
                elif faithful is False:
                    counts["primary_reference_discrepancies"] += 1
                    counts["discrepancies_flagged" if held else "discrepancies_unflagged"] += 1
                else:
                    counts["reference_faithful_flagged" if held else "reference_faithful_eligible"] += 1
        audit = value_of(row, "auditor")
        checks = {c["binding"]: c for c in audit["checks"]} if audit else {}
        for binding in packet["binding_index"]:
            for role in ROLES[:2]:
                actual = checks.get(binding, {}).get(role, "unavailable")
                faithful = fidelity[role][binding]
                counts = result["audit"]
                counts["unclear_or_unavailable_assessments"] += actual in {"unclear", "unavailable"}
                if faithful is None:
                    counts["unavailable_reference_role_bindings"] += 1
                elif faithful:
                    counts["reference_faithful_role_bindings"] += 1
                    counts["false_challenges_proposed"] += actual == "material-error"
                else:
                    counts["reference_discrepancy_role_bindings"] += 1
                    counts["coincident_material_challenges"] += actual == "material-error"
        if "control" in packet:
            counts = result["controls"]
            counts["planned"] += 1
            audit = value_of(row, "control")
            counts["valid"] += audit is not None
            checks = {c["binding"]: c for c in audit["checks"]} if audit else {}
            for binding in packet["binding_index"]:
                flags = [checks.get(binding, {}).get(role, "unavailable") for role in ROLES[:2]]
                counts["unassessed_role_bindings"] += sum(f in {"unclear", "unavailable"} for f in flags)
                if binding in packet["control"]["fault_bindings"]:
                    counts["fault_bindings"] += 1
                    counts["faults_both_challenged" if flags == ["material-error", "material-error"] else "faults_not_both_challenged"] += 1
                else:
                    counts["faithful_role_bindings"] += 2
                    counts["false_challenges"] += flags.count("material-error")
        complete = all(value_of(row, role) is not None for role in ROLES) and ("control" not in packet or value_of(row, "control") is not None)
        result["complete_snapshots"] += complete
        result["cases"][packet["id"]] = {"reference_fidelity": fidelity, "states": states, "diagnostic_gates": masks, "complete": complete}
    costs = {role: {"submitted": 0, "known_usd": 0.0, "unknown_billing": 0} for role in (*ROLES, "control")}
    for record in report["trace"]:
        counts = costs[record["kind"]]
        counts["submitted"] += 1
        if "accounted_usd" in record:
            counts["known_usd"] += record["accounted_usd"]
        else:
            counts["unknown_billing"] += 1
    i, v, a, c = (costs[role]["known_usd"] for role in (*ROLES, "control"))
    result["costs"] = {"roles": costs, "paired_arms_known_usd": {"single": i, "blind-check": i + v, "panel": i + v + a}, "authored_controls_known_usd": c, "total_known_usd": i + v + a + c, "accounted_or_reserved_usd": report.get("accounted_or_reserved_usd"), "warning": "Unknown billing is separate; these are not provider/global limits."}
    result["transitions"] = {arm: {"paired_bindings": 0, "unaffected_material_bindings": 0, "unaffected_faithful_eligible": 0, "unaffected_faithful_flagged": 0, "unaffected_discrepant": 0, "unaffected_unavailable": 0,
                                   "changed_state_queries": 0, "changed_state_pair_matches": 0, "changed_state_final_faithful_eligible": 0, "stable_supported_queries": 0, "stable_supported_final_faithful_eligible": 0} for arm in result["arms"]}
    for first in report["protocol"]["frozen"]["packets"]:
        if first["window"] != "w0":
            continue
        final = next(p for p in report["protocol"]["frozen"]["packets"] if p["thread"] == first["thread"] and p["window"] == "w1")
        before = ir.material(ir.compile_ledger(reference_ledger(first), first), first)
        after = ir.material(ir.compile_ledger(reference_ledger(final), final), final)
        old, new = result["cases"][first["id"]], result["cases"][final["id"]]
        for arm, counts in result["transitions"].items():
            for binding in first["binding_index"]:
                counts["paired_bindings"] += 1
                if before[binding] == after[binding]:
                    counts["unaffected_material_bindings"] += 1
                    faithful = new["reference_fidelity"]["interpreter"][binding]
                    if faithful is None:
                        counts["unaffected_unavailable"] += 1
                    elif not faithful:
                        counts["unaffected_discrepant"] += 1
                    else:
                        eligible = new["diagnostic_gates"][arm][binding]["candidate_eligible"]
                        counts["unaffected_faithful_eligible" if eligible else "unaffected_faithful_flagged"] += 1
            for query in final["queries"]:
                binding, key, expected = query["binding"], query["id"], query["expected"]
                pair_match = old["states"]["interpreter"][key] == expected["w0"] and new["states"]["interpreter"][key] == expected["w1"]
                eligible = new["reference_fidelity"]["interpreter"][binding] is True and new["diagnostic_gates"][arm][binding]["candidate_eligible"]
                if expected["w0"] != expected["w1"]:
                    counts["changed_state_queries"] += 1
                    counts["changed_state_pair_matches"] += pair_match
                    counts["changed_state_final_faithful_eligible"] += pair_match and eligible
                elif expected["w0"] == "supported":
                    counts["stable_supported_queries"] += 1
                    counts["stable_supported_final_faithful_eligible"] += pair_match and eligible
    return result


def run(report, checkpoint, sender=None):
    frozen = report["protocol"]["frozen"]
    if report["status"] != "prepared" or report["trace"] or report["requests"] or multi.pilot.digest(frozen) != report["protocol"]["sha256"] or report["rows"] != [{"id": p["id"]} for p in frozen["packets"]]:
        raise ValueError("changed or previously attempted paired trial")
    if sender is None:
        sender = lambda endpoint, payload, token: multi.bounded_transport(endpoint, payload, token, frozen["plan"]["transportTimeoutSeconds"], frozen["plan"]["maxResponseBytes"])
    ledger = multi.split.Ledger(report, checkpoint, sender=sender)
    report["status"] = "running"
    try:
        for packet, row in zip(frozen["packets"], report["rows"]):
            for role in (*ROLES, *(["control"] if "control" in packet else [])):
                op = operation(packet, row, role, frozen)
                report["requests"].append(copy.deepcopy(op))
                stage = row[role] = {"status": "pending-request", "source_window_sha256": multi.pilot.digest(context(packet, frozen["shared_contract"]))}
                checkpoint()
                before = len(report["trace"])
                try:
                    response = ledger.submit(op)
                except ValueError:
                    stage["status"] = "call-failed" if len(report["trace"]) > before else "not-attempted"
                    raise
                stage["status"] = "invalid"
                try:
                    stage["value"] = validate_response(response, op, packet)
                    stage["status"] = "valid"
                    if role in ROLES[:2]:
                        try:
                            stage["compiled"] = ir.compile_ledger(stage["value"], packet)
                            stage["views"] = ir.views(stage["compiled"], packet)
                        except ValueError:
                            stage["compilation_failure"] = "cyclic or ambiguous conditional revision"
                except (ValueError, KeyError, TypeError, IndexError, AttributeError, OverflowError):
                    stage["status"] = "invalid"
                    stage["failure_reason"] = "report validation failed; no replacement"
                checkpoint()
            row["diagnostic_gates"] = assessments(packet, row)
    except ValueError:
        report["status"] = "stopped-no-retry"
        report["summary"] = summarize(report)
        checkpoint()
        raise
    report["status"] = "completed"
    report["summary"] = summarize(report)
    checkpoint()
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True)
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--protocol-sha256", help="Required for live execution; must equal the offline frozen protocol")
    parser.add_argument("--budget-usd", type=float, default=5.0)
    parser.add_argument("--max-calls", type=int, default=49)
    args = parser.parse_args(argv)
    path, report, owned = Path(args.output), None, False
    try:
        if path.exists():
            raise ValueError("output exists")
        report = prepare(multi.export_cue(sorted(DIRECTORY.glob("*.cue"))), args.budget_usd, args.max_calls)
        if args.live and args.protocol_sha256 != report["protocol"]["sha256"]:
            raise ValueError("live protocol differs from the explicit frozen digest")
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("x") as stream:
            owned = True
            stream.write(json.dumps(report, indent=2, allow_nan=False) + "\n")
        if args.live:
            run(report, lambda: multi.pilot.checkpoint(path, report))
        print(json.dumps({"output": str(path), "status": report["status"], "protocol_sha256": report["protocol"]["sha256"], "calls": len(report["trace"]), "accounted_or_reserved_usd": report.get("accounted_or_reserved_usd"), "summary": report.get("summary")}, indent=2))
        return 0
    except (ValueError, KeyError, TypeError, OSError, OverflowError, subprocess.CalledProcessError):
        if owned:
            report["status"] = "stopped-no-retry"
            report["summary"] = summarize(report)
            multi.pilot.checkpoint(path, report)
        print("Reviewed paired trial stopped or output exists; no retry or canonical effect.")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
