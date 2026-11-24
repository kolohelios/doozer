"""Prepare one blind maintenance checkpoint or inspect a saved proposal offline."""

import argparse
import base64
import copy
import hashlib
import json
from pathlib import Path
import subprocess

from scripts import retry_maintenance, workbench as wb
from scripts.workbench_models import RecordedBackend


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def implementation():
    paths = [wb.CONTRACTS, Path(__file__), wb.ROOT / "flake.lock", wb.ROOT / "scripts/workbench.py", wb.ROOT / "scripts/retry_maintenance.py", wb.ROOT / "scripts/workbench_models.py"]
    return {str(p.relative_to(wb.ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}


def load():
    data = wb.export_cue(sorted((wb.ROOT / "experiments/workbench").glob("*.cue")))
    scenario = wb.export_cue(sorted((wb.ROOT / "corpus").glob("*.cue")))["scenarios"][data["proposerCheckpoint"]["scenario"]]
    return data, scenario


def prepare(data=None, scenario=None, *, append_only=False):
    if data is None or scenario is None:
        if data is not None or scenario is not None:
            raise ValueError("supply both fixture data and scenario, or neither")
        data, scenario = load()
    plan = copy.deepcopy(data["proposerCheckpoint"])
    if plan["plannedCalls"] != 0 or plan["budgetUSD"] != 0 or plan["model"] is not None or plan["provider"] is not None:
        raise ValueError("offline checkpoint cannot inherit execution authority")
    if type(append_only) is not bool:
        raise ValueError("view construction mode must be explicit boolean")
    backend = retry_maintenance.AppendOnlyBackend() if append_only else RecordedBackend()
    backend.responses = copy.deepcopy(data["recorded"])
    state = wb.run(scenario, backend, through=plan["through"])["state"]
    if not state["claims"] or set(state["processed"]) != set(state["received"]):
        raise ValueError("checkpoint must have current claims and no pending input")
    contract = subprocess.run(["cue", "def", str(wb.CONTRACTS), "-e", "#MaintenancePatch"], check=True, capture_output=True, text=True).stdout
    # This allowlist is the entire proposer boundary, not the fixture/report object.
    context = {"current_revision": state["revision"], "current_claims": copy.deepcopy(list(state["claims"].values())),
               "sources": {key: copy.deepcopy(state["received"][key]) for key in state["processed"]},
               "reserved_claim_ids": sorted(state["history"]), "existing_aliases": copy.deepcopy(state["redirects"])}
    messages = [{"role": "system", "content": plan["instructions"] + "\n\n" + plan["wire"] + "\n\n" + plan["boundary"] + "\n\nExact output contract:\n" + contract},
                {"role": "user", "content": json.dumps(context, sort_keys=True, allow_nan=False)}]
    if len(json.dumps(messages).encode()) > plan["maxPromptBytes"]:
        raise ValueError("checkpoint prompt exceeds byte bound")
    expectations = {step["id"]: step["expect"] for step in scenario["steps"]}
    frozen = {"version": plan["version"], "plan": plan, "before": state, "messages": messages,
              "output_contract": contract, "implementation_sha256": implementation(),
              "evaluation": {"rubrics": {key: copy.deepcopy(expectations[key]) for key in plan["evaluationCheckpoints"]},
                             "questions": plan["reviewQuestions"], "semantic_judgment": "pending-human-review"},
              "execution_authorization": "none; offline preparation and saved-response inspection only",
              "planned_calls": 0, "budget_usd": 0.0, "model": None, "provider": None}
    return {"status": "prepared-offline", "protocol": {"sha256": digest(frozen), "frozen": frozen}}


def check_prepared(prepared):
    frozen = prepared["protocol"]["frozen"]
    if (prepared["status"] != "prepared-offline" or digest(frozen) != prepared["protocol"]["sha256"]
            or frozen["implementation_sha256"] != implementation()
            or frozen["planned_calls"] != 0 or frozen["budget_usd"] != 0
            or frozen["model"] is not None or frozen["provider"] is not None
            or frozen["plan"]["plannedCalls"] != 0 or frozen["plan"]["budgetUSD"] != 0):
        raise ValueError("changed protocol or implementation; do not silently reassess")
    return frozen


def proposer_messages(prepared):
    """The only prospective model input; never transmit the private manifest."""
    return copy.deepcopy(check_prepared(prepared)["messages"])


def _pairs(items):
    result = {}
    for key, value in items:
        if key in result:
            raise ValueError("duplicate JSON member")
        result[key] = value
    return result


def _constant(value):
    raise ValueError("non-finite JSON number")


def inspect_proposal(prepared, raw):
    frozen = check_prepared(prepared)
    bound = frozen["plan"]["maxProposalBytes"]
    captured = raw[:bound]
    result = {"protocol": copy.deepcopy(prepared["protocol"]),
              "input": {"base64": base64.b64encode(captured).decode(), "captured_bytes": len(captured),
                        "captured_sha256": hashlib.sha256(captured).hexdigest(), "complete": len(raw) <= bound},
              "status": "not-applied", "canonical_acceptance": False, "network_calls": 0,
              "semantic_judgment": "not-evaluated", "evaluation": copy.deepcopy(frozen["evaluation"])}
    if len(raw) > bound:
        result.update(status="oversized-not-applied", reason="Only a bounded prefix captured; keep the unchanged original input file.")
        return result
    try:
        proposal = json.loads(raw.decode("utf-8"), object_pairs_hook=_pairs, parse_constant=_constant)
        pending = [(proposal, 0)]
        while pending:
            value, depth = pending.pop()
            if depth > frozen["plan"]["maxProposalDepth"]:
                raise ValueError("proposal nesting bound")
            if isinstance(value, dict):
                pending.extend((child, depth + 1) for child in value.values())
            elif isinstance(value, list):
                pending.extend((child, depth + 1) for child in value)
        json.dumps(proposal, allow_nan=False)  # Also reject finite-literal overflow such as 1e999.
    except (ValueError, UnicodeError, RecursionError):
        result.update(status="invalid-json-not-applied", reason="Strict JSON parsing or nesting bounds failed; raw bytes retained without repair.")
        return result
    result["proposal"] = copy.deepcopy(proposal)
    before = copy.deepcopy(frozen["before"])
    try:
        wb.validate("#MaintenancePatch", proposal)
        additions = [copy.deepcopy(op["assertion"]) for op in proposal["operations"] if op["op"] == "add"]
        # Adapter bookkeeping only: no new facts, opinion, or repaired operands.
        analysis = {"assertions": additions or copy.deepcopy(list(before["claims"].values()))}
        after = wb.maintain(before, proposal, analysis, {"action": "analyze"})
    except (ValueError, KeyError, TypeError, OverflowError, RecursionError) as error:
        result.update(status="rejected-not-applied", reason="Contract or local precondition rejected the unmodified proposal.",
                      failure={"type": type(error).__name__, "detail": str(error)})
        return result
    settings = {"queries": frozen["plan"]["readerQueries"], "references": frozen["plan"]["references"]}
    result.update(status="applied-in-isolated-copy" if proposal["operations"] else "no-op-in-isolated-copy",
                  semantic_judgment="pending-human-review", derived_analysis=analysis,
                  before=retry_maintenance.view(before, settings), after=retry_maintenance.view(after, settings),
                  isolated_state=after)
    if not proposal["operations"]:
        if after != before:
            raise ValueError("no-op mutated local state")
        result["recovery"] = {"status": "not-exercised-no-change", "material_unchanged": True}
        return result
    position = len(before["journal"])
    restored = wb.restore(after, {"baseRevision": after["revision"], "targetPosition": position,
                                  "reason": "Inspect the actual saved proposal's rollback, without external publication."})
    replayed = wb.replay(restored, position, base_revision=restored["revision"])
    recovered = (wb.material(restored) == wb.material(before) and wb.material(replayed) == wb.material(after)
                 and replayed["history"] == after["history"] and replayed["received"] == after["received"])
    if not recovered:
        raise ValueError("actual proposal recovery mismatch")
    result["recovery"] = {"status": "exercised", "material_recovered": True,
                          "restored": retry_maintenance.view(restored, settings),
                          "replayed": retry_maintenance.view(replayed, settings), "state": replayed}
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True)
    parser.add_argument("--prepared", help="Previously prepared local protocol, not a live request")
    parser.add_argument("--proposal", help="Saved raw JSON patch to inspect; never generated here")
    args = parser.parse_args(argv)
    if bool(args.prepared) != bool(args.proposal):
        parser.error("--prepared and --proposal are required together")
    path = Path(args.output)
    if path.exists():
        raise ValueError("output exists; no overwrite")
    if args.prepared:
        prepared = json.loads(Path(args.prepared).read_text())
        frozen = check_prepared(prepared)
        proposal_path = Path(args.proposal)
        if not proposal_path.is_file():
            raise ValueError("proposal must be a regular file")
        with proposal_path.open("rb") as stream:
            raw = stream.read(frozen["plan"]["maxProposalBytes"] + 1)
        result = inspect_proposal(prepared, raw)
    else:
        result = prepare()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x") as stream:
        stream.write(json.dumps(result, indent=2, allow_nan=False) + "\n")
    print(json.dumps({"output": str(path), "status": result["status"], "protocol_sha256": result["protocol"]["sha256"], "network_calls": 0}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
