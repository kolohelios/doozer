"""Durable local source receipt only; no reconciliation, worker, or network calls."""

import argparse
from contextlib import closing
import json
import os
from pathlib import Path
import sqlite3

from scripts import provenance, workbench as wb


MAX_SOURCE_BYTES = 256 * 1024
SCHEMA = """
CREATE TABLE IF NOT EXISTS source_inbox (
    position INTEGER PRIMARY KEY,
    source_id TEXT NOT NULL UNIQUE,
    payload TEXT NOT NULL
)
"""


def _sync_directory(directory):
    fd = os.open(directory, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def receive(path, source_id, source):
    """Return a receipt only after committing the immutable pending row."""
    payload = provenance.encoded(source)
    if len(payload.encode()) > MAX_SOURCE_BYTES:
        raise ValueError("source exceeds local inbox byte bound")
    wb.validate("#ID", source_id)
    wb.validate("#InboxSource", source)
    state = wb.new_state()
    wb.receive(state, source_id, source)
    if provenance.encoded(state["received"][source_id]) != payload:
        raise ValueError("inbox cannot silently drop source fields")
    path = Path(path).resolve()
    with closing(sqlite3.connect(path, isolation_level=None)) as db:
        if db.execute("PRAGMA journal_mode=DELETE").fetchone() != ("delete",):
            raise ValueError("inbox could not enable rollback journaling")
        db.execute("PRAGMA synchronous=EXTRA")
        db.execute("BEGIN IMMEDIATE")
        db.execute(SCHEMA)
        row = db.execute("SELECT position, payload FROM source_inbox WHERE source_id = ?", (source_id,)).fetchone()
        if row is None:
            position = db.execute("INSERT INTO source_inbox(source_id, payload) VALUES (?, ?)",
                                  (source_id, payload)).lastrowid
        else:
            position, recorded = row
            if recorded != payload:
                raise ValueError("source identity reused with different content")
        db.commit()
    # Sync creation of the database entry as well as SQLite's journal protocol.
    _sync_directory(path.parent)
    return {"source_id": source_id, "position": position, "status": "received-pending"}


def snapshot(path):
    """Export a workbench-shaped receipt snapshot. No row is marked processed."""
    state = wb.new_state()
    uri = Path(path).resolve().as_uri() + "?mode=ro"
    with closing(sqlite3.connect(uri, uri=True)) as db:
        rows = db.execute("SELECT source_id, payload FROM source_inbox ORDER BY position")
        for source_id, payload in rows:
            wb.receive(state, source_id, json.loads(payload, object_pairs_hook=provenance.unique_object))
    return {"state": state, "status": "receipt-snapshot", "network_calls": 0}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", required=True, help="Local SQLite path in an existing directory")
    modes = parser.add_subparsers(dest="mode", required=True)
    accept = modes.add_parser("receive")
    accept.add_argument("--source-id", required=True)
    accept.add_argument("--source", required=True, help="JSON source record")
    export = modes.add_parser("snapshot")
    export.add_argument("--output", required=True, help="New JSON workbench inspection artifact")
    args = parser.parse_args(argv)
    if args.mode == "receive":
        with Path(args.source).open("rb") as stream:
            raw = stream.read(MAX_SOURCE_BYTES + 1)
        if len(raw) > MAX_SOURCE_BYTES:
            raise ValueError("source file exceeds local inbox byte bound")
        source = json.loads(raw, object_pairs_hook=provenance.unique_object)
        print(json.dumps(receive(args.db, args.source_id, source)))
    else:
        report = snapshot(args.db)
        with Path(args.output).open("x") as stream:
            json.dump(report, stream, indent=2, allow_nan=False)
            stream.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
