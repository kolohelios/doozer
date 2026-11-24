"""Drive one checked-in synthetic reconciliation step into the local inbox."""

import argparse
import json

from scripts import source_inbox as inbox, workbench as wb
from scripts.workbench_models import RecordedBackend


def advance(path):
    """Run one recorded fixture transition or report why its batch is not ready."""
    saved = inbox.snapshot(path)
    position = saved["reconciliation_position"]
    state = saved["state"]
    corpus = wb.export_cue(sorted((wb.ROOT / "corpus").glob("*.cue")))
    fixture = wb.run(corpus["scenarios"]["retry-safety"], RecordedBackend())["state"]
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
    receipt = inbox.commit(path, f"recorded-retry-step-{position + 1}", base_position=position,
                           patch=entry["patch"], batch=entry["batch"], analysis=entry["analysis"], route=entry["route"])
    return {"status": "advanced", "receipt": receipt, "network_calls": 0}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", required=True, help="Existing local SQLite inbox with synthetic retry fixture receipts")
    args = parser.parse_args(argv)
    print(json.dumps(advance(args.db)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
