"""Inspect a saved source-free patch offline, then explicitly persist it locally."""

import argparse
import base64
import copy
import hashlib
import json
from pathlib import Path

from scripts import maintenance_proposer as proposer, source_inbox as inbox, workbench as wb
from scripts.standards_maintenance import read_json


VERSION = "local-maintenance-handoff-v1"


def implementation():
    paths = [Path(__file__), *(Path(module.__file__) for module in (wb, inbox, proposer)), wb.ROOT / "flake.lock"]
    return {str(path.relative_to(wb.ROOT)): hashlib.sha256(path.read_bytes()).hexdigest() for path in paths}


def inspect(path, raw):
    if len(raw) > inbox.MAX_COMMIT_BYTES:
        raise ValueError("saved patch exceeds local byte bound")
    patch = proposer.parse_proposal(raw, max_depth=64)
    wb.validate("#MaintenancePatch", patch)
    saved = inbox.snapshot(path)
    before = saved["state"]
    additions = [copy.deepcopy(op["assertion"]) for op in patch["operations"] if op["op"] == "add"]
    analysis = {"assertions": additions or copy.deepcopy(list(before["claims"].values()))}
    route = {"action": "analyze"}
    after = wb.maintain(before, patch, analysis, route)
    frozen = {"version": VERSION, "input_base64": base64.b64encode(raw).decode(),
              "request": {"base_position": saved["reconciliation_position"], "patch": patch,
                          "analysis": analysis, "route": route, "expected_state_sha256": inbox.state_digest(before)},
              "before": wb.project(before), "after": wb.project(after), "changed": after != before,
              "contract_sha256": hashlib.sha256(wb.CONTRACTS.read_bytes()).hexdigest(),
              "implementation_sha256": implementation()}
    return {"inspection_sha256": proposer.digest(frozen), "inspection": frozen,
            "semantic_judgment": "not-evaluated", "scope": "isolated preview; not an approval"}


def apply(path, operation_id, report, *, inspection_sha256):
    frozen = report["inspection"]
    if (frozen["version"] != VERSION or report["inspection_sha256"] != inspection_sha256
            or proposer.digest(frozen) != inspection_sha256):
        raise ValueError("exact inspection hash required")
    if (frozen["contract_sha256"] != hashlib.sha256(wb.CONTRACTS.read_bytes()).hexdigest()
            or frozen["implementation_sha256"] != implementation()):
        raise ValueError("maintenance gate changed since inspection")
    request = frozen["request"]
    raw = base64.b64decode(frozen["input_base64"], validate=True)
    if proposer.parse_proposal(raw, max_depth=64) != request["patch"]:
        raise ValueError("saved patch and inspected request disagree")
    return inbox.maintain(path, operation_id, **request)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", required=True)
    modes = parser.add_subparsers(dest="mode", required=True)
    review = modes.add_parser("inspect")
    review.add_argument("--patch", required=True)
    review.add_argument("--output", required=True)
    persist = modes.add_parser("apply")
    persist.add_argument("--inspection", required=True)
    persist.add_argument("--sha256", required=True)
    persist.add_argument("--operation-id", required=True)
    args = parser.parse_args(argv)
    if args.mode == "inspect":
        with Path(args.patch).open("rb") as stream:
            report = inspect(args.db, stream.read(inbox.MAX_COMMIT_BYTES + 1))
        with Path(args.output).open("x") as stream:
            json.dump(report, stream, indent=2, allow_nan=False)
            stream.write("\n")
        print(report["inspection_sha256"])
    else:
        print(json.dumps(apply(args.db, args.operation_id, read_json(args.inspection), inspection_sha256=args.sha256)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
