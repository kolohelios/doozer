"""Read-only PROV-O/JSON-LD projection of recorded local workbench state."""

import argparse
import hashlib
import json
from pathlib import Path

from scripts import workbench as wb


CONTEXT = {"prov": "http://www.w3.org/ns/prov#", "doozer": "urn:doozer:vocab:"}
MAX_INPUT_BYTES = 4 * 1024 * 1024


def encoded(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def project(state, *, dataset_id, projection_title="Retry safety"):
    """Describe recorded provenance, not truth, authenticated authorship, or authority."""
    if not isinstance(dataset_id, str) or not dataset_id.strip():
        raise ValueError("an explicit dataset identity is required")
    encoded(state)  # Reject non-finite/unserializable state before creating a projection.
    namespace = hashlib.sha256(dataset_id.encode()).hexdigest()
    nodes = {}

    def identity(kind, payload):
        return f"urn:doozer:prov:{namespace}:{kind}:{hashlib.sha256(encoded(payload).encode()).hexdigest()}"

    def ref(identifier):
        return {"@id": identifier}

    def entity(kind, payload, **properties):
        identifier = identity(kind, payload)
        nodes[identifier] = {"@id": identifier, "@type": "prov:Entity", "doozer:representationKind": kind, **properties}
        return identifier

    sources = {key: identity("source-record", {"id": key, "record": value}) for key, value in state["received"].items()}
    for key, source in sorted(state["received"].items()):
        if any(not isinstance(source.get(field), str) or not source[field] for field in ("kind", "text", "anchor")):
            raise ValueError("invalid source record")
        if any(field in source and not isinstance(source[field], str) for field in ("saidAt", "replyTo")):
            raise ValueError("invalid source context metadata")
        parents = source.get("derivedFrom", [])
        if not isinstance(parents, list) or any(not isinstance(parent, str) for parent in parents):
            raise ValueError("invalid declared source derivation")
        identifier = entity("source-record", {"id": key, "record": source}, **{
            "doozer:sourceId": key, "doozer:sourceKind": source["kind"], "doozer:recordJSON": encoded(source)})
        if "attributedTo" in source:
            actor = source["attributedTo"]
            if (not isinstance(actor, dict) or set(actor) != {"id", "label", "basis"}
                    or any(not isinstance(value, str) or not value.strip() for value in actor.values())):
                raise ValueError("invalid recorded source attribution")
            agent = entity("recorded-agent", actor, **{"@type": "prov:Agent", "doozer:recordedIdentity": actor["id"],
                                                       "doozer:label": actor["label"], "doozer:attributionBasis": actor["basis"]})
            nodes[identifier]["prov:wasAttributedTo"] = ref(agent)
        if "saidAt" in source:
            nodes[identifier]["doozer:statementTime"] = source["saidAt"]  # Not generation, receipt, or validity time.
        if "replyTo" in source:
            nodes[identifier]["doozer:replyToSourceId"] = source["replyTo"]
            if source["replyTo"] in sources:
                nodes[identifier]["doozer:replyTo"] = ref(sources[source["replyTo"]])
        if "derivedFrom" in source:
            nodes[identifier]["doozer:declaredDerivationSourceIdsJSON"] = encoded(source["derivedFrom"])
            nodes[identifier]["prov:wasDerivedFrom"] = [ref(sources[parent]) for parent in source["derivedFrom"] if parent in sources]

    claims = {}
    for key, claim in sorted(state["history"].items()):
        wb.validate("#Assertion", claim)
        if key != claim["id"]:
            raise ValueError("claim history identity mismatch")
        wb.check_evidence(claim, state["received"], canonical=True)
        quotations = []
        for citation in claim["evidence"]:
            quote = entity("quotation", {"source": sources[citation["source"]], "quote": citation["quote"]}, **{
                "prov:value": citation["quote"], "prov:wasQuotedFrom": ref(sources[citation["source"]])})
            quotations.append(ref(quote))
        claims[key] = entity("assertion-record", claim, **{
            "doozer:claimId": key, "doozer:recordJSON": encoded(claim), "doozer:cites": quotations})
        # Citations do not prove entailment or the proposer's actual reasoning process.

    snapshots, activities = [], []
    for position in range(len(state["journal"]) + 1):
        view = wb.historical_view(state, position)  # Reject legacy records; never infer missing recovery metadata.
        if not set(view["processed"]) <= sources.keys():
            raise ValueError("snapshot refers to unavailable processed sources")
        available = {key: state["received"][key] for key in view["processed"]}
        for key, claim in view["claims"].items():
            if state["history"].get(key) != claim:
                raise ValueError("snapshot rewrites immutable claim history")
            wb.check_evidence(claim, available, canonical=True)
        snapshot = entity("knowledge-snapshot", {"position": position, "view": view}, **{
            "doozer:datasetId": dataset_id, "doozer:journalPosition": position, "doozer:localRevision": view["revision"],
            "prov:hadMember": [ref(claims[key]) for key in sorted(view["claims"])],
            "doozer:processedSources": [ref(sources[key]) for key in sorted(view["processed"])],
            "doozer:aliasesJSON": encoded(view["redirects"])})
        nodes[snapshot]["@type"] = ["prov:Entity", "prov:Collection"]
        if position:
            record = state["journal"][position - 1]
            kind = record.get("kind")
            if kind not in ("patch", "restore") or record["revision"] != view["revision"]:
                raise ValueError("unsupported or inconsistent journal event")
            payload = record["patch"] if kind == "patch" else record["request"]
            wb.validate("#Patch" if kind == "patch" else "#Restore", payload)
            submitted = entity("patch-input" if kind == "patch" else "restore-request", payload, **{"prov:value": encoded(payload)})
            activity = identity("local-commit", {"position": position - 1, "record": record})
            nodes[activity] = {"@id": activity, "@type": "prov:Activity", "doozer:eventKind": kind,
                               "doozer:journalPosition": position - 1, "prov:used": [ref(snapshots[-1]), ref(submitted)]}
            if kind == "patch":
                nodes[activity]["doozer:maintenance"] = record["maintenance"]
                for operation in payload["operations"]:
                    if operation["op"] == "add":
                        claim = operation["assertion"]
                        if state["history"].get(claim["id"]) != claim:
                            raise ValueError("journal addition disagrees with immutable history")
                        if record.get("replayOf") is None:
                            nodes[claims[claim["id"]]].setdefault("prov:wasGeneratedBy", ref(activity))
                replay = record.get("replayOf")
                if replay is not None:
                    if type(replay) is not int or not 0 <= replay < len(activities):
                        raise ValueError("invalid recorded replay reference")
                    nodes[activity]["doozer:replayOf"] = ref(activities[replay])
            else:
                target = payload["targetPosition"]
                if not 0 <= target < len(snapshots):
                    raise ValueError("invalid recorded restore target")
                nodes[activity]["prov:used"].append(ref(snapshots[target]))
                nodes[snapshot]["prov:wasDerivedFrom"] = [ref(snapshots[target])]
            nodes[snapshot]["prov:wasGeneratedBy"] = ref(activity)
            nodes[snapshot]["prov:wasRevisionOf"] = ref(snapshots[-1])
            activities.append(activity)
        snapshots.append(snapshot)

    rendered = wb.project(state, title=projection_title)
    for name in ("handbook", "agentContext"):
        entity("projection", {"snapshot": snapshots[-1], "format": name, "text": rendered[name]}, **{
            "doozer:projectionFormat": name, "doozer:sourceKind": "projection", "prov:value": rendered[name],
            "prov:wasDerivedFrom": ref(snapshots[-1])})
    # Source agents require recorded metadata; activity actors/times are never guessed.
    # Retirement does not invalidate an immutable historical record.
    return {"@context": dict(CONTEXT), "@graph": [nodes[key] for key in sorted(nodes)]}


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON member")
        result[key] = value
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    inputs = parser.add_mutually_exclusive_group(required=True)
    inputs.add_argument("--input", help="Existing workbench JSON artifact with a state member")
    inputs.add_argument("--db", help="Existing SQLite inbox; read directly without refreshing the projection")
    parser.add_argument("--dataset-id", required=True)
    parser.add_argument("--projection-title", default="Retry safety", help="Projection label; legacy default retained")
    parser.add_argument("--output", required=True)
    args = parser.parse_args(argv)
    path = Path(args.output)
    if path.exists():
        raise ValueError("output exists; no overwrite")
    if args.db is not None:
        from scripts import source_inbox

        state = source_inbox.snapshot(args.db)["state"]
        if len(encoded(state).encode()) > MAX_INPUT_BYTES:
            raise ValueError("inbox snapshot exceeds local export bound")
    else:
        with Path(args.input).open("rb") as stream:
            raw = stream.read(MAX_INPUT_BYTES + 1)
        if len(raw) > MAX_INPUT_BYTES:
            raise ValueError("input exceeds local artifact bound")
        state = json.loads(raw, object_pairs_hook=unique_object)["state"]
    result = project(state, dataset_id=args.dataset_id,
                     projection_title=args.projection_title)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x") as stream:
        stream.write(json.dumps(result, indent=2, allow_nan=False) + "\n")
    print(json.dumps({"output": str(path), "nodes": len(result["@graph"]), "network_calls": 0, "canonical_acceptance": False}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
