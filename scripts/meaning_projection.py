"""Offline prospective extraction/projection checks under reviewed source meanings.

Legacy scalar consequences are reused unchanged. New annotations are untrusted
interpretations, not a natural-language parser or a semantic acceptance oracle.
"""

import argparse
import copy
import gzip
import json

from scripts import audit_contract, reviewed_ir as core, reviewed_panel as legacy, transfer_review
from scripts.cue_contract import compile_schema
from scripts.evaluation_client import validate_contract


def atom(kind, binding, **operands):
    return {"kind": kind, "binding": binding, "operator": "none", "value": None, "holder": None, "targetSource": None, "targetKind": None, "action": None, "alternatives": [], **operands}


def schema_for(data, context):
    base = legacy.schema_for(data["transferLedgerSchema"], context)["json"]
    entry = base["properties"]["ledger"]["items"]
    entry["required"].append("annotations")
    for placement in ("atoms", "conditions"):
        template = entry["properties"][placement]["items"]
        choices = []
        kinds = {"qualifier"} if placement == "conditions" else core.KINDS - {"source-uncertainty"}
        for kind in sorted(kinds):
            branch = copy.deepcopy(template)
            fields = branch["properties"]
            fields["kind"]["enum"] = [kind]
            fields["binding"] = {"type": "null"} if kind in {"qualifier", "other"} else {"type": "string", "enum": list(context["binding_index"])}
            fields["holder"] = {"type": "null"}
            fields["operator"]["enum"] = ["eq", "neq"] if kind in {"assertion", "assurance", "question"} else ["one-provisional" if kind == "qualifier" else "none"]
            fields["value"] = {"type": "string"} if kind in {"assertion", "assurance", "question"} else {"type": "null"}
            fields["action"] = template["properties"]["action"]["anyOf"][1] if kind == "directive" else {"type": "null"}
            if kind not in core.REVISION:
                fields["targetSource"] = fields["targetKind"] = {"type": "null"}
            if kind != "qualifier":
                fields["alternatives"] = {"type": "array", "items": {"type": "string"}, "maxItems": 0}
            choices.append(branch)
        entry["properties"][placement]["items"] = {"anyOf": choices}
    annotations = copy.deepcopy(data["meaningAnnotationSchema"])
    for branch in annotations["anyOf"][:2]:
        branch["properties"]["binding"]["enum"] = list(context["binding_index"])
    if context["topics"]:
        annotations["anyOf"][2]["properties"]["topic"]["enum"] = list(context["topics"])
    else:
        annotations["anyOf"] = annotations["anyOf"][:2]
    entry["properties"]["annotations"] = {"type": "array", "items": annotations}
    return {"json": base, "cue": compile_schema(json.dumps(base, sort_keys=True))}


def annotation_error(annotation, source, context):
    quote = annotation["quote"]
    if not quote.strip() or quote not in source["text"] or source["derivedFrom"]:
        return "annotation requires a literal original-source anchor, not new primary evidence from a digest"
    kind = annotation["kind"]
    if kind == "condition":
        if annotation["frame"] == "person":
            if annotation["stance"] != "does-not-know" or annotation["holder"] != source["actor"]:
                return "personal ignorance requires its actual holder and stance"
        elif annotation["holder"] is not None or annotation["stance"] not in {"no-finding-in-note", "not-established-in-notes"}:
            return "source-note coverage is not personal ignorance"
    elif kind == "speculation":
        if annotation["value"] not in quote:
            return "speculative proposition literal absent from its quote"
        return core.error(atom("question", annotation["binding"], operator=annotation["operator"], value=annotation["value"]), source, context, "atoms")
    else:
        for binding in context["topics"][annotation["topic"]]:
            error = core.error(atom("directive", binding, action=annotation["action"]), source, context, "atoms")
            if error:
                return error
    return None


def compile_ledger(value, context, schema):
    validate_contract(schema["cue"], "#Report", json.dumps(value, sort_keys=True, allow_nan=False))
    entries = value["ledger"]
    if len(entries) != len(context["source_index"]) or {e["span"] for e in entries} != set(context["source_index"]) or any(not e["rationale"].strip() for e in entries):
        raise ValueError("source entries must be complete, unique, and explained")
    if any(not limit["evidence"] or not limit["reason"].strip() for limit in value["extractionLimits"]):
        raise ValueError("extractor limits need original-source pointers and a reason")
    lowered = copy.deepcopy(value)
    annotations, rejected, lowerings = [], [], []
    for original, entry in zip(entries, lowered["ledger"]):
        source = context["source_index"][entry["span"]]
        del entry["annotations"]
        for index, annotation in enumerate(original["annotations"]):
            record = {"id": f'{source["id"]}-annotation-{index}', "source": source["id"], "speaker": source["actor"], "as_of": source["frame"], "annotation": copy.deepcopy(annotation)}
            error = annotation_error(annotation, source, context)
            if error:
                rejected.append({**record, "reason": error})
                continue
            annotations.append(record)
            if annotation["kind"] == "procedure":
                for binding in context["topics"][annotation["topic"]]:
                    generated = f'{source["id"]}-atoms-{len(entry["atoms"])}'
                    entry["atoms"].append(atom("directive", binding, action=copy.deepcopy(annotation["action"])))
                    lowerings.append({"annotation": record["id"], "record": generated, "about_binding": binding, "premise": "declared procedure-topic link, not semantic equivalence inferred by code"})
    compiled = core.compile_ledger(lowered, context)
    return {"core": compiled, "annotations": annotations, "rejected_annotations": rejected, "lowerings": lowerings,
            "original_proposal": copy.deepcopy(value), "source_index": copy.deepcopy(context["source_index"]),
            "canonical_acceptance": False}


def recover(compiled, source):
    return copy.deepcopy(compiled["source_index"][source])


def project(compiled, context, binding, value, consumer="fact", audit_report=None, availability=None):
    if consumer not in {"fact", "evidence-use"}:
        raise ValueError("unknown consumer")
    if binding not in context["binding_index"]:
        raise ValueError("procedure topics are not scalar world variables")
    records = compiled["core"]["records"]
    procedures = [{"id": r["id"], "source": r["span"], "speaker": context["source_index"][r["span"]]["actor"], "action": copy.deepcopy(r["atom"]["action"]), "source_text": recover(compiled, r["span"])["text"]} for r in records if r["atom"]["kind"] == "directive" and r["atom"]["binding"] == binding]
    conditions, historical, speculations = [], [], []
    for record in compiled["annotations"]:
        annotation = record["annotation"]
        if annotation.get("binding") != binding:
            continue
        if annotation["kind"] == "speculation":
            speculations.append(copy.deepcopy(record))
        elif annotation["kind"] == "condition":
            (conditions if record["as_of"] == context["window"] else historical).append(copy.deepcopy(record))
    view = core.views(compiled["core"], context)[binding]
    flags = core.gates(context, compiled["core"])[binding]["reasons"]
    for record in compiled["rejected_annotations"]:
        annotation = record["annotation"]
        affected = context["topics"][annotation["topic"]] if annotation["kind"] == "procedure" else [annotation["binding"]]
        if binding in affected:
            flags.append("annotation-mechanical")
    audit = None
    if availability is not None or audit_report is not None:
        schema = audit_contract.specialize(audit_contract.load(), list(context["binding_index"]), list(context["source_index"]))
        audit = audit_contract.project(audit_report, schema, availability or {})[binding]
    return {"scope": copy.deepcopy(context["binding_index"][binding]), "query_value": value, "understanding": core.evaluate(compiled["core"], binding, value),
            "coverage": {**view["coverage"], "frame": "source-window", "holder": None},
            "source_conditions": conditions, "historical_conditions": historical, "speculations": speculations,
            "procedure_links": [r["id"] for r in procedures], "procedures": procedures if consumer == "evidence-use" else [],
            "source_acts": [copy.deepcopy(r) for r in records if r["id"] in view["source_acts"]],
            "qualifications": [copy.deepcopy(r) for r in records if r["id"] in view["qualifications"]],
            "history_records": [copy.deepcopy(r) for r in records if r["id"] in view["history_records"]], "extractor_limits": view["extractor_limits"],
            "mechanical_flags": sorted(set(flags)), "audit": audit,
            "source_links": list(context["source_index"]), "canonical_acceptance": False,
            "warning": "Conditional untrusted interpretation. Hunches/conditions/procedures are not world witnesses; audit severity and source stance are not proved by code."}


def render(view):
    """Deterministic attributed reader projection, not a second model paraphrase."""
    scope = view["scope"]
    lines = [f'{scope["subject"]}: {scope["property"]} = {view["query_value"]} in {scope["scope"]}: {view["understanding"]["state"]}.',
             f'Bounded interpreted evidence in supplied window {view["coverage"]["window"]}; coverage alone is neither a global finding nor a claim about anyone\'s personal knowledge.']
    if scope["validTime"] is not None:
        lines.append("Validity context: " + scope["validTime"])
    for record in view["source_conditions"]:
        a = record["annotation"]
        lines.append(f'{a["frame"]} condition reported by {record["speaker"]}: {a["stance"]}: {a["quote"]}')
    for record in view["qualifications"]:
        lines.append("Source qualification: " + json.dumps(record["atom"], sort_keys=True))
    for record in view["speculations"]:
        lines.append(f'Attributed hunch by {record["speaker"]} as of source frame {record["as_of"]}, not world evidence: {record["annotation"]["quote"]}')
    for record in view["procedures"]:
        lines.append(f'Source instruction by {record["speaker"]} [{record["source"]}], not a newly assigned task: ' + record["source_text"])
    if view["mechanical_flags"]:
        lines.append("Mechanical concerns: " + ", ".join(view["mechanical_flags"]))
    if view["audit"] is not None:
        lines.append("Untrusted audit signal: " + json.dumps(view["audit"], sort_keys=True))
    lines.append("Unverified proposal only; no canonical acceptance.")
    return "\n".join(lines) + "\n"


def check_projection(compiled, context):
    """Check preservation of an interpreted ledger, not completeness/entailment of extraction."""
    records = {r["id"]: r for r in compiled["core"]["records"]}
    if any(records[c["witness"]]["atom"]["kind"] not in {"assertion", "assurance", "grant", "revocation"} for c in compiled["core"]["constraints"]):
        raise ValueError("non-world source act became a world witness")
    for binding, definition in context["binding_index"].items():
        candidates = definition["values"] or [c["value"] for c in compiled["core"]["constraints"] if c["binding"] == binding]
        query = candidates[0] if candidates else "projection-check"
        fact = project(compiled, context, binding, query)
        pertinent = project(compiled, context, binding, query, consumer="evidence-use")
        if fact["canonical_acceptance"] or set(fact["source_links"]) != set(context["source_index"]) or fact["coverage"]["frame"] != "source-window" or fact["coverage"]["holder"] is not None:
            raise ValueError("projection lost its source/coverage boundary")
        expected = {r["id"] for r in compiled["annotations"] if r["annotation"].get("binding") == binding}
        recovered = {r["id"] for field in ("source_conditions", "historical_conditions", "speculations") for r in fact[field]}
        if expected != recovered:
            raise ValueError("projection lost an interpreted condition or hunch")
        related = [r for r in records.values() if binding in core.affected(r["atom"], context)]
        qualifiers = {r["id"] for r in related if r["atom"]["kind"] == "qualifier"}
        acts = {r["id"] for r in related if r["atom"]["kind"] not in {"assertion", "qualifier", "other", "source-uncertainty"}}
        if qualifiers != {r["id"] for r in fact["qualifications"]} or acts != {r["id"] for r in fact["source_acts"]}:
            raise ValueError("projection lost a source qualification, question, or act")
        directives = {r["id"] for r in related if r["atom"]["kind"] == "directive"}
        if set(fact["procedure_links"]) != directives or {r["id"] for r in pertinent["procedures"]} != directives:
            raise ValueError("pertinent consumer lost its instruction recovery path")
        if any(r["source_text"] != recover(compiled, r["source"])["text"] for r in pertinent["procedures"]):
            raise ValueError("instruction lost its original referent context")
    return len(context["binding_index"])


def prepare(data):
    reviewed = transfer_review.validate(transfer_review.load())
    if len(transfer_review.approval_status(reviewed)["approved_examples"]) != 2:
        raise ValueError("required individual source reviews incomplete")
    archive = transfer_review.load()["transferReviewArchive"]
    packets = json.loads(gzip.decompress((legacy.multi.ROOT / archive["path"]).read_bytes()))["protocol"]["frozen"]["packets"]
    index = {p["id"]: p for p in packets}
    cases = {}
    for key, case in sorted(data["projectionCases"].items()):
        original = index[case["packet"]]
        if not set(case["annotations"]) <= original["source_index"].keys() or any(d["span"] not in original["source_index"] for d in case["directives"]):
            raise ValueError("authored annotation or directive has an unknown source")
        context = {field: copy.deepcopy(original[field]) for field in ("window", "sources", "bindings", "unavailable_reference_ids")}
        context["topics"] = copy.deepcopy(case["topics"])
        value = legacy.reference_ledger(original)
        for entry in value["ledger"]:
            entry["annotations"] = copy.deepcopy(case["annotations"].get(entry["span"], []))
        for directive in case["directives"]:
            next(e for e in value["ledger"] if e["span"] == directive["span"])["atoms"].append(atom("directive", directive["binding"], action=directive["action"]))
        for source in case["addedSources"]:
            context["sources"].append({k: copy.deepcopy(v) for k, v in source.items() if k not in {"atoms", "annotations"}})
            context["window"] = source["frame"]
            value["ledger"].append({"span": source["id"], "atoms": copy.deepcopy(source["atoms"]), "conditions": [], "annotations": copy.deepcopy(source["annotations"]), "rationale": "Authored mechanical control, not model output or independent gold."})
        context["binding_index"] = {b["id"]: b for b in context["bindings"]}
        context["source_index"] = {s["id"]: s for s in context["sources"]}
        if len(context["source_index"]) != len(context["sources"]) or any(not ids or len(set(ids)) != len(ids) or not set(ids) <= context["binding_index"].keys() for ids in context["topics"].values()):
            raise ValueError("duplicate source or invalid declared topic link")
        schema = schema_for(data, context)
        compiled = compile_ledger(value, context, schema)
        if compiled["core"]["rejected"] or compiled["rejected_annotations"]:
            raise ValueError("authored control fails mechanical checks")
        check_projection(compiled, context)
        for query in case["expected"]:
            if project(compiled, context, query["binding"], query["value"])["understanding"]["state"] != query["state"]:
                raise ValueError("authored conditional state disagrees with declared expectation")
        cases[key] = {"context": context, "proposal": value, "schema": schema, "compiled": compiled, "expected": copy.deepcopy(case["expected"])}
    return cases


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    parser.parse_args(argv)
    data = legacy.multi.export_cue(sorted(legacy.DIRECTORY.glob("*.cue")))
    cases = prepare(data)
    print(json.dumps({"version": data["meaningContract"]["version"], "status": data["meaningContract"]["status"], "authored_controls": len(cases), "conditional_query_checks": sum(len(c["expected"]) for c in cases.values()), "binding_projection_checks": sum(len(c["context"]["binding_index"]) for c in cases.values()), "paid_calls": 0, "canonical_acceptance": False, "archived_results_rescored": False}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
