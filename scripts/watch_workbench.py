"""Watch recorded playback or durable activity in an existing local inbox."""

import argparse
import copy
from difflib import unified_diff
import json
from pathlib import Path
import sqlite3
from tempfile import TemporaryDirectory
import time

from scripts import maintenance_handoff as handoff, recorded_dispatch, source_inbox as inbox, workbench as wb


def play(path, *, emit, pause=None, maintenance=False):
    if Path(path).exists():
        raise ValueError("playback requires a new inbox")
    corpus = wb.export_cue(sorted((wb.ROOT / "corpus").glob("*.cue")))
    fixture = corpus["scenarios"]["retry-safety"]
    emit("Recorded synthetic playback — no model calls or semantic verdicts.")
    previous = ""
    seen = set()

    def proposed(entry):
        batch = entry["batch"]
        label = f"recorded patch for {', '.join(batch)}" if batch else "authored maintenance (no incoming source)"
        emit(f"  Proposed  · {label}")
        for op in entry["patch"]["operations"]:
            if op["op"] == "add":
                claim = op["assertion"]
                sources = ", ".join(dict.fromkeys(c["source"] for c in claim["evidence"]))
                emit(f"    + {claim['id']} [{claim['scope']}] ← {sources}")
            else:
                emit(f"    − {op['id']} → {op['replacement']}")
        if not entry["patch"]["operations"]:
            emit("    No claim operations; source accounting only." if batch else "    No claim operations or source accounting.")

    def render():
        nonlocal previous
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
        render()
        if pause and (index < len(fixture["steps"]) or maintenance):
            pause()
    result = recorded_dispatch.advance(path)
    if result["status"] != "complete":
        emit(f"\nStopped · {result['status']}")
        return 2
    position = result["position"]
    if maintenance:
        try:
            position = play_maintenance(path, base=position, emit=emit, proposed=proposed, render=render, pause=pause)
        except ValueError as error:
            emit(f"  Rejected  · {error}")
            return 2
        except (OSError, sqlite3.Error) as error:
            emit(f"  Stopped   · {error}; acknowledgment unavailable")
            return 2
    emit(f"\nComplete · {position} durable commits, no model calls.")
    return 0


def play_maintenance(path, *, base, emit, proposed, render, pause):
    fixture = wb.export_cue(sorted((wb.ROOT / "experiments/workbench").glob("*.cue")))["maintenance"]["consolidation"]
    def inspect_fixture(patch):
        prepared = handoff.prepare(path)
        context = prepared["preparation"]
        emit(f"  Prepared  · reconciliation {context['base_position']}; offline snapshot, no incoming source")
        # Encode the authored operations in the same reference vocabulary as a saved proposal.
        refs = {key: ref for ref, key in context["claim_refs"]["existing"].items()}
        wire = copy.deepcopy(patch)
        del wire["accounting"]  # The prepared response carries no intake dispositions.
        additions = [op for op in wire["operations"] if op["op"] == "add"]
        slots = context["claim_refs"]["new"]
        if len(additions) > len(slots):
            raise ValueError("fixture exceeds its offered claim slots")
        for op, slot in zip(additions, slots):
            claim = op["assertion"]
            refs[claim["id"]] = slot
            claim["id"] = slot
        for op in wire["operations"]:
            if op["op"] == "retire":
                op["id"], op["replacement"] = refs[op["id"]], refs[op["replacement"]]
        proposed({"patch": wire, "batch": []})
        report = handoff.inspect(path, json.dumps(wire).encode(), prepared=prepared)
        inspected = report["inspection"]
        emit(f"  Inspected · {len(inspected['before']['claims'])} → {len(inspected['after']['claims'])} active claims in a copy; not committed")
        for op in additions:
            slot = op["assertion"]["id"]
            emit(f"    {slot} → {slots[slot]}")
        return report

    def show_receipt(label, receipt):
        emit(f"  {label:<9} · position {receipt['position']}, revision {receipt['revision']}")
        render()
        if pause:
            pause()

    emit("\nMaintenance · consolidate with no incoming source")
    report = inspect_fixture(fixture["patch"])
    if pause:
        pause()
    applied = handoff.apply(path, "demo-consolidate", report, inspection_sha256=report["inspection_sha256"])
    show_receipt("Maintained", applied)

    emit("\nMaintenance · recorded no-op")
    report = inspect_fixture(fixture["repeatPatch"])
    repeat = handoff.apply(path, "demo-maintenance-noop", report, inspection_sha256=report["inspection_sha256"])
    if repeat["status"] != "no-change":
        raise ValueError("fixture no-op unexpectedly changed the inbox")
    show_receipt("No commit", repeat)

    emit("\nRecovery · restore the view before consolidation")
    restored = inbox.restore(path, "demo-undo-consolidation", base_position=applied["position"],
                             request={"baseRevision": applied["revision"], "targetPosition": base,
                                      "reason": "Show the earlier active claims without deleting history."})
    show_receipt("Restored", restored)

    emit("\nRecovery · replay the recorded consolidation")
    replayed = inbox.replay(path, "demo-redo-consolidation", base_position=restored["position"],
                            journal_position=base, base_revision=restored["revision"])
    emit(f"  Replayed  · position {replayed['position']}, revision {replayed['revision']}")
    render()
    return replayed["position"]


def poll(path, *, emit, previous=None):
    current = inbox.activity(path, after=(0, 0) if previous is None else previous["positions"],
                             after_rejection=0 if previous is None else previous["rejection_position"])
    for position, source_id in current["receipts"]:
        emit(f"Received  · intake {position}: {source_id}")
    for commit in current["commits"]:
        label = {"patch": "Committed", "restore": "Restored", "replay": "Replayed", "processing-only": "Processed", "maintenance": "Maintained"}[commit["kind"]]
        emit(f"{label:<9} · reconciliation {commit['position']}, revision {commit['revision']}: {commit['operation']}")
    for position, operation, base in current["rejections"]:
        emit(f"Rejected  · attempt {position} at reconciliation {base}: {operation} (patch not applied)")
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
    parser.add_argument("--maintenance", action="store_true", help="Extend playback with consolidation, no-op, restore, and replay")
    parser.add_argument("--db", help="Read durable activity from an existing inbox instead of playing the fixture")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--follow", action="store_true", help="Poll --db once per second until interrupted")
    mode.add_argument("--explain", type=int, metavar="POSITION", help="Show one reconciliation transition, including claim text and citations")
    args = parser.parse_args(argv)
    if (not args.db and (args.follow or args.explain is not None)) or (args.db and (args.step or args.maintenance)):
        parser.error("--follow and --explain require --db; --step and --maintenance are only for playback")
    if args.explain is not None:
        try:
            detail = inbox.explain(args.db, args.explain)
        except ValueError as error:
            parser.error(str(error))
        print(json.dumps(detail, indent=2, ensure_ascii=True))
        return 0
    if args.db:
        emit = lambda line: print(line, flush=True)
        emit("Durable inbox activity — intake, reconciliation, and rejections have separate positions.")
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
                        pause=(lambda: input("Enter to continue… ")) if args.step else None, maintenance=args.maintenance)
        except (EOFError, KeyboardInterrupt):
            print("\nPlayback stopped.")
            return 130


if __name__ == "__main__":
    raise SystemExit(main())
