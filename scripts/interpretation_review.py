"""Offline, content-addressed review of proposed interpretation meanings; no judge."""

import argparse
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
DIRECTORY = ROOT / "experiments/judgment"
FILES = (DIRECTORY / "interpretation-review.cue", DIRECTORY / "interpretation-examples.cue")
PROJECTION = ROOT / "docs/interpretation-review.md"


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def load():
    return json.loads(subprocess.run(["cue", "export", *map(str, FILES)], check=True, capture_output=True, text=True).stdout)


def unique(items, name):
    if len(items) != len(set(items)):
        raise ValueError("duplicate " + name)


def validate(data):
    policy = data["interpretationReview"]
    if policy["status"] != "pending-user-review":
        raise ValueError("this draft tool cannot approve reference meanings")
    unique([p["id"] for p in policy["policies"]], "policy")
    for example in data["contractExamples"].values():
        sources = {s["id"]: s for s in example["sources"]}
        reports = {s["id"]: s for s in example["extractorReports"]}
        meanings = {m["id"]: m for m in example["meanings"]}
        if len(sources) != len(example["sources"]) or len(reports) != len(example["extractorReports"]) or len(meanings) != len(example["meanings"]):
            raise ValueError("duplicate review identity")
        unique(example["bindings"], "binding")
        unique([v["id"] for v in example["representations"]], "representation")
        windows = example["windows"]
        if example["currentWindow"] not in windows:
            raise ValueError("missing current frame")
        for members in windows.values():
            unique(members, "window member")
            if not set(members) <= sources.keys():
                raise ValueError("window refers to absent source")
        for report in reports.values():
            if report["window"] not in windows:
                raise ValueError("extractor report has no basis window")
        for meaning in meanings.values():
            if meaning["window"] not in windows:
                raise ValueError("meaning has no basis window")
            for field in ("about", "possibleAbout", "affects"):
                unique(meaning[field], field)
                if not set(meaning[field]) <= set(example["bindings"]):
                    raise ValueError("unknown binding")
            if meaning["possibleAbout"] and (len(meaning["possibleAbout"]) < 2 or meaning["about"]):
                raise ValueError("ambiguous targets cannot silently become definite targets")
            channels = set()
            for anchor in meaning["anchors"]:
                channels.add(anchor["channel"])
                collection = sources if anchor["channel"] == "source" else reports
                if anchor["id"] not in collection or not anchor["quote"].strip() or anchor["quote"] not in collection[anchor["id"]]["text"]:
                    raise ValueError("invented or non-contiguous anchor")
                if anchor["channel"] == "source" and anchor["id"] not in windows[meaning["window"]]:
                    raise ValueError("source unavailable in meaning's basis frame")
                if anchor["channel"] == "extractor" and reports[anchor["id"]]["window"] != meaning["window"]:
                    raise ValueError("extractor report crosses its basis frame")
            if meaning["origin"] == "source" and channels != {"source"}:
                raise ValueError("derived interpretation cannot become source evidence")
            if meaning["origin"] == "extractor" and "extractor" not in channels:
                raise ValueError("extractor limitation requires an attributed extractor report")
            if meaning["origin"] == "derived" and channels != {"source"}:
                raise ValueError("derived view requires original source anchors")
            kind = meaning["kind"]
            source_kinds = {"assertion", "source-uncertainty", "source-qualifier", "question", "directive", "assurance", "assurance-withdrawal", "grant", "revocation"}
            if kind in source_kinds and meaning["origin"] != "source":
                raise ValueError("source meaning cannot originate from extractor opinion")
            if kind in {"derived-state", "contested"} and meaning["origin"] != "derived":
                raise ValueError("derived condition is not a newly uttered source assertion")
            if kind == "source-uncertainty" and (meaning["origin"] != "source" or meaning["holder"] not in {sources[a["id"]]["actor"] for a in meaning["anchors"] if a["channel"] == "source"}):
                raise ValueError("source uncertainty holder is not grounded")
            if kind == "extractor-limit" and (meaning["origin"] != "extractor" or meaning["holder"] not in {reports[a["id"]]["actor"] for a in meaning["anchors"] if a["channel"] == "extractor"}):
                raise ValueError("extractor limitation is not source professed ignorance")
            if kind == "coverage-limit" and meaning["origin"] not in {"source", "derived"}:
                raise ValueError("coverage is a framed source/window condition, not an extractor's personal ignorance")
            if not set(meaning["affects"]) <= set(meaning["about"]):
                raise ValueError("affected world binding must be identified, not silently borrowed from another topic")
            if kind in {"coverage-limit", "derived-state", "contested"} and meaning["holder"] is not None:
                raise ValueError("window condition cannot invent a knowledge holder")
            if meaning["affects"] and kind not in {"grant", "revocation"}:
                raise ValueError("topic or epistemic act cannot assign a world binding")
            if kind in {"grant", "revocation"} and not meaning["affects"]:
                raise ValueError("normative act needs an affected binding")
            if (kind == "directive") != ("action" in meaning):
                raise ValueError("directive needs action object and condition, not a scalar assignment")
            target = meaning["target"]
            if target is not None:
                expected = {"assurance-withdrawal": "assurance", "revocation": "grant"}.get(kind)
                if target not in meanings or target == meaning["id"] or meanings[target]["kind"] != expected:
                    raise ValueError("act targets the wrong kind of prior meaning")
                if not {a["id"] for a in meanings[target]["anchors"] if a["channel"] == "source"} <= set(windows[meaning["window"]]):
                    raise ValueError("act target unavailable in its basis window")
            elif kind in {"assurance-withdrawal", "revocation"}:
                raise ValueError("revision act lacks its prior target")
        required = {m["id"] for m in meanings.values() if m["required"]}
        for variant in example["representations"]:
            unique(variant["retains"], "preservation witness")
            if not required <= set(variant["retains"]) <= meanings.keys():
                raise ValueError("representation does not declare all required meanings recoverable")
    return data


def fingerprints(data):
    policy = data["interpretationReview"]
    shared = {key: policy[key] for key in ("version", "boundary", "policies")}
    return {"packet_sha256": digest({"contract": shared, "examples": data["contractExamples"]}),
            "policy_sha256": digest(shared), "examples": {key: digest(value) for key, value in sorted(data["contractExamples"].items())}}


def render(data):
    hashes = fingerprints(data)
    policy = data["interpretationReview"]
    lines = ["# Interpretation contract: exact review examples", "", "**Draft — pending your review. No paid calls or semantic approval.**", "",
             "This is a reproducible review projection of [`interpretation-review.cue`](../experiments/judgment/interpretation-review.cue) and [`interpretation-examples.cue`](../experiments/judgment/interpretation-examples.cue), not another evidence source or a production IR specification.", "",
             f'Packet SHA-256: `{hashes["packet_sha256"]}`', f'Policy SHA-256: `{hashes["policy_sha256"]}`', "",
             policy["approval"], "", policy["boundary"], "", "Approval can name all eight examples under this packet hash, or specific example IDs plus the policy hash and their content hashes. Merging this PR is not label approval. Corrections produce new hashes; approval records must remain separate from reviewed content.", "", "## Proposed shared rules", ""]
    for rule in policy["policies"]:
        lines.append(f'- **{rule["id"]}:** {rule["proposal"]}')
    lines += ["", "## Exact source → proposed meaning pairs", "", "The records below are review notation, not a required storage layout. 'Retains' names material meaning obligations; it does not require one node per obligation. Validators check anchors, frames, ownership, references, and declared coverage, not natural-language entailment or encoding equivalence."]
    for key, example in sorted(data["contractExamples"].items()):
        lines += ["", f'### {key}: {example["title"]}', "", f'Example SHA-256: `{hashes["examples"][key]}`', "", f'**Decision:** {example["decision"]}', "", example["context"], "",
                  "**Frames:** " + "; ".join(f'{name} = {", ".join(ids)}' for name, ids in example["windows"].items()) + f'. Current view: {example["currentWindow"]}. These are bounded supplied snapshots, not global coverage or durable-ingestion guarantees.', ""]
        for source in example["sources"]:
            lines += [f'**Source {source["id"]} — {source["actor"]}, said {source["saidAt"]}:**', "", "> " + source["text"], ""]
        for report in example["extractorReports"]:
            lines += [f'**Hypothetical extractor report {report["id"]} — {report["actor"]}, basis {report["window"]}; not source evidence:**', "", "> " + report["text"], ""]
        lines += ["**Proposed material interpretation:**", ""]
        for meaning in example["meanings"]:
            metadata = [meaning["kind"], "origin=" + meaning["origin"], "basis=" + meaning["window"]]
            if meaning["holder"] is not None:
                metadata.append("holder=" + meaning["holder"])
            for field in ("about", "possibleAbout", "affects"):
                if meaning[field]:
                    metadata.append(field + "=" + ",".join(meaning[field]))
            if meaning["target"]:
                metadata.append("target=" + meaning["target"])
            if "action" in meaning:
                metadata.append("action=" + json.dumps(meaning["action"], sort_keys=True))
            anchors = "; ".join(f'{a["channel"]}:{a["id"]} “{a["quote"]}”' for a in meaning["anchors"])
            lines.append(f'- `{meaning["id"]}` ({"; ".join(metadata)}; {"required" if meaning["required"] else "optional"}): {meaning["content"]} Anchor: {anchors}')
        lines += ["", "**Acceptable representation alternatives:**", ""]
        for variant in example["representations"]:
            lines.append(f'- `{variant["id"]}`: {variant["description"]} Retains: {", ".join(variant["retains"])}.')
        lines += ["", "**Forbidden inferences:**", ""]
        for forbidden in example["forbidden"]:
            lines.append(f'- “{forbidden["interpretation"]}” — {forbidden["why"]}')
        lines += ["", "**Pertinent current projection:** " + example["projection"]["current"], "", "**History/recovery boundary:** " + example["projection"]["history"]]
    return "\n".join(lines) + "\n"


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true", help="check the committed review projection; no writes")
    mode.add_argument("--render", action="store_true", help="print the exact review projection")
    mode.add_argument("--output", help="write a NEW review projection path, never overwrite")
    args = parser.parse_args(argv)
    try:
        data = validate(load())
        text = render(data)
        if args.check and PROJECTION.read_text() != text:
            raise ValueError("review projection is stale")
        if args.output:
            path = Path(args.output)
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("x") as stream:
                stream.write(text)
        if args.render:
            print(text, end="")
        else:
            print(json.dumps({"status": "pending-user-review", "paid_calls": 0, "semantic_approval": False, **fingerprints(data)}, indent=2))
        return 0
    except (ValueError, KeyError, TypeError, OSError, subprocess.CalledProcessError):
        print("Review check failed, projection stale, or output exists. No approval or model call occurred.")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
