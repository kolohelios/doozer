"""Bounded public-source intake and saved-patch execution in isolated local state; no live calls."""

import argparse
import base64
import copy
import hashlib
import json
from pathlib import Path
import subprocess

from scripts import maintenance_proposer as proposer, provenance, standards_replay as replay, workbench as wb


TITLE = "HTTP problem details"


def implementation():
    paths = ("scripts/standards_maintenance.py", "scripts/standards_replay.py", "scripts/workbench.py",
             "scripts/maintenance_proposer.py", "scripts/provenance.py", "experiments/workbench/contracts.cue",
             "experiments/workbench/standards-maintenance.cue", "flake.lock")
    return {p: hashlib.sha256((wb.ROOT / p).read_bytes()).hexdigest() for p in paths}


def source_records(capture, plan, checkpoint):
    context = json.loads(replay.packet(capture, plan, checkpoint)["messages"][1]["content"])
    originals = {row["id"]: row for row in capture["sources"]}
    result = {}
    for key, row in context["sources"].items():
        original = originals[key]
        origin = {"artifact": key, "kind": row["kind"], "bodySHA256": original["bodySHA256"], "bodyBytes": original["bodyBytes"],
                  "captureSHA256": plan["captureSHA256"], "versionNotBefore": row["versionNotBefore"],
                  "availabilityBasis": row["availabilityBasis"], "attribution": row["attribution"], "thread": row["thread"],
                  "rights": "IETF TLP 5.0 section 3.c.iii; https://trustee.ietf.org/documents/trust-legal-provisions/tlp-5/"}
        if "legalNotice" in row:
            origin["legalNotice"] = row["legalNotice"]
        source = {"kind": "document" if row["kind"] in ("published-rfc", "internet-draft") else "conversation",
                  "text": "\n\n".join(e["text"] for e in row["excerpts"]), "excerpts": copy.deepcopy(row["excerpts"]),
                  "anchor": row["anchor"], "scope": "Recorded " + row["kind"] + "; scope/authority require interpretation.", "origin": origin}
        if row["statementAt"] is not None:
            source["saidAt"] = row["statementAt"]
        if row["actor"] is not None:
            source["attributedTo"] = copy.deepcopy(row["actor"])
        result[key] = source
    return result, context


def prepare(checkpoint_id, *, state=None, source_id=None, maintenance=False):
    capture, plan = replay.load()
    approval = replay.approval_status(capture, plan)
    settings = wb.export_cue(sorted((wb.ROOT / "experiments/workbench").glob("*.cue")))["standardsMaintenance"]
    if (settings["plannedCalls"] != 0 or settings["budgetUSD"] != 0 or settings["model"] is not None
            or settings["provider"] is not None or type(maintenance) is not bool or (maintenance and source_id is not None)):
        raise ValueError("invalid offline batch mode or execution authority")
    checkpoint = next((c for c in plan["checkpoints"] if c["id"] == checkpoint_id), None)
    if checkpoint is None:
        raise ValueError("unknown corpus cutoff")
    eligible, context = source_records(capture, plan, checkpoint)
    before = copy.deepcopy(wb.new_state() if state is None else state)
    if not set(before["received"]) <= eligible.keys():
        raise ValueError("state contains sources unavailable at this cutoff; no inferred historical filtering")
    if len(before["processed"]) != len(set(before["processed"])) or not set(before["processed"]) <= before["received"].keys():
        raise ValueError("invalid processing coverage")
    for key, source in eligible.items():
        wb.receive(before, key, source)  # Pure copy; redelivery cannot change source/version/attribution.
    available = {key: before["received"][key] for key in before["processed"]}
    for key, claim in before["claims"].items():
        wb.validate("#Assertion", claim)
        if claim["id"] != key or before["history"].get(key) != claim:
            raise ValueError("current claim disagrees with immutable history")
        wb.check_evidence(claim, available, canonical=True)
    pending = sorted(set(before["received"]) - set(before["processed"]),
                     key=lambda key: (before["received"][key]["origin"]["versionNotBefore"], key))
    if maintenance and not before["claims"]:
        raise ValueError("source-free maintenance needs an existing working view")
    if source_id is not None and source_id not in pending:
        raise ValueError("requested source is unavailable or already processed; do not fabricate intake")
    batch = [] if maintenance or not pending else [source_id or pending[0]]
    mode = "maintenance" if maintenance else "ingest" if batch else "idle"
    cited = {c["source"] for claim in before["claims"].values() for c in claim["evidence"]}
    shown = cited | set(batch)
    public_sources = {}
    for key in sorted(shown):
        value = copy.deepcopy(before["received"][key])
        del value["text"]  # Search index concatenation is never presented as continuous evidence.
        public_sources[key] = value
    public = {"as_of": checkpoint["asOf"], "mode": mode, "current_revision": before["revision"],
              "current_claims": copy.deepcopy(list(before["claims"].values())), "incoming": batch,
              "reserved_claim_ids": sorted(before["history"]), "existing_aliases": copy.deepcopy(before["redirects"]),
              "sources": public_sources, "unavailable_context": context["unavailableContext"],
              "coverage": {"received": len(before["received"]), "processed": len(before["processed"]),
                           "pending_outside_batch": len(pending) - len(batch),
                           "boundary": "One source artifact per batch; all current claims and their complete retained source excerpts are protected. Other pending text is withheld, not reconciled or globally absent."}}
    contract = subprocess.run(["cue", "def", str(wb.CONTRACTS), "-e", "#Patch"], check=True, capture_output=True, text=True).stdout
    messages = [] if mode == "idle" else [{"role": "system", "content": settings["instructions"] + "\n\nExact patch contract:\n" + contract},
                                           {"role": "user", "content": json.dumps(public, sort_keys=True)}]
    if len(json.dumps(messages).encode()) > settings["maxPromptBytes"]:
        raise ValueError("protected context plus batch exceeds byte bound; no source/claim truncation or processing")
    frozen = {"plan": settings, "capture_sha256": plan["captureSHA256"], "checkpoint": checkpoint,
              "before": before, "batch": batch, "mode": mode, "messages": messages, "shown_sources": sorted(shown),
              "implementation_sha256": implementation(),
              "evaluation": {"original_full_context_approval": approval, "original_reference": plan["references"][checkpoint_id],
                             "boundary": "Approved meanings refer to the original full cutoff contexts, not this partial working view or a generated patch. No semantic score or automatic acceptance follows."}}
    return {"status": "idle-no-unprocessed-source" if mode == "idle" else "prepared-offline-batch",
            "protocol": {"sha256": proposer.digest(frozen), "frozen": frozen}, "network_calls": 0, "canonical_acceptance": False}


def check(prepared):
    frozen = prepared["protocol"]["frozen"]
    if (prepared["status"] != "prepared-offline-batch" or proposer.digest(frozen) != prepared["protocol"]["sha256"]
            or frozen["implementation_sha256"] != implementation() or frozen["mode"] not in ("ingest", "maintenance")
            or frozen["plan"]["plannedCalls"] != 0 or frozen["plan"]["budgetUSD"] != 0):
        raise ValueError("changed/inactive preparation; never silently reapply or reassess")
    return frozen


def model_messages(prepared):
    """The prospective model boundary; never transmit the private preparation/state."""
    return copy.deepcopy(check(prepared)["messages"])


def view(state, *, title=TITLE):
    return {"revision": state["revision"], "claims": len(state["claims"]), "received": len(state["received"]),
            "processed": len(state["processed"]), "projection": wb.project(state, title=title)}


def inspect_proposal(prepared, raw):
    frozen = check(prepared)
    bound = frozen["plan"]["maxProposalBytes"]
    captured = raw[:bound]
    before = copy.deepcopy(frozen["before"])
    result = {"status": "not-applied", "protocol": copy.deepcopy(prepared["protocol"]),
              "input": {"base64": base64.b64encode(captured).decode(), "captured_bytes": len(captured),
                        "sha256": hashlib.sha256(captured).hexdigest(), "complete": len(raw) <= bound},
              "state": before, "network_calls": 0, "canonical_acceptance": False, "semantic_judgment": "not-evaluated"}
    if len(raw) > bound:
        result.update(status="oversized-not-applied", reason="Only a bounded prefix captured; retain original bytes.")
        return result
    try:
        patch = proposer.parse_proposal(raw, max_depth=frozen["plan"]["maxProposalDepth"])
    except (ValueError, UnicodeError, RecursionError):
        result.update(status="invalid-json-not-applied", reason="Strict JSON/depth validation failed; no repair.")
        return result
    result["proposal"] = copy.deepcopy(patch)
    try:
        wb.validate("#MaintenancePatch" if frozen["mode"] == "maintenance" else "#Patch", patch)
        additions = [copy.deepcopy(op["assertion"]) for op in patch["operations"] if op["op"] == "add"]
        citations = [c for assertion in additions for c in assertion["evidence"]]
        citations += [c for disposition in patch["accounting"].values() for c in disposition.get("basis", [])]
        if not {c["source"] for c in citations} <= set(frozen["shown_sources"]):
            raise ValueError("proposal cites source text outside the transmitted context")
        analysis = {"assertions": additions or copy.deepcopy(list(before["claims"].values()))}
        after = wb.commit(before, patch, frozen["batch"], analysis, {"action": "analyze"}, maintenance=frozen["mode"] == "maintenance")
    except (ValueError, KeyError, TypeError, OverflowError, RecursionError) as error:
        result.update(status="rejected-not-applied", failure={"type": type(error).__name__, "detail": str(error)})
        return result
    title = frozen.get("projection_title", TITLE)
    changed = wb.material(after) != wb.material(before)
    result.update(status="applied-in-isolated-copy" if patch["operations"] else "processing-only-in-isolated-copy" if changed else "no-op-in-isolated-copy",
                  state=after, derived_analysis=analysis, before=view(before, title=title), after=view(after, title=title), semantic_judgment="pending-human-review")
    if not changed:
        result["recovery"] = {"status": "not-exercised-no-change"}
        return result
    position = len(before["journal"])
    restored = wb.restore(after, {"baseRevision": after["revision"], "targetPosition": position,
                                  "reason": "Exercise the actual isolated batch proposal without publication."})
    replayed = wb.replay(restored, position, base_revision=restored["revision"])
    if (wb.material(restored) != wb.material(before) or wb.material(replayed) != wb.material(after)
            or replayed["history"] != after["history"] or replayed["received"] != after["received"]):
        raise ValueError("actual batch rollback/replay mismatch")
    result["recovery"] = {"status": "exercised", "material_recovered": True,
                          "restored": view(restored, title=title), "replayed": view(replayed, title=title), "state": replayed}
    return result


def read_json(path):
    with Path(path).open("rb") as stream:
        raw = stream.read(16 * 1024 * 1024 + 1)
    if len(raw) > 16 * 1024 * 1024:
        raise ValueError("local state/preparation exceeds artifact bound")
    value = json.loads(raw, object_pairs_hook=provenance.unique_object)
    provenance.encoded(value)
    return value


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, help="New private artifact; only model_messages() is prospective model input")
    parser.add_argument("--checkpoint")
    parser.add_argument("--state", help="Existing local workbench/inspection artifact containing state")
    parser.add_argument("--source-id", help="Explicit eligible unprocessed artifact; default oldest available version")
    parser.add_argument("--maintenance", action="store_true")
    parser.add_argument("--prepared")
    parser.add_argument("--proposal", help="Saved raw patch; never generated here")
    args = parser.parse_args(argv)
    if bool(args.prepared) != bool(args.proposal):
        parser.error("--prepared and --proposal are required together")
    if args.prepared and (args.checkpoint or args.state or args.source_id or args.maintenance):
        parser.error("saved inspection cannot change its source/cutoff/context")
    if not args.prepared and not args.checkpoint:
        parser.error("preparation requires --checkpoint")
    path = Path(args.output)
    if path.exists():
        raise ValueError("output exists; no overwrite")
    if args.prepared:
        prepared = read_json(args.prepared)
        frozen = check(prepared)
        with Path(args.proposal).open("rb") as stream:
            result = inspect_proposal(prepared, stream.read(frozen["plan"]["maxProposalBytes"] + 1))
    else:
        result = prepare(args.checkpoint, state=read_json(args.state)["state"] if args.state else None,
                         source_id=args.source_id, maintenance=args.maintenance)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x") as stream:
        stream.write(json.dumps(result, indent=2, allow_nan=False) + "\n")
    print(json.dumps({"output": str(path), "status": result["status"], "network_calls": 0, "canonical_acceptance": False}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
