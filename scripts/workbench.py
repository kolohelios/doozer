"""A fixture-driven local reconciliation experiment, not a durable ingest service."""

import argparse
import copy
import functools
import json
from pathlib import Path
import re
import subprocess
import tempfile

from scripts.jev_probe import export_cue


ROOT = Path(__file__).resolve().parents[1]
CONTRACTS = ROOT / "experiments/workbench/contracts.cue"
SOURCE_FIELDS = ("kind", "text", "anchor", "saidAt", "scope", "replyTo", "derivedFrom")


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
    if source_id in state["received"] and state["received"][source_id] != value:
        raise ValueError("source identity reused with different content")
    state["received"][source_id] = value


def check_evidence(assertion, sources, *, canonical):
    seen = set()
    for citation in assertion["evidence"]:
        source_id, quote = citation["source"], citation["quote"]
        if source_id not in sources or quote not in sources[source_id]["text"]:
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


def commit(state, patch, batch, analysis, route):
    """Validate against a copy; publish all canonical effects or none."""
    validate("#Patch", patch)
    validate("#Analysis", analysis)
    validate("#Route", route)
    if patch["baseRevision"] != state["revision"]:
        raise ValueError("stale neighborhood revision")
    if not batch or len(batch) != len(set(batch)) or set(batch) & set(state["processed"]):
        raise ValueError("processing batch must contain distinct, not-yet-processed sources")
    if not set(batch) <= state["received"].keys():
        raise ValueError("unreceived processing batch")
    available_ids = set(state["processed"]) | set(batch)
    available = {key: state["received"][key] for key in available_ids}
    for assertion in analysis["assertions"]:
        check_evidence(assertion, available, canonical=False)
    proposed = copy.deepcopy(state)
    additions, retirements = {}, {}
    for operation in patch["operations"]:
        if operation["op"] == "add":
            assertion = operation["assertion"]
            claim_id = assertion["id"]
            if claim_id in state["history"] or claim_id in additions:
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
    proposed["journal"].append({
        "revision": proposed["revision"], "batch": list(batch),
        "before": copy.deepcopy(state["claims"]), "patch": copy.deepcopy(patch),
        "analysis": copy.deepcopy(analysis), "route": copy.deepcopy(route),
    })
    # Projection construction must succeed before publishing the new state.
    project(proposed)
    return proposed


def resolve(state, claim_id):
    visited = set()
    while claim_id in state["redirects"]:
        if claim_id in visited:
            raise ValueError("cyclic historical reference")
        visited.add(claim_id)
        claim_id = state["redirects"][claim_id]
    return copy.deepcopy(state["claims"].get(claim_id))


def project(state):
    lines = []
    for claim in state["claims"].values():
        refs = ", ".join(
            f"[{c['source']}]({state['received'][c['source']]['anchor']})"
            for c in claim["evidence"]
        )
        lines.append(f"- **{claim['scope']}** ({claim['attribution']}): {claim['text']} Sources: {refs}")
    body = "\n".join(lines) or "No reconciled claims yet."
    result = {
        "revision": state["revision"], "claims": list(state["claims"]),
        "handbook": "# Retry safety\n\n" + body,
        "agentContext": "# Scoped evidence context\n\nApply only within each stated scope; this context is not unconditional authorization.\n\n" + body,
    }
    validate("#Projection", result)
    return result


def discover(state, query):
    terms = set(re.findall(r"[a-z0-9]+", query.lower())) - {
        "the", "a", "an", "is", "are", "can", "i", "we", "what", "of", "to", "for", "in",
    }
    hits = []
    for claim_id, claim in state["claims"].items():
        aliases = [key for key in state["redirects"] if resolve(state, key)["id"] == claim_id]
        haystack = " ".join([claim_id, claim["text"], claim["scope"], *aliases]).lower()
        score = len(terms & set(re.findall(r"[a-z0-9]+", haystack)))
        if score:
            hits.append({
                "score": score, "claim": copy.deepcopy(claim),
                "sources": {c["source"]: state["received"][c["source"]]["anchor"] for c in claim["evidence"]},
            })
    return {
        "revision": state["revision"],
        "pending": sorted(set(state["received"]) - set(state["processed"])),
        "status": "matches" if hits else "no-matching-knowledge",
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
    args = parser.parse_args(argv)
    if args.live and args.inspect:
        parser.error("inspection is always offline")
    if args.output and Path(args.output).exists():
        parser.error("output already exists; use a new run path")
    try:
        if args.inspect:
            state = json.loads(Path(args.inspect).read_text())["state"]
            result = {"discovery": discover(state, args.query)}
            if args.reference:
                result["historical"] = state["history"].get(args.reference)
                result["current"] = resolve(state, args.reference)
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
