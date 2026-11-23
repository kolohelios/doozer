"""Offline, source-bound review of two transfer disputes; no approval or model calls."""

import argparse
import copy
import gzip
import hashlib
import json
from pathlib import Path
import subprocess

from scripts import interpretation_review as review
from scripts.calibration_pilot import digest as protocol_digest

FILES = tuple(review.DIRECTORY / name for name in ("interpretation-review.cue", "reviewed-panel.cue", "reviewed-threads.cue", "transfer-review.cue"))
PROJECTION = review.ROOT / "docs/transfer-review.md"
APPROVALS = review.DIRECTORY / "transfer-approvals.cue"


def load():
    return json.loads(subprocess.run(["cue", "export", *map(str, FILES)], check=True, capture_output=True, text=True).stdout)


def validate(raw):
    archive = raw["transferReviewArchive"]
    encoded = (review.ROOT / archive["path"]).read_bytes()
    if hashlib.sha256(encoded).hexdigest() != archive["sha256"]:
        raise ValueError("review archive changed")
    saved = json.loads(gzip.decompress(encoded))
    if protocol_digest(saved["protocol"]["frozen"]) != saved["protocol"]["sha256"]:
        raise ValueError("frozen context hash mismatch")
    packets = {p["id"]: p for p in saved["protocol"]["frozen"]["packets"]}
    examples = copy.deepcopy(raw["transferExamples"])
    if set(examples) != set(raw["transferReviewOrigins"]) or len(examples) != 2:
        raise ValueError("review origin identities mismatch")
    for key, example in examples.items():
        if example["extractorReports"]:
            raise ValueError("source-only review cannot import model opinions")
        packet_id = raw["transferReviewOrigins"][key]
        original = packets[packet_id]
        expected = [{"id": s["id"], "actor": s["actor"], "saidAt": s["sentAt"], "text": s["text"], "authority": s["authority"], "origin": s["origin"], "replyTo": s["replyTo"], "derivedFrom": s["derivedFrom"]} for s in original["sources"]]
        if example["sources"] != expected or example["currentWindow"] != original["window"] or example["windows"][example["currentWindow"]] != [s["id"] for s in expected]:
            raise ValueError("review sources or frame differ from frozen context")
        for window, members in example["windows"].items():
            basis = packets.get(original["thread"] + "/" + window)
            if basis is None or members != [s["id"] for s in basis["sources"]]:
                raise ValueError("historical review frame differs from frozen context")
        example["review_basis"] = {"archive": copy.deepcopy(archive), "packet_id": packet_id}
    return review.validate({"interpretationReview": raw["transferReview"], "contractExamples": examples})


def load_decisions():
    return json.loads(subprocess.run(["cue", "export", str(APPROVALS)], check=True, capture_output=True, text=True).stdout)["transferApprovals"]


def approval_status(data, record=None):
    record = load_decisions() if record is None else record
    status = review.approval_status(data, record)
    return {**status, "pending_examples": sorted(set(data["contractExamples"]) - set(status["approved_examples"])), "decision_sha256": review.digest(record)}


def render(data, selected=None):
    hashes = review.fingerprints(data)
    policy = data["interpretationReview"]
    lines = ["# Transfer disputes: proposed meanings", "", "**Review proposal snapshot. See the [separate decision record](../experiments/judgment/transfer-approvals.cue) for current example approvals. Validation and merging grant no approval.**", "",
             "Generated from [`transfer-review.cue`](../experiments/judgment/transfer-review.cue), using the existing interpretation-review notation. Original sources are checked against the immutable partial-run archive, not model verdicts. Earlier approvals and frozen scores are unchanged.", "",
             f'Packet SHA-256: `{hashes["packet_sha256"]}`', f'Policy SHA-256: `{hashes["policy_sha256"]}`', "", policy["approval"], "", policy["boundary"], "",
             "Approve, reject, or amend one example at a time. Each example hash binds its full sources, proposed meanings, alternatives, projections, and archive context. No decision for one example applies to the other. These are semantic proposals, not new mandatory atom layouts. Mechanical checks verify anchors and declared recovery, not entailment or actual equivalence."]
    for rule in policy["policies"]:
        lines += ["", f'**Proposed scope rule — {rule["id"]}:** {rule["proposal"]}']
    for key, example in sorted(data["contractExamples"].items()):
        if selected is not None and key != selected:
            continue
        lines += ["", f'## {key}: {example["title"]}', "", f'Example SHA-256: `{hashes["examples"][key]}`', "", f'**Proposed decision:** {example["decision"]}', "", example["context"], "",
                  f'**Frozen context:** `{example["review_basis"]["packet_id"]}`; current window `{example["currentWindow"]}`. Archive SHA-256: `{example["review_basis"]["archive"]["sha256"]}`.', "", "### Exact sources", ""]
        lines += ["**Frames:** " + "; ".join(f'{name} = {", ".join(ids)}' for name, ids in example["windows"].items()) + ".", "", "**Bindings:** " + ", ".join(example["bindings"]) + ".", ""]
        for source in example["sources"]:
            lines += [f'**{source["id"]} — {source["actor"]}, {source["saidAt"]}** (declared authority `{source["authority"]}`, origin `{source["origin"]}`, reply `{source["replyTo"]}`, derived from {source["derivedFrom"]}):', "", "> " + source["text"], ""]
        lines += ["### Proposed interpretation", ""]
        for meaning in example["meanings"]:
            metadata = {k: v for k, v in meaning.items() if k not in {"content", "anchors"}}
            anchors = "; ".join(f'{a["channel"]}:{a["id"]} “{a["quote"]}”' for a in meaning["anchors"])
            lines += [f'- **{meaning["id"]}:** {meaning["content"]}', f'  Review fields: `{json.dumps(metadata, sort_keys=True)}`. Anchors: {anchors}']
        lines += ["", "### Acceptable recovery paths", ""]
        for variant in example["representations"]:
            lines += [f'- **{variant["id"]}:** {variant["description"]} Retains: {", ".join(variant["retains"])}.']
        lines += ["", "### Forbidden inferences", ""]
        for item in example["forbidden"]:
            lines += [f'- “{item["interpretation"]}” {item["why"]}']
        lines += ["", "**Pertinent current projection:** " + example["projection"]["current"], "", "**History/recovery:** " + example["projection"]["history"]]
    return "\n".join(lines) + "\n"


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--render", action="store_true")
    mode.add_argument("--output", help="new projection path only")
    parser.add_argument("--example", choices=("01-coverage-frame", "02-invitation-directive"), help="render only this example, without approving it")
    args = parser.parse_args(argv)
    try:
        if args.example and not args.render:
            raise ValueError("single-example selection requires render")
        data = validate(load())
        decisions = approval_status(data)
        text = render(data, args.example)
        if args.check and PROJECTION.read_text() != text:
            raise ValueError("stale review projection")
        if args.output:
            with Path(args.output).open("x") as stream:
                stream.write(text)
        if args.render:
            print(text, end="")
        else:
            print(json.dumps({**decisions, "proposal_snapshot_status": data["interpretationReview"]["status"], "paid_calls": 0, "validation_grants_approval": False, **review.fingerprints(data)}, indent=2))
        return 0
    except (ValueError, KeyError, TypeError, OSError, subprocess.CalledProcessError):
        print("Transfer review failed or output exists. No approval, model call, or rescore occurred.")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
