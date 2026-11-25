"""Watch recorded playback or durable activity in an existing local inbox."""

import argparse
from difflib import unified_diff
import json
from pathlib import Path
import sqlite3
from tempfile import TemporaryDirectory
import time

from scripts import recorded_dispatch, source_inbox as inbox, workbench as wb


def play(path, *, emit, pause=None):
    if Path(path).exists():
        raise ValueError("playback requires a new inbox")
    corpus = wb.export_cue(sorted((wb.ROOT / "corpus").glob("*.cue")))
    fixture = corpus["scenarios"]["retry-safety"]
    emit("Recorded synthetic playback — no model calls or semantic verdicts.")
    previous = ""
    seen = set()

    def proposed(entry):
        emit(f"  Proposed  · recorded patch for {', '.join(entry['batch'])}")
        for op in entry["patch"]["operations"]:
            if op["op"] == "add":
                claim = op["assertion"]
                sources = ", ".join(dict.fromkeys(c["source"] for c in claim["evidence"]))
                emit(f"    + {claim['id']} [{claim['scope']}] ← {sources}")
            else:
                emit(f"    − {op['id']} → {op['replacement']}")
        if not entry["patch"]["operations"]:
            emit("    No claim operations; source accounting only.")

    for index, step in enumerate(fixture["steps"], 1):
        emit(f"\n{index:02d}  {step['id']}")
        for key in step["receive"]:
            source = fixture["sources"][key]
            receipt = inbox.receive(path, key, source)
            label = "Redelivery" if key in seen else "Received"
            emit(f"  {label} · {key} #{receipt['position']} {source['anchor']}: {json.dumps(source['text'], ensure_ascii=False)}")
            seen.add(key)
        state = inbox.snapshot(path)["state"]
        batch = set(step["reconcile"]) - set(state["processed"])
        if batch:
            def show_proposal(entry):
                if set(entry["batch"]) != batch:
                    raise ValueError("recorded proposal disagrees with playback round")
                proposed(entry)

            try:
                result = recorded_dispatch.advance(path, on_proposal=show_proposal)
            except ValueError as error:
                emit(f"  Rejected  · {error}")
                return 2
            except (OSError, sqlite3.Error) as error:
                emit(f"  Stopped   · {error}; commit acknowledgment unavailable")
                return 2
            if result["status"] != "advanced":
                emit(f"  Stopped   · {result['status']}")
                return 2
            receipt = result["receipt"]
            emit(f"  Committed · position {receipt['position']}, revision {receipt['revision']}")
        else:
            boundary = "receipt only" if not step["reconcile"] else "batch already processed"
            emit(f"  No commit · {boundary}")
        state = inbox.snapshot(path)["state"]
        pending = sorted(set(state["received"]) - set(state["processed"]))
        if pending:
            emit(f"  Pending   · {', '.join(pending)}")
        cached = inbox.projection(path)
        if cached["status"] == "behind":
            emit("  Behind    · cached reader view needs refresh")
        projection = inbox.refresh_projection(path)
        positions = projection["projected"]
        label = "Unchanged" if cached["status"] == "caught-up" else "Refreshed"
        emit(f"  {label:<9} · reader view at intake {positions['intake']}, reconciliation {positions['reconciliation']}")
        handbook = projection["projection"]["handbook"]
        for line in unified_diff(previous.splitlines(), handbook.splitlines(), fromfile="before", tofile="after", lineterm="", n=0):
            emit("    " + line)
        previous = handbook
        if pause and index < len(fixture["steps"]):
            pause()
    result = recorded_dispatch.advance(path)
    if result["status"] != "complete":
        emit(f"\nStopped · {result['status']}")
        return 2
    emit(f"\nComplete · {result['position']} durable commits, no model calls.")
    return 0


def poll(path, *, emit, previous=None):
    current = inbox.activity(path, after=(0, 0) if previous is None else previous["positions"])
    for position, source_id in current["receipts"]:
        emit(f"Received  · intake {position}: {source_id}")
    for commit in current["commits"]:
        label = {"patch": "Committed", "restore": "Restored", "replay": "Replayed", "processing-only": "Processed"}[commit["kind"]]
        emit(f"{label:<9} · reconciliation {commit['position']}, revision {commit['revision']}: {commit['operation']}")
    freshness = (current["projection_status"], current["projected"], current["positions"])
    if previous is None or freshness != (previous["projection_status"], previous["projected"], previous["positions"]):
        projected = current["projected"]
        cached = "none" if projected is None else f"intake {projected[1]}, reconciliation {projected[0]}"
        rec, intake = current["positions"]
        emit(f"Reader    · {current['projection_status']}; cached {cached}; available intake {intake}, reconciliation {rec}")
    return current


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--step", action="store_true", help="Pause for Enter between fixture rounds")
    parser.add_argument("--db", help="Read durable activity from an existing inbox instead of playing the fixture")
    parser.add_argument("--follow", action="store_true", help="Poll --db once per second until interrupted")
    args = parser.parse_args(argv)
    if (args.follow and not args.db) or (args.db and args.step):
        parser.error("--follow requires --db; --step is only for playback")
    if args.db:
        emit = lambda line: print(line, flush=True)
        emit("Durable inbox activity — intake and reconciliation are shown in separate position order.")
        previous = None
        try:
            while True:
                previous = poll(args.db, emit=emit, previous=previous)
                if not args.follow:
                    return 0
                time.sleep(1)
        except KeyboardInterrupt:
            return 130
    with TemporaryDirectory(prefix="doozer-watch-") as directory:
        try:
            return play(Path(directory) / "watch.sqlite", emit=lambda line: print(line, flush=True),
                        pause=(lambda: input("Enter to continue… ")) if args.step else None)
        except (EOFError, KeyboardInterrupt):
            print("\nPlayback stopped.")
            return 130


if __name__ == "__main__":
    raise SystemExit(main())
