"""A separate, frozen schema-language control on saved reconciliation contexts."""

import argparse
import copy
import gzip
import hashlib
import json
from pathlib import Path
import subprocess

from scripts import evidence_expansion as expansion
from scripts.evaluation_client import validate_contract, OutputFailure

BASELINE = expansion.DIRECTORY / "results/first-evidence-expansion.json.gz"


def rename_schema(old, plan):
    schema = copy.deepcopy(old)
    item = schema["properties"]["proofs"]["items"]
    mapping = {"positive": "supports_hypothesis", "negative": "incompatible_fact_spans"}
    fields = {mapping.get(key, key): value for key, value in item["properties"].items()}
    item["properties"] = fields
    fields["supports_hypothesis"]["description"] = plan["supportDescription"]
    fields["incompatible_fact_spans"]["description"] = plan["incompatibleDescription"]
    item["required"] = [mapping.get(key, key) for key in item["required"]]
    fields["rationale"]["description"] = "Explain witness direction relative to the selected unchanged hypothesis P, not merely why your summary is justified."
    return schema


def prepare(data, budget=0.5, calls=12):
    plan = copy.deepcopy(data["directionPlan"])
    if not expansion.multi.is_number(budget) or not 0 < budget <= plan["maxBudgetUSD"] or type(calls) is not int or not 1 <= calls <= plan["maxCalls"]:
        raise ValueError("invalid control limits")
    compressed = BASELINE.read_bytes()
    if hashlib.sha256(compressed).hexdigest() != plan["baselineArchiveSHA256"]:
        raise ValueError("baseline archive changed")
    baseline = json.loads(gzip.decompress(compressed))
    if baseline["status"] != "completed" or expansion.multi.pilot.digest(baseline["protocol"]["frozen"]) != baseline["protocol"]["sha256"]:
        raise ValueError("baseline incomplete or changed")
    families = {family["id"]: family for family in baseline["protocol"]["frozen"]["families"]}
    cases = {branch["id"]: (family, branch) for family in families.values() for branch in family["branches"]}
    old_rows = {row["id"]: row for root in baseline["families"] for row in root["branches"]}
    items = []
    for old_op in baseline["requests"]:
        if old_op["kind"] != "reconciled":
            continue
        family, branch = cases[old_op["sample"]]
        payload = copy.deepcopy(old_op["payload"])
        binding = plan["roles"]["direction"]
        if payload["model"] != binding["model"] or payload["provider"] != expansion.multi.split.provider(binding):
            raise ValueError("control cannot change role or provider")
        schema = rename_schema(payload["response_format"]["json_schema"]["schema"], plan)
        payload["response_format"]["json_schema"]["schema"] = schema
        payload["messages"][0]["content"] += "\n" + plan["instructions"]
        items.append({"id": old_op["sample"], "family": family, "branch": branch,
                      "baseline_compiled": old_rows[old_op["sample"]]["reconciled"].get("compiled"),
                      "schema": schema, "compiled_schema": expansion.multi.compile_schema(json.dumps(schema, sort_keys=True)),
                      "operation": {"kind": "direction", "sample": old_op["sample"], "endpoint": old_op["endpoint"], "payload": payload},
                      "baseline_request_sha256": hashlib.sha256(json.dumps(old_op["payload"], allow_nan=False).encode()).hexdigest()})
    limits = baseline["protocol"]["frozen"]["limits"]
    if len(items) != 12 or len(items) > calls or len(baseline["trace"]) + len(items) > limits["max_calls"] or baseline["accounted_or_reserved_usd"] + budget > limits["budget_usd"]:
        raise ValueError("control exceeds remaining investigation limits")
    names = ("evidence_direction.py", "evidence_expansion.py", "evidence_graph.py", "jev_multipass.py", "split_judgment.py", "evaluation_client.py")
    frozen = {"plan": plan, "items": items, "limits": {"budget_usd": float(budget), "max_calls": calls, "retries": 0},
              "baseline_archive_sha256": hashlib.sha256(compressed).hexdigest(), "baseline_protocol_sha256": baseline["protocol"]["sha256"],
              "baseline_calls": len(baseline["trace"]), "baseline_reported_cost_usd": baseline["accounted_or_reserved_usd"],
              "implementation_sha256": {name: hashlib.sha256((expansion.ROOT / "scripts" / name).read_bytes()).hexdigest() for name in names}}
    return {"protocol": {"sha256": expansion.multi.pilot.digest(frozen), "frozen": frozen}, "source_commit": expansion.multi.pilot.source_commit(),
            "status": "prepared", "trace": [], "rows": [{"id": item["id"], "status": "not-attempted"} for item in items],
            "warning": "Post-observation schema-language control on development fixtures; original outputs unchanged. Not independent evaluation or canonical acceptance."}


def summarize(report):
    result = {"planned": len(report["rows"]), "submitted": len(report["trace"]), "invalid": 0, "states_compared": 0,
              "baseline_matches_proposed": 0, "control_matches_proposed": 0, "cases": {}}
    for item, row in zip(report["protocol"]["frozen"]["items"], report["rows"]):
        result["invalid"] += row["status"] == "invalid"
        current = row.get("compiled", {})
        baseline = item["baseline_compiled"] or {}
        expected = item["branch"]["expected"]
        for key, label in expected.items():
            result["states_compared"] += 1
            result["baseline_matches_proposed"] += baseline.get(key, {}).get("guarded_state") == label
            result["control_matches_proposed"] += current.get(key, {}).get("guarded_state") == label
        result["cases"][item["id"]] = {"expected_provisional": expected, "baseline": {key: value["guarded_state"] for key, value in baseline.items()},
                                         "control": {key: value["guarded_state"] for key, value in current.items()}, "status": row["status"]}
    return result


def run(report, checkpoint, sender=None):
    frozen = report["protocol"]["frozen"]
    if report["status"] != "prepared" or report["trace"] or expansion.multi.pilot.digest(frozen) != report["protocol"]["sha256"] or report["rows"] != [{"id": item["id"], "status": "not-attempted"} for item in frozen["items"]]:
        raise ValueError("changed or previously attempted control")
    if sender is None:
        sender = expansion.multi.bounded_transport
    ledger = expansion.multi.split.Ledger(report, checkpoint, sender=sender)
    report["status"] = "running"
    for item, row in zip(frozen["items"], report["rows"]):
        row["status"] = "submitted"
        checkpoint()
        try:
            response = ledger.submit(item["operation"])
        except ValueError:
            row["status"] = "call-failed"
            report["status"] = "stopped-no-retry"
            report["summary"] = summarize(report)
            checkpoint()
            raise
        row["status"] = "invalid"
        try:
            choice = response["choices"][0]
            model = response.get("model", "")
            requested = item["operation"]["payload"]["model"]
            if not (model == requested or model.startswith(requested + "-")) or choice["finish_reason"] != "stop":
                raise OutputFailure("unexpected model or incomplete output")
            value = json.loads(choice["message"]["content"])
            row["raw_new_schema_output"] = value
            validate_contract(item["compiled_schema"], "#Report", json.dumps(value, sort_keys=True))
            ids = {hypothesis["id"] for hypothesis in item["family"]["hypotheses"]}
            if len(value["proofs"]) != len(ids) or {proof["id"] for proof in value["proofs"]} != ids:
                raise OutputFailure("proof membership")
            if not value["summary"].strip() or any(not proof["rationale"].strip() for proof in value["proofs"]):
                raise OutputFailure("empty summary or rationale")
            mapped = copy.deepcopy(value)
            for proof in mapped["proofs"]:
                proof["positive"] = proof.pop("supports_hypothesis")
                proof["negative"] = proof.pop("incompatible_fact_spans")
                if any(len(set(proof[key])) != len(proof[key]) for key in ("positive", "negative")):
                    raise OutputFailure("duplicate witnesses")
            row["slot_mapping_only"] = mapped
            row["compiled"] = expansion.compile_report(mapped, item["family"], item["branch"]["after"])
            row["status"] = "valid"
        except (ValueError, KeyError, TypeError, IndexError, AttributeError):
            row["failure_reason"] = "control output invalid; no replacement"
        checkpoint()
    report["status"] = "completed"
    report["summary"] = summarize(report)
    checkpoint()
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True)
    parser.add_argument("--live", action="store_true")
    args = parser.parse_args(argv)
    path, report, owned = Path(args.output), None, False
    try:
        if path.exists():
            raise ValueError("output exists")
        data = expansion.multi.export_cue(sorted(expansion.DIRECTORY.glob("*.cue")))
        report = prepare(data)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("x") as stream:
            owned = True
            stream.write(json.dumps(report, indent=2, allow_nan=False) + "\n")
        if args.live:
            run(report, lambda: expansion.multi.pilot.checkpoint(path, report))
        print(json.dumps({"output": str(path), "status": report["status"], "protocol_sha256": report["protocol"]["sha256"], "calls": len(report["trace"]),
                          "accounted_or_reserved_usd": report.get("accounted_or_reserved_usd"), "summary": report.get("summary")}, indent=2))
        return 0
    except (ValueError, KeyError, TypeError, OSError, subprocess.CalledProcessError):
        if owned:
            report["status"] = "stopped-no-retry"
            report["summary"] = summarize(report)
            expansion.multi.pilot.checkpoint(path, report)
        print("Direction control stopped or output exists; no retry and no original result changed.")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
