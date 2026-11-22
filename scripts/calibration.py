"""Offline draft review of saved answers; no model calls or semantic scoring."""

import argparse
import copy
import hashlib
import json
from pathlib import Path
import re
import subprocess

from scripts.jev_probe import export_cue


ROOT = Path(__file__).resolve().parents[1]
DIRECTORY = ROOT / "experiments/calibration"
ARMS = ("full", "vector", "vector-links")
ANSWER_POINTER = re.compile(r"^/(summary|claims/(0|[1-9][0-9]*)/(text|scope|attribution)|directives/(0|[1-9][0-9]*)/(instruction|scope)|uncertainties/(0|[1-9][0-9]*))$")


def resolve(value, pointer):
    if not ANSWER_POINTER.fullmatch(pointer):
        raise ValueError("pointer is not a candidate answer text field")
    current = value
    for token in pointer.split("/")[1:]:
        token = token.replace("~1", "/").replace("~0", "~")
        try:
            current = current[int(token)] if isinstance(current, list) else current[token]
        except (KeyError, IndexError, TypeError, ValueError):
            raise ValueError("answer pointer does not resolve") from None
    if not isinstance(current, str):
        raise ValueError("answer pointer does not resolve to text")
    return current


def check_spans(answer, spans):
    for span in spans:
        if not span["quote"].strip() or span["quote"] not in resolve(answer, span["pointer"]):
            raise ValueError("draft annotation misquotes saved answer")


def check_evidence(citations, sources):
    for citation in citations:
        if citation["source"] not in sources or not citation["quote"].strip() or citation["quote"] not in sources[citation["source"]]["text"]:
            raise ValueError("unknown or misquoted authoritative source")


def bundle_available(bundle, context):
    documents = {doc["id"]: doc for doc in context}
    required = {citation["source"] for citation in bundle["allOf"]}
    for citation in bundle["allOf"]:
        source = documents.get(citation["source"])
        if not source or citation["quote"] not in source["text"]:
            return False
        if "replyTo" in source and source["replyTo"] not in required:
            return False
    return True


def draft_support(meanings, context):
    result = []
    for meaning in meanings:
        if meaning["surface"] != "answer" or meaning["applicability"] != "required":
            continue
        available = [bundle["id"] for bundle in meaning["sufficient"] if bundle_available(bundle, context)]
        result.append({"meaning": meaning["id"], "available_bundles": available,
                       "bundle_available": bool(available)})
    return result


def validate(data, artifact):
    if data["meta"]["status"] != "pending-user-review" or data["meta"]["semanticScoringEnabled"] is not False:
        raise ValueError("this tool accepts drafts only; it cannot approve or score calibration labels")
    rows = {}
    for row in artifact["rows"]:
        key = (row["case"], row["arm"])
        if key in rows:
            raise ValueError("duplicate saved answer")
        rows[key] = row
    cases = set(data["meanings"])
    if set(rows) != {(case, arm) for case in cases for arm in ARMS} or set(data["reviews"]) != cases:
        raise ValueError("review must cover exactly the nine saved case/arm answers")
    sources = {}
    for row in rows.values():
        for document in row["context"]:
            if document["id"] in sources and sources[document["id"]] != document:
                raise ValueError("conflicting saved source snapshots")
            sources[document["id"]] = document
    for case in cases:
        authoritative = {doc["id"]: doc for doc in rows[case, "full"]["context"]}
        meanings = data["meanings"][case]
        ids = [meaning["id"] for meaning in meanings]
        if not any(meaning["applicability"] == "required" for meaning in meanings):
            raise ValueError("case has no required answer meanings")
        if len(ids) != len(set(ids)) or set(data["reviews"][case]) != set(ARMS):
            raise ValueError("duplicate meanings or missing review arms")
        for meaning in meanings:
            check_evidence(meaning["references"], authoritative)
            bundles = meaning.get("sufficient", [])
            if len({bundle["id"] for bundle in bundles}) != len(bundles):
                raise ValueError("duplicate support bundle identity")
            for bundle in bundles:
                check_evidence(bundle["allOf"], authoritative)
                required = {citation["source"] for citation in bundle["allOf"]}
                for source in required:
                    if "replyTo" in authoritative[source] and authoritative[source]["replyTo"] not in required:
                        raise ValueError("contextual support bundle omits its reply target")
        for arm in ARMS:
            assessments = data["reviews"][case][arm]
            if set(assessments) != set(ids):
                raise ValueError("review omits or invents meaning assessments")
            for meaning in meanings:
                assessment = assessments[meaning["id"]]
                label = assessment["label"]
                if meaning["applicability"] == "retention-only" and label != "not-assessed":
                    raise ValueError("answer-only review cannot establish history retention")
                if meaning["applicability"] == "required" and label not in {"pass", "fail", "uncertain"}:
                    raise ValueError("required answer meaning cannot be silently excluded")
                if label == "not-applicable" and meaning["applicability"] != "if-mentioned":
                    raise ValueError("not-applicable requires a conditional criterion")
                if label == "pass" and not assessment["spans"]:
                    raise ValueError("draft pass requires a real candidate span")
                check_spans(rows[case, arm]["understanding"], assessment["spans"])
    sample_ids = set()
    for sample in data["samples"]:
        if sample["id"] in sample_ids or (sample["case"], sample["arm"]) not in rows:
            raise ValueError("duplicate sample or unknown saved candidate")
        sample_ids.add(sample["id"])
        if sample["expected"] == "pass" and not sample["spans"]:
            raise ValueError("draft calibration pass requires a candidate span")
        if sample["target"] == "excerpt" and not sample["spans"]:
            raise ValueError("excerpt sample needs candidate spans")
        if sample["target"] == "claim" and (len(sample["spans"]) != 1 or not re.fullmatch(r"/claims/[0-9]+/text", sample["spans"][0]["pointer"])):
            raise ValueError("claim sample needs one claim-text anchor")
        check_spans(rows[sample["case"], sample["arm"]]["understanding"], sample["spans"])
        authoritative = {doc["id"]: doc for doc in rows[sample["case"], "full"]["context"]}
        check_evidence(sample["evidence"], authoritative)
    return rows


def load():
    data = export_cue(sorted(DIRECTORY.glob("*.cue")))
    path = ROOT / data["meta"]["artifact"]
    if path.resolve() != (ROOT / "experiments/understanding/results/first-comparison.json").resolve():
        raise ValueError("unexpected source artifact")
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != data["meta"]["artifactSHA256"]:
        raise ValueError("saved experiment changed; do not silently rebind annotations")
    artifact = json.loads(raw)
    rows = validate(data, artifact)
    return data, artifact, rows


def report(data, rows):
    reviewed = []
    for case, arm in sorted(rows):
        row = rows[case, arm]
        support = draft_support(data["meanings"][case], row["context"])
        reviewed.append({
            "case": case, "arm": arm, "original_source_recall": row["retrieval"]["recall"],
            "proposed_support_available": sum(item["bundle_available"] for item in support),
            "proposed_support_total": len(support), "support": support,
            "draft_assessments": copy.deepcopy(data["reviews"][case][arm]),
        })
    samples = []
    for sample in data["samples"]:
        row = rows[sample["case"], sample["arm"]]
        if sample["target"] == "whole-answer":
            candidate = row["understanding"]
        elif sample["target"] == "claim":
            index = int(sample["spans"][0]["pointer"].split("/")[2])
            candidate = row["understanding"]["claims"][index]
        else:
            candidate = [span["quote"] for span in sample["spans"]]
        # This is a prospective, label-blind judge input. No model is called.
        judge_input = {"question": row["question"], "criterion": sample["criterion"],
                       "target": sample["target"], "candidate": copy.deepcopy(candidate),
                       "authoritative_sources": copy.deepcopy(rows[sample["case"], "full"]["context"])}
        samples.append({"id": sample["id"], "provenance": {"case": sample["case"], "arm": sample["arm"]},
                        "status": "pending-user-review", "split": "development",
                        "draft_expected": sample["expected"], "draft_reason": sample["reason"],
                        "highlighted_evidence": sample["evidence"], "judge_input": judge_input})
    return {"meta": copy.deepcopy(data["meta"]), "coverage_is_entailment_proof": False,
            "rows": reviewed, "calibration_samples": samples,
            "warning": "Draft support availability and unblinded annotations, not human gold labels or semantic accuracy."}


def packet(data, rows, result):
    lines = ["# Draft meaning review — pending user approval", "",
             "Unblinded development annotations. No original result is rewritten; no judge is run.",
             "Proposed support bundles are not entailment proofs. Resolve uncertain labels before promotion.", ""]
    for case in sorted(data["meanings"]):
        lines.extend(["## " + case, "", rows[case, "full"]["question"], "", "### Authoritative case sources", ""])
        for source in rows[case, "full"]["context"]:
            metadata = {field: source[field] for field in ("kind", "saidAt", "replyTo", "derivedFrom") if field in source}
            lines.extend([f"- **{source['id']}** (`{source['anchor']}`; {json.dumps(metadata)}): {source['text']}"])
        lines.extend(["", "### Proposed contracts", ""])
        for meaning in data["meanings"][case]:
            lines.extend([f"- **{meaning['id']}** ({meaning['surface']}; {meaning['applicability']}): {meaning['statement']}"])
            for bundle in meaning.get("sufficient", []):
                lines.append(f"  - Proposed bundle **{bundle['id']}**: {bundle['note']}")
                for citation in bundle["allOf"]:
                    lines.append(f"    - `{citation['source']}`: {citation['quote']}")
        for arm in ARMS:
            row = rows[case, arm]
            lines.extend(["", "### " + arm, "", "```json", json.dumps(row["understanding"], indent=2), "```", "",
                          "Draft annotations (not scores):", ""])
            for meaning, assessment in data["reviews"][case][arm].items():
                lines.append(f"- **{meaning}: {assessment['label']}** — {assessment['reason']}")
                for span in assessment["spans"]:
                    lines.append(f"  - `{span['pointer']}`: {span['quote']}")
    lines.extend(["", "## Calibration examples", ""])
    for sample in result["calibration_samples"]:
        lines.extend([f"### {sample['id']} — draft {sample['draft_expected']}", "", sample["judge_input"]["criterion"], "",
                      sample["draft_reason"], "", "Candidate:", "```json",
                      json.dumps(sample["judge_input"]["candidate"], indent=2), "```", ""])
        for citation in sample["highlighted_evidence"]:
            lines.append(f"- `{citation['source']}`: {citation['quote']}")
        lines.append("")
    return "\n".join(lines) + "\n"


def write_new(path, content):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    # Exclusive creation: never overwrite the original result or any prior packet.
    with path.open("x") as stream:
        stream.write(content)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", help="new optional draft JSON report")
    parser.add_argument("--packet", help="new optional Markdown packet with all nine saved answers")
    args = parser.parse_args(argv)
    try:
        for path in (args.output, args.packet):
            if path and Path(path).exists():
                raise ValueError("output already exists")
        if args.output and args.packet and Path(args.output).resolve() == Path(args.packet).resolve():
            raise ValueError("packet and report need different paths")
        data, artifact, rows = load()
        result = report(data, rows)
        if args.output:
            write_new(args.output, json.dumps(result, indent=2, allow_nan=False) + "\n")
        if args.packet:
            write_new(args.packet, packet(data, rows, result))
        print("DRAFT — pending user review; semantic scoring disabled; no model calls.")
        for row in result["rows"]:
            print(f"{row['case']}/{row['arm']}: {row['proposed_support_available']}/{row['proposed_support_total']} proposed answer-support bundles available")
        print(f"{len(result['rows'])} saved answers; {len(result['calibration_samples'])} development calibration samples.")
        return 0
    except (ValueError, KeyError, TypeError, OSError, subprocess.CalledProcessError):
        print("Draft review failed integrity/reference checks or output path is unavailable; original experiment untouched.")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
