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
MAX_BATCH_BYTES = 1024 * 1024
MAX_BATCH_SOURCES = 64
MAX_PREPARATION_BYTES = 128 * 1024
MAX_BATCH_INSPECTION_BYTES = 4 * 1024 * 1024
BATCH_INSPECTION_VERSION = "local-batch-inspection-v2"
MAX_COMMIT_BYTES = 1024 * 1024
PROJECTION_VERSION = 1
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


def _source_payload(source_id, source):
    payload = provenance.encoded(source)
    if len(payload.encode()) > MAX_SOURCE_BYTES:
        raise ValueError("source exceeds local inbox byte bound")
    wb.validate("#ID", source_id)
    wb.validate("#InboxSource", source)
    state = wb.new_state()
    wb.receive(state, source_id, source)
    if provenance.encoded(state["received"][source_id]) != payload:
        raise ValueError("inbox cannot silently drop source fields")
    return payload


def receive_batch(path, records):
    """Acknowledge a bounded ordered batch only after all its rows are durable."""
    if not isinstance(records, list) or not 1 <= len(records) <= MAX_BATCH_SOURCES:
        raise ValueError("batch requires between 1 and 64 source records")
    if len(provenance.encoded(records).encode()) > MAX_BATCH_BYTES:
        raise ValueError("source batch exceeds local byte bound")
    payloads = []
    for record in records:
        if not isinstance(record, dict) or set(record) != {"source_id", "source"}:
            raise ValueError("batch record requires exactly source_id and source")
        key = record["source_id"]
        payloads.append((key, _source_payload(key, record["source"])))
    receipts = []
    with _writer(path, create=True) as db:
        db.execute(SCHEMA)
        for key, payload in payloads:
            row = db.execute("SELECT position, payload FROM source_inbox WHERE source_id = ?", (key,)).fetchone()
            if row is None:
                position = db.execute("INSERT INTO source_inbox(source_id, payload) VALUES (?, ?)", (key, payload)).lastrowid
            else:
                position, recorded = row
                if recorded != payload:
                    raise ValueError("source identity reused with different content")
            receipts.append({"source_id": key, "position": position, "status": "received-pending"})
    return receipts


def receive(path, source_id, source):
    """Return a receipt only after committing the immutable pending row."""
    return receive_batch(path, [{"source_id": source_id, "source": source}])[0]


def _has_table(db, name):
    return db.execute("SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?", (name,)).fetchone() is not None


def _load_reconciliation(db):
    state = wb.new_state()
    position = 0
    if _has_table(db, "reconciliation_state"):
        row = db.execute("SELECT position, payload FROM reconciliation_state WHERE singleton = 1").fetchone()
        if row is not None:
            position, payload = row
            state.update(json.loads(payload, object_pairs_hook=provenance.unique_object))
    return position, state


def _load(db):
    position, state = _load_reconciliation(db)
    for source_id, payload in db.execute("SELECT source_id, payload FROM source_inbox ORDER BY position"):
        wb.receive(state, source_id, json.loads(payload, object_pairs_hook=provenance.unique_object))
    return position, state


def commit(path, operation_id, *, base_position, patch, batch, analysis, route, expected_state_sha256=None):
    """Atomically persist a validated ingestion patch and its idempotency receipt."""
    if not isinstance(batch, list) or any(not isinstance(key, str) for key in batch):
        raise ValueError("batch must be a list of source IDs")

    def apply(state, args):
        return wb.commit(state, args["patch"], args["batch"], args["analysis"], args["route"])

    operands = {"patch": patch, "batch": batch, "analysis": analysis, "route": route}
    if expected_state_sha256 is not None:
        operands["expected_state_sha256"] = expected_state_sha256
    return _transition(path, operation_id, base_position, operands, apply, record_rejection=True)


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
    row = db.execute("SELECT reconciliation_position, intake_position, payload FROM reader_projection WHERE singleton = 1").fetchone()
    if row is None:
        return None
    rec, intake, raw = row
    payload = json.loads(raw, object_pairs_hook=provenance.unique_object)
    if set(payload) == {"renderer_version", "projection"}:
        return rec, intake, payload["renderer_version"], payload["projection"]
    return rec, intake, None, payload  # Legacy unversioned render.


def _projection_freshness(heads, cached):
    if cached is None:
        return "missing"
    return "caught-up" if cached[:3] == (*heads, PROJECTION_VERSION) else "behind"


def _projection_status(heads, cached):
    def positions(pair):
        return dict(zip(("reconciliation", "intake"), pair))

    return {"status": _projection_freshness(heads, cached),
            "available": positions(heads), "projected": None if cached is None else positions(cached[:2]),
            "projection": None if cached is None else cached[3]}


def projection(path):
    """Read the cached projection and freshness markers from one snapshot."""
    with _reader(path) as db:
        return _projection_status(_heads(db), _cached(db))


def refresh_projection(path):
    """Coalesce pending invalidations into a latest local projection transaction."""
    with _writer(path) as db:
        heads, cached = _heads(db), _cached(db)
        if _projection_freshness(heads, cached) != "caught-up":
            position, state = _load(db)
            if position != heads[0]:
                raise ValueError("reconciliation state disagrees with durable commit markers")
            rendered = wb.project(state)
            payload = provenance.encoded({"renderer_version": PROJECTION_VERSION, "projection": rendered})
            db.execute(PROJECTION_SCHEMA)
            db.execute("INSERT INTO reader_projection VALUES (1, ?, ?, ?) ON CONFLICT(singleton) DO UPDATE "
                       "SET reconciliation_position = excluded.reconciliation_position, "
                       "intake_position = excluded.intake_position, payload = excluded.payload", (*heads, payload))
            cached = (*heads, PROJECTION_VERSION, rendered)
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
        cached = _cached(db)
        projected = cached[:2] if cached is not None else None
    return {"positions": heads, "receipts": receipts, "commits": commits, "projected": projected,
            "rejection_position": rejection_head, "rejections": rejections,
            "projection_status": _projection_freshness(heads, cached)}


def pending(path, *, limit=20):
    """Read the pending intake backlog without exposing source payloads."""
    if type(limit) is not int or not 1 <= limit <= 256:
        raise ValueError("pending limit must be between 1 and 256")
    with _reader(path) as db:
        reconciliation, state = _load_reconciliation(db)
        _, intake = _heads(db)
        processed = set(state["processed"])
        rows = []
        total = 0
        for position, source_id in db.execute("SELECT position, source_id FROM source_inbox ORDER BY position"):
            if source_id in processed:
                continue
            total += 1
            if len(rows) < limit:
                rows.append({"position": position, "source_id": source_id})
    return {"positions": {"reconciliation": reconciliation, "intake": intake},
            "pending_count": total, "pending": rows, "truncated": total > limit}


def snapshot(path):
    """Read receipt and reconciliation state from the same database snapshot."""
    with _reader(path) as db:
        position, state = _load(db)
    return {"state": state, "reconciliation_position": position, "status": "receipt-snapshot", "network_calls": 0}


def prepare_batch(path, source_ids, *, evidence_ids=(), nominate_evidence=False):
    """Prepare a local read-only starting point for a saved reconciliation patch."""
    return _prepare_batch(snapshot(path), source_ids, evidence_ids, nominate_evidence=nominate_evidence)


def _retained_source_view(source):
    record = source.copy()
    if "excerpts" in record:
        wb.citation_passages(record)
        del record["text"]  # The joined index is not a contiguous quotation.
    return record


def _prepare_batch(saved, source_ids, evidence_ids=(), *, nominate_evidence=False):
    if (not isinstance(source_ids, list) or not 1 <= len(source_ids) <= MAX_BATCH_SOURCES
            or any(not isinstance(key, str) for key in source_ids) or len(set(source_ids)) != len(source_ids)):
        raise ValueError("select between 1 and 64 distinct pending source IDs")
    state = saved["state"]
    received = state["received"]
    processed = set(state["processed"])
    if (not isinstance(evidence_ids, (list, tuple)) or len(evidence_ids) > MAX_BATCH_SOURCES
            or any(not isinstance(key, str) for key in evidence_ids) or len(set(evidence_ids)) != len(evidence_ids)):
        raise ValueError("select at most 64 distinct evidence source IDs")
    if not set(evidence_ids) <= processed:
        raise ValueError("additional evidence must already be processed")
    pending_ids = received.keys() - processed
    if not set(source_ids) <= pending_ids:
        raise ValueError("selected sources must all be durably received and pending")
    claims = [state["claims"][key] for key in sorted(state["claims"])]
    cited = {c["source"] for claim in claims for c in claim["evidence"]}
    extra = set(evidence_ids) - cited
    shown = set(source_ids) | cited | extra
    parents = {received[key]["replyTo"] for key in shown if "replyTo" in received[key]}
    reply_context = {key: wb.recorded_reply_context(received, processed, key) for key in sorted(parents - shown)}
    prepared = {"commit_binding": {"base_position": saved["reconciliation_position"], "batch": source_ids,
                                   "expected_state_sha256": state_digest(state)},
                "base_revision": state["revision"], "current_claims": claims,
                "incoming": {key: _retained_source_view(received[key]) for key in source_ids},
                "cited_sources": {key: _retained_source_view(received[key]) for key in sorted(cited)},
                "reply_context": reply_context, "other_pending_count": len(pending_ids) - len(source_ids),
                "boundary": "Local preparation only. Reply context is not a citation. Unselected pending text is withheld; no processing occurred."}
    if extra:
        prepared["additional_evidence"] = {key: _retained_source_view(received[key]) for key in sorted(extra)}
    if nominate_evidence:
        terms = set().union(*(wb.discovery_terms(received[key]["text"]) for key in source_ids
                              if received[key]["kind"] != "projection"))
        prepared["evidence_nominations"] = _rank_sources(state, terms, cited=cited, limit=8, exclude=shown)
    if len(provenance.encoded(prepared).encode()) > MAX_PREPARATION_BYTES:
        raise ValueError("batch preparation exceeds local byte bound; no evidence was trimmed")
    return prepared


def inspect_batch(path, prepared, proposal, *, query=None, scope=None):
    """Preview a saved reconciliation request without writing to the inbox."""
    if scope is not None and query is None:
        raise ValueError("reader comparison requires a nonempty lexical query")
    if not isinstance(proposal, dict) or set(proposal) != {"patch", "analysis", "route"}:
        raise ValueError("proposal requires exactly patch, analysis, and route")
    saved = snapshot(path)
    binding = prepared["commit_binding"]
    extra = list(prepared.get("additional_evidence", {}))
    if (binding["expected_state_sha256"] != state_digest(saved["state"])
            or prepared != _prepare_batch(saved, binding["batch"], extra, nominate_evidence="evidence_nominations" in prepared)):
        raise ValueError("batch preparation no longer matches this inbox")
    request = {**binding, **proposal}
    if len(provenance.encoded(request).encode()) > MAX_COMMIT_BYTES:
        raise ValueError("commit exceeds local byte bound")
    patch, analysis, route = (proposal[key] for key in ("patch", "analysis", "route"))
    state = saved["state"]
    updated = wb.commit(state, patch, binding["batch"], analysis, route)
    cited = {c["source"] for claim in analysis["assertions"] for c in claim["evidence"]}
    cited.update(c["source"] for op in patch["operations"] if op["op"] == "add" for c in op["assertion"]["evidence"])
    cited.update(c["source"] for disposition in patch["accounting"].values() for c in disposition.get("basis", []))
    if not cited <= prepared["incoming"].keys() | prepared["cited_sources"].keys() | set(extra):
        raise ValueError("proposal cites a source outside the prepared batch context")
    report = {"version": BATCH_INSPECTION_VERSION, "request": request,
              "before": wb.project(state), "after": wb.project(updated),
              "scope_impact": wb.scope_impact(state, updated),
              "recovery": wb.rehearse_recovery(state, updated),
              "semantic_judgment": "not-evaluated", "status": "inspected-in-isolated-copy"}
    if query is not None:
        report["reader_comparison"] = wb.compare_discovery(state, updated, query, scope=scope)
    report["inspection_sha256"] = state_digest(report)
    if len(json.dumps(report, indent=2).encode()) + 1 > MAX_BATCH_INSPECTION_BYTES:
        raise ValueError("batch inspection exceeds local byte bound")
    return report


def apply_batch(path, operation_id, report, *, inspection_sha256):
    """Commit the exact request in an explicitly selected local inspection."""
    if (not isinstance(report, dict) or report.get("version") != BATCH_INSPECTION_VERSION
            or report.get("inspection_sha256") != inspection_sha256
            or state_digest({key: value for key, value in report.items() if key != "inspection_sha256"}) != inspection_sha256):
        raise ValueError("exact batch inspection hash required")
    request = report.get("request")
    if (not isinstance(request, dict) or set(request) != {"base_position", "expected_state_sha256", "batch", "patch", "analysis", "route"}
            or not isinstance(request["expected_state_sha256"], str)):
        raise ValueError("batch inspection requires a snapshot-bound request")
    return commit(path, operation_id, **request)


def _read_bounded_json(path, limit):
    with Path(path).open("rb") as stream:
        raw = stream.read(limit + 1)
    if len(raw) > limit:
        raise ValueError("input file exceeds local byte bound")
    return json.loads(raw, object_pairs_hook=provenance.unique_object)


def _reader_state(path, at_position=None):
    with _reader(path) as db:
        position, state = _load(db)
        _, intake = _heads(db)
    if at_position is None:
        return state, {"reconciliation": position, "intake": intake}
    return wb.reconciliation_prefix(state, at_position), {"reconciliation": at_position, "intake": None}


def _reader_result(result, positions):
    if positions["intake"] is None:
        if "pending" in result:
            result["pending"] = None
        for field in ("reply_context", "derivation_inputs"):
            for entry in result.get(field, {}).values():
                if entry["status"] == "missing":
                    entry["status"] = "not-in-prefix"
        result["position_boundary"] = "Recorded reconciliation prefix only; historical intake and pending coverage are not reconstructed."
    return {**result, "positions": positions}


def evidence(path, claim_id, *, at_position=None, locate_quotes=False):
    state, positions = _reader_state(path, at_position)
    return _reader_result(wb.claim_evidence(state, claim_id, locate_quotes=locate_quotes), positions)


def claim_timeline(path, claim_id):
    """Show changes in active membership or reference resolution for an exact ID."""
    wb.validate("#ID", claim_id)
    saved = snapshot(path)
    state = saved["state"]
    position = saved["reconciliation_position"]
    events = []
    if claim_id in state["history"]:
        def reference(view):
            target = wb.resolve(view, claim_id)
            return {"active": claim_id in view["claims"], "resolves_to": target["id"] if target else None}

        before = reference(wb.historical_view(state, 0))
        for index, entry in enumerate(state["journal"], 1):
            view = wb.historical_view(state, index)
            after = reference(view)
            if after != before:
                events.append({"position": index, "revision": view["revision"], "kind": _entry_kind(entry),
                               "before": before, "after": after})
            before = after
    return {"claim_id": claim_id, "status": "known-claim" if claim_id in state["history"] else "unknown-claim",
            "reconciliation_position": position, "events": events,
            "boundary": "Recorded membership and reference changes only; not a source-time history or a truth verdict."}


def _source_status(state, source_id, at_position):
    if source_id not in state["received"]:
        return "unknown-source" if at_position is None else "not-in-prefix"
    return "processed" if source_id in state["processed"] else "pending"


def show_source(path, source_id, *, at_position=None):
    """Display one processed record, preserving retained excerpt boundaries."""
    wb.validate("#ID", source_id)
    state, positions = _reader_state(path, at_position)
    status = _source_status(state, source_id, at_position)
    record = _retained_source_view(state["received"][source_id]) if status == "processed" else None
    return _reader_result({"source_id": source_id, "status": status, "record": record,
                           "boundary": "Retained source only; not a verdict about authority or support."}, positions)


def _source_processing_history(state, source_id):
    events = []
    for position, entry in enumerate(state["journal"], 1):
        if entry["kind"] == "patch" and source_id in entry["batch"]:
            disposition = entry["patch"]["accounting"][source_id]
            events.append({"position": position, "kind": _entry_kind(entry), "status": "processed",
                           "disposition": {key: disposition[key] for key in ("mode", "claims", "reason")}})
        elif entry["kind"] == "restore":
            before = source_id in entry["beforeProcessed"]
            after = source_id in wb.historical_view(state, position)["processed"]
            if before != after:
                events.append({"position": position, "kind": "restore", "status": "processed" if after else "pending"})
    return events


def source_usage(path, source_id, *, at_position=None, processing_history=False):
    """List active and historical citations to one exact source ID."""
    wb.validate("#ID", source_id)
    state, positions = _reader_state(path, at_position)
    source = state["received"].get(source_id)
    status = _source_status(state, source_id, at_position)
    active, historical = [], []
    for key, claim in sorted(state["history"].items()):
        if any(citation["source"] == source_id for citation in claim["evidence"]):
            target = active if key in state["claims"] else historical
            target.append({"id": key, "scope": claim["scope"]})
    result = {"revision": state["revision"], "source_id": source_id, "status": status,
              "anchor": source["anchor"] if status == "processed" else None,
              "active": active, "historical": historical,
              "boundary": "Direct citations only; not reply links, derivation, or evidence of entailment."}
    if processing_history:
        result["processing_history"] = _source_processing_history(state, source_id)
        result["processing_boundary"] = "Recorded dispositions and coverage changes, not truth or current support."
    return _reader_result(result, positions)


def search_sources(path, query, *, limit=10, at_position=None):
    """Nominate processed original sources by lexical overlap, without returning text."""
    if type(limit) is not int or not 1 <= limit <= 64:
        raise ValueError("source search limit must be between 1 and 64")
    terms = wb.discovery_terms(query)
    if not terms:
        raise ValueError("source search requires a nonempty lexical query")
    state, positions = _reader_state(path, at_position)
    cited = {c["source"] for claim in state["claims"].values() for c in claim["evidence"]}
    return _reader_result(_rank_sources(state, terms, cited=cited, limit=limit), positions)


def _rank_sources(state, terms, *, cited, limit, exclude=()):
    hits = []
    for key in state["processed"]:
        source = state["received"][key]
        if key in exclude or source["kind"] == "projection":
            continue
        score = len(terms & wb.discovery_terms(source["text"]))
        if score:
            hits.append({"source_id": key, "anchor": source["anchor"], "score": score, "cited_by_active_claim": key in cited})
    hits.sort(key=lambda hit: (-hit["score"], hit["source_id"]))
    return {"hits": hits[:limit], "matching_sources": len(hits), "truncated": len(hits) > limit,
            "boundary": "Lexical nominations only. Pending sources and projections are not searched; matches do not establish support."}


def discover(path, query=None, *, scope=None, find_scopes=False, scope_history=None, at_position=None):
    """Read committed claims, history, and pending coverage at one durable position."""
    if sum((scope is not None, find_scopes, scope_history is not None)) > 1:
        raise ValueError("select at most one scope mode")
    if (query is None) != (scope_history is not None):
        raise ValueError("a query is required except for historical scope lookup")
    state, positions = _reader_state(path, at_position)
    if scope_history is not None:
        result = wb.discover_scope_history(state, scope_history)
    elif find_scopes:
        result = wb.discover_scopes(state, query)
    else:
        result = wb.discover(state, query, scope=scope)
    return _reader_result(result, positions)


def browse(path, scope, *, at_position=None):
    """Read every active claim under an explicitly selected exact label."""
    if scope is None:
        raise ValueError("browse requires an exact scope")
    state, positions = _reader_state(path, at_position)
    claims = wb.scoped_claims(state, scope)
    received = state["received"]
    sources = sorted({citation["source"] for claim in claims.values() for citation in claim["evidence"]})
    return _reader_result({"revision": state["revision"], "exact_scope": scope,
                           "status": "matches" if claims else "no-matching-knowledge",
                           "claims": [claims[key] for key in sorted(claims)],
                           "source_anchors": {key: received[key]["anchor"] for key in sources},
                           "pending": sorted(received.keys() - set(state["processed"])),
                           "boundary": "Exact active scope only; no inference about applicability or completeness."}, positions)


def compare(path, query, *, from_position, to_position, scope=None):
    """Compare two reconciliation prefixes of one read-only inbox snapshot."""
    if type(from_position) is not int or type(to_position) is not int or from_position >= to_position:
        raise ValueError("comparison requires two increasing reconciliation positions")
    state = snapshot(path)["state"]
    before, after = (wb.reconciliation_prefix(state, position) for position in (from_position, to_position))
    result = wb.compare_discovery(before, after, query, scope=scope)
    for key, position in (("before", from_position), ("after", to_position)):
        result[key] = _reader_result(result[key], {"reconciliation": position, "intake": None})
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", required=True, help="Local SQLite path in an existing directory")
    modes = parser.add_subparsers(dest="mode", required=True)
    accept = modes.add_parser("receive")
    accept.add_argument("--source-id", required=True)
    accept.add_argument("--source", required=True, help="JSON source record")
    bulk = modes.add_parser("receive-batch", help="Atomically receive an ordered JSON array of source records")
    bulk.add_argument("--sources", required=True, help="JSON array of {source_id, source} records")
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
    batch_preview = modes.add_parser("prepare-batch", help="Show selected pending sources and active claims for local reconciliation")
    batch_preview.add_argument("--source-id", action="append", required=True, help="Pending source ID; repeat to select a batch")
    batch_preview.add_argument("--evidence-id", action="append", default=[], help="Explicitly include an already-processed source as evidence")
    batch_preview.add_argument("--nominate-evidence", action="store_true", help="Suggest older sources by overlap with selected incoming text")
    inspection = modes.add_parser("inspect-batch", help="Preview a saved reconciliation patch against a prepared batch")
    inspection.add_argument("--prepared", required=True, help="Saved prepare-batch JSON")
    inspection.add_argument("--proposal", required=True, help="JSON with patch, analysis, and route")
    inspection.add_argument("--query", help="Compare local lexical search before and after the patch")
    inspection.add_argument("--scope", help="Restrict the comparison to this exact active scope")
    apply_inspection = modes.add_parser("apply-batch", help="Commit the request from an exact saved batch inspection")
    apply_inspection.add_argument("--inspection", required=True)
    apply_inspection.add_argument("--sha256", required=True)
    apply_inspection.add_argument("--operation-id", required=True)
    backlog = modes.add_parser("pending", help="List pending source IDs in intake order, without payloads")
    backlog.add_argument("--limit", type=int, default=20, help="Maximum rows to display (1–256)")
    export = modes.add_parser("snapshot")
    export.add_argument("--output", required=True, help="New JSON workbench inspection artifact")
    modes.add_parser("projection", help="Read the local projection and its freshness markers")
    modes.add_parser("refresh-projection", help="Catch up the local projection")
    trail = modes.add_parser("evidence", help="Read a claim's citations and recorded reply context")
    trail.add_argument("--claim", required=True, help="Exact active or historical claim ID")
    trail.add_argument("--quote-locations", action="store_true", help="List byte ranges for literal quotation matches")
    search = modes.add_parser("discover", help="Search a read-only snapshot of committed inbox state")
    search.add_argument("--query", help="Lexical search terms")
    scopes = search.add_mutually_exclusive_group()
    scopes.add_argument("--scope", help="Restrict current search to this exact scope")
    scopes.add_argument("--find-scopes", action="store_true", help="List candidate active scopes without selecting one")
    scopes.add_argument("--scope-history", help="Look up inactive claims by their original exact scope, without a query")
    browse_mode = modes.add_parser("browse", help="List all active claims under an exact scope without a lexical query")
    browse_mode.add_argument("--scope", required=True, help="Exact stored scope label")
    timeline = modes.add_parser("claim-timeline", help="Show recorded active membership and reference changes for an exact claim ID")
    timeline.add_argument("--claim", required=True)
    usage = modes.add_parser("source-usage", help="List active and historical claims citing an exact source ID")
    usage.add_argument("--source-id", required=True)
    usage.add_argument("--processing-history", action="store_true", help="Include recorded dispositions and processing changes")
    source_view = modes.add_parser("show-source", help="Show one processed source and its retained metadata")
    source_view.add_argument("--source-id", required=True)
    source_search = modes.add_parser("search-sources", help="Find processed sources by words in their retained text")
    source_search.add_argument("--query", required=True)
    source_search.add_argument("--limit", type=int, default=10)
    for reader in (trail, search, browse_mode, usage, source_view, source_search):
        reader.add_argument("--at-position", type=int, help="Read a recorded reconciliation prefix, not historical intake")
    comparison = modes.add_parser("compare", help="Compare lexical search at two recorded reconciliation positions")
    comparison.add_argument("--query", required=True)
    comparison.add_argument("--scope", help="Restrict both searches to this exact scope")
    comparison.add_argument("--from-position", type=int, required=True)
    comparison.add_argument("--to-position", type=int, required=True)
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
    elif args.mode == "receive-batch":
        with Path(args.sources).open("rb") as stream:
            raw = stream.read(MAX_BATCH_BYTES + 1)
        if len(raw) > MAX_BATCH_BYTES:
            raise ValueError("source batch file exceeds local byte bound")
        records = json.loads(raw, object_pairs_hook=provenance.unique_object)
        print(json.dumps(receive_batch(args.db, records)))
    elif args.mode in ("commit", "maintain", "restore", "replay"):
        with Path(args.request).open("rb") as stream:
            raw = stream.read(MAX_COMMIT_BYTES + 1)
        if len(raw) > MAX_COMMIT_BYTES:
            raise ValueError("commit file exceeds local byte bound")
        request = json.loads(raw, object_pairs_hook=provenance.unique_object)
        apply = {"commit": commit, "maintain": maintain, "restore": restore, "replay": replay}[args.mode]
        print(json.dumps(apply(args.db, args.operation_id, **request)))
    elif args.mode == "prepare-batch":
        print(json.dumps(prepare_batch(args.db, args.source_id, evidence_ids=args.evidence_id,
                                       nominate_evidence=args.nominate_evidence), indent=2))
    elif args.mode == "inspect-batch":
        prepared = _read_bounded_json(args.prepared, MAX_COMMIT_BYTES)
        proposal = _read_bounded_json(args.proposal, MAX_COMMIT_BYTES)
        print(json.dumps(inspect_batch(args.db, prepared, proposal, query=args.query, scope=args.scope), indent=2))
    elif args.mode == "apply-batch":
        report = _read_bounded_json(args.inspection, MAX_BATCH_INSPECTION_BYTES)
        print(json.dumps(apply_batch(args.db, args.operation_id, report, inspection_sha256=args.sha256)))
    elif args.mode == "pending":
        print(json.dumps(pending(args.db, limit=args.limit), indent=2))
    elif args.mode == "projection":
        print(json.dumps(projection(args.db)))
    elif args.mode == "refresh-projection":
        print(json.dumps(refresh_projection(args.db)))
    elif args.mode == "evidence":
        print(json.dumps(evidence(args.db, args.claim, at_position=args.at_position,
                                  locate_quotes=args.quote_locations), indent=2))
    elif args.mode == "claim-timeline":
        print(json.dumps(claim_timeline(args.db, args.claim), indent=2))
    elif args.mode == "search-sources":
        print(json.dumps(search_sources(args.db, args.query, limit=args.limit, at_position=args.at_position), indent=2))
    elif args.mode == "show-source":
        print(json.dumps(show_source(args.db, args.source_id, at_position=args.at_position), indent=2))
    elif args.mode == "source-usage":
        print(json.dumps(source_usage(args.db, args.source_id, at_position=args.at_position,
                                      processing_history=args.processing_history), indent=2))
    elif args.mode == "browse":
        print(json.dumps(browse(args.db, args.scope, at_position=args.at_position), indent=2))
    elif args.mode == "compare":
        print(json.dumps(compare(args.db, args.query, from_position=args.from_position,
                                 to_position=args.to_position, scope=args.scope), indent=2))
    elif args.mode == "discover":
        print(json.dumps(discover(args.db, args.query, scope=args.scope, find_scopes=args.find_scopes,
                                  scope_history=args.scope_history, at_position=args.at_position), indent=2))
    else:
        report = snapshot(args.db)
        with Path(args.output).open("x") as stream:
            json.dump(report, stream, indent=2, allow_nan=False)
            stream.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
