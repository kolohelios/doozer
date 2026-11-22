"""Conditional scalar reasoning over untrusted source-centric typed proposals."""

from collections import defaultdict
import datetime
import json

FIELDS = ("kind", "binding", "operator", "value", "target")
REVISION = {"withdraw-assurance", "revoke-permission", "supersedes"}
PERMISSION = {"grant-permission", "revoke-permission"}


def signature(atom):
    return tuple(atom[field] for field in FIELDS)


def material(atoms):
    return {signature(atom) for atom in atoms if atom["kind"] != "other"}


def atom_error(atom, span, packet):
    binding = packet["binding_index"][atom["binding"]]
    source = packet["source_index"][span["source"]]
    kind, op, value, target = (atom[key] for key in ("kind", "operator", "value", "target"))
    if atom["binding"] not in source["bindings"]:
        return "binding not allowed by declared source context"
    if kind == "world":
        if op not in {"eq", "neq"} or not isinstance(value, str) or not value.strip() or target is not None:
            return "world atom requires a concrete eq/neq value, not a modal or revision operand"
        if atom["binding"] not in source.get("worldBindings", source["bindings"]):
            return "world binding outside declared assertion scope"
        if value not in span["text"]:
            return "value literal not grounded in cited original paragraph"
        if binding["values"] and value not in binding["values"]:
            return "value outside declared scalar domain"
        if binding["property"] == "effective-date":
            try:
                if datetime.date.fromisoformat(value).isoformat() != value:
                    return "date is not a canonical ISO calendar date"
            except ValueError:
                return "date is not a canonical ISO calendar date"
    else:
        if value is not None or op != ("unknown" if kind == "epistemic" else "none"):
            return "source act or local knowledge cannot carry a world value"
        if kind not in REVISION and target is not None:
            return "non-revision act cannot have a prior-source operand"
    if kind in PERMISSION and binding["property"] != "permission":
        return "permission act applied to a non-permission predicate"
    if kind in REVISION:
        if target not in packet["source_index"] or target == span["source"]:
            return "missing or self-referential revision target"
        prior = packet["source_index"][target]
        if atom["binding"] not in prior["bindings"] or source["authority"] != prior["authority"]:
            return "revision crosses declared binding or authority"
        if target not in span["text"]:
            return "revision target not named in cited paragraph"
    return None


def compile_ledger(value, packet):
    records, rejected = [], []
    for entry in value["ledger"]:
        seen = set()
        for index, atom in enumerate(entry["atoms"]):
            record = {"id": f'{entry["span"]}-a{index}', "span": entry["span"], "source": packet["spans"][entry["span"]]["source"],
                      "atom": atom, "current_effect": True}
            error = atom_error(atom, packet["spans"][entry["span"]], packet)
            if signature(atom) in seen:
                error = "duplicate atom"
            seen.add(signature(atom))
            if error:
                rejected.append({**record, "reason": error})
            else:
                records.append(record)
    # Detect cycles by binding; never let a cyclic patch choose current truth.
    edges = defaultdict(set)
    for record in records:
        atom = record["atom"]
        if atom["kind"] in REVISION:
            edges[(atom["binding"], record["source"])].add((atom["binding"], atom["target"]))
    def visit(key, path):
        if key in path:
            raise ValueError("cyclic proposed source revision")
        for target in edges[key]:
            visit(target, path | {key})
    for key in list(edges):
        visit(key, set())
    invalid = set()
    for record in records:
        atom = record["atom"]
        if atom["kind"] == "revoke-permission" and not any(other["source"] == atom["target"] and other["atom"]["binding"] == atom["binding"] and other["atom"]["kind"] == "grant-permission" for other in records):
            rejected.append({**record, "reason": "revocation has no interpreted grant in its declared prior source"})
            invalid.add(record["id"])
    records = [record for record in records if record["id"] not in invalid]
    for revision in records:
        act = revision["atom"]
        if act["kind"] not in REVISION:
            continue
        for old in records:
            if old["source"] == act["target"] and old["atom"]["binding"] == act["binding"]:
                kinds = {"world"} if act["kind"] == "withdraw-assurance" else {"world", *PERMISSION}
                if old["atom"]["kind"] in kinds:
                    old["current_effect"] = False
    constraints = []
    for record in records:
        atom = record["atom"]
        if not record["current_effect"]:
            continue
        if atom["kind"] == "world":
            constraints.append({"binding": atom["binding"], "operator": atom["operator"], "value": atom["value"], "witness": record["id"]})
        elif atom["kind"] in PERMISSION:
            constraints.append({"binding": atom["binding"], "operator": "eq", "value": "permitted" if atom["kind"] == "grant-permission" else "forbidden", "witness": record["id"]})
    return {"records": records, "rejected": rejected, "constraints": constraints,
            "domains": {key: binding["values"] for key, binding in packet["binding_index"].items()},
            "warning": "Consequences are conditional on semantic extraction, canonical scalar domains, declared scope, and authority. No canonical acceptance."}


def evaluate(compiled, binding, value):
    positive, negative = [], []
    for constraint in compiled["constraints"]:
        if constraint["binding"] != binding:
            continue
        same = constraint["value"] == value
        if constraint["operator"] == "eq":
            (positive if same else negative).append(constraint["witness"])
        elif same:
            negative.append(constraint["witness"])
        elif compiled.get("domains", {}).get(binding) and set(compiled["domains"][binding]) - {constraint["value"]} == {value}:
            positive.append(constraint["witness"])
    state = "contested" if positive and negative else "supported" if positive else "opposed" if negative else "unestablished"
    return {"state": state, "positive": positive, "negative": negative}


def render(compiled, packet, role):
    lines = [f"Unverified {role} interpretation; not canonical knowledge."]
    for record in compiled["records"]:
        atom = record["atom"]
        binding = packet["binding_index"][atom["binding"]]
        mode = "current effect" if record["current_effect"] else "historical effect"
        lines.append(f'{record["span"]} [{mode}] {binding["subject"]} / {binding["property"]} / {binding["scope"]} / valid={binding["validTime"]}: ' + json.dumps(atom, sort_keys=True))
    lines.extend(f'REJECTED {item["id"]}: {item["reason"]}' for item in compiled["rejected"])
    return "\n".join(lines)
