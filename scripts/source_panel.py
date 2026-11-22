"""Fixed specialist panel: two blind source interpretations, an audit, and code."""

import argparse
import copy
import hashlib
import json
from pathlib import Path
import subprocess

from scripts import jev_multipass as multi, source_ir as ir
from scripts.evaluation_client import OutputFailure, validate_contract

PASSES = ("interpreter", "verifier", "auditor", "audit_control", "baseline")
EXTRACTORS = PASSES[:2]
DIRECTORY = multi.DIRECTORY


def schema_for(base, packet, audit=False):
    schema = copy.deepcopy(base)
    fields = schema["properties"]["checks" if audit else "ledger"]["items"]["properties"]
    fields["span"]["enum"] = list(packet["spans"])
    if audit:
        fields["issues"]["items"]["properties"]["evidence"]["items"]["enum"] = list(packet["spans"])
    else:
        atom = fields["atoms"]["items"]["properties"]
        atom["binding"]["enum"] = list(packet["binding_index"])
        atom["target"]["enum"] = [None, *packet["source_index"]]
    return {"json": schema, "cue": multi.compile_schema(json.dumps(schema, sort_keys=True))}


def prepare(data, budget=5.0, calls=40):
    plan = copy.deepcopy(data["panelPlan"])
    if not multi.is_number(budget) or not 0 < budget <= plan["maxBudgetUSD"] or type(calls) is not int or not 1 <= calls <= plan["maxCalls"] or plan["retries"] != 0:
        raise ValueError("invalid panel limits")
    packets = []
    for key, case in sorted(data["panelCases"].items()):
        packet = {"id": key, **copy.deepcopy(case)}
        packet["binding_index"] = {item["id"]: item for item in case["bindings"]}
        packet["source_index"] = {item["id"]: item for item in case["sources"]}
        if len(packet["binding_index"]) != len(case["bindings"]) or len(packet["source_index"]) != len(case["sources"]):
            raise ValueError("duplicate context identity")
        packet["spans"] = {f'{source["id"]}-p{index}': {"source": source["id"], "text": text} for source in case["sources"] for index, text in enumerate(source["paragraphs"])}
        for source in case["sources"]:
            if not set(source["bindings"]) <= set(packet["binding_index"]) or not set(source.get("worldBindings", source["bindings"])) <= set(source["bindings"]):
                raise ValueError("invalid declared binding scope")
        if set(packet["reference"]) != set(packet["spans"]) or len({q["id"] for q in case["queries"]}) != len(case["queries"]):
            raise ValueError("reference or query membership")
        packet["ledger_schema"] = schema_for(data["panelLedgerSchema"], packet)
        packet["audit_schema"] = schema_for(data["panelAuditSchema"], packet, audit=True)
        reference = reference_ledger(packet)
        compiled = ir.compile_ledger(reference, packet)
        if compiled["rejected"] or any(ir.evaluate(compiled, q["binding"], q["value"])["state"] != q["expected"] for q in case["queries"]):
            raise ValueError("proposed references disagree with conditional scalar rules")
        packet["shared_control"] = shared_control(packet)
        packets.append(packet)
    packets.sort(key=lambda packet: multi.pilot.digest([plan["orderSeed"], packet["id"]]))
    if len(packets) * len(PASSES) > calls:
        raise ValueError("call ceiling cannot accommodate fixed panel")
    names = ("source_panel.py", "source_ir.py", "jev_multipass.py", "split_judgment.py", "evaluation_client.py", "calibration_pilot.py", "calibration.py", "jev_probe.py", "workbench_models.py")
    frozen = {"plan": plan, "packets": packets, "passes": list(PASSES), "planned_calls": len(packets) * len(PASSES),
              "limits": {"budget_usd": float(budget), "max_calls": calls, "retries": 0},
              "implementation_sha256": {name: hashlib.sha256((multi.ROOT / "scripts" / name).read_bytes()).hexdigest() for name in names},
              "metadata": {name: json.loads((DIRECTORY / "metadata" / name).read_text()) for name in ("analyst.json", "expansion-auditor.json", "panel-auditor.json", "jev.json")},
              "flake_lock_sha256": hashlib.sha256((multi.ROOT / "flake.lock").read_bytes()).hexdigest()}
    return {"protocol": {"sha256": multi.pilot.digest(frozen), "frozen": frozen}, "source_commit": multi.pilot.source_commit(),
            "status": "prepared", "trace": [], "requests": [], "rows": [{"id": packet["id"]} for packet in packets],
            "warning": "Provisional development references, manually declared bindings/scopes/authority. Schema and literal grounding are not semantic proof. No voting, canonical acceptance, or retirement."}


def reference_ledger(packet):
    return {"ledger": [{"span": key, "atoms": copy.deepcopy(atoms), "rationale": "Provisional authored control."} for key, atoms in packet["reference"].items()], "limitations": []}


def shared_control(packet):
    value = reference_ledger(packet)
    for entry in value["ledger"]:
        entry["rationale"] = "Interpretation of this original paragraph."
    fault = packet["controlFault"]
    entry = next(item for item in value["ledger"] if item["span"] == fault["span"])
    if fault["mode"] == "add-world":
        entry["atoms"].append(copy.deepcopy(fault["atom"]))
    elif fault["mode"] == "omit-binding":
        entry["atoms"] = [atom for atom in entry["atoms"] if atom["binding"] != fault["binding"]]
    else:
        excluded = [atom for atom in entry["atoms"] if atom["binding"] == fault["binding"] and atom["operator"] == "neq"]
        if len(excluded) != 1:
            raise ValueError("ambiguous control mutation")
        excluded[0]["operator"] = "eq"
    compiled = ir.compile_ledger(value, packet)
    if compiled["rejected"] or not any(ir.evaluate(compiled, q["binding"], q["value"])["state"] != q["expected"] for q in packet["queries"]):
        raise ValueError("control must be mechanically admissible and alter a proposed state")
    return {"value": value, "compiled": compiled, "fault_span": fault["span"], "origin": "authored shared-error control; not actual model output"}


def reference_match(actual, packet, span):
    if actual is None:
        return None
    required = ir.material(packet["reference"][span])
    allowed = required | ir.material(packet.get("optionalReference", {}).get(span, []))
    return required <= actual <= allowed


def original_context(packet):
    # Allowlist deliberately excludes evaluation queries, references, and case identity.
    return {"bindings": packet["bindings"], "sources": packet["sources"], "paragraph_spans": packet["spans"],
            "domain_assumptions": "Each binding denotes one scoped scalar value. Values are canonical exact source literals. Authority and source binding allowlists are controlled metadata assumptions, not verified extraction. Statement time is not effective time."}


def value_of(row, role):
    stage = row.get(role, {})
    return stage.get("value") if stage.get("status") == "structurally-valid" else None


def operation(packet, row, role, plan):
    state = original_context(packet)
    binding = plan["roles"][role]
    if role == "baseline":
        state["evaluation_hypotheses"] = [{key: query[key] for key in ("id", "binding", "value")} for query in packet["queries"]]
        questions = {q["id"]: {"type": "choice", "instructions": plan["baselineInstructions"] + "\nAssess exactly: " + json.dumps({key: q[key] for key in ("binding", "value")}, sort_keys=True), "criteria": plan["criteria"]} for q in packet["queries"]}
        payload = {"model": binding["model"], "provider": multi.split.provider(binding), "state": state, "questions": questions}
    else:
        audit = role in {"auditor", "audit_control"}
        schema = packet["audit_schema" if audit else "ledger_schema"]
        if role == "audit_control":
            control = packet["shared_control"]
            state["untrusted_interpretations"] = {name: {"status": "structurally-valid", "proposal": control["value"], "mechanical_checks": control["compiled"]} for name in EXTRACTORS}
        elif audit:
            state["untrusted_interpretations"] = {name: {"status": row.get(name, {}).get("status", "unavailable"), "proposal": value_of(row, name), "mechanical_checks": row.get(name, {}).get("compiled")} for name in EXTRACTORS}
        payload = {"model": binding["model"], "max_tokens": 4000 if role == "interpreter" else 8000,
                   "provider": multi.split.provider(binding), "response_format": {"type": "json_schema", "json_schema": {"name": "source_panel", "strict": True, "schema": schema["json"]}},
                   "messages": [{"role": "system", "content": plan["auditInstructions" if audit else "extractionInstructions"]},
                                {"role": "user", "content": json.dumps(state, sort_keys=True)}]}
        if not audit:
            payload["temperature"] = 0
        if role == "verifier":
            payload["reasoning"] = {"max_tokens": 2048, "exclude": True}
        elif audit:
            payload["reasoning"] = {"effort": "medium", "exclude": True}
    return {"kind": role, "sample": packet["id"], "endpoint": multi.split.DECISIONS if role == "baseline" else multi.split.CHAT_ENDPOINT, "payload": payload}


def validate_response(response, op, packet):
    requested, served = op["payload"]["model"], response.get("model", "")
    if not isinstance(served, str) or not (served == requested or served.startswith(requested + "-")):
        raise OutputFailure("unexpected served model")
    role = op["kind"]
    if role == "baseline":
        answers = response["answers"]
        if set(answers) != set(op["payload"]["questions"]) or any(item.get("type") != "choice" or item.get("choice") not in op["payload"]["questions"][key]["criteria"] for key, item in answers.items()):
            raise OutputFailure("invalid baseline choices")
        return answers
    choice = response["choices"][0]
    if choice["finish_reason"] != "stop":
        raise OutputFailure("refused or incomplete output")
    value = json.loads(choice["message"]["content"])
    audit = role in {"auditor", "audit_control"}
    validate_contract(packet["audit_schema" if audit else "ledger_schema"]["cue"], "#Report", json.dumps(value, sort_keys=True))
    entries = value["checks" if audit else "ledger"]
    if len(entries) != len(packet["spans"]) or {item["span"] for item in entries} != set(packet["spans"]) or any(not item["rationale"].strip() for item in entries):
        raise OutputFailure("omitted/duplicated paragraph or empty rationale")
    if audit:
        for entry in entries:
            for issue in entry["issues"]:
                if not issue["evidence"] or not issue["detail"].strip():
                    raise OutputFailure("unanchored audit issue")
            inputs = json.loads(op["payload"]["messages"][1]["content"])["untrusted_interpretations"]
            for name in EXTRACTORS:
                if inputs[name]["proposal"] is None and entry[name] != "unavailable":
                    raise OutputFailure("audit claims to assess unavailable proposal")
                if entry[name] == "material-error" and not any(issue["affects"] in {name, "both"} and entry["span"] in issue["evidence"] for issue in entry["issues"]):
                    raise OutputFailure("audit error lacks role-specific source anchor")
                if entry[name] == "faithful" and any(issue["affects"] in {name, "both"} for issue in entry["issues"]):
                    raise OutputFailure("audit faithful label conflicts with its material issue")
    return value


def panel_status(row):
    if any(value_of(row, role) is None for role in (*EXTRACTORS, "auditor")):
        return "unresolved-unavailable"
    if any("compiled" not in row[role] or row[role]["compiled"]["rejected"] for role in EXTRACTORS):
        return "unresolved-mechanical-check"
    a, b = ({item["span"]: ir.material(item["atoms"]) for item in value_of(row, role)["ledger"]} for role in EXTRACTORS)
    if a != b:
        return "unresolved-interpretation-disagreement"
    if any(check[role] != "faithful" for check in value_of(row, "auditor")["checks"] for role in EXTRACTORS) or any(check["issues"] for check in value_of(row, "auditor")["checks"]):
        return "unresolved-audit"
    return "unchecked-agreement-not-acceptance"


def summarize(report):
    result = {"reference_status": report["protocol"]["frozen"]["plan"]["referenceStatus"], "planned_calls": report["protocol"]["frozen"]["planned_calls"],
              "submitted_calls": len(report["trace"]), "complete_trajectories": 0, "complete_panel_trajectories": 0, "roles": {}, "cases": {},
              "shared_controls": {"planned": len(report["rows"]), "structurally_valid": 0, "both_challenged": 0, "partly_challenged": 0, "unchallenged": 0, "unassessed": 0, "false_challenges_on_unchanged_spans": 0},
              "audit": {"role_span_comparisons": 0, "provisional_discrepancies": 0, "challenged_discrepancies": 0, "unchallenged_discrepancies": 0, "false_challenges": 0, "unassessed": 0, "shared_discrepancy_spans": 0, "shared_discrepancies_both_challenged": 0}}
    for role in (*EXTRACTORS, "baseline"):
        result["roles"][role] = {"packets": 0, "structurally_valid": 0, "reference_span_matches": 0, "reference_spans": 0, "unavailable_reference_spans": 0, "state_matches_proposed": 0, "state_cells": 0, "mechanically_rejected_atoms": 0, "compilation_unavailable_packets": 0}
    for packet, row in zip(report["protocol"]["frozen"]["packets"], report["rows"]):
        states, fidelity = {}, {}
        for role in (*EXTRACTORS, "baseline"):
            counts = result["roles"][role]
            counts["packets"] += 1
            value = value_of(row, role)
            counts["structurally_valid"] += value is not None
            compiled = row.get(role, {}).get("compiled")
            if role in EXTRACTORS:
                counts["mechanically_rejected_atoms"] += len(compiled["rejected"]) if compiled else 0
                counts["compilation_unavailable_packets"] += compiled is None
                entries = {entry["span"]: ir.material(entry["atoms"]) for entry in value["ledger"]} if value else {}
                fidelity[role] = {span: reference_match(entries.get(span), packet, span) for span in packet["spans"]}
                counts["reference_spans"] += len(packet["spans"])
                counts["unavailable_reference_spans"] += sum(item is None for item in fidelity[role].values())
                counts["reference_span_matches"] += sum(item is True for item in fidelity[role].values())
            states[role] = {}
            for query in packet["queries"]:
                actual = value.get(query["id"], {}).get("choice", "unavailable") if role == "baseline" and value else ir.evaluate(compiled, query["binding"], query["value"])["state"] if compiled else "unavailable"
                states[role][query["id"]] = actual
                counts["state_cells"] += 1
                counts["state_matches_proposed"] += actual == query["expected"]
        audit = value_of(row, "auditor")
        checks = {entry["span"]: entry for entry in audit["checks"]} if audit else {}
        for span in packet["spans"]:
            shared = all(fidelity[role][span] is False for role in EXTRACTORS)
            result["audit"]["shared_discrepancy_spans"] += shared
            both = True
            for role in EXTRACTORS:
                observed = checks.get(span, {}).get(role, "unavailable")
                challenged = observed == "material-error"
                both = both and challenged
                result["audit"]["role_span_comparisons"] += 1
                result["audit"]["unassessed"] += observed in {"unavailable", "unclear"}
                if fidelity[role][span] is False:
                    result["audit"]["provisional_discrepancies"] += 1
                    result["audit"]["challenged_discrepancies" if challenged else "unchallenged_discrepancies"] += 1
                elif fidelity[role][span] is True and challenged:
                    result["audit"]["false_challenges"] += 1
            result["audit"]["shared_discrepancies_both_challenged"] += shared and both
        control_audit = value_of(row, "audit_control")
        control_checks = {entry["span"]: entry for entry in control_audit["checks"]} if control_audit else {}
        control_counts = result["shared_controls"]
        control_counts["structurally_valid"] += control_audit is not None
        fault = packet["shared_control"]["fault_span"]
        flags = [control_checks.get(fault, {}).get(role, "unavailable") for role in EXTRACTORS]
        if any(flag in {"unavailable", "unclear"} for flag in flags):
            control_counts["unassessed"] += 1
        else:
            control_counts["both_challenged" if flags.count("material-error") == 2 else "partly_challenged" if "material-error" in flags else "unchallenged"] += 1
        control_counts["false_challenges_on_unchanged_spans"] += sum(check[role] == "material-error" for span, check in control_checks.items() if span != fault for role in EXTRACTORS)
        complete = all(value_of(row, role) is not None for role in PASSES)
        result["complete_trajectories"] += complete
        result["complete_panel_trajectories"] += all(value_of(row, role) is not None for role in (*EXTRACTORS, "auditor"))
        result["cases"][packet["id"]] = {"states": states, "reference_fidelity": fidelity, "panel": panel_status(row), "complete": complete,
                                          "expected_provisional": {q["id"]: q["expected"] for q in packet["queries"]}}
    return result


def run(report, checkpoint, sender=None):
    frozen = report["protocol"]["frozen"]
    if report["status"] != "prepared" or report["trace"] or report["requests"] or multi.pilot.digest(frozen) != report["protocol"]["sha256"] or report["rows"] != [{"id": packet["id"]} for packet in frozen["packets"]]:
        raise ValueError("changed or previously attempted panel")
    if sender is None:
        sender = lambda endpoint, payload, token: multi.bounded_transport(endpoint, payload, token, frozen["plan"]["transportTimeoutSeconds"], frozen["plan"]["maxResponseBytes"])
    ledger = multi.split.Ledger(report, checkpoint, sender=sender)
    report["status"] = "running"
    try:
        for packet, row in zip(frozen["packets"], report["rows"]):
            for role in PASSES:
                op = operation(packet, row, role, frozen["plan"])
                report["requests"].append(copy.deepcopy(op))
                stage = row[role] = {"status": "pending-request", "source_window_sha256": multi.pilot.digest(original_context(packet))}
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
                    stage["status"] = "structurally-valid"
                    if role in EXTRACTORS:
                        try:
                            stage["compiled"] = ir.compile_ledger(stage["value"], packet)
                            stage["projection"] = ir.render(stage["compiled"], packet, role)
                        except ValueError:
                            stage["compilation_failure"] = "cyclic or otherwise invalid conditional interpretation"
                except (ValueError, KeyError, TypeError, IndexError, AttributeError, OverflowError):
                    stage["status"] = "invalid"
                    stage["failure_reason"] = "contract, membership, model, or anchor validation failed; no replacement"
                checkpoint()
            row["panel_status"] = panel_status(row)
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
    parser.add_argument("--budget-usd", type=float, default=5.0)
    parser.add_argument("--max-calls", type=int, default=40)
    args = parser.parse_args(argv)
    path, report, owned = Path(args.output), None, False
    try:
        if path.exists():
            raise ValueError("output exists")
        report = prepare(multi.export_cue(sorted(DIRECTORY.glob("*.cue"))), args.budget_usd, args.max_calls)
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
        print("Source panel stopped or output exists; no retry, vote, or canonical effect.")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
