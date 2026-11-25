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
REJECTION_SCHEMA = """
CREATE TABLE IF NOT EXISTS reconciliation_rejections (
    position INTEGER PRIMARY KEY,
    operation_id TEXT NOT NULL,
    base_position INTEGER NOT NULL
)
"""
STATE_SCHEMA = """
CREATE TABLE IF NOT EXISTS reconciliation_state (
    singleton INTEGER PRIMARY KEY CHECK (singleton = 1),
    position INTEGER NOT NULL,
    payload TEXT NOT NULL
)
"""
PROJECTION_SCHEMA = """
CREATE TABLE IF NOT EXISTS reader_projection (
    singleton INTEGER PRIMARY KEY CHECK (singleton = 1),
    reconciliation_position INTEGER NOT NULL,
    intake_position INTEGER NOT NULL,
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


def _has_table(db, name):
    return db.execute("SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?", (name,)).fetchone() is not None


def _load(db):
    state = wb.new_state()
    position = 0
    if _has_table(db, "reconciliation_state"):
        row = db.execute("SELECT position, payload FROM reconciliation_state WHERE singleton = 1").fetchone()
        if row is not None:
            position, payload = row
            state.update(json.loads(payload, object_pairs_hook=provenance.unique_object))
    for source_id, payload in db.execute("SELECT source_id, payload FROM source_inbox ORDER BY position"):
        wb.receive(state, source_id, json.loads(payload, object_pairs_hook=provenance.unique_object))
    return position, state


def commit(path, operation_id, *, base_position, patch, batch, analysis, route):
    """Atomically persist a validated ingestion patch and its idempotency receipt."""
    if not isinstance(batch, list) or any(not isinstance(key, str) for key in batch):
        raise ValueError("batch must be a list of source IDs")

    def apply(state, args):
        return wb.commit(state, args["patch"], args["batch"], args["analysis"], args["route"])

    return _transition(path, operation_id, base_position,
                       {"patch": patch, "batch": batch, "analysis": analysis, "route": route}, apply, record_rejection=True)


def maintain(path, operation_id, *, base_position, patch, analysis, route, expected_state_sha256=None):
    """Persist maintenance over already processed evidence, without source intake."""
    def apply(state, args):
        request = args["maintenance"]
        return wb.maintain(state, request["patch"], request["analysis"], request["route"])

    operands = {"maintenance": {"patch": patch, "analysis": analysis, "route": route}}
    if expected_state_sha256 is not None:
        operands["expected_state_sha256"] = expected_state_sha256
    return _transition(path, operation_id, base_position, operands, apply, record_rejection=True, allow_no_change=True)


def state_digest(state):
    return hashlib.sha256(provenance.encoded(state).encode()).hexdigest()


def restore(path, operation_id, *, base_position, request):
    """Persist a compensating restore without deleting source receipts or history."""
    return _transition(path, operation_id, base_position, {"restore": request},
                       lambda state, args: wb.restore(state, args["restore"]))


def replay(path, operation_id, *, base_position, journal_position, base_revision):
    """Persist exact replay of a recorded patch, not redelivery of its receipt."""
    return _transition(path, operation_id, base_position,
                       {"replay": {"journal_position": journal_position, "base_revision": base_revision}},
                       lambda state, args: wb.replay(state, args["replay"]["journal_position"],
                                                     base_revision=args["replay"]["base_revision"]))


def _transition(path, operation_id, base_position, operands, apply, *, record_rejection=False, allow_no_change=False):
    wb.validate("#ID", operation_id)
    if type(base_position) is not int or base_position < 0:
        raise ValueError("base_position must be a nonnegative commit position")
    request = provenance.encoded({"base_position": base_position, **operands}).encode()
    if len(request) > MAX_COMMIT_BYTES:
        raise ValueError("commit exceeds local byte bound")
    digest = hashlib.sha256(request).hexdigest()
    rejection = None
    with _writer(path) as db:
        row = (db.execute("SELECT position, request_digest, revision FROM reconciliation_receipts WHERE operation_id = ?",
                          (operation_id,)).fetchone() if _has_table(db, "reconciliation_receipts") else None)
        if row is not None:
            position, recorded, revision = row
            if recorded != digest:
                raise ValueError("operation identity reused with different content")
        else:
            latest, state = _load(db)
            if base_position != latest:
                raise ValueError("stale reconciliation position")
            if "expected_state_sha256" in operands and operands["expected_state_sha256"] != state_digest(state):
                raise ValueError("inbox state changed since inspection")
            # Apply the exact serialized request used for the idempotency key.
            try:
                updated = apply(state, json.loads(request))
            except ValueError as error:
                if not record_rejection:
                    raise
                # Record only a confirmed patch rejection, not its request or exception text.
                db.execute(REJECTION_SCHEMA)
                db.execute("INSERT INTO reconciliation_rejections(operation_id, base_position) VALUES (?, ?)",
                           (operation_id, base_position))
                rejection = error
            else:
                if updated == state:
                    if allow_no_change:
                        return {"operation_id": operation_id, "position": latest,
                                "revision": state["revision"], "status": "no-change"}
                    raise ValueError("no state change; no operation receipt recorded")
                position, revision = latest + 1, updated["revision"]
                material = {key: value for key, value in updated.items() if key != "received"}
                db.execute(COMMIT_SCHEMA)
                db.execute(STATE_SCHEMA)
                db.execute("INSERT INTO reconciliation_receipts VALUES (?, ?, ?, ?)", (position, operation_id, digest, revision))
                db.execute("INSERT INTO reconciliation_state VALUES (1, ?, ?) ON CONFLICT(singleton) DO UPDATE "
                           "SET position = excluded.position, payload = excluded.payload", (position, provenance.encoded(material)))
    if rejection is not None:
        raise rejection
    return {"operation_id": operation_id, "position": position, "revision": revision, "status": "committed-locally"}


@contextmanager
def _reader(path):
    uri = Path(path).resolve().as_uri() + "?mode=ro"
    with closing(sqlite3.connect(uri, uri=True)) as db:
        db.execute("BEGIN")
        yield db


def _heads(db):
    # Durable commit receipts double as ordered invalidation markers.
    reconciliation = 0
    if _has_table(db, "reconciliation_receipts"):
        reconciliation, = db.execute("SELECT COALESCE(MAX(position), 0) FROM reconciliation_receipts").fetchone()
    intake, = db.execute("SELECT COALESCE(MAX(position), 0) FROM source_inbox").fetchone()
    return reconciliation, intake


def _cached(db):
    if not _has_table(db, "reader_projection"):
        return None
    return db.execute("SELECT reconciliation_position, intake_position, payload FROM reader_projection WHERE singleton = 1").fetchone()


def _projection_status(heads, cached):
    def positions(pair):
        return dict(zip(("reconciliation", "intake"), pair))

    return {"status": "missing" if cached is None else "caught-up" if cached[:2] == heads else "behind",
            "available": positions(heads), "projected": None if cached is None else positions(cached[:2]),
            "projection": None if cached is None else json.loads(cached[2], object_pairs_hook=provenance.unique_object)}


def projection(path):
    """Read the cached projection and freshness markers from one snapshot."""
    with _reader(path) as db:
        return _projection_status(_heads(db), _cached(db))


def refresh_projection(path):
    """Coalesce pending invalidations into a latest local projection transaction."""
    with _writer(path) as db:
        heads, cached = _heads(db), _cached(db)
        if cached is None or cached[:2] != heads:
            position, state = _load(db)
            if position != heads[0]:
                raise ValueError("reconciliation state disagrees with durable commit markers")
            payload = provenance.encoded(wb.project(state))
            db.execute(PROJECTION_SCHEMA)
            db.execute("INSERT INTO reader_projection VALUES (1, ?, ?, ?) ON CONFLICT(singleton) DO UPDATE "
                       "SET reconciliation_position = excluded.reconciliation_position, "
                       "intake_position = excluded.intake_position, payload = excluded.payload", (*heads, payload))
            cached = (*heads, payload)
    return _projection_status(heads, cached)


def _entry_kind(entry):
    if entry["kind"] == "restore":
        return "restore"
    if entry["replayOf"] is not None:
        return "replay"
    if entry.get("maintenance", False):
        return "maintenance"
    return "patch" if entry["patch"]["operations"] else "processing-only"


def explain(path, position):
    """Read the recorded effect of one durable reconciliation position."""
    if type(position) is not int or position < 1:
        raise ValueError("reconciliation position must be a positive integer")
    with _reader(path) as db:
        latest, state = _load(db)
        if position > latest:
            raise ValueError("unknown reconciliation position")
        row = db.execute("SELECT operation_id, revision FROM reconciliation_receipts WHERE position = ?", (position,)).fetchone()
    if row is None or len(state["journal"]) != latest:
        raise ValueError("reconciliation receipt disagrees with the journal")
    operation, revision = row
    before, after = (wb.historical_view(state, prefix) for prefix in (position - 1, position))
    entry = state["journal"][position - 1]
    if revision != after["revision"] or revision != entry["revision"]:
        raise ValueError("receipt revision disagrees with the journal")
    added = {key: value for key, value in after["claims"].items() if key not in before["claims"]}
    removed = {key: value for key, value in before["claims"].items() if key not in after["claims"]}
    processed = sorted(set(after["processed"]) - set(before["processed"]))
    reopened = sorted(set(before["processed"]) - set(after["processed"]))
    kind = _entry_kind(entry)
    detail = {"position": position, "operation": operation, "kind": kind,
              "revision_before": before["revision"], "revision_after": revision,
              "added_claims": added, "removed_claims": removed,
              "redirects_added": {key: value for key, value in after["redirects"].items() if before["redirects"].get(key) != value},
              "redirects_removed": {key: value for key, value in before["redirects"].items() if after["redirects"].get(key) != value},
              "processed": processed, "returned_to_pending": reopened}
    source_ids = set(processed) | set(reopened)
    for claim in (*added.values(), *removed.values()):
        source_ids.update(citation["source"] for citation in claim["evidence"])
    if kind == "restore":
        detail["reason"] = entry["request"]["reason"]
        detail["target_prefix"] = entry["request"]["targetPosition"]
    else:
        detail["reason"] = entry["patch"]["rationale"]
        detail["accounting"] = entry["patch"]["accounting"]
        if kind == "replay":
            detail["replayed_position"] = entry["replayOf"] + 1
        for disposition in detail["accounting"].values():
            source_ids.update(citation["source"] for citation in disposition.get("basis", []))
    detail["source_anchors"] = {key: state["received"][key]["anchor"] for key in sorted(source_ids)}
    return detail


def activity(path, *, after=(0, 0), after_rejection=0):
    """Read durable activity since (reconciliation, intake) positions."""
    if len(after) != 2 or any(type(position) is not int or position < 0 for position in after):
        raise ValueError("activity cursor requires two nonnegative positions")
    if type(after_rejection) is not int or after_rejection < 0:
        raise ValueError("rejection cursor requires a nonnegative position")
    with _reader(path) as db:
        heads = _heads(db)
        rejection_head, rejections = 0, []
        if _has_table(db, "reconciliation_rejections"):
            rejection_head, = db.execute("SELECT COALESCE(MAX(position), 0) FROM reconciliation_rejections").fetchone()
            rejections = db.execute("SELECT position, operation_id, base_position FROM reconciliation_rejections "
                                    "WHERE position > ? ORDER BY position", (after_rejection,)).fetchall()
        if any(old > head for old, head in zip(after, heads)) or after_rejection > rejection_head:
            raise ValueError("inbox positions moved backwards; restart the watch")
        receipts = db.execute("SELECT position, source_id FROM source_inbox WHERE position > ? ORDER BY position",
                              (after[1],)).fetchall()
        commits = []
        if heads[0] > after[0]:
            position, payload = db.execute("SELECT position, payload FROM reconciliation_state WHERE singleton = 1").fetchone()
            journal = json.loads(payload)["journal"]
            if position != heads[0] or len(journal) != position:
                raise ValueError("reconciliation positions disagree with the journal")
            for number, operation, revision in db.execute(
                    "SELECT position, operation_id, revision FROM reconciliation_receipts WHERE position > ? ORDER BY position", (after[0],)):
                entry = journal[number - 1]
                if entry["revision"] != revision:
                    raise ValueError("receipt revision disagrees with the journal")
                commits.append({"position": number, "operation": operation, "revision": revision, "kind": _entry_kind(entry)})
            if len(commits) != heads[0] - after[0]:
                raise ValueError("missing reconciliation receipt")
        projected = (db.execute("SELECT reconciliation_position, intake_position FROM reader_projection WHERE singleton = 1").fetchone()
                     if _has_table(db, "reader_projection") else None)
    return {"positions": heads, "receipts": receipts, "commits": commits, "projected": projected,
            "rejection_position": rejection_head, "rejections": rejections,
            "projection_status": "missing" if projected is None else "caught-up" if projected == heads else "behind"}


def snapshot(path):
    """Read receipt and reconciliation state from the same database snapshot."""
    with _reader(path) as db:
        position, state = _load(db)
    return {"state": state, "reconciliation_position": position, "status": "receipt-snapshot", "network_calls": 0}


def _reader_state(path):
    with _reader(path) as db:
        position, state = _load(db)
        _, intake = _heads(db)
    return state, {"reconciliation": position, "intake": intake}


def evidence(path, claim_id):
    state, positions = _reader_state(path)
    return {**wb.claim_evidence(state, claim_id), "positions": positions}


def discover(path, query=None, *, scope=None, find_scopes=False, scope_history=None):
    """Read committed claims, history, and pending coverage at one durable position."""
    if sum((scope is not None, find_scopes, scope_history is not None)) > 1:
        raise ValueError("select at most one scope mode")
    if (query is None) != (scope_history is not None):
        raise ValueError("a query is required except for historical scope lookup")
    state, positions = _reader_state(path)
    if scope_history is not None:
        result = wb.discover_scope_history(state, scope_history)
    elif find_scopes:
        result = wb.discover_scopes(state, query)
    else:
        result = wb.discover(state, query, scope=scope)
    return {**result, "positions": positions}


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
    maintenance = modes.add_parser("maintain", help="Persist a source-free maintenance patch")
    maintenance.add_argument("--operation-id", required=True)
    maintenance.add_argument("--request", required=True, help="Saved JSON envelope: base_position, patch, analysis, route")
    recover = modes.add_parser("restore", help="Persist a compensating restore to a journal prefix")
    recover.add_argument("--operation-id", required=True)
    recover.add_argument("--request", required=True, help="Saved JSON envelope: base_position and request (baseRevision, targetPosition, reason)")
    repeat = modes.add_parser("replay", help="Persist exact replay of a recorded patch")
    repeat.add_argument("--operation-id", required=True)
    repeat.add_argument("--request", required=True, help="Saved JSON envelope: base_position, journal_position, base_revision")
    export = modes.add_parser("snapshot")
    export.add_argument("--output", required=True, help="New JSON workbench inspection artifact")
    modes.add_parser("projection", help="Read the local projection and its freshness markers")
    modes.add_parser("refresh-projection", help="Catch up the local projection")
    trail = modes.add_parser("evidence", help="Read a claim's citations and recorded reply context")
    trail.add_argument("--claim", required=True, help="Exact active or historical claim ID")
    search = modes.add_parser("discover", help="Search a read-only snapshot of committed inbox state")
    search.add_argument("--query", help="Lexical search terms")
    scopes = search.add_mutually_exclusive_group()
    scopes.add_argument("--scope", help="Restrict current search to this exact scope")
    scopes.add_argument("--find-scopes", action="store_true", help="List candidate active scopes without selecting one")
    scopes.add_argument("--scope-history", help="Look up inactive claims by their original exact scope, without a query")
    args = parser.parse_args(argv)
    if args.mode == "discover" and (args.query is None) != (args.scope_history is not None):
        search.error("--query is required except with --scope-history")
    if args.mode == "receive":
        with Path(args.source).open("rb") as stream:
            raw = stream.read(MAX_SOURCE_BYTES + 1)
        if len(raw) > MAX_SOURCE_BYTES:
            raise ValueError("source file exceeds local inbox byte bound")
        source = json.loads(raw, object_pairs_hook=provenance.unique_object)
        print(json.dumps(receive(args.db, args.source_id, source)))
    elif args.mode in ("commit", "maintain", "restore", "replay"):
        with Path(args.request).open("rb") as stream:
            raw = stream.read(MAX_COMMIT_BYTES + 1)
        if len(raw) > MAX_COMMIT_BYTES:
            raise ValueError("commit file exceeds local byte bound")
        request = json.loads(raw, object_pairs_hook=provenance.unique_object)
        apply = {"commit": commit, "maintain": maintain, "restore": restore, "replay": replay}[args.mode]
        print(json.dumps(apply(args.db, args.operation_id, **request)))
    elif args.mode == "projection":
        print(json.dumps(projection(args.db)))
    elif args.mode == "refresh-projection":
        print(json.dumps(refresh_projection(args.db)))
    elif args.mode == "evidence":
        print(json.dumps(evidence(args.db, args.claim), indent=2))
    elif args.mode == "discover":
        print(json.dumps(discover(args.db, args.query, scope=args.scope, find_scopes=args.find_scopes,
                                  scope_history=args.scope_history), indent=2))
    else:
        report = snapshot(args.db)
        with Path(args.output).open("x") as stream:
            json.dump(report, stream, indent=2, allow_nan=False)
            stream.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
