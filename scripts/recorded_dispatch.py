"""Drive checked-in synthetic reconciliation steps into the local inbox."""

import argparse
import copy
import json
import time

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


def drain(path, *, max_steps, on_commit=None, refresh_projection=False, wait_seconds=0):
    """Process ready fixture batches and optionally wait for missing receipts."""
    if type(wait_seconds) is not int or not 0 <= wait_seconds <= 60:
        raise ValueError("wait_seconds must be an integer between 0 and 60")
    result = _drain(path, max_steps=max_steps, on_commit=on_commit, wait_seconds=wait_seconds)
    if refresh_projection:
        projected = inbox.refresh_projection(path)
        result["projection"] = {key: projected[key] for key in ("status", "available", "projected")}
    return result


def _drain(path, *, max_steps, on_commit, wait_seconds):
    if type(max_steps) is not int or max_steps < 1:
        raise ValueError("max_steps must be a positive integer")
    fixture = _fixture()
    deadline = time.monotonic() + wait_seconds
    for committed in range(max_steps):
        result = _advance(path, fixture)
        while result["status"] == "waiting-for-sources" and wait_seconds:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                return {**result, "status": "wait-expired", "committed_steps": committed}
            time.sleep(min(0.25, remaining))
            if time.monotonic() >= deadline:
                return {**result, "status": "wait-expired", "committed_steps": committed}
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
    parser.add_argument("--refresh-projection", action="store_true", help="Catch up the local projection after the drain stops")
    parser.add_argument("--wait-seconds", type=int, default=0, help="Poll for missing sources within one 0–60 second drain window")
    args = parser.parse_args(argv)
    if not 0 <= args.wait_seconds <= 60:
        parser.error("--wait-seconds must be between 0 and 60")
    if args.max_steps is None:
        if args.refresh_projection or args.wait_seconds:
            parser.error("--refresh-projection and --wait-seconds require --max-steps")
        print(json.dumps(advance(args.db)))
    else:
        if args.max_steps < 1:
            parser.error("--max-steps must be positive")
        result = drain(args.db, max_steps=args.max_steps, refresh_projection=args.refresh_projection,
                       wait_seconds=args.wait_seconds, on_commit=lambda receipt: print(json.dumps({"receipt": receipt}), flush=True))
        print(json.dumps(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
