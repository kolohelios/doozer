"""Conditional metadata and witness algebra; not natural-language entailment proof."""

import copy
from collections import deque
import json
import re


def links(source):
    result = set(source.get("references", []) + source.get("derivedFrom", []) + source.get("supersedes", []))
    result.update(source[key] for key in ("replyTo", "originFrom") if key in source)
    return result


def expand(initial, catalog, limits):
    visible = {source["id"]: copy.deepcopy(source) for source in initial}
    index = {source["id"]: source for source in catalog}
    if len(visible) != len(initial) or len(index) != len(catalog) or set(visible) & set(index):
        raise ValueError("duplicate source identity")
    frontier = deque((key, 1) for key in sorted({key for source in initial for key in links(source)} - set(visible)))
    seen, log, added, used = set(visible), [], 0, 0
    while frontier:
        key, hop = frontier.popleft()
        if key in seen:
            continue
        seen.add(key)
        entry = {"id": key, "hop": hop}
        log.append(entry)
        if hop > limits["maxHops"]:
            entry["status"] = "hop-limit"
        elif added >= limits["maxDocuments"]:
            entry["status"] = "document-limit"
        elif key not in index:
            entry["status"] = "unavailable"
        else:
            size = len(json.dumps(index[key], sort_keys=True).encode())
            if used + size > limits["maxBytes"]:
                entry["status"] = "byte-limit"
                continue
            visible[key] = copy.deepcopy(index[key])
            added += 1
            used += size
            entry.update(status="retrieved", bytes=size)
            frontier.extend((target, hop + 1) for target in sorted(links(index[key]) - seen))
    return list(visible.values()), {"requests": log, "documents_added": added, "bytes_added": used,
                                  "unresolved_ids": sorted({key for source in visible.values() for key in links(source)} - set(visible))}


def view(sources):
    index = {source["id"]: source for source in sources}
    if len(index) != len(sources):
        raise ValueError("duplicate sources")
    edges, ignored = {}, []
    for source in sources:
        edges[source["id"]] = []
        for target in source.get("supersedes", []):
            if target in index and index[target]["scope"] == source["scope"]:
                edges[source["id"]].append(target)
            else:
                ignored.append([source["id"], target])
    def visit(key, path):
        if key in path:
            raise ValueError("cyclic supersession")
        for target in edges.get(key, []):
            visit(target, path | {key})
    for key in index:
        visit(key, set())
    retired = {target for targets in edges.values() for target in targets}
    spans = {source["id"] + "-s" + str(i): {"source": source["id"], "scope": source["scope"], "current": source["id"] not in retired, "text": text}
             for source in sources for i, text in enumerate(re.split(r"(?<=[.!?])\s+", source["text"]))}
    return {"sources": copy.deepcopy(sources), "spans": spans, "retired_source_ids": sorted(retired),
            "ignored_supersessions": ignored,
            "unread_reference_ids": sorted({key for source in sources for key in links(source)} - set(index))}


def origin_guard(proposition, sources):
    if proposition["guard"] != "origins":
        return None
    index = {source["id"]: source for source in sources}
    def roots(key, path):
        if key in path:
            raise ValueError("cyclic origin metadata")
        if key not in index:
            return set(), {key}
        source = index[key]
        known = {source["origin"]} if "origin" in source else set()
        parents = ([source["originFrom"]] if "originFrom" in source else []) + source.get("derivedFrom", [])
        unknown = set()
        for parent in parents:
            a, b = roots(parent, path | {key})
            known.update(a)
            unknown.update(b)
        if not known and not parents:
            unknown.add(key)
        return known, unknown
    resolved = []
    for subject in proposition["subjects"]:
        known, unknown = roots(subject, set())
        resolved.append({"source": subject, "declared_origins": sorted(known), "unresolved_roots": sorted(unknown)})
    if len(resolved) != 2 or any(len(item["declared_origins"]) != 1 or item["unresolved_roots"] for item in resolved):
        state = "unestablished"
    else:
        state = "opposed" if resolved[0]["declared_origins"] == resolved[1]["declared_origins"] else "supported"
    return {"state": state, "resolved": resolved, "assumption": "Declared origin/lineage identifies observation groups; this is not statistical independence or verified extraction from prose."}


def evidence_state(positive, negative):
    return "contested" if positive and negative else "supported" if positive else "opposed" if negative else "unestablished"


def compile_proof(proposition, proof, packet):
    accepted, rejected = {"positive": [], "negative": []}, []
    for polarity in accepted:
        for span_id in proof[polarity]:
            if span_id not in packet["spans"]:
                raise ValueError("invented witness")
            span = packet["spans"][span_id]
            if not span["current"] or span["scope"] != proposition["scope"]:
                rejected.append({"span": span_id, "polarity": polarity, "reason": "historical" if not span["current"] else "different-scope"})
            else:
                accepted[polarity].append(span_id)
    conditional = evidence_state(accepted["positive"], accepted["negative"])
    guard = origin_guard(proposition, packet["sources"])
    return {"raw_proposed_state": evidence_state(proof["positive"], proof["negative"]),
            "scope_current_state": conditional, "guarded_state": guard["state"] if guard else conditional,
            "accepted": accepted, "rejected": rejected, "metadata_guard": guard,
            "guard_disagrees_with_proposal": guard is not None and guard["state"] != conditional,
            "conditional_only": "Witness text entailment and metadata correctness are not proved by this compiler."}
