"""Reproduce a reviewed excerpt capture from explicit local public-source files; no network."""

import argparse
import hashlib
import json
import re
from pathlib import Path


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def curate(directory, *, curated_at):
    directory = Path(directory)
    inputs, sources = {}, []

    def raw(name):
        data = (directory / ("doozer-" + name)).read_bytes()
        inputs[name] = {"bytes": len(data), "sha256": sha(data)}
        return data

    def load(name):
        return json.loads(raw(name))

    def add(key, kind, anchor, body, ranges, timing, *, attribution, actor=None, thread=None, reason=None):
        data = body.encode()
        excerpts = [{"startByte": start, "endByte": end, "text": data[start:end].decode(), "sha256": sha(data[start:end])}
                    for start, end in ranges]
        sources.append({"id": key, "kind": kind, "anchor": anchor, "bodyBytes": len(data), "bodySHA256": sha(data),
                        "excerpts": excerpts, "timing": timing, "attribution": attribution,
                        "actor": actor, "thread": thread, "omission": reason})

    # The historical repository notice predates every selected GitHub contribution.
    notice = raw("field-notice")
    if sha(notice) != "34eacc032d37437ca918d97ce1afafc620108c4659ed9903fcfe261dfef2f83c":
        raise ValueError("reviewed contribution notice changed")
    raw("tlp5.html")
    events = load("field-docevents")["objects"] + load("field-docevents-2")["objects"]
    rfc_events = {"rfc7807": load("field-rfc7807-events")["objects"], "rfc9457": load("field-rfc-events")["objects"]}
    notices = ["# IETF source excerpts — separate terms\n\nOnly the excerpts in `capture.json` are third-party material. They are attributed\nto IETF and the identified documents/contributions under IETF Trust Legal\nProvisions 5.0 (effective March 25, 2015; corrected September 21, 2021),\nsection 3.c.iii (unmodified portions), not MIT OR Apache-2.0.\n\nTerms: https://trustee.ietf.org/documents/trust-legal-provisions/tlp-5/\nRepository notice (predating these contributions):\nhttps://github.com/ietf-wg-httpapi/rfc7807bis/blob/8bc8348b75df3254e609a6dea87847212ccae30b/CONTRIBUTING.md\n\nGitHub excerpts retain public account attribution and exact comment anchors in\nthe capture. No legal identity, authority, endorsement, patent license, or license\nto publish modified IETF prose is asserted. Interpretations must be labeled\nanalysis, not edited standards. Technical examples are quoted data under section\n3.c.iii, not code adopted for implementation. Signatures/contact details and\nnontechnical pings are omitted as identified byte ranges, not rewritten text.\nThe original documents, including their notices and authorship, remain at their\nrecorded official URLs. This scoped reuse review is not a blanket approval of\nother sources, provider transmission, or downstream uses.\n"]
    for key in ("rfc7807", "draft-03", "draft-04", "draft-05", "rfc9457"):
        data = raw(key)
        text = data.decode()
        start = data.index(b"\n1.  Introduction\n") + 1
        end = re.search(rb"\n[0-9]+\.  IANA Considerations\n", data[start:]).start() + start
        ranges = [(start, end)]
        # A personal-address URI example is not needed for this header-field arc.
        if key.startswith("draft"):
            line = next(line for line in data.splitlines() if line.startswith(b"   tag:") and b"@" in line)
            position = data.index(line, start)
            ranges = [(start, position), (position + len(line), end)]
        if key.startswith("draft"):
            event = next(e for e in events if e["type"] == "new_revision" and e["rev"] == key[-2:])
            anchor = f"https://www.ietf.org/archive/id/draft-ietf-httpapi-rfc7807bis-{key[-2:]}.txt"
        else:
            event = next(e for e in rfc_events[key] if e["type"] == "published_rfc")
            anchor = f"https://www.rfc-editor.org/rfc/{key}.txt"
        timing = {"statementAt": None, "versionNotBefore": event["time"], "basis": "datatracker-availability-event",
                  "evidence": f"https://datatracker.ietf.org/api/v1/doc/docevent/{event['id']}/"}
        add(key, "internet-draft" if key.startswith("draft") else "published-rfc", anchor, text, ranges, timing,
            attribution=f"IETF {key}; Mark Nottingham, Erik Wilde" + (", Sanjay Dalal" if key != "rfc7807" else ""),
            reason="Technical-body excerpts; notices/authorship below, references/contact sections excluded. Draft excerpts additionally omit one personal-address URI example; not a full-document reproduction.")
        legal_start = data.index(b"\nStatus of This Memo\n") + 1
        legal_end = data.index(b"\nTable of Contents\n", legal_start)
        sources[-1]["legalNotice"] = data[legal_start:legal_end].decode()
        notices.append(f"\n## {key}\n\n{anchor}\n\nAuthors: Mark Nottingham, Erik Wilde" + (", Sanjay Dalal" if key != "rfc7807" else "") + "\n\n```text\n" + data[legal_start:legal_end].decode() + "\n```\n")

    for number in (35, 39, 67):
        root = load(f"field-issue-{number}")
        comments = load(f"field-comments-{number}")
        if len(comments) != root["comments"] or len(comments) >= 100:
            raise ValueError("thread pagination/count changed; review before recapture")
        for row, suffix in [(root, "body"), *[(c, "c-" + str(c["id"])) for c in comments]]:
            body = row["body"] or ""
            end = body.find("\n-- \n")
            end = len(body) if end < 0 else end
            reason = "Email signature/contact footer excluded." if end < len(body) else None
            ranges = [(0, len(body[:end].encode()))] if body else []
            if row["id"] in (1031248592, 1060022468):
                ranges, reason = [], "Nontechnical social-link/ping locator only; original body hash retained."
            add(f"g{number}-{suffix}", "github-issue-body" if suffix == "body" else "github-comment", row["html_url"], body, ranges,
                {"statementAt": row["created_at"], "versionNotBefore": row["updated_at"], "basis": "github-api-last-update-not-edit-history", "evidence": row["url"]},
                actor={"id": f"https://api.github.com/user/{row['user']['id']}", "label": row["user"]["login"],
                       "basis": "GitHub API reported account at capture; not verified legal identity or authority"},
                attribution=f"IETF Contribution by GitHub account {row['user']['login']}; {row['html_url']}", thread=root["html_url"], reason=reason)
    for category in ("reviews", "inline"):
        for row in load(f"field-{category}-39"):
            body = row["body"] or ""
            add("g39-" + category + "-" + str(row["id"]), "github-review" if category == "reviews" else "github-inline-comment",
                row["html_url"], body, [(0, len(body.encode()))] if category == "reviews" else [],
                {"statementAt": row.get("submitted_at") or row.get("created_at"), "versionNotBefore": row.get("updated_at"),
                 "basis": "review-body-edit-history-unknown" if category == "reviews" else "github-api-last-update-not-edit-history", "evidence": row["html_url"]},
                actor={"id": f"https://api.github.com/user/{row['user']['id']}", "label": row["user"]["login"],
                       "basis": "GitHub API reported account at capture; not verified legal identity or authority"},
                attribution=f"IETF Contribution by GitHub account {row['user']['login']}; {row['html_url']}",
                thread="https://github.com/ietf-wg-httpapi/rfc7807bis/pull/39", reason="Formatting-only inline suggestion excluded." if category == "inline" else "Current review body retained; submission time is not proof of body-version visibility.")
    removal = load("field-removal")
    body = removal["commit"]["message"]
    add("removal-commit", "editor-commit", removal["html_url"], body, [(0, len(body.encode()))],
        {"statementAt": removal["commit"]["committer"]["date"], "versionNotBefore": None,
         "basis": "commit-time-is-not-publication-time", "evidence": removal["html_url"]},
        attribution=f"IETF Contribution; {removal['html_url']}",
        reason="Commit message links issues 67 and 56. Historical push/visibility time unknown; not inserted into earlier packets from committer time alone.")
    return {"version": "http-field-capture-v1", "curatedAt": curated_at, "rights": "IETF-TLP-5.0-3.c.iii", "inputCaptures": inputs,
            "sources": sources, "coverage": "All 52 issue comments, three thread bodies, one review and one inline comment indexed; selected technical excerpts, five document bodies and one removal message. External mailing-list/HTTP-WG/#56 context is not captured. Current-body API timestamps are conditional visibility evidence, not authenticated edit history."}, "\n".join(notices)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-directory", required=True)
    parser.add_argument("--output-directory", required=True)
    parser.add_argument("--curated-at", required=True, help="UTC curation time, not inferred source receipt time")
    args = parser.parse_args(argv)
    target = Path(args.output_directory)
    if (target / "capture.json").exists() or (target / "NOTICE.md").exists():
        raise ValueError("capture or notice exists; no overwrite")
    capture, notice = curate(args.input_directory, curated_at=args.curated_at)
    target.mkdir(parents=True, exist_ok=True)
    (target / "capture.json").write_text(json.dumps(capture, indent=2, ensure_ascii=False, allow_nan=False) + "\n")
    (target / "NOTICE.md").write_text(notice)
    print(json.dumps({"sources": len(capture["sources"]), "network_calls": 0, "rights": capture["rights"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
