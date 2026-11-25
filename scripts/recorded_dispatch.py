"""Drive checked-in synthetic reconciliation steps into the local inbox."""

import argparse
import copy
import json

from scripts import source_inbox as inbox, workbench as wb
from scripts.workbench_models import RecordedBackend


def _fixture():
    corpus = wb.export_cue(sorted((wb.ROOT / "corpus").glob("*.cue")))
    return wb.run(corpus["scenarios"]["retry-safety"], RecordedBackend())["state"]


def advance(path, *, on_proposal=None):
    """Run one recorded fixture transition or report why its batch is not ready."""
    return _advance(path, _fixture(), on_proposal=on_proposal)


def _advance(path, fixture, *, on_proposal=None):
    saved = inbox.snapshot(path)
    position = saved["reconciliation_position"]
    state = saved["state"]
    if any(fixture["received"].get(key) != source for key, source in state["received"].items()):
        raise ValueError("inbox contains evidence outside the recorded synthetic fixture")
    if position > len(fixture["journal"]):
        raise ValueError("inbox state is not an exact recorded fixture prefix")
    prefix = fixture["journal"][:position]
    expected = wb.historical_view(fixture, position)
    history = {op["assertion"]["id"]: op["assertion"] for entry in prefix
               for op in entry["patch"]["operations"] if op["op"] == "add"}
    if (state["journal"] != prefix or wb.historical_view(state, len(state["journal"])) != expected
            or state["history"] != history):
        raise ValueError("inbox state is not an exact recorded fixture prefix")
    if position == len(fixture["journal"]):
        return {"status": "complete", "position": position, "network_calls": 0}
    entry = fixture["journal"][position]
    missing = [key for key in entry["batch"] if key not in state["received"]]
    if missing:
        return {"status": "waiting-for-sources", "position": position, "missing": missing, "network_calls": 0}
    if on_proposal is not None:
        on_proposal(copy.deepcopy(entry))
    receipt = inbox.commit(path, f"recorded-retry-step-{position + 1}", base_position=position,
                           patch=entry["patch"], batch=entry["batch"], analysis=entry["analysis"], route=entry["route"])
    return {"status": "advanced", "receipt": receipt, "network_calls": 0}


def drain(path, *, max_steps, on_commit=None):
    """Process ready fixture batches with an explicit per-invocation commit limit."""
    if type(max_steps) is not int or max_steps < 1:
        raise ValueError("max_steps must be a positive integer")
    fixture = _fixture()
    for committed in range(max_steps):
        result = _advance(path, fixture)
        if result["status"] != "advanced":
            return {**result, "committed_steps": committed}
        receipt = result["receipt"]
        if on_commit is not None:
            on_commit(receipt.copy())
        position = receipt["position"]
        if position == len(fixture["journal"]):
            return {"status": "complete", "position": position, "committed_steps": committed + 1, "network_calls": 0}
    return {"status": "step-limit", "position": position, "committed_steps": max_steps, "network_calls": 0}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", required=True, help="Existing local SQLite inbox with synthetic retry fixture receipts")
    parser.add_argument("--max-steps", type=int, help="Drain ready batches up to this limit, streaming durable receipts as JSON lines")
    args = parser.parse_args(argv)
    if args.max_steps is None:
        print(json.dumps(advance(args.db)))
    else:
        if args.max_steps < 1:
            parser.error("--max-steps must be positive")
        result = drain(args.db, max_steps=args.max_steps,
                       on_commit=lambda receipt: print(json.dumps({"receipt": receipt}), flush=True))
        print(json.dumps(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
