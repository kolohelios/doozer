"""Prepare, or explicitly run, the ten approved judge-only development calls."""

import argparse
import copy
import hashlib
import json
from pathlib import Path
import os
import subprocess
import tempfile

from scripts import calibration
from scripts.evaluation_client import CallFailure, Client, Contracts, OutputFailure
from scripts.jev_probe import is_number
from scripts.workbench_models import transport


CONTRACT = calibration.DIRECTORY / "pilot.cue"


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode()).hexdigest()


def prepare(data, contracts, budget, max_calls):
    approval = data["pilotApproval"]
    if approval["status"] != "user-approved-development-reference" or approval["retries"] != 0:
        raise ValueError("explicit development approval required")
    if not is_number(budget) or not 0 < budget <= approval["maxBudgetUSD"] or type(max_calls) is not int or not 1 <= max_calls <= approval["maxCalls"]:
        raise ValueError("limits exceed user authorization")
    samples = calibration.contrast_samples(data)
    if {sample["id"] for sample in samples} != set(approval["labels"]):
        raise ValueError("approved sample membership changed")
    for sample in samples:
        reference = approval["labels"][sample["id"]]
        if sample["input_sha256"] != reference["inputSHA256"] or sample["draft_expected"] != reference["label"]:
            raise ValueError("approved input or reference label changed")
    plan = copy.deepcopy(data["pilotPlan"])
    samples.sort(key=lambda sample: digest([plan["orderSeed"], sample["id"]]))
    sources = ["calibration_pilot.py", "calibration.py", "evaluation_client.py", "workbench_models.py", "jev_probe.py"]
    frozen = {"plan": plan, "approval": copy.deepcopy(approval), "contract": contracts.schema,
              "limits": {"budget_usd": budget, "max_calls": max_calls, "retries": 0},
              "samples": [{"id": sample["id"], "cohort": sample["cohort"],
                           "reference": sample["draft_expected"], "judge_input": sample["judge_input"],
                           "input_sha256": sample["input_sha256"]} for sample in samples],
              "implementation_sha256": {name: hashlib.sha256((calibration.ROOT / "scripts" / name).read_bytes()).hexdigest() for name in sources}}
    return {"protocol": {"sha256": digest(frozen), "frozen": frozen}, "status": "prepared", "trace": [],
            "rows": [{"id": sample["id"], "cohort": sample["cohort"], "reference": sample["draft_expected"],
                      "status": "not-attempted"} for sample in samples],
            "warning": "Authored development controls, not held-out accuracy or evidence of autonomous reconciliation."}


def validate_judgment(value, context):
    if not value["rationale"].strip():
        raise OutputFailure("empty rationale")
    quotes = value["answerQuotes"]
    if value["result"] == "pass" and not quotes:
        raise OutputFailure("pass without answer evidence")
    if any(not quote.strip() or quote not in context["candidate"] for quote in quotes):
        raise OutputFailure("misquoted candidate")
    sources = {source["id"]: source for source in context["authoritative_sources"]}
    for cite in value["citations"]:
        if cite["source"] not in sources or not cite["quote"].strip() or cite["quote"] not in sources[cite["source"]]["text"]:
            raise OutputFailure("misquoted authoritative evidence")


def summarize(rows):
    result = {}
    for cohort in ("primary", "robustness"):
        group = [row for row in rows if row["cohort"] == cohort]
        counts = {reference: {label: 0 for label in ("pass", "fail", "uncertain")} for reference in ("pass", "fail")}
        mismatches = []
        for row in group:
            if row["status"] == "judged":
                label = row["judgment"]["result"]
                counts[row["reference"]][label] += 1
                if label != row["reference"]:
                    mismatches.append(row["id"])
        result[cohort] = {"planned": len(group), "judged": sum(row["status"] == "judged" for row in group),
                          "invalid": sum(row["status"] == "invalid-output-no-replacement" for row in group),
                          "not_attempted": sum(row["status"] == "not-attempted" for row in group),
                          "call_failed": sum(row["status"] == "call-failed" for row in group),
                          "reference_by_judge": counts, "disagreements_or_abstentions": mismatches}
    return result


def run(report, client, checkpoint):
    frozen = report["protocol"]["frozen"]
    if digest(frozen) != report["protocol"]["sha256"] or report["status"] != "prepared":
        raise ValueError("protocol changed or run already attempted; no resume/retry mode")
    expected_rows = [{"id": sample["id"], "cohort": sample["cohort"], "reference": sample["reference"], "status": "not-attempted"} for sample in frozen["samples"]]
    if report["rows"] != expected_rows or report["trace"]:
        raise ValueError("prepared row identities or statuses changed")
    limits = frozen["limits"]
    if client.plan != frozen["plan"] or client.budget != limits["budget_usd"] or client.max_calls != limits["max_calls"] or client.contracts.schema != frozen["contract"]:
        raise ValueError("client binding differs from frozen protocol")
    report["status"] = "running"
    report["trace"] = client.trace
    checkpoint()
    for sample, row in zip(frozen["samples"], report["rows"]):
        row["status"] = "submitted"
        checkpoint()
        try:
            value = client.call("judge", "#PilotJudgment", sample["judge_input"], sample["id"])
            row["judgment"] = client.redact(value)
            validate_judgment(value, sample["judge_input"])
            row["status"] = "judged"
        except OutputFailure as error:
            row["status"] = "invalid-output-no-replacement"
            row["failure_reason"] = str(error)
        except CallFailure:
            row["status"] = "call-failed"
            report["status"] = "stopped-no-retry"
            checkpoint()
            break
        checkpoint()
    else:
        report["status"] = "completed"
    report["summary"] = summarize(report["rows"])
    report["accounted_or_reserved_usd"] = client.spent
    checkpoint()
    return report


def checkpoint(path, report):
    encoded = json.dumps(report, indent=2, allow_nan=False) + "\n"
    with tempfile.NamedTemporaryFile(mode="w", dir=path.parent, delete=False) as stream:
        temporary = Path(stream.name)
        try:
            stream.write(encoded)
            stream.flush()
            os.fsync(stream.fileno())
        except BaseException:
            temporary.unlink(missing_ok=True)
            raise
    os.replace(temporary, path)


def source_commit():
    try:
        result = subprocess.run(["jj", "log", "-r", "@", "--no-graph", "-T", "commit_id"], capture_output=True, text=True)
        return result.stdout.strip() if result.returncode == 0 else None
    except OSError:
        return None  # Nix's offline source snapshot need not contain a VCS checkout.


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True)
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--budget-usd", type=float, default=0.10)
    parser.add_argument("--max-calls", type=int, default=10)
    args = parser.parse_args(argv)
    report, path, owned = None, Path(args.output), False
    try:
        if path.exists():
            raise ValueError("output exists")
        data, _, _ = calibration.load()
        contracts = Contracts(CONTRACT)
        report = prepare(data, contracts, args.budget_usd, args.max_calls)
        report["source_commit"] = source_commit()
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("x") as stream:
            owned = True
            stream.write(json.dumps(report, indent=2, allow_nan=False) + "\n")
        if args.live:
            def capture(endpoint, payload, token):
                response = transport(endpoint, payload, token)
                current = next(row for row in report["rows"] if row["status"] == "submitted")
                current["response_choices"] = client.redact(response.get("choices"))
                checkpoint(path, report)
                return response
            limits = report["protocol"]["frozen"]["limits"]
            client = Client(report["protocol"]["frozen"]["plan"], contracts, budget=limits["budget_usd"],
                            max_calls=limits["max_calls"], sender=capture, on_trace=lambda: checkpoint(path, report))
            run(report, client, lambda: checkpoint(path, report))
        print(json.dumps({"output": str(path), "status": report["status"], "protocol_sha256": report["protocol"]["sha256"],
                          "summary": report.get("summary"), "accounted_or_reserved_usd": report.get("accounted_or_reserved_usd")}, indent=2))
        return 0 if report["status"] in {"prepared", "completed"} else 2
    except (ValueError, KeyError, TypeError, OSError, subprocess.CalledProcessError):
        # No resume or replacement mode; a submitted call may be billed even if interrupted.
        if owned and report is not None and path.exists():
            report["status"] = "stopped-no-retry"
            checkpoint(path, report)
        print("Pilot stopped or output exists; no automatic retry. Inspect the saved artifact; no canonical knowledge changed.")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
