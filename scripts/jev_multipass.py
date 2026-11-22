"""Fixed-depth Jev evidence investigation; no convergence loop or canonical writes."""

import argparse
import copy
import functools
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
import time
import urllib.error
import urllib.request

from scripts import calibration_pilot as pilot, split_judgment as split
from scripts.evaluation_client import OutputFailure, validate_contract
from scripts.jev_probe import NoRedirect, export_cue, is_number

ROOT = split.calibration.ROOT
DIRECTORY = ROOT / "experiments/judgment"
PASSES = ("direct", "atoms", "analyst", "skeptic", "recheck", "order", "repeat")
RELATIONS = {"supported", "contradicted", "not-established", "meta", "uncertain"}


@functools.lru_cache(maxsize=64)
def compile_schema(encoded):
    schema = json.loads(encoded)
    schema["$schema"] = "http://json-schema.org/draft-07/schema#"
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "schema.json"
        path.write_text(json.dumps(schema))
        result = subprocess.run(["cue", "import", "jsonschema", str(path), "-o", "-"], check=True, capture_output=True, text=True)
    return "package judgment\n#Report: {\n" + result.stdout + "\n}\n"


def specialize_schema(base, claims, spans):
    schema = copy.deepcopy(base)
    properties = schema["properties"]
    properties["claims"]["items"]["properties"]["id"]["enum"] = list(claims)
    properties["claims"]["items"]["properties"]["evidence"]["items"]["enum"] = list(spans)
    properties["issues"]["items"]["properties"]["claim"]["enum"] = [*claims, "whole"]
    properties["issues"]["items"]["properties"]["evidence"]["items"]["enum"] = list(spans)
    return schema


def packets(data):
    result = []
    for family_id, family in sorted(data["families"].items()):
        if not family["candidate"].strip():
            raise ValueError("blank candidate")
        if len(family["variants"]) < 2:
            raise ValueError("counterfactual family needs multiple worlds")
        for variant_id, variant in sorted(family["variants"].items()):
            sources = copy.deepcopy(family["base"] + variant["extra"])
            ids = [source["id"] for source in sources]
            if len(ids) != len(set(ids)):
                raise ValueError("duplicate source identity inside packet")
            spans = {source["id"] + "-" + sentence["id"]: {"source": source["id"], "text": sentence["text"]}
                     for source in sources for sentence in split.sentences(source["text"])}
            claims = {"c" + str(index): sentence["text"] for index, sentence in enumerate(split.sentences(family["candidate"]))}
            schema = specialize_schema(data["reportSchema"], claims, spans)
            result.append({"id": family_id + "/" + variant_id, "family": family_id, "variant": variant_id,
                           "candidate": family["candidate"], "claims": claims, "sources": sources, "spans": spans,
                           "reference": variant["reference"], "reference_reason": variant["reason"],
                           "schema": schema, "compiled_schema": compile_schema(json.dumps(schema, sort_keys=True)),
                           "packet_math": {"missing_reply_targets": sorted({source["replyTo"] for source in sources if "replyTo" in source} - set(ids)),
                                           "declared_origin_groups": sorted({source["origin"] for source in sources if "origin" in source}),
                                           "sources_without_declared_origin": [source["id"] for source in sources if "origin" not in source],
                                           "echo_edges": [[source["id"], parent] for source in sources for parent in source.get("derivedFrom", [])]}})
    return result


def prepare(data, budget=5, calls=140):
    plan = copy.deepcopy(data["plan"])
    if not is_number(budget) or not 0 < budget <= plan["maxBudgetUSD"] or type(calls) is not int or not 1 <= calls <= plan["maxCalls"] or plan["retries"] != 0:
        raise ValueError("invalid limits")
    cases = packets(data)
    if len(cases) * len(PASSES) > calls:
        raise ValueError("call limit cannot accommodate the fixed-depth plan")
    cases.sort(key=lambda packet: pilot.digest([plan["orderSeed"], packet["id"]]))
    names = ("jev_multipass.py", "split_judgment.py", "calibration_pilot.py", "calibration.py", "evaluation_client.py", "jev_probe.py", "workbench_models.py")
    frozen = {"plan": plan, "packets": cases, "passes": list(PASSES), "limits": {"budget_usd": budget, "max_calls": calls, "retries": 0},
              "implementation_sha256": {name: hashlib.sha256((ROOT / "scripts" / name).read_bytes()).hexdigest() for name in names},
              "metadata": {path.name: json.loads(path.read_text()) for path in sorted((DIRECTORY / "metadata").glob("*.json"))},
              "flake_lock_sha256": hashlib.sha256((ROOT / "flake.lock").read_bytes()).hexdigest()}
    return {"protocol": {"sha256": pilot.digest(frozen), "frozen": frozen}, "source_commit": pilot.source_commit(),
            "status": "prepared", "trace": [], "requests": [],
            "rows": [{"id": packet["id"], "family": packet["family"], "variant": packet["variant"], "reference": packet["reference"]} for packet in cases],
            "warning": "Fresh controlled synthetic fixtures with provisional references, not adjudicated human gold or population accuracy. No canonical effects."}


def state(packet, plan, reverse=False):
    return {"criterion": plan["criterion"], "candidate": packet["candidate"], "claims": copy.deepcopy(packet["claims"]),
            "authoritative_sources": copy.deepcopy(list(reversed(packet["sources"])) if reverse else packet["sources"]),
            "source_spans": copy.deepcopy(packet["spans"]), "packet_math": copy.deepcopy(packet["packet_math"])}


def proposals(row):
    return {kind: {"status": row[kind]["status"], "report": row[kind].get("value") if row[kind]["status"] == "valid" else None}
            for kind in ("direct", "atoms", "analyst", "skeptic") if kind in row}


def operation(packet, row, kind, plan):
    context = state(packet, plan, reverse=kind == "order")
    if kind in {"skeptic", "recheck"}:
        context["untrusted_analysis_proposals"] = proposals(row)
    role = plan["roles"][kind]
    if kind in {"analyst", "skeptic"}:
        payload = {"model": role["model"], "temperature": plan["temperature"], "max_tokens": plan["maxOutputTokens"],
                   "provider": split.provider(role),
                   "response_format": {"type": "json_schema", "json_schema": {"name": "evidence_audit", "strict": True, "schema": packet["schema"]}},
                   "messages": [{"role": "system", "content": plan[kind + "Instructions"]}, {"role": "user", "content": json.dumps(context, sort_keys=True)}]}
        endpoint = split.CHAT_ENDPOINT
    else:
        instruction = plan["jevInstructions"] + ("\n" + plan["recheckInstructions"] if kind == "recheck" else "")
        questions = {}
        if kind != "atoms":
            questions["verdict"] = {"type": "choice", "instructions": instruction + "\nAssess the whole candidate under the criterion.", "criteria": plan["verdictCriteria"]}
        if kind in {"atoms", "recheck"}:
            for claim_id in packet["claims"]:
                questions["relation-" + claim_id] = {"type": "choice", "instructions": instruction + "\nAssess only original claim " + claim_id + ".", "criteria": plan["relationCriteria"]}
                questions["anchor-" + claim_id] = {"type": "choice", "instructions": "Nominate one primary original-source exploration anchor for claim " + claim_id + ". This is not a complete proof bundle; use none when no anchor is appropriate.",
                                                   "criteria": {"none": "No single useful original-source anchor is appropriate.", **{span_id: "Original source span " + span_id + " in the supplied inventory." for span_id in packet["spans"]}}}
        payload = {"model": role["model"], "provider": split.provider(role), "state": context, "questions": questions}
        endpoint = split.DECISIONS
    return {"kind": kind, "sample": packet["id"], "endpoint": endpoint, "payload": payload}


def validate_response(response, op, packet):
    kind, requested = op["kind"], op["payload"]["model"]
    model = response.get("model", "")
    aliases = ("anthropic/claude-4.5-sonnet-20250929",) if requested == "anthropic/claude-sonnet-4.5" else ()
    if not isinstance(model, str) or not (model == requested or model.startswith(requested + "-") or model in aliases):
        raise OutputFailure("unexpected served model")
    if kind in {"analyst", "skeptic"}:
        choice = response["choices"][0]
        if choice["finish_reason"] != "stop":
            raise OutputFailure("truncated/refused audit")
        value = json.loads(choice["message"]["content"])
        validate_contract(packet["compiled_schema"], "#Report", json.dumps(value, sort_keys=True))
        if not value["rationale"].strip() or len(value["claims"]) != len(packet["claims"]) or {claim["id"] for claim in value["claims"]} != set(packet["claims"]):
            raise OutputFailure("empty audit or missing/duplicate claims")
        for claim in value["claims"]:
            if not claim["rationale"].strip() or len(set(claim["evidence"])) != len(claim["evidence"]):
                raise OutputFailure("empty rationale or duplicate anchors")
            if claim["kind"] == "world" and claim["relation"] == "meta":
                raise OutputFailure("world claim marked meta")
            if claim["kind"] == "world" and claim["relation"] in {"supported", "contradicted"} and not claim["evidence"]:
                raise OutputFailure("unanchored factual assessment")
        if any(not issue["problem"].strip() for issue in value["issues"]):
            raise OutputFailure("empty issue")
        return value
    answers = response["answers"]
    if set(answers) != set(op["payload"]["questions"]):
        raise OutputFailure("omitted/invented questions")
    for key, answer in answers.items():
        choices = op["payload"]["questions"][key]["criteria"]
        if answer.get("type") != "choice" or answer.get("choice") not in choices:
            raise OutputFailure("refusal or invalid typed choice")
        if answer.get("confidence") is not None and not is_number(answer["confidence"], maximum=1):
            raise OutputFailure("invalid diagnostic confidence")
        probabilities = answer.get("probabilities")
        if probabilities is not None and (not isinstance(probabilities, dict) or not set(probabilities) <= set(choices) or any(not is_number(p, maximum=1) for p in probabilities.values()) or abs(sum(probabilities.values()) - 1) > 0.02):
            raise OutputFailure("invalid probability vector")
    return answers


def decision(row, kind):
    stage = row.get(kind, {})
    if stage.get("status") != "valid":
        return stage.get("status", "not-attempted")
    value = stage["value"]
    if kind in {"analyst", "skeptic"}:
        return value["verdict"]
    if kind == "atoms":
        relations = [answer["choice"] for key, answer in value.items() if key.startswith("relation-")]
        return "fail" if any(relation in {"contradicted", "not-established"} for relation in relations) else "pass" if all(relation in {"supported", "meta"} for relation in relations) else "uncertain"
    return value["verdict"]["choice"]


def summarize(report):
    rows, cases = report["rows"], report["protocol"]["frozen"]["packets"]
    result = {"reference_status": "proposed-controlled-fixture-not-human-gold", "planned_packets": len(rows), "planned_calls": len(rows) * len(PASSES),
              "submitted_calls": len(report["trace"]), "per_pass": {}, "controls": {}, "families": {}}
    for kind in PASSES:
        matrix = {label: {} for label in ("pass", "fail", "uncertain")}
        for row in rows:
            label = decision(row, kind)
            matrix[row["reference"]][label] = matrix[row["reference"]].get(label, 0) + 1
        result["per_pass"][kind] = matrix
    for control in ("order", "repeat"):
        result["controls"][control] = {"stable": 0, "changed": 0, "unavailable": 0, "no_op": 0}
        for row in rows:
            packet = next(packet for packet in cases if packet["id"] == row["id"])
            if control == "order" and len(packet["sources"]) < 2:
                result["controls"][control]["no_op"] += 1
                continue
            a, b = decision(row, "direct"), decision(row, control)
            label = "unavailable" if a not in {"pass", "fail", "uncertain"} or b not in {"pass", "fail", "uncertain"} else "stable" if a == b else "changed"
            result["controls"][control][label] += 1
    for family in sorted({row["family"] for row in rows}):
        group = [row for row in rows if row["family"] == family]
        hashes = {hashlib.sha256(case["candidate"].encode()).hexdigest() for case in cases if case["family"] == family}
        result["families"][family] = {"same_candidate": len(hashes) == 1,
                                      "variants": {row["variant"]: {"reference": row["reference"], **{kind: decision(row, kind) for kind in PASSES}} for row in group}}
    result["adjudication_changes"] = [{"id": row["id"], "before": decision(row, "direct"), "after": decision(row, "recheck")} for row in rows if decision(row, "direct") != decision(row, "recheck")]
    result["analyst_skeptic_disagreements"] = [row["id"] for row in rows if decision(row, "analyst") != decision(row, "skeptic")]
    result["internal_pass_contradictions"] = []
    for row in rows:
        for kind in ("analyst", "skeptic", "recheck"):
            if decision(row, kind) != "pass":
                continue
            value = row[kind]["value"]
            relations = [claim["relation"] for claim in value["claims"]] if kind != "recheck" else [answer["choice"] for key, answer in value.items() if key.startswith("relation-")]
            if "contradicted" in relations or "not-established" in relations:
                result["internal_pass_contradictions"].append({"id": row["id"], "stage": kind})
    return result


def bounded_transport(endpoint, payload, token, timeout=120, maximum=1048576):
    request = urllib.request.Request(endpoint, data=json.dumps(payload).encode(), headers={"Authorization": "Bearer " + token, "Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.build_opener(NoRedirect).open(request, timeout=timeout) as response:
            raw = response.read(maximum + 1)
        if len(raw) > maximum:
            raise ValueError("response limit")
        return json.loads(raw)
    except (urllib.error.URLError, OSError, ValueError):
        raise ValueError("transport failed; body suppressed, no retry") from None


def run(report, checkpoint, sender=None):
    frozen = report["protocol"]["frozen"]
    if report["status"] != "prepared" or report["trace"] or report["requests"] or pilot.digest(frozen) != report["protocol"]["sha256"]:
        raise ValueError("changed/previously attempted protocol")
    expected = [{"id": packet["id"], "family": packet["family"], "variant": packet["variant"], "reference": packet["reference"]} for packet in frozen["packets"]]
    if report["rows"] != expected or frozen["passes"] != list(PASSES):
        raise ValueError("changed row identity or pass schedule")
    if sender is None:
        sender = lambda endpoint, payload, token: bounded_transport(endpoint, payload, token, frozen["plan"]["transportTimeoutSeconds"], frozen["plan"]["maxResponseBytes"])
    ledger = split.Ledger(report, checkpoint, sender=sender)
    report["status"] = "running"
    checkpoint()
    for packet, row in zip(frozen["packets"], report["rows"]):
        for kind in PASSES:
            op = operation(packet, row, kind, frozen["plan"])
            report["requests"].append(copy.deepcopy(op))
            stage = {"status": "pending-request"}
            row[kind] = stage
            checkpoint()
            before = len(report["trace"])
            started = time.monotonic()
            try:
                response = ledger.submit(op)
            except ValueError:
                stage["status"] = "call-failed" if len(report["trace"]) > before else "not-attempted"
                report["status"] = "stopped-no-retry"
                report["summary"] = summarize(report)
                checkpoint()
                raise
            stage["elapsed_seconds"] = round(time.monotonic() - started, 3)
            stage["status"] = "invalid"
            try:
                stage["value"] = validate_response(response, op, packet)
                stage["status"] = "valid"
            except (ValueError, KeyError, TypeError, IndexError, AttributeError, OverflowError):
                stage["failure_reason"] = "response failed structural/anchor validation; raw response retained, no replacement"
            checkpoint()
    report["status"] = "completed"
    report["summary"] = summarize(report)
    checkpoint()
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True)
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--budget-usd", type=float, default=5)
    parser.add_argument("--max-calls", type=int, default=140)
    args = parser.parse_args(argv)
    path, report, owned = Path(args.output), None, False
    try:
        if path.exists():
            raise ValueError("output exists")
        data = export_cue(sorted(DIRECTORY.glob("*.cue")))
        report = prepare(data, args.budget_usd, args.max_calls)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("x") as stream:
            owned = True
            stream.write(json.dumps(report, indent=2, allow_nan=False) + "\n")
        if args.live:
            run(report, lambda: pilot.checkpoint(path, report))
        print(json.dumps({"output": str(path), "status": report["status"], "protocol_sha256": report["protocol"]["sha256"],
                          "calls": len(report["trace"]), "accounted_or_reserved_usd": report.get("accounted_or_reserved_usd"), "summary": report.get("summary")}, indent=2))
        return 0
    except (ValueError, KeyError, TypeError, OSError, OverflowError, subprocess.CalledProcessError):
        if owned:
            report["status"] = "stopped-no-retry"
            report["summary"] = summarize(report)
            pilot.checkpoint(path, report)
        print("Multi-pass investigation stopped or output exists; no retry. Inspect the artifact. No canonical knowledge changed.")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
