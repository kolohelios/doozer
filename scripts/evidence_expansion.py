"""Forked evidence updates with bounded retrieval and conditional proof checks."""

import argparse
import copy
import hashlib
import json
from pathlib import Path
import subprocess

from scripts import evidence_graph as graph, jev_multipass as multi
from scripts.evaluation_client import OutputFailure, validate_contract

ROOT, DIRECTORY = multi.ROOT, multi.DIRECTORY
INITIAL = ("initial", "initial_probe")
BRANCH = ("expanded", "expanded_probe", "audit", "reconciled", "final_probe")
STATES = ("supported", "opposed", "contested", "unestablished")


def report_schema(base, hypotheses, spans, audit=False):
    schema = copy.deepcopy(base)
    field = "ledgers" if audit else "proofs"
    properties = schema["properties"][field]["items"]["properties"]
    properties["id"]["enum"] = [item["id"] for item in hypotheses]
    if audit:
        properties["spans"]["items"]["properties"]["id"]["enum"] = list(spans)
    else:
        for polarity in ("positive", "negative"):
            properties[polarity]["items"]["enum"] = list(spans)
    return {"json": schema, "cue": multi.compile_schema(json.dumps(schema, sort_keys=True))}


def prepare(data, budget=5.0, calls=80):
    plan = copy.deepcopy(data["expansionPlan"])
    if not multi.is_number(budget) or not 0 < budget <= plan["maxBudgetUSD"] or type(calls) is not int or not 1 <= calls <= plan["maxCalls"]:
        raise ValueError("invalid limits")
    families, branch_count = [], 0
    for key, value in sorted(data["expansionFamilies"].items()):
        hypotheses = copy.deepcopy(value["propositions"])
        ids = {item["id"] for item in hypotheses}
        if len(ids) != len(hypotheses) or set(value["initialExpected"]) != ids:
            raise ValueError("invalid proposition membership")
        before = graph.view(value["initial"])
        for hypothesis in hypotheses:
            graph.origin_guard(hypothesis, before["sources"])
        family = {"id": key, "question": value["question"], "hypotheses": hypotheses, "before": before,
                  "initial_expected": value["initialExpected"],
                  "initial_schema": report_schema(data["expansionReportSchema"], hypotheses, before["spans"]), "branches": []}
        for variant, branch in sorted(value["branches"].items()):
            if set(branch["expected"]) != ids:
                raise ValueError("branch omits expected proposition")
            catalog = copy.deepcopy(branch["catalog"]) + [{"id": "d9", "scope": "unrelated", "text": "UNRETRIEVED_CATALOG_CANARY. A superficially related note is deliberately not linked by this packet. It must not appear in a model's visible evidence."}]
            sources, retrieval = graph.expand(value["initial"], catalog, plan["expansion"])
            after = graph.view(sources)
            for hypothesis in hypotheses:
                graph.origin_guard(hypothesis, after["sources"])
            family["branches"].append({"id": key + "/" + variant, "variant": variant, "catalog": catalog,
                                       "after": after, "retrieval": retrieval, "expected": branch["expected"], "reference_reason": branch["reason"],
                                       "schema": report_schema(data["expansionReportSchema"], hypotheses, after["spans"]),
                                       "audit_schema": report_schema(data["expansionAuditSchema"], hypotheses, after["spans"], audit=True)})
            branch_count += 1
        family["branches"].sort(key=lambda item: multi.pilot.digest([plan["orderSeed"], item["id"]]))
        families.append(family)
    planned = len(families) * len(INITIAL) + branch_count * len(BRANCH)
    if planned > calls:
        raise ValueError("call limit cannot accommodate DAG")
    families.sort(key=lambda item: multi.pilot.digest([plan["orderSeed"], item["id"]]))
    names = ("evidence_expansion.py", "evidence_graph.py", "jev_multipass.py", "split_judgment.py", "calibration_pilot.py", "evaluation_client.py", "jev_probe.py", "workbench_models.py")
    frozen = {"plan": plan, "families": families, "initial_passes": list(INITIAL), "branch_passes": list(BRANCH), "planned_calls": planned,
              "limits": {"budget_usd": float(budget), "max_calls": calls, "retries": 0},
              "implementation_sha256": {name: hashlib.sha256((ROOT / "scripts" / name).read_bytes()).hexdigest() for name in names},
              "auditor_metadata": json.loads((DIRECTORY / "metadata/expansion-auditor.json").read_text())}
    return {"protocol": {"sha256": multi.pilot.digest(frozen), "frozen": frozen}, "source_commit": multi.pilot.source_commit(),
            "status": "prepared", "trace": [], "requests": [], "families": [{"id": family["id"], "branches": [{"id": branch["id"]} for branch in family["branches"]]} for family in families],
            "warning": "Proposed synthetic controls, not human gold. Metadata guards are conditional; schema and witness references do not prove prose entailment. No canonical effects."}


def valid_value(container, key):
    stage = container.get(key, {})
    return stage.get("value") if stage.get("status") == "valid" else None


def context(family, packet):
    return {"question": family["question"], "hypotheses_not_premises": [{key: item[key] for key in ("id", "text", "scope")} for item in family["hypotheses"]],
            "visible_packet": copy.deepcopy(packet),
            "metadata_assumption": "Activity and scope are declared fixture metadata. They are not verified natural-language extraction or proof of empirical truth."}


def operation(family, branch, root, row, kind, plan):
    initial = kind in INITIAL
    packet = family["before"] if initial else branch["after"]
    state = context(family, packet)
    role = plan["roles"][kind]
    if kind in {"initial", "expanded", "reconciled"}:
        if kind != "initial":
            state["untrusted_previous_proposal"] = valid_value(root, "initial") if kind == "expanded" else valid_value(row, "expanded")
            state["previous_source_window"] = family["before"] if kind == "expanded" else branch["after"]
            state["retrieval_log"] = branch["retrieval"]
        if kind == "reconciled":
            state["untrusted_audit"] = valid_value(row, "audit")
        schema = family["initial_schema"] if initial else branch["schema"]
        payload = chat(plan, role, state, schema, plan["reasonInstructions"], plan["maxOutputTokens"])
    elif kind == "audit":
        # The independent source ledger sees the proposed narrative, not its witness labels or Jev opinions.
        proposal = valid_value(row, "expanded")
        state["proposal_summary"] = proposal["summary"] if proposal else None
        payload = chat(plan, role, state, branch["audit_schema"], plan["auditInstructions"], plan["auditOutputTokens"])
        payload["reasoning"] = {"max_tokens": 2048, "exclude": True}
    else:
        proposal = valid_value(root, "initial") if initial else valid_value(row, "expanded" if kind == "expanded_probe" else "reconciled")
        state["untrusted_proposal"] = proposal
        if kind == "final_probe":
            state["untrusted_audit"] = valid_value(row, "audit")
        questions = {"warrant": {"type": "choice", "instructions": plan["jevInstructions"] + "\nAssess only the warrant of the actual proposal, including coverage qualifications. Use uncertain when no valid proposal exists.", "criteria": plan["warrantCriteria"]}}
        for hypothesis in family["hypotheses"]:
            questions["evidence-" + hypothesis["id"]] = {"type": "choice", "instructions": plan["jevInstructions"] + "\nAssess visible-packet evidence for hypothesis " + hypothesis["id"] + ", not whether an unqualified assertion should be accepted. A known unread reference is a freshness gap, not an opposite fact.", "criteria": plan["evidenceCriteria"]}
        payload = {"model": role["model"], "provider": multi.split.provider(role), "state": state, "questions": questions}
    return {"kind": kind, "sample": family["id"] if initial else branch["id"], "endpoint": multi.split.DECISIONS if kind.endswith("probe") else multi.split.CHAT_ENDPOINT, "payload": payload}


def chat(plan, role, state, schema, instructions, output):
    return {"model": role["model"], "temperature": plan["temperature"], "max_tokens": output, "provider": multi.split.provider(role),
            "response_format": {"type": "json_schema", "json_schema": {"name": "evidence_update", "strict": True, "schema": schema["json"]}},
            "messages": [{"role": "system", "content": instructions}, {"role": "user", "content": json.dumps(state, sort_keys=True)}]}


def validate(response, op, family, branch):
    model, requested = response.get("model", ""), op["payload"]["model"]
    if not isinstance(model, str) or not (model == requested or model.startswith(requested + "-")):
        raise OutputFailure("unexpected served model")
    kind = op["kind"]
    if kind.endswith("probe"):
        answers = response["answers"]
        if set(answers) != set(op["payload"]["questions"]):
            raise OutputFailure("question membership")
        for key, answer in answers.items():
            if answer.get("type") != "choice" or answer.get("choice") not in op["payload"]["questions"][key]["criteria"]:
                raise OutputFailure("refusal or unknown choice")
            if answer.get("confidence") is not None and not multi.is_number(answer["confidence"], maximum=1):
                raise OutputFailure("invalid diagnostic confidence")
        return answers
    choice = response["choices"][0]
    if choice["finish_reason"] != "stop":
        raise OutputFailure("truncated/refused output")
    value = json.loads(choice["message"]["content"])
    schema = family["initial_schema"] if kind == "initial" else branch["audit_schema"] if kind == "audit" else branch["schema"]
    validate_contract(schema["cue"], "#Report", json.dumps(value, sort_keys=True))
    field = "ledgers" if kind == "audit" else "proofs"
    expected = {item["id"] for item in family["hypotheses"]}
    if len(value[field]) != len(expected) or {item["id"] for item in value[field]} != expected:
        raise OutputFailure("proposition membership")
    packet = family["before"] if kind == "initial" else branch["after"]
    for item in value[field]:
        if kind == "audit":
            if len(item["spans"]) != len(packet["spans"]) or {span["id"] for span in item["spans"]} != set(packet["spans"]):
                raise OutputFailure("audit omits/duplicates source spans")
            if any(not span["rationale"].strip() for span in item["spans"]):
                raise OutputFailure("empty rationale")
        else:
            if not item["rationale"].strip() or any(len(set(item[key])) != len(item[key]) for key in ("positive", "negative")):
                raise OutputFailure("empty rationale or duplicate witnesses")
    if not value["rationale" if kind == "audit" else "summary"].strip():
        raise OutputFailure("empty report")
    return value


def compile_report(value, family, packet, audit=False):
    if value is None:
        return None
    proposals = {item["id"]: item for item in value["ledgers" if audit else "proofs"]}
    result = {}
    for hypothesis in family["hypotheses"]:
        item = proposals[hypothesis["id"]]
        if audit:
            proof = {"positive": [span["id"] for span in item["spans"] if span["relation"] in {"supports", "both"}],
                     "negative": [span["id"] for span in item["spans"] if span["relation"] in {"opposes", "both"}]}
        else:
            proof = item
        result[hypothesis["id"]] = graph.compile_proof(hypothesis, proof, packet)
        if audit:
            result[hypothesis["id"]]["audit_unclear_span_ids"] = [span["id"] for span in item["spans"] if span["relation"] == "unclear"]
    return result


def summarize(report):
    frozen = report["protocol"]["frozen"]
    result = {"reference_status": frozen["plan"]["referenceStatus"], "planned_calls": frozen["planned_calls"], "submitted_calls": len(report["trace"]),
              "complete_trajectories": 0, "cases": {}}
    for family, root in zip(frozen["families"], report["families"]):
        for branch, row in zip(family["branches"], root["branches"]):
            states = {}
            for kind in BRANCH:
                stage = row.get(kind, {})
                if kind.endswith("probe"):
                    states[kind] = {h["id"]: stage.get("value", {}).get("evidence-" + h["id"], {}).get("choice", stage.get("status", "not-attempted")) for h in family["hypotheses"]}
                else:
                    compiled = compile_report(valid_value(row, kind), family, branch["after"], audit=kind == "audit")
                    states[kind] = {key: value["guarded_state"] for key, value in compiled.items()} if compiled else stage.get("status", "not-attempted")
            complete = all(root.get(kind, {}).get("status") == "valid" for kind in INITIAL) and all(row.get(kind, {}).get("status") == "valid" for kind in BRANCH)
            result["complete_trajectories"] += complete
            result["cases"][branch["id"]] = {"expected_provisional": branch["expected"], "states": states,
                                               "retrieved": branch["retrieval"]["documents_added"], "complete": complete}
    return result


def run(report, checkpoint, sender=None):
    frozen = report["protocol"]["frozen"]
    if report["status"] != "prepared" or report["trace"] or report["requests"] or multi.pilot.digest(frozen) != report["protocol"]["sha256"]:
        raise ValueError("changed or previously attempted run")
    expected = [{"id": f["id"], "branches": [{"id": b["id"]} for b in f["branches"]]} for f in frozen["families"]]
    if report["families"] != expected:
        raise ValueError("changed fork identity")
    if sender is None:
        sender = lambda endpoint, payload, token: multi.bounded_transport(endpoint, payload, token, frozen["plan"]["transportTimeoutSeconds"], frozen["plan"]["maxResponseBytes"])
    ledger = multi.split.Ledger(report, checkpoint, sender=sender)
    report["status"] = "running"
    def invoke(family, branch, root, row, kind):
        target = root if kind in INITIAL else row
        op = operation(family, branch, root, row, kind, frozen["plan"])
        report["requests"].append(copy.deepcopy(op))
        packet = family["before"] if kind in INITIAL else branch["after"]
        parent_proposal = valid_value(root, "initial") if kind in {"expanded", "initial_probe"} else valid_value(row, "expanded") if kind in {"audit", "reconciled", "expanded_probe"} else valid_value(row, "reconciled") if kind == "final_probe" else None
        target[kind] = {"status": "pending-request", "source_window_sha256": multi.pilot.digest(packet),
                        "parent_proposal_sha256": multi.pilot.digest(parent_proposal) if parent_proposal is not None else None}
        checkpoint()
        before = len(report["trace"])
        try:
            response = ledger.submit(op)
        except ValueError:
            target[kind]["status"] = "call-failed" if len(report["trace"]) > before else "not-attempted"
            raise
        stage = target[kind]
        stage["status"] = "invalid"
        try:
            stage["value"] = validate(response, op, family, branch)
            stage["status"] = "valid"
            if not kind.endswith("probe"):
                packet = family["before"] if kind == "initial" else branch["after"]
                stage["compiled"] = compile_report(stage["value"], family, packet, audit=kind == "audit")
        except (ValueError, KeyError, TypeError, IndexError, AttributeError, OverflowError):
            stage["status"] = "invalid"
            stage["failure_reason"] = "report/anchor validation failed; no replacement"
        checkpoint()
    try:
        for family, root in zip(frozen["families"], report["families"]):
            for kind in INITIAL:
                invoke(family, None, root, None, kind)
            parent = {"source_window_sha256": multi.pilot.digest(family["before"]), "proposal_sha256": multi.pilot.digest(valid_value(root, "initial"))}
            for branch, row in zip(family["branches"], root["branches"]):
                row["shared_initial_parent"] = copy.deepcopy(parent)
                for kind in BRANCH:
                    invoke(family, branch, root, row, kind)
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
    parser.add_argument("--max-calls", type=int, default=80)
    args = parser.parse_args(argv)
    path, report, owned = Path(args.output), None, False
    try:
        if path.exists():
            raise ValueError("output exists")
        data = multi.export_cue(sorted(DIRECTORY.glob("*.cue")))
        report = prepare(data, args.budget_usd, args.max_calls)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("x") as stream:
            owned = True
            stream.write(json.dumps(report, indent=2, allow_nan=False) + "\n")
        if args.live:
            run(report, lambda: multi.pilot.checkpoint(path, report))
        print(json.dumps({"output": str(path), "status": report["status"], "protocol_sha256": report["protocol"]["sha256"], "calls": len(report["trace"]),
                          "accounted_or_reserved_usd": report.get("accounted_or_reserved_usd"), "summary": report.get("summary")}, indent=2))
        return 0
    except (ValueError, KeyError, TypeError, OSError, OverflowError, subprocess.CalledProcessError):
        if owned:
            report["status"] = "stopped-no-retry"
            report["summary"] = summarize(report)
            multi.pilot.checkpoint(path, report)
        print("Evidence update stopped or output exists; no retry. Inspect the artifact. No canonical knowledge changed.")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
