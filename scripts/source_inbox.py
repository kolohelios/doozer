"""Durable local source receipt and saved-patch commits; no worker or network calls."""

import argparse
from contextlib import closing, contextmanager
import hashlib
import json
import os
from pathlib import Path
import sqlite3

from scripts import provenance, workbench as wb


MAX_SOURCE_BYTES = 256 * 1024
MAX_COMMIT_BYTES = 1024 * 1024
COMMIT_SCHEMA = """
CREATE TABLE IF NOT EXISTS reconciliation_receipts (
    position INTEGER PRIMARY KEY,
    operation_id TEXT NOT NULL UNIQUE,
    request_digest TEXT NOT NULL,
    revision INTEGER NOT NULL
)
"""
STATE_SCHEMA = """
CREATE TABLE IF NOT EXISTS reconciliation_state (
    singleton INTEGER PRIMARY KEY CHECK (singleton = 1),
    position INTEGER NOT NULL,
    payload TEXT NOT NULL
)
"""
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


@contextmanager
def _writer(path, *, create=False):
    path = Path(path).resolve()
    uri = path.as_uri() + ("?mode=rwc" if create else "?mode=rw")
    with closing(sqlite3.connect(uri, uri=True, isolation_level=None)) as db:
        if db.execute("PRAGMA journal_mode=DELETE").fetchone() != ("delete",):
            raise ValueError("inbox could not enable rollback journaling")
        db.execute("PRAGMA synchronous=EXTRA")
        db.execute("BEGIN IMMEDIATE")
        yield db
        db.commit()
    _sync_directory(path.parent)


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
    with _writer(path, create=True) as db:
        db.execute(SCHEMA)
        row = db.execute("SELECT position, payload FROM source_inbox WHERE source_id = ?", (source_id,)).fetchone()
        if row is None:
            position = db.execute("INSERT INTO source_inbox(source_id, payload) VALUES (?, ?)",
                                  (source_id, payload)).lastrowid
        else:
            position, recorded = row
            if recorded != payload:
                raise ValueError("source identity reused with different content")
    return {"source_id": source_id, "position": position, "status": "received-pending"}


def _load(db):
    state = wb.new_state()
    position = 0
    if db.execute("SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'reconciliation_state'").fetchone():
        row = db.execute("SELECT position, payload FROM reconciliation_state WHERE singleton = 1").fetchone()
        if row is not None:
            position, payload = row
            state.update(json.loads(payload, object_pairs_hook=provenance.unique_object))
    for source_id, payload in db.execute("SELECT source_id, payload FROM source_inbox ORDER BY position"):
        wb.receive(state, source_id, json.loads(payload, object_pairs_hook=provenance.unique_object))
    return position, state


def commit(path, operation_id, *, base_position, patch, batch, analysis, route):
    """Atomically persist a validated ingestion patch and its idempotency receipt."""
    wb.validate("#ID", operation_id)
    if type(base_position) is not int or base_position < 0:
        raise ValueError("base_position must be a nonnegative commit position")
    if not isinstance(batch, list) or any(not isinstance(key, str) for key in batch):
        raise ValueError("batch must be a list of source IDs")
    request = provenance.encoded({"base_position": base_position, "patch": patch, "batch": batch,
                                  "analysis": analysis, "route": route}).encode()
    if len(request) > MAX_COMMIT_BYTES:
        raise ValueError("commit exceeds local byte bound")
    digest = hashlib.sha256(request).hexdigest()
    with _writer(path) as db:
        db.execute(COMMIT_SCHEMA)
        db.execute(STATE_SCHEMA)
        row = db.execute("SELECT position, request_digest, revision FROM reconciliation_receipts WHERE operation_id = ?",
                         (operation_id,)).fetchone()
        if row is not None:
            position, recorded, revision = row
            if recorded != digest:
                raise ValueError("operation identity reused with different content")
        else:
            latest, state = _load(db)
            if base_position != latest:
                raise ValueError("stale reconciliation position")
            # Apply the exact serialized request used for the idempotency key.
            args = json.loads(request)
            updated = wb.commit(state, args["patch"], args["batch"], args["analysis"], args["route"])
            position, revision = latest + 1, updated["revision"]
            material = {key: value for key, value in updated.items() if key != "received"}
            db.execute("INSERT INTO reconciliation_receipts VALUES (?, ?, ?, ?)", (position, operation_id, digest, revision))
            db.execute("INSERT INTO reconciliation_state VALUES (1, ?, ?) ON CONFLICT(singleton) DO UPDATE "
                       "SET position = excluded.position, payload = excluded.payload", (position, provenance.encoded(material)))
    return {"operation_id": operation_id, "position": position, "revision": revision, "status": "committed-locally"}


def snapshot(path):
    """Read receipt and reconciliation state from the same database snapshot."""
    uri = Path(path).resolve().as_uri() + "?mode=ro"
    with closing(sqlite3.connect(uri, uri=True)) as db:
        db.execute("BEGIN")
        position, state = _load(db)
    return {"state": state, "reconciliation_position": position, "status": "receipt-snapshot", "network_calls": 0}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", required=True, help="Local SQLite path in an existing directory")
    modes = parser.add_subparsers(dest="mode", required=True)
    accept = modes.add_parser("receive")
    accept.add_argument("--source-id", required=True)
    accept.add_argument("--source", required=True, help="JSON source record")
    reconcile = modes.add_parser("commit")
    reconcile.add_argument("--operation-id", required=True)
    reconcile.add_argument("--request", required=True, help="Saved JSON envelope: base_position, patch, batch, analysis, route")
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
    elif args.mode == "commit":
        with Path(args.request).open("rb") as stream:
            raw = stream.read(MAX_COMMIT_BYTES + 1)
        if len(raw) > MAX_COMMIT_BYTES:
            raise ValueError("commit file exceeds local byte bound")
        request = json.loads(raw, object_pairs_hook=provenance.unique_object)
        print(json.dumps(commit(args.db, args.operation_id, **request)))
    else:
        report = snapshot(args.db)
        with Path(args.output).open("x") as stream:
            json.dump(report, stream, indent=2, allow_nan=False)
            stream.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
