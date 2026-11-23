"""Reviewed-contract scalar consequences and binding-local diagnostic gates.

All consequences are conditional on extraction and declared metadata, not proof
of natural-language entailment. Nothing here accepts canonical knowledge.
"""

import copy
import datetime
import json

KINDS = {"assertion", "assurance", "source-uncertainty", "question", "directive", "grant", "revocation", "assurance-withdrawal", "supersession", "qualifier", "other"}
REVISION = {"revocation", "assurance-withdrawal", "supersession"}
CONDITIONS = {"source-uncertainty", "qualifier"}
FIELDS = ("kind", "binding", "operator", "value", "holder", "targetSource", "targetKind", "action", "alternatives")


def freeze(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def affected(atom, packet):
    return sorted(set(atom["alternatives"]) if atom["kind"] == "qualifier" else {atom["binding"]} if atom["binding"] in packet["binding_index"] else set(packet["binding_index"]))


def error(atom, source, packet, placement):
    kind, binding = atom["kind"], atom["binding"]
    if placement == "conditions" and kind not in CONDITIONS:
        return "conditions placement cannot smuggle world assertions or normative acts"
    if kind not in KINDS:
        return "unknown constructor"
    if source["derivedFrom"] and kind != "other":
        return "projection/echo is not new primary evidence"
    if kind == "other":
        if any(atom[k] is not None for k in ("value", "holder", "targetSource", "targetKind", "action")) or atom["operator"] != "none" or atom["alternatives"]:
            return "other has no material operands"
        return None
    if kind == "qualifier":
        if binding is not None or atom["value"] is not None or atom["operator"] != "one-provisional" or len(set(atom["alternatives"])) < 2 or not set(atom["alternatives"]) <= packet["binding_index"].keys():
            return "unresolved qualifier requires alternative topics, not definite world assignments"
    elif binding not in packet["binding_index"] or atom["alternatives"]:
        return "missing topic or alternatives on the wrong constructor"
    if kind in {"assertion", "assurance", "question"}:
        value = atom["value"]
        if atom["operator"] not in {"eq", "neq"} or not isinstance(value, str) or not value.strip() or value not in source["text"]:
            return "concrete proposition literal not grounded in original message"
        definition = packet["binding_index"][binding]
        if definition["values"] and value not in definition["values"]:
            return "value outside canonical scalar domain"
        if definition["property"] == "effective-date":
            try:
                if datetime.date.fromisoformat(value).isoformat() != value:
                    return "noncanonical effective date"
            except ValueError:
                return "noncanonical effective date"
    elif atom["value"] is not None or atom["operator"] != ("unknown" if kind == "source-uncertainty" else "one-provisional" if kind == "qualifier" else "none"):
        return "modal or act constructor cannot carry a world value"
    if kind == "source-uncertainty":
        if atom["holder"] != source["actor"]:
            return "source uncertainty must retain its holder, not extractor/global ignorance"
    elif atom["holder"] is not None:
        return "holder belongs only to source uncertainty"
    if kind == "directive":
        action = atom["action"]
        if not action or any(not part.strip() or part.casefold() not in source["text"].casefold() for part in action.values()):
            return "directive requires grounded action object and condition"
    elif atom["action"] is not None:
        return "action arguments on non-directive"
    if kind in {"grant", "revocation"} and packet["binding_index"][binding]["property"] != "permission":
        return "permission act applied to another property"
    if kind in REVISION | {"grant"} and source["authority"] != packet["binding_index"][binding]["authority"]:
        return "act outside declared binding authority"
    if kind in REVISION:
        expected = {"revocation": {"grant"}, "assurance-withdrawal": {"assurance"}, "supersession": {"assertion", "qualifier"}}[kind]
        target = packet["source_index"].get(atom["targetSource"])
        if atom["targetKind"] not in expected or not target or target["id"] == source["id"] or target["authority"] != source["authority"]:
            return "revision target kind, identity, or declared authority mismatch"
        if kind == "assurance-withdrawal" and source["actor"] != target["actor"]:
            return "assurance withdrawal outside declared endorsement ownership"
        if target["id"] not in source["text"] and source["replyTo"] != target["id"]:
            return "prior target not grounded in message or explicit reply"
    elif atom["targetSource"] is not None or atom["targetKind"] is not None:
        return "non-revision cannot carry prior-target operands"
    return None


def compile_ledger(value, packet):
    records, rejected, seen = [], [], set()
    for entry in value["ledger"]:
        source = packet["source_index"][entry["span"]]
        for placement in ("atoms", "conditions"):
            for index, original in enumerate(entry[placement]):
                atom = copy.deepcopy(original)
                atom["alternatives"] = sorted(set(atom["alternatives"]))
                record = {"id": f'{source["id"]}-{placement}-{index}', "span": source["id"], "frame": source["frame"], "atom": atom, "not_explicitly_retired": True}
                why = error(atom, source, packet, placement)
                key = freeze([source["id"], atom])
                if why:
                    rejected.append({**record, "reason": why})
                elif key not in seen:
                    records.append(record)
                    seen.add(key)
    edges, targets = {}, {}
    for record in records:
        atom = record["atom"]
        if atom["kind"] not in REVISION:
            continue
        matches = [other for other in records if other["span"] == atom["targetSource"] and other["atom"]["kind"] == atom["targetKind"] and atom["binding"] in affected(other["atom"], packet)]
        if len(matches) != 1 or (matches[0]["atom"]["kind"] == "qualifier" and len(affected(matches[0]["atom"], packet)) > 1):
            rejected.append({**record, "reason": "named prior interpretation missing or ambiguous; no inferred repair"})
            continue
        targets[record["id"]] = [other["id"] for other in matches]
        edges[record["id"]] = targets[record["id"]]
    def visit(key, path):
        if key in path:
            raise ValueError("cyclic source revision")
        for target in edges.get(key, []):
            visit(target, path | {key})
    for key in edges:
        visit(key, set())
    rejected_ids = {r["id"] for r in rejected}
    records = [r for r in records if r["id"] not in rejected_ids]
    retired = {target for values in targets.values() for target in values}
    constraints = []
    for record in records:
        atom = record["atom"]
        record["not_explicitly_retired"] = record["id"] not in retired
        if not record["not_explicitly_retired"]:
            continue
        if atom["kind"] in {"assertion", "assurance"}:
            constraints.append({"binding": atom["binding"], "operator": atom["operator"], "value": atom["value"], "witness": record["id"]})
        elif atom["kind"] in {"grant", "revocation"}:
            constraints.append({"binding": atom["binding"], "operator": "eq", "value": "permitted" if atom["kind"] == "grant" else "forbidden", "witness": record["id"]})
    return {"records": records, "rejected": rejected, "constraints": constraints,
            "domains": {key: b["values"] for key, b in packet["binding_index"].items()},
            "window": packet["window"], "source_ids": list(packet["source_index"]),
            "extractor_limits": copy.deepcopy(value["extractionLimits"]),
            "warning": "Unverified conditional interpretation, not canonical acceptance. Scalar aliases, authority, frames, and origins are declared premises."}


def evaluate(compiled, binding, value):
    positive, negative = [], []
    for item in compiled["constraints"]:
        if item["binding"] != binding:
            continue
        same = item["value"] == value
        if item["operator"] == "eq":
            (positive if same else negative).append(item["witness"])
        elif same:
            negative.append(item["witness"])
        elif compiled["domains"][binding] and set(compiled["domains"][binding]) - {item["value"]} == {value}:
            positive.append(item["witness"])
    return {"state": "contested" if positive and negative else "supported" if positive else "opposed" if negative else "unestablished", "positive": positive, "negative": negative,
            "basis_window": compiled["window"], "bounded_sources": compiled["source_ids"]}


def material(compiled, packet):
    result = {key: set() for key in packet["binding_index"]}
    for record in [*compiled["records"], *compiled["rejected"]]:
        atom, source = record["atom"], packet["source_index"][record["span"]]
        if atom["kind"] == "other":
            continue
        op, value = atom["operator"], atom["value"]
        binding = atom["binding"]
        if op == "neq" and binding in packet["binding_index"]:
            domain = set(packet["binding_index"][binding]["values"])
            if value in domain and len(domain) == 2:
                op, value = "eq", next(iter(domain - {value}))
        if atom["kind"] == "assertion":
            identity = ["derived-primary-not-admissible", source["id"]] if source["derivedFrom"] else source["origin"]
        elif atom["kind"] in {"source-uncertainty", "qualifier"}:
            identity = [source["actor"], source["frame"] if atom["kind"] == "source-uncertainty" else source["origin"]]
        else:
            identity = source["id"]
        action = atom["action"]
        if action:
            action = {key: " ".join(part.casefold().split()) for key, part in action.items()}
            action["object"] = action["object"].removeprefix("the ")
        key = freeze([atom["kind"], identity, binding, op, value, atom["holder"], atom["targetSource"], atom["targetKind"], action, atom["alternatives"]])
        for topic in affected(atom, packet):
            result[topic].add(key)
    return result


def views(compiled, packet):
    result = {}
    for binding in packet["binding_index"]:
        current, history = [], []
        for record in compiled["records"]:
            if binding not in affected(record["atom"], packet) or record["atom"]["kind"] not in CONDITIONS:
                continue
            (history if record["atom"]["kind"] == "source-uncertainty" and record["frame"] != packet["window"] else current).append(record["id"])
        related = [r for r in compiled["records"] if binding in affected(r["atom"], packet) and r["atom"]["kind"] != "other"]
        result[binding] = {"scope": packet["binding_index"][binding], "constraints": [c for c in compiled["constraints"] if c["binding"] == binding],
                           "qualifications": current, "historical_source_conditions": history,
                           "source_acts": [r["id"] for r in related if r["atom"]["kind"] not in CONDITIONS | {"assertion"}],
                           "history_records": [r["id"] for r in related if not r["not_explicitly_retired"] or r["id"] in history],
                           "extractor_limits": [{"origin": "extractor-interpretation", **limit} for limit in compiled["extractor_limits"] if not limit["about"] or binding in limit["about"]],
                           "coverage": {"window": packet["window"], "sources": list(packet["source_index"]), "unavailable_reference_ids": packet["unavailable_reference_ids"], "claim": "Only these supplied sources were processed; not global completeness."}}
    return result


def gates(packet, primary, verifier=None, audit=None, panel=False, audit_required=True):
    result = {binding: [] for binding in packet["binding_index"]}
    if primary is None:
        return {binding: {"candidate_eligible": False, "reasons": ["primary-unavailable"], "warning": "Diagnostic unavailability; original sources remain recoverable."} for binding in result}
    for record in primary["rejected"]:
        for binding in affected(record["atom"], packet):
            result[binding].append("primary-mechanical")
    if panel:
        if verifier is None:
            for reasons in result.values():
                reasons.append("verifier-unavailable")
        else:
            for record in verifier["rejected"]:
                for binding in affected(record["atom"], packet):
                    result[binding].append("verifier-mechanical")
            a, b = material(primary, packet), material(verifier, packet)
            for binding in result:
                if a[binding] != b[binding]:
                    result[binding].append("material-disagreement")
        if audit_required:
            checks = {c["binding"]: c for c in audit["checks"]} if audit else {}
            for binding in result:
                check = checks.get(binding)
                if not check or any(check[role] != "faithful" for role in ("interpreter", "verifier")) or check["issues"]:
                    result[binding].append("audit-concern-or-unavailable")
    return {binding: {"candidate_eligible": not reasons, "reasons": sorted(set(reasons)), "warning": "Diagnostic eligibility, never canonical acceptance; source-qualified views remain available even when flagged."} for binding, reasons in result.items()}
