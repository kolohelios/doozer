"""Paired retrieval/understanding experiment; no canonical knowledge writes."""

import argparse
import copy
import hashlib
import json
from pathlib import Path
import subprocess

from scripts.evaluation_client import CallFailure, Client, Contracts, OutputFailure
from scripts.jev_probe import export_cue
from scripts.retrieval import connect, context_size, fingerprint, load_snapshot, neighborhood, validate_cache, vector_rank
from scripts.retrieval_probe import embed, write_json
from scripts.workbench import ROOT


DIRECTORY = ROOT / "experiments/understanding"
ARMS = ("full", "vector", "vector-links")


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, allow_nan=False).encode()).hexdigest()


def load_inputs(noise=None):
    data = export_cue(sorted(DIRECTORY.glob("*.cue")))
    documents, raw, _supplied_graph, embedding_plan = load_snapshot(noise)
    # Existing hand-authored knowledge links are deliberately NOT used here.
    case_ids, incoming = {}, []
    for case_id, case in sorted(data["cases"].items()):
        case_ids[case_id] = []
        check_ids = [check["id"] for check in case["checks"]]
        if len(check_ids) != len(set(check_ids)):
            raise ValueError("duplicate rubric check")
        for source_id, source in sorted(case["sources"].items()):
            key = "heldout/" + source_id
            if key in documents:
                raise ValueError("held-out source identity is not unique")
            document = {"id": key, **{field: source[field] for field in ("text", "anchor", "kind", "saidAt")}}
            if "replyTo" in source:
                document["replyTo"] = "heldout/" + source["replyTo"]
            documents[key], raw[key] = document, set()
            case_ids[case_id].append(key)
            incoming.append(key)
    for key in incoming:
        if "replyTo" in documents[key]:
            connect(raw, key, documents[key]["replyTo"])
    queries = {key: {"text": case["question"]} for key, case in data["cases"].items()}
    embedding_plan = {**embedding_plan, "queries": queries}
    return data, documents, raw, embedding_plan, case_ids, sorted(incoming)


def protocol(data, documents, raw, embedding_plan, case_ids, contracts):
    frozen = {
        "plan": data["plan"], "cases": data["cases"], "case_sources": case_ids,
        "contract_sha256": hashlib.sha256(contracts.schema.encode()).hexdigest(),
        "index_fingerprint": fingerprint(documents, embedding_plan["queries"], "openai/text-embedding-3-small",
                                         embedding_plan["embeddingDimensions"]),
        "raw_graph_sha256": digest({key: sorted(value) for key, value in raw.items()}),
        "documents": len(documents), "source_snapshot_sha256": digest(documents),
        "implementation": {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in (
            "scripts/understanding.py", "scripts/evaluation_client.py", "scripts/retrieval.py",
            "scripts/retrieval_probe.py", "scripts/workbench_models.py", "scripts/jev_probe.py",
        )},
    }
    frozen = copy.deepcopy(frozen)
    return {"sha256": digest(frozen), "frozen": frozen}


def validate_links(value, incoming, candidates, documents, maximum):
    counts = {key: 0 for key in incoming}
    seen = set()
    for link in value["links"]:
        left, right = link["from"], link["to"]
        if left == right or not any(
            source in incoming and other in candidates[source] for source, other in ((left, right), (right, left))
        ):
            raise OutputFailure("link outside incoming candidate neighborhoods")
        if left not in documents or right not in documents:
            raise OutputFailure("unknown link endpoint")
        if link["fromQuote"] not in documents[left]["text"] or link["toQuote"] not in documents[right]["text"]:
            raise OutputFailure("fabricated link quotation")
        pair = tuple(sorted((left, right)))
        if pair in seen:
            raise OutputFailure("duplicate proposed link")
        seen.add(pair)
        for source in counts:
            if source in pair:
                counts[source] += 1
                if counts[source] > maximum:
                    raise OutputFailure("too many links for incoming source")


def discover_links(documents, raw, vectors, incoming, plan, client, report, checkpoint):
    graph = {key: set(values) for key, values in raw.items()}
    for start in range(0, len(incoming), plan["linkBatchSize"]):
        batch = incoming[start:start + plan["linkBatchSize"]]
        candidates = {}
        for key in batch:
            view = {**vectors, "q:incoming": vectors["d:" + key]}
            ranked = [other for other in vector_rank(documents, view, "incoming") if other != key]
            candidates[key] = sorted(set(ranked[:plan["linkNeighbors"]]) | raw[key])
        allowed = set(batch) | {key for neighbors in candidates.values() for key in neighbors}
        source_view = {key: documents[key] for key in sorted(allowed)}
        context = {"incoming": batch, "candidates": candidates, "sources": list(source_view.values())}
        record = {"incoming": batch, "candidates": candidates, "status": "pending", "links": []}
        report["link_batches"].append(record)
        try:
            value = client.call("link", "#Links", context, f"link-{start}")
            validate_links(value, batch, candidates, source_view, plan["maxLinksPerSource"])
            for link in value["links"]:
                connect(graph, link["from"], link["to"])
            record.update(status="validated-proposal", links=value["links"])
        except OutputFailure:
            record["status"] = "invalid-output-no-replacement"
        checkpoint()
    return graph


def make_contexts(documents, raw, graph, vectors, embedding_plan, cases, case_ids, plan):
    result = []
    order = sorted(cases, key=lambda key: digest([plan["orderSeed"], key]))
    for position, case_id in enumerate(order):
        case = cases[case_id]
        ranked = vector_rank(documents, vectors, case_id)
        raw_context, _ = neighborhood(documents, ranked, raw, budget=plan["contextBytes"],
                                       seeds=plan["seedCount"], hops=plan["graphHops"])
        raw_selected = {doc["id"] for doc in raw_context}
        rotated = ARMS[position % len(ARMS):] + ARMS[:position % len(ARMS)]
        for arm in rotated:
            if arm == "full":
                context = [documents[key] for key in case_ids[case_id]]
            else:
                context, _ = neighborhood(
                    documents, ranked, graph if arm == "vector-links" else raw,
                    budget=plan["contextBytes"], seeds=plan["seedCount"] if arm == "vector-links" else plan["candidateCount"],
                    hops=plan["graphHops"] if arm == "vector-links" else 0,
                )
            context = sorted(context, key=lambda doc: doc["id"])
            selected = {doc["id"] for doc in context}
            required = {"heldout/" + ref for check in case["checks"] for ref in check["evidence"]}
            result.append({
                "case": case_id, "arm": arm, "question": case["question"], "context": context,
                "context_bytes": context_size(context), "status": "pending",
                "retrieval": {"required": sorted(required), "missing": sorted(required - selected),
                              "recall": len(required & selected) / len(required),
                              "raw_links_recall": len(required & raw_selected) / len(required),
                              "known_link_boundary": sorted({neighbor for key in selected for neighbor in graph[key]} - selected)},
            })
    return result


def answer_text(answer):
    return "\n".join([answer["summary"],
                      *[claim["scope"] + " | " + claim["attribution"] + " | " + claim["text"] for claim in answer["claims"]],
                      *[directive["scope"] + " | " + directive["instruction"] for directive in answer["directives"]],
                      *answer["uncertainties"]])


def validate_understanding(answer, context):
    sources = {doc["id"]: doc for doc in context}
    for claim in answer["claims"] + answer["directives"]:
        for citation in claim["evidence"]:
            if citation["source"] not in sources or citation["quote"] not in sources[citation["source"]]["text"]:
                raise OutputFailure("understanding cites unavailable or fabricated evidence")
            if sources[citation["source"]]["kind"] == "projection":
                raise OutputFailure("derived text used as independent support")


def judge_context(row, case, documents, case_ids):
    answer = row["understanding"]
    cited = {citation["source"] for claim in answer["claims"] + answer["directives"] for citation in claim["evidence"]}
    source_ids = set(case_ids) | cited
    return {
        "question": case["question"], "candidate": answer, "answer_text": answer_text(answer),
        "authoritative_sources": [documents[key] for key in sorted(source_ids)],
        "rubric": [{"id": check["id"], "requirement": check["requirement"],
                    "supportingSources": ["heldout/" + ref for ref in check["evidence"]]}
                   for check in case["checks"]],
    }


def validate_judgment(value, context):
    expected = {check["id"] for check in context["rubric"]}
    if set(value["checks"]) != expected:
        raise OutputFailure("judge omitted or invented rubric checks")
    sources = {doc["id"]: doc for doc in context["authoritative_sources"]}
    for check in value["checks"].values():
        quotes = check["answerQuotes"]
        if (check["result"] == "pass" and not quotes) or any(
            not quote.strip() or quote not in context["answer_text"] for quote in quotes
        ):
            raise OutputFailure("judge misquotes candidate or passes an omission")
        for citation in check["citations"]:
            if citation["source"] not in sources or citation["quote"] not in sources[citation["source"]]["text"]:
                raise OutputFailure("judge fabricates supporting source span")
    for unsupported in value["unsupported"]:
        if unsupported["answerQuote"] not in context["answer_text"]:
            raise OutputFailure("judge fabricates unsupported answer span")


def summarize(rows):
    by_arm = {}
    for arm in ARMS:
        group = [row for row in rows if row["arm"] == arm]
        judged = [row for row in group if row["status"] == "judged"]
        scores = [sum(check["result"] == "pass" for check in row["judgment"]["checks"].values()) /
                  len(row["judgment"]["checks"]) for row in judged]
        by_arm[arm] = {
            "planned": len(group), "judged": len(judged),
            "status_counts": {status: sum(row["status"] == status for row in group) for status in sorted({row["status"] for row in group})},
            "mean_evidence_recall": sum(row["retrieval"]["recall"] for row in group) / len(group),
            "provisional_pass_fraction": sum(scores) / len(scores) if scores else None,
            "unsupported_findings": sum(len(row["judgment"]["unsupported"]) for row in judged),
            "fully_passing": sum(not row["judgment"]["unsupported"] and
                                 all(check["result"] == "pass" for check in row["judgment"]["checks"].values()) for row in judged),
        }
    paired = []
    for case_id in sorted({row["case"] for row in rows}):
        group = {row["arm"]: row for row in rows if row["case"] == case_id}
        if len(group) != 3 or any(row["status"] != "judged" for row in group.values()):
            continue
        scores = {arm: sum(check["result"] == "pass" for check in row["judgment"]["checks"].values()) /
                  len(row["judgment"]["checks"]) for arm, row in group.items()}
        paired.append({"case": case_id, "evidence": {arm: row["retrieval"]["recall"] for arm, row in group.items()},
                       "provisional_pass": scores,
                       "vector_to_links_evidence_delta": group["vector-links"]["retrieval"]["recall"] - group["vector"]["retrieval"]["recall"],
                       "vector_to_links_pass_delta": scores["vector-links"] - scores["vector"]})
    return {"by_arm": by_arm, "complete_pairs": paired,
            "warning": "Provisional model judgments, not semantic proof or statistical confirmation; human review required."}


def run(data, documents, raw, embedding_plan, case_ids, incoming, cache, client, report, checkpoint):
    plan, cases = data["plan"], data["cases"]
    vectors = validate_cache(cache, documents, embedding_plan["queries"])
    report["status"], report["link_batches"] = "linking", []
    graph = discover_links(documents, raw, vectors, incoming, plan, client, report, checkpoint)
    report["rows"] = make_contexts(documents, raw, graph, vectors, embedding_plan, cases, case_ids, plan)
    report["status"] = "generating"
    generations = {}
    for row in report["rows"]:
        context = {"question": row["question"], "sources": row["context"]}
        key = digest(context)
        value = None
        try:
            if key in generations:
                cached = generations[key]
                row["generation_reused_from"] = cached["label"]
                if "failure_reason" in cached:
                    value = cached.get("rejected_value")
                    raise OutputFailure(cached["failure_reason"])
                row["understanding"] = copy.deepcopy(cached["value"])
            else:
                value = client.call("reason", "#Understanding", context, row["case"] + ":" + row["arm"])
                validate_understanding(value, row["context"])
                row["understanding"] = value
                generations[key] = {"value": copy.deepcopy(value), "label": row["case"] + ":" + row["arm"]}
            row["status"] = "generated"
        except OutputFailure as error:
            row["status"] = "invalid-understanding-no-replacement"
            row["failure_reason"] = str(error)
            if value is not None:
                row["rejected_understanding"] = getattr(client, "redact", copy.deepcopy)(value)
            generations.setdefault(key, {"label": row["case"] + ":" + row["arm"],
                                         "failure_reason": str(error), "rejected_value": row.get("rejected_understanding")})
        checkpoint()
    return judge_rows(data, documents, case_ids, client, report, checkpoint)


def judge_rows(data, documents, case_ids, client, report, checkpoint):
    plan, cases = data["plan"], data["cases"]
    report["status"] = "judging"
    judgments = {}
    for row in sorted(report["rows"], key=lambda item: digest(["judge", plan["orderSeed"], item["case"], item["arm"]])):
        if row["status"] != "generated":
            continue
        context = judge_context(row, cases[row["case"]], documents, case_ids[row["case"]])
        key = digest(context)
        value = None
        try:
            if key in judgments:
                row["judgment_reused"] = True
                if "failure_reason" in judgments[key]:
                    value = judgments[key].get("rejected_value")
                    raise OutputFailure(judgments[key]["failure_reason"])
                row["judgment"] = copy.deepcopy(judgments[key]["value"])
            else:
                value = client.call("judge", "#Judgment", context, row["case"] + ":" + row["arm"])
                validate_judgment(value, context)
                row["judgment"] = value
                judgments[key] = {"value": copy.deepcopy(value)}
            row["status"] = "judged"
        except OutputFailure as error:
            row["status"] = "invalid-judge-output-no-replacement"
            row["failure_reason"] = str(error)
            if value is not None:
                row["rejected_judgment"] = getattr(client, "redact", copy.deepcopy)(value)
            judgments.setdefault(key, {"failure_reason": str(error), "rejected_value": row.get("rejected_judgment")})
        checkpoint()
    report["summary"] = summarize(report["rows"])
    report["status"] = "complete-provisional"
    checkpoint()
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--embed", action="store_true")
    mode.add_argument("--live", action="store_true")
    mode.add_argument("--audit", help="new judge-only assessment of saved answers; never regenerates them")
    parser.add_argument("--cache")
    parser.add_argument("--noise", type=int)
    parser.add_argument("--budget-usd", type=float)
    parser.add_argument("--max-calls", type=int, default=40)
    parser.add_argument("--output", required=True)
    for role in ("link", "reason", "judge"):
        parser.add_argument("--" + role + "-model")
        parser.add_argument("--" + role + "-provider")
    args = parser.parse_args(argv)
    if Path(args.output).exists():
        parser.error("output exists; use a new run path")
    if args.cache and Path(args.cache).resolve() == Path(args.output).resolve():
        parser.error("cache and report paths must differ")
    report, client = {}, None
    try:
        data, documents, raw, embedding_plan, case_ids, incoming = load_inputs(args.noise)
        for role in ("link", "reason", "judge"):
            for field in ("model", "provider"):
                override = getattr(args, role + "_" + field)
                if override:
                    data["plan"]["roles"][role][field] = override
        if data["plan"]["roles"]["reason"]["model"] == data["plan"]["roles"]["judge"]["model"]:
            raise ValueError("this comparison requires a different judge model")
        contracts = Contracts(DIRECTORY / "contracts.cue")
        report = {"protocol": protocol(data, documents, raw, embedding_plan, case_ids, contracts),
                  "status": "prepared", "trace": [], "rows": []}
        write_json(args.output, report)  # Freeze rubric, prompts, roles, and inputs BEFORE calls.
        if args.embed:
            if not args.cache:
                raise ValueError("new cache path required")
            cache = embed(documents, embedding_plan, "openai/text-embedding-3-small", budget=args.budget_usd,
                          max_calls=args.max_calls, cache_path=args.cache)
            report.update(status="index-built", embedding_trace=cache["trace"])
            write_json(args.output, report)
        elif args.audit:
            parent = json.loads(Path(args.audit).read_text())
            frozen = parent["protocol"]["frozen"]
            if digest(frozen) != parent["protocol"]["sha256"]:
                raise ValueError("parent protocol hash mismatch")
            if digest(frozen["cases"]) != digest(data["cases"]) or frozen["source_snapshot_sha256"] != digest(documents):
                raise ValueError("audit cannot change rubric or source evidence")
            if frozen["plan"]["reasonInstructions"] != data["plan"]["reasonInstructions"] or frozen["plan"]["roles"]["reason"] != data["plan"]["roles"]["reason"]:
                raise ValueError("audit cannot change generation treatment")
            report.update(parent_protocol=parent["protocol"]["sha256"], parent_rows_sha256=digest(parent["rows"]),
                          rows=copy.deepcopy(parent["rows"]), audit_only=True)
            for row in report["rows"]:
                row["parent_status"] = row["status"]
                row.pop("judgment", None)
                row.pop("judgment_reused", None)
                for field in ("failure_reason", "rejected_judgment"):
                    if field in row:
                        row["parent_" + field] = row.pop(field)
                if "understanding" in row:
                    contracts.validate("#Understanding", row["understanding"])
                    validate_understanding(row["understanding"], row["context"])
                    row["status"] = "generated"
            client = Client(data["plan"], contracts, budget=args.budget_usd, max_calls=args.max_calls,
                            on_trace=lambda: write_json(args.output, report))
            report["trace"] = client.trace
            write_json(args.output, report)
            judge_rows(data, documents, case_ids, client, report, lambda: write_json(args.output, report))
        elif args.live:
            if not args.cache:
                raise ValueError("existing embedding cache required")
            cache = json.loads(Path(args.cache).read_text())
            validate_cache(cache, documents, embedding_plan["queries"])
            maximum = (len(incoming) + data["plan"]["linkBatchSize"] - 1) // data["plan"]["linkBatchSize"] + len(data["cases"]) * 6
            if args.max_calls < maximum:
                raise ValueError("call limit cannot accommodate the planned comparison")
            client = Client(data["plan"], contracts, budget=args.budget_usd, max_calls=args.max_calls,
                            on_trace=lambda: write_json(args.output, report))
            report["trace"] = client.trace
            run(data, documents, raw, embedding_plan, case_ids, incoming, cache, client, report,
                checkpoint=lambda: write_json(args.output, report))
        print(json.dumps({"output": args.output, "status": report["status"],
                          "protocol_sha256": report["protocol"]["sha256"], "summary": report.get("summary")}, indent=2))
        return 0
    except (ValueError, KeyError, TypeError, OSError, subprocess.CalledProcessError):
        if report:
            report["status"] = "stopped-no-automatic-retry"
            write_json(args.output, report)
        print("Experiment stopped; inspect the frozen protocol, stage statuses, and accounting. No canonical knowledge was changed.")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
