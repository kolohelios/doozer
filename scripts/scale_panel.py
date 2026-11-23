"""Frozen larger paired comparison; offline by default, one fixed paid schedule."""

import argparse
import copy
import hashlib
import json
from pathlib import Path
import subprocess

from scripts import audit_contract as audit, deadline_transport, interpretation_review as review, meaning_projection as meaning, reviewed_ir as core, reviewed_panel as prior, transfer_review
from scripts.evaluation_client import OutputFailure

ROLES = ("interpreter", "verifier", "auditor")


def profile(compiled, context):
    """Finite operational equivalence, not a general semantic entailment checker."""
    result = {b: set() for b in context["binding_index"]}
    for record in [*compiled["core"]["records"], *compiled["core"]["rejected"]]:
        one = {**compiled["core"], "records": [record], "rejected": []}
        for binding, values in core.material(one, context).items():
            for value in values:
                parts = json.loads(value)
                if record["atom"]["kind"] == "directive":
                    source = context["source_index"][record["span"]]
                    parts[1] = [source["actor"], source["origin"]]
                result[binding].add(core.freeze(parts))
    for record in [*compiled["annotations"], *compiled["rejected_annotations"]]:
        annotation = record["annotation"]
        if annotation["kind"] == "procedure":
            # Successful lowering is already represented by core directives.
            if "reason" in record:
                for binding in context["topics"][annotation["topic"]]:
                    result[binding].add(core.freeze(["rejected-procedure", record]))
        elif annotation["kind"] == "speculation":
            operator, value = annotation["operator"], annotation["value"]
            domain = set(context["binding_index"][annotation["binding"]]["values"])
            if operator == "neq" and value in domain and len(domain) == 2:
                operator, value = "eq", next(iter(domain - {value}))
            result[annotation["binding"]].add(core.freeze(["speculation", record["speaker"], record["source"], operator, value]))
        elif annotation["frame"] == "person" or "reason" in record:
            result[annotation["binding"]].add(core.freeze(["condition", record["speaker"], record["as_of"], annotation["frame"], annotation["stance"], annotation["holder"]]))
    return result


def note_profile(compiled):
    return sorted(core.freeze([r["source"], r["annotation"]]) for r in compiled["annotations"] if r["annotation"]["kind"] == "condition" and r["annotation"]["frame"] == "source-note")


def compiled_of(row, role):
    return row.get(role, {}).get("compiled") if row.get(role, {}).get("status") == "valid" else None


def reference(packet):
    return copy.deepcopy(packet["reference"])


def compile_value(value, packet):
    return meaning.compile_ledger(value, packet["context"], packet["ledger_schema"])


def controls(packet, specification):
    a, b = reference(packet), reference(packet)
    entry = next(e for e in b["ledger"] if e["span"] == specification["span"])
    mode, binding = specification["mode"], specification["binding"]
    if mode == "hunch-world":
        hunch = next(n for n in entry["annotations"] if n["kind"] == "speculation" and n["binding"] == binding)
        entry["annotations"].remove(hunch)
        entry["atoms"].append(meaning.atom("assertion", binding, operator=hunch["operator"], value=hunch["value"]))
    elif mode == "add-world":
        entry["atoms"].append(copy.deepcopy(specification["atom"]))
    elif mode == "omit-kind":
        entry["atoms"] = [n for n in entry["atoms"] if not (n["kind"] == specification["targetKind"] and n["binding"] == binding)]
    elif mode == "omit-origin-world":
        origin = packet["context"]["source_index"][specification["span"]]["origin"]
        for item in b["ledger"]:
            if packet["context"]["source_index"][item["span"]]["origin"] == origin:
                item["atoms"] = [n for n in item["atoms"] if not (n["kind"] == "assertion" and n["binding"] == binding)]
    elif mode == "drop-note":
        entry["annotations"] = [n for n in entry["annotations"] if n["kind"] != "condition"]
    elif mode == "procedure-layout":
        for node in entry["annotations"][:]:
            if node["kind"] == "procedure":
                entry["annotations"].remove(node)
                for about in packet["context"]["topics"][node["topic"]]:
                    entry["atoms"].append(meaning.atom("directive", about, action=copy.deepcopy(node["action"])))
    elif mode == "duplicate":
        entry["atoms"] += copy.deepcopy(entry["atoms"])
    elif mode == "qualifier-layout":
        moved = [n for n in entry["atoms"] if n["kind"] == "qualifier"]
        entry["atoms"] = [n for n in entry["atoms"] if n["kind"] != "qualifier"]
        entry["conditions"] += moved + copy.deepcopy(moved)
    else:
        raise ValueError("unknown predeclared control")
    if specification["kind"] == "fault":
        a = copy.deepcopy(b)
    proposals = {}
    for role, value in (("interpreter", a), ("verifier", b)):
        compiled = compile_value(value, packet)
        if compiled["core"]["rejected"] or compiled["rejected_annotations"]:
            raise ValueError("authored control not mechanically admissible")
        proposals[role] = {"status": "valid", "value": value, "compiled": compiled}
    expected = profile(compile_value(reference(packet), packet), packet["context"])
    differences = {b for b in expected if any(profile(p["compiled"], packet["context"])[b] != expected[b] for p in proposals.values())}
    if differences != ({binding} if specification["kind"] == "fault" else set()):
        raise ValueError("control mutation/equivalence mismatch")
    return {"kind": specification["kind"], "fault_bindings": sorted(differences), "proposals": proposals, "specification": copy.deepcopy(specification)}


def prepare(data, budget=5.0, calls=84):
    plan = copy.deepcopy(data["scalePlan"])
    if not prior.multi.is_number(budget) or not 0 < budget <= plan["maxBudgetUSD"] or type(calls) is not int or calls != plan["maxCalls"] or plan["retries"] != 0:
        raise ValueError("invalid fixed scale limits")
    reviewed = review.validate(review.load())
    transferred = transfer_review.validate(transfer_review.load())
    if len(review.approval_status(reviewed)["approved_examples"]) != 8 or len(transfer_review.approval_status(transferred)["approved_examples"]) != 2:
        raise ValueError("required individual reviews incomplete")
    if len(data["scaleCorpus"]) != 12:
        raise ValueError("fixed twelve-thread corpus required")
    metadata = {name: json.loads((prior.DIRECTORY / "metadata" / ("scale-" + name + ".json")).read_text()) for name in ROLES}
    for name, snapshot in metadata.items():
        binding = plan["roles"][name]
        endpoints = [e for e in snapshot["data"]["endpoints"] if e.get("tag") == binding["provider"]]
        if snapshot["data"]["id"] != binding["model"] or not any(e.get("status") == 0 and {"max_tokens", "response_format"} <= set(e["supported_parameters"]) and float(e["pricing"]["prompt"]) * 1000000 <= float(binding["promptPrice"]) and float(e["pricing"]["completion"]) * 1000000 <= float(binding["completionPrice"]) and (e.get("max_completion_tokens") is None or e["max_completion_tokens"] >= plan["maxOutputTokens"]) for e in endpoints):
            raise ValueError("pinned endpoint snapshot does not support frozen limits")
    packets = []
    for key, thread in sorted(data["scaleCorpus"].items()):
        if len(thread["sources"]) != 16 or len({s["id"] for s in thread["sources"]}) != 16 or not set(thread["reference"]) <= {s["id"] for s in thread["sources"]}:
            raise ValueError("source count/identity/reference mismatch")
        for length, window in ((8, "w0"), (16, "w1")):
            sources = copy.deepcopy(thread["sources"][:length])
            context = {"window": window, "sources": sources, "bindings": copy.deepcopy(thread["bindings"]), "topics": copy.deepcopy(thread["topics"])}
            context["binding_index"] = {b["id"]: b for b in context["bindings"]}
            context["source_index"] = {s["id"]: s for s in sources}
            if len(context["binding_index"]) != 3 or any(not set(ids) <= context["binding_index"].keys() for ids in context["topics"].values()):
                raise ValueError("binding/topic premise mismatch")
            referenced = {ref for s in sources for ref in ([s["replyTo"]] if s["replyTo"] else []) + s["derivedFrom"]}
            context["unavailable_reference_ids"] = sorted(referenced - context["source_index"].keys())
            if not set(context["unavailable_reference_ids"]) <= {"absent-parent"}:
                raise ValueError("unexpected missing parent")
            value = {"ledger": [], "extractionLimits": []}
            for source in sources:
                proposed = thread["reference"].get(source["id"], {"atoms": [], "annotations": []})
                value["ledger"].append({"span": source["id"], "atoms": copy.deepcopy(proposed["atoms"]), "conditions": [], "annotations": copy.deepcopy(proposed["annotations"]), "rationale": "Authored development interpretation, not a model response or human gold."})
            packet = {"id": key + "/" + window, "thread": key, "context": context, "reference": value, "queries": copy.deepcopy(thread["queries"])}
            packet["ledger_schema"] = meaning.schema_for(data, context)
            packet["audit_schema"] = audit.specialize(data["auditReportV2"], list(context["binding_index"]), list(context["source_index"]))
            compiled = compile_value(value, packet)
            if compiled["core"]["rejected"] or compiled["rejected_annotations"]:
                raise ValueError("reference fails mechanical checks: " + packet["id"])
            meaning.check_projection(compiled, context)
            for query in packet["queries"]:
                if core.evaluate(compiled["core"], query["binding"], query["value"])["state"] != query["expected"][window]:
                    raise ValueError("reference state mismatch: " + packet["id"])
            if window == "w1":
                packet["control"] = controls(packet, thread["control"])
            packets.append(packet)
    packets.sort(key=lambda p: (prior.multi.pilot.digest([plan["orderSeed"], p["thread"]]), p["context"]["window"]))
    frozen = {"plan": plan, "contract": copy.deepcopy(data["meaningContract"]), "audit_contract": copy.deepcopy(data["auditReportV2"]),
              "packets": packets, "planned_calls": len(packets) * 3 + sum("control" in p for p in packets),
              "limits": {"budget_usd": float(budget), "max_calls": calls, "retries": 0},
              "review": {"original_hashes": review.fingerprints(reviewed), "original_decisions": review.approval_status(reviewed), "transfer_hashes": review.fingerprints(transferred), "transfer_decisions": transfer_review.load_decisions(), "scope": "Reviewed development examples only; broader policy is not separately approved."},
              "execution_authorization": {"summary_not_verbatim": "The user authorized proceeding with the proposed comparison before preparation; a later account top-up does not change the limits.", "scope": "The preceding proposal: twelve fresh sixteen-message threads, two checkpoints, 84 fixed calls, $5 local ceiling. No retry or canonical changes."},
              "implementation_sha256": {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((prior.multi.ROOT / "scripts").glob("*.py"))},
              "metadata": metadata,
              "flake_lock_sha256": hashlib.sha256((prior.multi.ROOT / "flake.lock").read_bytes()).hexdigest()}
    if frozen["planned_calls"] != calls:
        raise ValueError("schedule exceeds limits")
    return {"protocol": {"sha256": prior.multi.pilot.digest(frozen), "frozen": frozen}, "source_commit": prior.multi.pilot.source_commit(), "status": "prepared", "trace": [], "requests": [], "rows": [{"id": p["id"]} for p in packets]}


def role_context(packet, frozen):
    context = packet["context"]
    return {"common_contract": frozen["contract"], "current_window": context["window"], "bindings": context["bindings"], "procedure_topics": context["topics"], "original_sources": context["sources"], "unavailable_reference_ids": context["unavailable_reference_ids"], "boundary": "Supplied source window only; model proposals/checks are not new source evidence or verified truth."}


def operation(packet, row, role, frozen):
    state = role_context(packet, frozen)
    auditing = role in {"auditor", "control"}
    if auditing:
        proposals = packet["control"]["proposals"] if role == "control" else row
        state["audit_reporting_contract"] = frozen["audit_contract"]["instructions"]
        state["untrusted_proposals"] = {}
        for name in ROLES[:2]:
            proposal = prior.value_of(proposals, name)
            compiled = proposals.get(name, {}).get("compiled")
            state["untrusted_proposals"][name] = {"availability": proposal is not None, "proposal": proposal,
                "mechanical_checker_output_not_a_model_statement": None if compiled is None else {"rejected_atoms": compiled["core"]["rejected"], "rejected_annotations": compiled["rejected_annotations"], "declared_topic_lowerings": compiled["lowerings"]}}
    binding = frozen["plan"]["roles"][role]
    payload = {"model": binding["model"], "provider": prior.multi.split.provider(binding), "max_tokens": frozen["plan"]["maxOutputTokens"],
               "response_format": {"type": "json_schema", "json_schema": {"name": "larger_source_interpretation", "strict": True, "schema": packet["audit_schema" if auditing else "ledger_schema"]["json"]}},
               "messages": [{"role": "system", "content": frozen["plan"]["audit" if auditing else "extract"]}, {"role": "user", "content": json.dumps(state, sort_keys=True)}]}
    if not auditing:
        payload["temperature"] = 0
    if role == "verifier":
        payload["reasoning"] = {"max_tokens": 2048, "exclude": True}
    elif auditing:
        payload["reasoning"] = {"effort": "medium", "exclude": True}
    return {"kind": role, "sample": packet["id"], "endpoint": prior.multi.split.CHAT_ENDPOINT, "payload": payload}


def parse_response(response, op):
    requested, served = op["payload"]["model"], response.get("model", "")
    if not isinstance(served, str) or not (served == requested or served.startswith(requested + "-")) or response["choices"][0]["finish_reason"] != "stop":
        raise OutputFailure("unexpected model or unfinished output")
    return json.loads(response["choices"][0]["message"]["content"])


def masks(packet, row):
    context = packet["context"]
    primary, verifier = (compiled_of(row, r) for r in ROLES[:2])
    flags = {arm: {b: [] for b in context["binding_index"]} for arm in ("single", "blind-check", "panel")}
    if primary is None:
        return {arm: {b: ["primary-unavailable"] for b in context["binding_index"]} for arm in flags}
    for b in context["binding_index"]:
        flags["single"][b] = meaning.project(primary, context, b, "diagnostic")["mechanical_flags"]
        flags["blind-check"][b] = flags["single"][b][:]
    if verifier is None:
        for reasons in flags["blind-check"].values():
            reasons.append("verifier-unavailable")
    else:
        a, b = profile(primary, context), profile(verifier, context)
        for binding in a:
            flags["blind-check"][binding] += ["verifier-mechanical"] if meaning.project(verifier, context, binding, "diagnostic")["mechanical_flags"] else []
            if a[binding] != b[binding]:
                flags["blind-check"][binding].append("material-profile-disagreement")
    for b in context["binding_index"]:
        flags["panel"][b] = flags["blind-check"][b][:]
    projected = audit.project(prior.value_of(row, "auditor"), packet["audit_schema"], {r: prior.value_of(row, r) is not None for r in ROLES[:2]})
    for binding, result in projected.items():
        if any(result["audit_blocks"].values()):
            flags["panel"][binding].append("audit-material-unclear-or-unavailable")
    return flags


def summarize(report):
    frozen = report["protocol"]["frozen"]
    result = {"planned_calls": frozen["planned_calls"], "submitted_calls": len(report["trace"]), "snapshot_denominator": len(frozen["packets"]), "complete_real_snapshots": 0, "complete_evaluations": 0,
              "roles": {r: {"planned": len(frozen["packets"]), "valid": 0, "unavailable_binding_units": 0, "binding_units": 0, "profile_matches": 0, "missing_memberships": 0, "extra_memberships": 0, "mechanical_rejections": 0, "query_cells": 0, "query_matches": 0, "unsupported_support": 0, "missing_support": 0, "spurious_opposition": 0, "missing_opposition": 0, "note_difference_snapshots": 0} for r in ROLES[:2]},
              "arms": {a: {"binding_units": 0, "unavailable_primary": 0, "discrepant_flagged": 0, "discrepant_unflagged": 0, "reference_matching_flagged": 0, "reference_matching_eligible": 0} for a in ("single", "blind-check", "panel")},
              "audit": {"planned_role_binding_assessments": 0, "discrepant_assessed": 0, "coincident_material_challenges": 0, "reference_matching_assessed": 0, "proposed_false_challenges": 0, "unavailable_assessments": 0},
              "controls": {"planned": 0, "valid": 0, "fault_bindings_planned": 0, "fault_bindings_assessed": 0, "faults_both_challenged": 0, "faithful_role_bindings_assessed": 0, "proposed_false_challenges": 0}, "cases": {}}
    for packet, row in zip(frozen["packets"], report["rows"]):
        context = packet["context"]
        expected_compiled = compile_value(reference(packet), packet)
        expected = profile(expected_compiled, context)
        fidelity, states = {}, {}
        for role in ROLES[:2]:
            compiled = compiled_of(row, role)
            actual = profile(compiled, context) if compiled is not None else None
            counts = result["roles"][role]
            counts["valid"] += compiled is not None
            counts["binding_units"] += len(expected)
            counts["unavailable_binding_units"] += len(expected) if actual is None else 0
            counts["mechanical_rejections"] += len(compiled["core"]["rejected"]) + len(compiled["rejected_annotations"]) if compiled else 0
            counts["note_difference_snapshots"] += compiled is not None and note_profile(compiled) != note_profile(expected_compiled)
            fidelity[role] = {b: actual[b] == values if actual is not None else None for b, values in expected.items()}
            for b, values in expected.items():
                counts["profile_matches"] += fidelity[role][b] is True
                if actual is not None:
                    counts["missing_memberships"] += len(values - actual[b])
                    counts["extra_memberships"] += len(actual[b] - values)
            states[role] = {}
            for query in packet["queries"]:
                state = core.evaluate(compiled["core"], query["binding"], query["value"])["state"] if compiled else "unavailable"
                wanted = query["expected"][context["window"]]
                states[role][query["id"]] = state
                counts["query_cells"] += 1
                counts["query_matches"] += state == wanted
                if compiled:
                    pos, want_pos = state in {"supported", "contested"}, wanted in {"supported", "contested"}
                    neg, want_neg = state in {"opposed", "contested"}, wanted in {"opposed", "contested"}
                    counts["unsupported_support"] += pos and not want_pos
                    counts["missing_support"] += want_pos and not pos
                    counts["spurious_opposition"] += neg and not want_neg
                    counts["missing_opposition"] += want_neg and not neg
        flags = masks(packet, row)
        for arm, bindings in flags.items():
            counts = result["arms"][arm]
            for b, reasons in bindings.items():
                counts["binding_units"] += 1
                faithful = fidelity["interpreter"][b]
                if faithful is None:
                    counts["unavailable_primary"] += 1
                elif not faithful:
                    counts["discrepant_flagged" if reasons else "discrepant_unflagged"] += 1
                else:
                    counts["reference_matching_flagged" if reasons else "reference_matching_eligible"] += 1
        judged = prior.value_of(row, "auditor")
        checks = {c["binding"]: c for c in judged["checks"]} if judged else {}
        for b in expected:
            for role in ROLES[:2]:
                counts = result["audit"]
                counts["planned_role_binding_assessments"] += 1
                verdict = checks.get(b, {}).get(role, "unavailable")
                if verdict in {"unclear", "unavailable"} or fidelity[role][b] is None:
                    counts["unavailable_assessments"] += 1
                elif fidelity[role][b]:
                    counts["reference_matching_assessed"] += 1
                    counts["proposed_false_challenges"] += verdict == "material-error"
                else:
                    counts["discrepant_assessed"] += 1
                    counts["coincident_material_challenges"] += verdict == "material-error"
        if "control" in packet:
            counts = result["controls"]
            counts["planned"] += 1
            counts["fault_bindings_planned"] += len(packet["control"]["fault_bindings"])
            controlled = prior.value_of(row, "control")
            counts["valid"] += controlled is not None
            if controlled:
                for check in controlled["checks"]:
                    if check["binding"] in packet["control"]["fault_bindings"]:
                        counts["fault_bindings_assessed"] += 1
                        counts["faults_both_challenged"] += all(check[r] == "material-error" for r in ROLES[:2])
                    else:
                        for role in ROLES[:2]:
                            counts["faithful_role_bindings_assessed"] += check[role] not in {"unclear", "unavailable"}
                            counts["proposed_false_challenges"] += check[role] == "material-error"
        complete = all(prior.value_of(row, r) is not None for r in ROLES)
        result["complete_real_snapshots"] += complete
        result["complete_evaluations"] += complete and ("control" not in packet or prior.value_of(row, "control") is not None)
        result["cases"][packet["id"]] = {"fidelity": fidelity, "states": states, "flags": flags}
    roles = {r: {"submitted": 0, "known_usd": 0.0, "unknown_billing": 0} for r in (*ROLES, "control")}
    for record in report["trace"]:
        cost = roles[record["kind"]]
        cost["submitted"] += 1
        if "accounted_usd" in record:
            cost["known_usd"] += record["accounted_usd"]
        else:
            cost["unknown_billing"] += 1
    i, v, a, c = (roles[r]["known_usd"] for r in (*ROLES, "control"))
    result["costs"] = {"roles": roles, "known_total_usd": i + v + a + c, "known_arms_usd": {"single": i, "blind-check": i + v, "panel": i + v + a}, "accounted_or_reserved_usd": report.get("accounted_or_reserved_usd")}
    transitions = {a: {"paired_bindings": 0, "unchanged_profiles": 0, "unchanged_matching_eligible": 0, "unchanged_matching_flagged": 0, "unchanged_discrepant": 0, "unchanged_unavailable": 0, "state_changes": 0, "state_pair_matches": 0} for a in result["arms"]}
    packets = {p["id"]: p for p in frozen["packets"]}
    for packet in frozen["packets"]:
        if packet["context"]["window"] != "w0":
            continue
        final = packets[packet["thread"] + "/w1"]
        before = profile(compile_value(reference(packet), packet), packet["context"])
        after = profile(compile_value(reference(final), final), final["context"])
        old, new = result["cases"][packet["id"]], result["cases"][final["id"]]
        for arm, counts in transitions.items():
            for b in before:
                counts["paired_bindings"] += 1
                if before[b] == after[b]:
                    counts["unchanged_profiles"] += 1
                    faithful = new["fidelity"]["interpreter"][b]
                    if faithful is None:
                        counts["unchanged_unavailable"] += 1
                    elif not faithful:
                        counts["unchanged_discrepant"] += 1
                    else:
                        counts["unchanged_matching_flagged" if new["flags"][arm][b] else "unchanged_matching_eligible"] += 1
            for query in packet["queries"]:
                if query["expected"]["w0"] != query["expected"]["w1"]:
                    counts["state_changes"] += 1
                    counts["state_pair_matches"] += old["states"]["interpreter"][query["id"]] == query["expected"]["w0"] and new["states"]["interpreter"][query["id"]] == query["expected"]["w1"]
    result["transitions"] = transitions
    return result


def run(report, checkpoint, sender=None):
    frozen = report["protocol"]["frozen"]
    if report["status"] != "prepared" or report["trace"] or report["requests"] or prior.multi.pilot.digest(frozen) != report["protocol"]["sha256"] or report["rows"] != [{"id": p["id"]} for p in frozen["packets"]]:
        raise ValueError("changed or previously attempted scale comparison")
    if sender is None:
        sender = deadline_transport.ledger_sender(report, checkpoint, timeout=frozen["plan"]["transportTimeoutSeconds"], maximum=frozen["plan"]["maxResponseBytes"], max_request_bytes=frozen["plan"]["maxRequestBytes"])
    ledger = prior.multi.split.Ledger(report, checkpoint, sender=sender)
    report["status"] = "running"
    try:
        for packet, row in zip(frozen["packets"], report["rows"]):
            for role in (*ROLES, *(["control"] if "control" in packet else [])):
                op = operation(packet, row, role, frozen)
                report["requests"].append(copy.deepcopy(op))
                stage = row[role] = {"status": "pending-request", "source_context_sha256": prior.multi.pilot.digest(role_context(packet, frozen))}
                checkpoint()
                count = len(report["trace"])
                try:
                    response = ledger.submit(op)
                except ValueError:
                    stage["status"] = "call-failed" if len(report["trace"]) > count else "not-attempted"
                    raise
                stage["status"] = "invalid"
                try:
                    value = parse_response(response, op)
                    if role in ROLES[:2]:
                        stage["compiled"] = compile_value(value, packet)
                        meaning.check_projection(stage["compiled"], packet["context"])
                        stage["reader_views"] = {q["binding"]: {consumer: meaning.project(stage["compiled"], packet["context"], q["binding"], q["value"], consumer=consumer) for consumer in ("fact", "evidence-use")} for q in packet["queries"]}
                    else:
                        availability = {r: prior.value_of(packet["control"]["proposals"] if role == "control" else row, r) is not None for r in ROLES[:2]}
                        audit.validate(value, packet["audit_schema"], availability)
                    stage.update(value=value, status="valid")
                except (ValueError, KeyError, TypeError, IndexError, AttributeError, OverflowError):
                    stage["status"] = "invalid"
                    stage["failure_reason"] = "validation or conditional compilation failed; no replacement"
                checkpoint()
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
    parser.add_argument("--protocol-sha256")
    parser.add_argument("--budget-usd", type=float, default=5.0)
    parser.add_argument("--max-calls", type=int, default=84)
    args = parser.parse_args(argv)
    path, report, owned = Path(args.output), None, False
    try:
        if path.exists():
            raise ValueError("output exists")
        report = prepare(prior.multi.export_cue(sorted(prior.DIRECTORY.glob("*.cue"))), args.budget_usd, args.max_calls)
        if args.live and args.protocol_sha256 != report["protocol"]["sha256"]:
            raise ValueError("explicit frozen digest required")
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("x") as stream:
            owned = True
            stream.write(json.dumps(report, indent=2, allow_nan=False) + "\n")
        if args.live:
            run(report, lambda: prior.multi.pilot.checkpoint(path, report))
        print(json.dumps({"output": str(path), "status": report["status"], "protocol_sha256": report["protocol"]["sha256"], "calls": len(report["trace"]), "summary": report.get("summary")}, indent=2))
        return 0
    except (ValueError, KeyError, TypeError, OSError, OverflowError, subprocess.CalledProcessError):
        if owned:
            report["status"] = "stopped-no-retry"
            report["summary"] = summarize(report)
            prior.multi.pilot.checkpoint(path, report)
        print("Scale comparison stopped or output exists. No retry, repair, fallback, or automatic continuation.")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
