"""A fixture-driven local reconciliation experiment, not a durable ingest service."""

import argparse
import copy
import functools
import hashlib
import json
from pathlib import Path
import re
import subprocess
import tempfile

from scripts.jev_probe import export_cue


ROOT = Path(__file__).resolve().parents[1]
CONTRACTS = ROOT / "experiments/workbench/contracts.cue"
SOURCE_FIELDS = ("kind", "text", "anchor", "saidAt", "scope", "replyTo", "derivedFrom", "attributedTo", "excerpts", "origin")


@functools.lru_cache(maxsize=512)
def _validate(definition, encoded):
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "value.json"
        path.write_text(encoded)
        result = subprocess.run(
            ["cue", "vet", "-c", str(CONTRACTS), str(path), "-d", definition],
            capture_output=True, text=True,
        )
    if result.returncode:
        raise ValueError(f"{definition} contract rejected; payload suppressed")


def validate(definition, value):
    _validate(definition, json.dumps(value, sort_keys=True, allow_nan=False))


def new_state():
    return {
        "revision": 0, "received": {}, "processed": [], "claims": {},
        "history": {}, "redirects": {}, "journal": [],
    }


def receive(state, source_id, source):
    value = {key: copy.deepcopy(source[key]) for key in SOURCE_FIELDS if key in source}
    if "excerpts" in value:
        citation_passages(value)
    if "origin" in value:
        validate("#SourceOrigin", value["origin"])
        if value["origin"]["artifact"] != source_id:
            raise ValueError("source identity disagrees with recorded origin")
    if source_id in state["received"] and state["received"][source_id] != value:
        raise ValueError("source identity reused with different content")
    state["received"][source_id] = value


def citation_passages(source):
    """Discontinuous excerpts share an artifact, but a citation cannot cross their gaps."""
    if "excerpts" not in source:
        return (source["text"],)
    validate("#SourceExcerpts", source["excerpts"])
    previous, passages = 0, []
    for excerpt in source["excerpts"]:
        raw = excerpt["text"].encode()
        if (not previous <= excerpt["startByte"] < excerpt["endByte"]
                or len(raw) != excerpt["endByte"] - excerpt["startByte"]
                or hashlib.sha256(raw).hexdigest() != excerpt["sha256"]
                or ("origin" in source and excerpt["endByte"] > source["origin"]["bodyBytes"])):
            raise ValueError("invalid source excerpt range or digest")
        previous = excerpt["endByte"]
        passages.append(excerpt["text"])
    if source["text"] != "\n\n".join(passages):
        raise ValueError("source index text disagrees with retained excerpts")
    return tuple(passages)


def check_evidence(assertion, sources, *, canonical):
    seen = set()
    for citation in assertion["evidence"]:
        source_id, quote = citation["source"], citation["quote"]
        if source_id not in sources or not any(quote in text for text in citation_passages(sources[source_id])):
            raise ValueError("unavailable source or fabricated quotation")
        if canonical and sources[source_id]["kind"] == "projection":
            raise ValueError("derived projections cannot corroborate canonical claims")
        if (source_id, quote) in seen:
            raise ValueError("duplicate citation")
        seen.add((source_id, quote))


def retrieval(state, analysis):
    query = " ".join(item["text"] + " " + item["scope"] for item in analysis["assertions"])
    terms = set(re.findall(r"[a-z0-9]+", query.lower()))
    cited = {c["source"] for item in analysis["assertions"] for c in item["evidence"]}
    scores = []
    for claim_id, claim in state["claims"].items():
        words = set(re.findall(r"[a-z0-9]+", (claim["text"] + " " + claim["scope"]).lower()))
        linked = any(c["source"] in cited for c in claim["evidence"])
        score = len(terms & words) + 10 * linked
        if score:
            scores.append((score, claim_id))
    result = {
        "method": "lexical-and-links", "revision": state["revision"],
        "candidates": [key for _, key in sorted(scores, key=lambda x: (-x[0], x[1]))],
        "protected": copy.deepcopy(list(state["claims"].values())),
    }
    validate("#Retrieval", result)
    return result


def commit(state, patch, batch, analysis, route, *, replay_of=None, maintenance=False):
    """Validate against a copy; publish all canonical effects or none."""
    if type(maintenance) is not bool:
        raise ValueError("maintenance mode must be explicit boolean")
    validate("#Patch", patch)
    validate("#Analysis", analysis)
    validate("#Route", route)
    if patch["baseRevision"] != state["revision"]:
        raise ValueError("stale neighborhood revision")
    if maintenance and batch:
        raise ValueError("maintenance cannot pretend to ingest new evidence")
    if (not batch and not maintenance) or len(batch) != len(set(batch)) or set(batch) & set(state["processed"]):
        raise ValueError("processing batch must contain distinct, not-yet-processed sources")
    if not set(batch) <= state["received"].keys():
        raise ValueError("unreceived processing batch")
    available_ids = set(state["processed"]) | set(batch)
    available = {key: state["received"][key] for key in available_ids}
    for assertion in analysis["assertions"]:
        check_evidence(assertion, available, canonical=False)
    if replay_of is not None:
        original = replay_record(state, replay_of)
        expected = copy.deepcopy(original["patch"])
        expected["baseRevision"] = state["revision"]
        if (patch != expected or batch != original["batch"] or maintenance != original.get("maintenance", False)
                or analysis != original["analysis"] or route != original["route"]
                or material(state) != material(historical_view(state, replay_of))):
            raise ValueError("replay requires the exact accepted patch and original material preconditions")
    proposed = copy.deepcopy(state)
    additions, retirements = {}, {}
    for operation in patch["operations"]:
        if operation["op"] == "add":
            assertion = operation["assertion"]
            claim_id = assertion["id"]
            if (claim_id in additions or claim_id in state["claims"]
                    or (claim_id in state["history"] and (replay_of is None or state["history"][claim_id] != assertion))):
                raise ValueError("claim identity already exists; use an explicit new revision")
            check_evidence(assertion, available, canonical=True)
            additions[claim_id] = copy.deepcopy(assertion)
        else:
            claim_id = operation["id"]
            if claim_id not in state["claims"] or claim_id in retirements:
                raise ValueError("retirement must name one active claim exactly once")
            retirements[claim_id] = operation
    active = copy.deepcopy(state["claims"])
    active.update(additions)
    for claim_id, retirement in retirements.items():
        replacement = retirement["replacement"]
        if replacement not in active or replacement in retirements or replacement == claim_id:
            raise ValueError("retirement requires a surviving replacement")
        old_evidence = {c["source"] for c in active[claim_id]["evidence"]}
        new_evidence = {c["source"] for c in active[replacement]["evidence"]}
        if not old_evidence <= new_evidence:
            raise ValueError("replacement drops source discovery paths")
        proposed["redirects"][claim_id] = replacement
        del active[claim_id]
    if set(patch["accounting"]) != set(batch):
        raise ValueError("unaccounted or extraneous incoming source")
    for source_id, disposition in patch["accounting"].items():
        claim_ids = disposition["claims"]
        if not set(claim_ids) <= active.keys():
            raise ValueError("source accounting must name surviving claims")
        cited = {c["source"] for claim_id in claim_ids for c in active[claim_id]["evidence"]}
        if disposition["mode"] == "represented":
            if source_id not in cited:
                raise ValueError("incoming source is not represented by its declared claims")
        else:
            basis = disposition["basis"]
            check_evidence({"evidence": basis},
                           {key: state["received"][key] for key in state["processed"]}, canonical=True)
            if not {item["source"] for item in basis} <= cited:
                raise ValueError("dependent no-op basis must support the declared claims")
    # No old active claim can disappear without an explicit retirement record.
    proposed["claims"] = active
    proposed["history"].update(copy.deepcopy(additions))
    proposed["processed"] = sorted(available_ids)
    if patch["operations"]:
        proposed["revision"] += 1
    if maintenance and not patch["operations"]:
        return copy.deepcopy(state)  # No source processing or semantic effect to journal.
    proposed["journal"].append({
        "kind": "patch", "maintenance": maintenance, "revision": proposed["revision"], "batch": list(batch),
        **before_record(state), "replayOf": replay_of, "patch": copy.deepcopy(patch),
        "analysis": copy.deepcopy(analysis), "route": copy.deepcopy(route),
    })
    # Projection construction must succeed before publishing the new state.
    project(proposed)
    return proposed


def maintain(state, patch, analysis, route):
    """Source-free local maintenance; only already-processed evidence is eligible."""
    return commit(state, patch, [], analysis, route, maintenance=True)


def material(state):
    """Operational knowledge/processing view, not natural-language equivalence."""
    return {key: copy.deepcopy(state[key]) for key in ("claims", "redirects", "processed")}


def before_record(state):
    return {"before": copy.deepcopy(state["claims"]), "beforeRedirects": copy.deepcopy(state["redirects"]),
            "beforeProcessed": list(state["processed"]), "beforeRevision": state["revision"]}


def historical_view(state, position):
    """View after a journal prefix; positions include processing-only no-ops."""
    if type(position) is not int or not 0 <= position <= len(state["journal"]):
        raise ValueError("invalid historical journal position")
    if position == len(state["journal"]):
        return {"revision": state["revision"], **material(state)}
    record = state["journal"][position]
    if not {"before", "beforeRedirects", "beforeProcessed", "beforeRevision"} <= record.keys():
        raise ValueError("legacy journal lacks recovery metadata; no inferred repair")
    return {"revision": record["beforeRevision"], "claims": copy.deepcopy(record["before"]),
            "redirects": copy.deepcopy(record["beforeRedirects"]), "processed": list(record["beforeProcessed"])}


def restore(state, request):
    """Append a compensating local recovery event; never erase sources/history."""
    validate("#Restore", request)
    if request["baseRevision"] != state["revision"]:
        raise ValueError("stale restore revision")
    if not request["reason"].strip():
        raise ValueError("restore needs a reason")
    view = historical_view(state, request["targetPosition"])
    if material(view) == material(state):
        return copy.deepcopy(state)
    available = {key: state["received"][key] for key in view["processed"]}
    for claim_id, claim in view["claims"].items():
        if state["history"].get(claim_id) != claim:
            raise ValueError("recovery cannot rewrite immutable claim history")
        check_evidence(claim, available, canonical=True)
    proposed = copy.deepcopy(state)
    proposed.update(material(view))
    proposed["revision"] += 1  # Do not reset versions and make stale patches current again.
    proposed["journal"].append({"kind": "restore", "revision": proposed["revision"],
                                **before_record(state), "request": copy.deepcopy(request)})
    for alias in proposed["redirects"]:
        if resolve(proposed, alias) is None:
            raise ValueError("recovery contains a broken historical reference")
    project(proposed)
    return proposed


def replay_record(state, position):
    historical_view(state, position)  # Validate position and recovery metadata.
    if position == len(state["journal"]) or state["journal"][position].get("kind") != "patch":
        raise ValueError("replay requires a recorded patch, not a restore event")
    return copy.deepcopy(state["journal"][position])


def replay(state, position, *, base_revision):
    """Revalidate one exact prior local patch against its original material view."""
    if type(base_revision) is not int or base_revision != state["revision"]:
        raise ValueError("stale replay revision")
    record = replay_record(state, position)
    patch = copy.deepcopy(record["patch"])
    patch["baseRevision"] = base_revision
    return commit(state, patch, record["batch"], record["analysis"], record["route"], replay_of=position, maintenance=record.get("maintenance", False))


def resolve(state, claim_id):
    visited = set()
    while claim_id in state["redirects"]:
        if claim_id in visited:
            raise ValueError("cyclic historical reference")
        visited.add(claim_id)
        claim_id = state["redirects"][claim_id]
    return copy.deepcopy(state["claims"].get(claim_id))


def _check_scope(scope):
    if not isinstance(scope, str) or not scope.strip():
        raise ValueError("scope must be a nonempty exact label")


def scoped_claims(state, scope):
    if scope is None:
        return state["claims"]
    _check_scope(scope)
    return {key: claim for key, claim in state["claims"].items() if claim["scope"] == scope}


def project(state, *, title="Retry safety", scope=None):
    claims = scoped_claims(state, scope)
    lines = []
    for claim in claims.values():
        refs = ", ".join(
            f"[{c['source']}]({state['received'][c['source']]['anchor']})"
            for c in claim["evidence"]
        )
        lines.append(f"- **{claim['scope']}** ({claim['attribution']}): {claim['text']} Sources: {refs}")
    body = "\n".join(lines) or ("No reconciled claims yet." if scope is None else "No reconciled claims match the requested scope.")
    coverage = f"Processed source snapshot: {len(state['processed'])} of {len(state['received'])} locally received sources."
    if set(state["received"]) - set(state["processed"]):
        coverage += " Received evidence remains unreconciled; this view does not include all received material."
    if scope is not None:
        coverage += " Exact scope selection only; it does not determine which guidance is current or complete."
    cited = sorted({c["source"] for claim in claims.values() for c in claim["evidence"]})
    notices = []
    for key in cited:
        origin = state["received"][key].get("origin")
        if origin:
            notices.append(origin["attribution"] + "\n\n" + origin["rights"] + "\n\n" + origin.get("legalNotice", ""))
    if notices:
        body += "\n\n## Source attribution and separate terms\n\n" + "\n\n".join(notices)
    result = {
        "revision": state["revision"], "claims": list(claims),
        "handbook": "# " + title + "\n\n" + coverage + "\n\n" + body,
        "agentContext": "# Scoped evidence context\n\nApply only within each stated scope; this context is not unconditional authorization.\n\n" + coverage + "\n\n" + body,
    }
    validate("#Projection", result)
    return result


def discovery_terms(query):
    return set(re.findall(r"[a-z0-9]+", query.lower())) - {
        "the", "a", "an", "is", "are", "can", "i", "we", "what", "of", "to", "for", "in",
    }


def discover_scopes(state, query):
    """Nominate stored scope labels, without deciding applicability."""
    terms = discovery_terms(query)
    matches = {}
    for claim_id, claim in state["claims"].items():
        words = set(re.findall(r"[a-z0-9]+", (claim["text"] + " " + claim["scope"]).lower()))
        if terms & words:
            matches.setdefault(claim["scope"], []).append(claim_id)
    return {
        "revision": state["revision"],
        "pending": sorted(set(state["received"]) - set(state["processed"])),
        "status": "scope-options" if matches else "no-matching-scopes",
        "coverage": {"processed_sources": list(state["processed"]),
                     "boundary": "Lexical matches in active claims only, not historical aliases. No scope is selected or inferred applicable. No match does not establish global absence."},
        "options": [{"scope": scope, "matched_claim_ids": sorted(ids)} for scope, ids in sorted(matches.items())],
    }


def recorded_reply_context(received, processed, parent):
    """Distinguish a visible parent from pending intake and missing context."""
    if parent not in processed:
        return {"status": "pending" if parent in received else "missing"}
    record = received[parent]
    return {"status": "processed", "anchor": record["anchor"], "passages": list(citation_passages(record))}


def claim_evidence(state, claim_id):
    """Read literal citations and one hop of recorded reply context for an exact claim ID."""
    active = claim_id in state["claims"]
    claim = state["claims"].get(claim_id) if active else state["history"].get(claim_id)
    result = {"revision": state["revision"], "status": "active-claim" if active else "historical-claim" if claim else "unknown-claim",
              "claim": copy.deepcopy(claim), "citations": [], "reply_context": {},
              "boundary": "Recorded citations are not entailment verdicts. Reply parents are context, not independent support."}
    if claim is None:
        return result
    received, processed = state["received"], set(state["processed"])
    for citation in claim["evidence"]:
        key = citation["source"]
        source = received[key]
        entry = {**citation, "anchor": source["anchor"], "coverage": "processed" if key in processed else "pending"}
        if "replyTo" in source:
            parent = source["replyTo"]
            entry["reply_to"] = parent
            if parent not in result["reply_context"]:
                result["reply_context"][parent] = recorded_reply_context(received, processed, parent)
        result["citations"].append(entry)
    return result


def discover_scope_history(state, scope):
    """Find inactive assertions by their original exact scope, not as current guidance."""
    _check_scope(scope)
    records = []
    for ref, historical in sorted(state["history"].items()):
        if ref in state["claims"] or historical["scope"] != scope:
            continue
        target = resolve(state, ref)
        records.append({"historical": copy.deepcopy(historical),
                        "sources": {c["source"]: state["received"][c["source"]]["anchor"] for c in historical["evidence"]},
                        "current_reference": {"id": target["id"], "scope": target["scope"]} if target else None})
    return {"revision": state["revision"], "exact_scope": scope, "records": records,
            "status": "historical-matches" if records else "no-matching-history",
            "pending": sorted(set(state["received"]) - set(state["processed"])),
            "boundary": "Inactive assertions only. A current reference does not establish applicability to the historical scope."}


def discover(state, query, *, scope=None):
    terms = discovery_terms(query)
    hits = []
    for claim_id, claim in scoped_claims(state, scope).items():
        aliases = [key for key in state["redirects"]
                   if (scope is None or state["history"][key]["scope"] == scope) and resolve(state, key)["id"] == claim_id]
        former = [state["history"][key] for key in aliases]
        haystack = " ".join([claim_id, claim["text"], claim["scope"], *aliases,
                             *(item["text"] + " " + item["scope"] for item in former)]).lower()
        score = len(terms & set(re.findall(r"[a-z0-9]+", haystack)))
        if score:
            hits.append({
                "score": score, "claim": copy.deepcopy(claim),
                "historical_matches": [item["id"] for item in former if terms & set(re.findall(r"[a-z0-9]+", (item["text"] + " " + item["scope"]).lower()))],
                "sources": {c["source"]: state["received"][c["source"]]["anchor"] for c in claim["evidence"]},
            })
    return {
        "revision": state["revision"],
        "pending": sorted(set(state["received"]) - set(state["processed"])),
        "status": "matches" if hits else "no-matching-knowledge",
        "coverage": {"processed_sources": list(state["processed"]),
                     "boundary": "Bounded local lexical search; no match does not establish global absence.",
                     **({"exact_scope": scope, "scope_boundary": "Scope selection does not infer applicability or supersession."}
                        if scope is not None else {})},
        "hits": sorted(hits, key=lambda item: (-item["score"], item["claim"]["id"])),
    }


def process_batch(state, batch, backend, step_id):
    available = set(state["processed"]) | set(batch)
    if not available <= state["received"].keys():
        raise ValueError("corpus schedule processes unreceived evidence")
    context = {
        "sources": {key: copy.deepcopy(state["received"][key]) for key in sorted(available)},
        "incoming": batch, "already_processed": list(state["processed"]),
        "currentRevision": state["revision"],
        "current": copy.deepcopy(list(state["claims"].values())),
    }
    route = backend.route(step_id, copy.deepcopy(context))
    validate("#Route", route)
    # Routing cannot silently discard a newly received source or authorize a write.
    disposition = "analyze" if route["action"] == "no-op" else route["action"]
    context["route"] = {"action": disposition}
    analysis = backend.analyze(step_id, copy.deepcopy(context))
    validate("#Analysis", analysis)
    ids = [item["id"] for item in analysis["assertions"]]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate analysis assertion identity")
    for assertion in analysis["assertions"]:
        check_evidence(assertion, context["sources"], canonical=False)
    context["analysis"] = analysis
    context["retrieval"] = retrieval(state, analysis)
    patch = backend.reason(step_id, copy.deepcopy(context))
    return commit(state, patch, batch, analysis, route), disposition


def run(scenario, backend, *, through=None, checkpoint=None):
    state, snapshots = new_state(), []
    step_ids = {step["id"] for step in scenario["steps"]}
    if through is not None and through not in step_ids:
        raise ValueError("unknown stopping checkpoint")
    for step in scenario["steps"]:
        for source_id in step["receive"]:
            receive(state, source_id, scenario["sources"][source_id])
        # Capture receipt before model work; this local artifact is not an ingest ACK.
        if checkpoint:
            checkpoint(state, snapshots, backend.trace)
        batch = sorted(set(step["reconcile"]) - set(state["processed"]))
        disposition = "received-only" if not step["reconcile"] else "exact-replay"
        if batch:
            try:
                state, disposition = process_batch(state, batch, backend, step["id"])
            except (ValueError, KeyError, TypeError, OSError, subprocess.CalledProcessError):
                if checkpoint:
                    checkpoint(state, snapshots, backend.trace)
                raise
        snapshots.append({
            "step": step["id"], "disposition": disposition,
            "revision": state["revision"],
            "pending": sorted(set(state["received"]) - set(state["processed"])),
            "projection": project(state),
            "discovery": discover(state, "notifications"),
        })
        if checkpoint:
            checkpoint(state, snapshots, backend.trace)
        if step["id"] == through:
            break
    return {"state": state, "snapshots": snapshots, "trace": backend.trace}


def review(scenario, snapshots):
    """Evaluator-side rubrics, joined only after all model stages have finished."""
    expected = {step["id"]: step["expect"] for step in scenario["steps"]}
    actual = {item["step"]: item for item in snapshots}
    result = []
    for snapshot in snapshots:
        rubric = expected[snapshot["step"]]
        structural = {"pending_matches": snapshot["pending"] == rubric["pending"]}
        if "equivalentTo" in rubric:
            old = actual[rubric["equivalentTo"]]
            structural["active_claims_unchanged"] = snapshot["projection"]["claims"] == old["projection"]["claims"]
        result.append({
            "step": snapshot["step"], "structural": structural,
            "required": rubric["must"], "forbidden": rubric["mustNot"],
            "actual": snapshot["projection"]["handbook"],
            "semantic_judgment": "pending-human-review",
        })
    return result


def save(path, state, snapshots, trace, *, evaluation=None):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    # Atomic visibility of a local snapshot, not a claim of fsync/crash durability.
    with tempfile.NamedTemporaryFile(mode="w", dir=path.parent, delete=False) as stream:
        temporary = Path(stream.name)
        json.dump({"state": state, "snapshots": snapshots, "trace": trace, "evaluation": evaluation}, stream, indent=2, allow_nan=False)
    temporary.replace(path)


def main(argv=None):
    from scripts.workbench_models import LiveBackend, RecordedBackend

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--router", choices=("rules", "jev"), default="rules", help="live routing backend; default rules makes no routing API call")
    parser.add_argument("--analysis-model")
    parser.add_argument("--reasoning-model")
    parser.add_argument("--budget-usd", type=float)
    parser.add_argument("--max-calls", type=int, default=18)
    parser.add_argument("--through")
    files = parser.add_mutually_exclusive_group(required=True)
    files.add_argument("--output", help="new local JSON artifact, e.g. runs/retry.json")
    files.add_argument("--inspect", help="inspect an existing artifact offline; never calls models")
    parser.add_argument("--query", default="notifications", help="lexical query for --inspect")
    parser.add_argument("--reference", help="historical claim ID to resolve with --inspect")
    scopes = parser.add_mutually_exclusive_group()
    scopes.add_argument("--scope", help="exact claim scope for offline discovery and projection")
    scopes.add_argument("--find-scopes", action="store_true", help="list candidate scopes for the query without selecting one")
    scopes.add_argument("--scope-history", help="look up inactive assertions by their original exact scope")
    args = parser.parse_args(argv)
    if args.live and args.inspect:
        parser.error("inspection is always offline")
    if (args.scope is not None or args.find_scopes or args.scope_history is not None) and not args.inspect:
        parser.error("scope options require --inspect")
    if (args.find_scopes or args.scope_history is not None) and args.reference:
        parser.error("resolve references separately from scope lookups")
    if args.output and Path(args.output).exists():
        parser.error("output already exists; use a new run path")
    try:
        if args.inspect:
            artifact = json.loads(Path(args.inspect).read_text())
            # Batch inspection reports nest the same saved state under inspection.
            state = artifact["state"] if "state" in artifact else artifact["inspection"]["state"]
            if args.find_scopes:
                print(json.dumps(discover_scopes(state, args.query), indent=2))
                return 0
            if args.scope_history is not None:
                print(json.dumps(discover_scope_history(state, args.scope_history), indent=2))
                return 0
            result = {"discovery": discover(state, args.query, scope=args.scope)}
            if args.scope is not None:
                result["projection"] = project(state, scope=args.scope, title="Selected scope")
            if args.reference:
                result["historical"] = state["history"].get(args.reference)
                target = resolve(state, args.reference)
                result["current"] = target if args.scope is None or (target and target["scope"] == args.scope) else None
            print(json.dumps(result, indent=2))
            return 0
        output = Path(args.output)
        corpus = export_cue(sorted((ROOT / "corpus").glob("*.cue")))
        backend = LiveBackend(args) if args.live else RecordedBackend()
        result = run(
            corpus["scenarios"]["retry-safety"], backend, through=args.through,
            checkpoint=lambda state, snapshots, trace: save(output, state, snapshots, trace),
        )
        save(output, result["state"], result["snapshots"], backend.trace,
             evaluation=review(corpus["scenarios"]["retry-safety"], result["snapshots"]))
        print(json.dumps({
            "mode": "live" if args.live else "recorded",
            "output": str(output), "revision": result["state"]["revision"],
            "checkpoints": len(result["snapshots"]), "stage_records": len(backend.trace),
            "network_calls": sum(item["network"] for item in backend.trace),
            "semantic_accuracy": "not-automatically-scored; review against corpus rubrics",
        }, indent=2))
        return 0
    except (ValueError, KeyError, TypeError, subprocess.CalledProcessError, OSError):
        print("Workbench stopped: invalid contract, model configuration, budget, or transport. No invalid patch was committed; inspect the last local artifact.")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
