"""Bounded retrieval mechanics and evaluator-side coverage metrics."""

from collections import Counter, deque
import hashlib
import json
import math
import re

from scripts.jev_probe import export_cue
from scripts.workbench import ROOT


STOP = set("a an and are as at be by can do does for from how i in is it of on or our that the this to was we what when where which with without".split())


def tokens(text):
    result = []
    for word in re.findall(r"[a-z0-9]+", text.lower()):
        if word in STOP:
            continue
        if word.endswith("ies") and len(word) > 4:
            word = word[:-3] + "y"
        elif word.endswith("s") and not word.endswith("ss") and len(word) > 4:
            word = word[:-1]
        result.append(word)
    return result


def connect(graph, left, right):
    if left not in graph or right not in graph or left == right:
        raise ValueError("unknown or self-referential knowledge link")
    graph[left].add(right)
    graph[right].add(left)


def load_snapshot(noise=None):
    experiment = export_cue(sorted((ROOT / "experiments/retrieval").glob("*.cue")))
    corpus = export_cue(sorted((ROOT / "corpus").glob("*.cue")))
    plan, generator = experiment["plan"], experiment["generator"]
    noise = plan["noiseDocuments"] if noise is None else noise
    if type(noise) is not int or not 0 <= noise <= 8192:
        raise ValueError("noise count outside 0..8192")
    documents, sources = {}, {}
    for scenario_id, scenario in sorted(corpus["scenarios"].items()):
        if scenario["synthetic"] is not True:
            raise ValueError("only synthetic fixtures are allowed")
        for source_id, source in sorted(scenario["sources"].items()):
            key = scenario_id + "/" + source_id
            documents[key] = {"id": key, "text": source["text"], "anchor": source["anchor"], "kind": source["kind"], "saidAt": source["saidAt"]}
            if "replyTo" in source:
                documents[key]["replyTo"] = scenario_id + "/" + source["replyTo"]
            if "derivedFrom" in source:
                documents[key]["derivedFrom"] = [scenario_id + "/" + ref for ref in source["derivedFrom"]]
            sources[key] = (scenario_id, source)
    for index in range(noise):
        key = f"archive/memo-{index:05d}"
        topic = generator["topics"][index % len(generator["topics"])]
        documents[key] = {
            "id": key, "kind": "document", "anchor": f"fixture://archive/memo/{index}",
            "text": f"Satellite archive memo {index}, site {index % 37}, workshop cycle {index // 37}. {topic}",
        }
    raw = {key: set() for key in documents}
    for key, (scenario_id, source) in sources.items():
        refs = source.get("derivedFrom", [])
        if "replyTo" in source:
            refs = refs + [source["replyTo"]]
        for reference in refs:
            connect(raw, key, scenario_id + "/" + reference)
    linked = {key: set(values) for key, values in raw.items()}
    for link in experiment["knowledgeLinks"]:
        connect(linked, link["from"], link["to"])
    for query in plan["queries"].values():
        required = query["requiredSources"]
        if len(required) != len(set(required)) or not set(required) <= documents.keys():
            raise ValueError("invalid evaluator source references")
        if query["negative"] != (not required):
            raise ValueError("negative probes must have an empty required set")
    return documents, raw, linked, plan


def embedding_items(documents, queries):
    # The provider sees strings only: never expected sources, tags, or graph links.
    return [("d:" + key, doc["text"]) for key, doc in sorted(documents.items())] + [
        ("q:" + key, query["text"]) for key, query in sorted(queries.items())
    ]


def fingerprint(documents, queries, model, dimensions):
    # Temporal/relationship metadata is reloaded for each benchmark, not embedded. Keep
    # its revision separate so raw-text vectors need not be bought again.
    indexed = {key: {field: doc[field] for field in ("id", "text", "anchor", "kind")} for key, doc in documents.items()}
    data = {"documents": indexed, "queries": {key: value["text"] for key, value in queries.items()},
            "model": model, "dimensions": dimensions}
    return hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()


def unit(vector, dimensions):
    if not isinstance(vector, list) or len(vector) != dimensions or not all(
        type(value) in (int, float) and math.isfinite(value) for value in vector
    ):
        raise ValueError("invalid embedding values or dimension")
    norm = math.sqrt(sum(value * value for value in vector))
    if not math.isfinite(norm) or norm == 0:
        raise ValueError("invalid embedding norm")
    return [value / norm for value in vector]


def validate_cache(cache, documents, queries):
    if cache.get("complete") is not True:
        raise ValueError("embedding cache is incomplete")
    dimensions = cache["dimensions"]
    if type(dimensions) is not int or not 1 <= dimensions <= 4096:
        raise ValueError("invalid cache dimensions")
    if cache["fingerprint"] != fingerprint(documents, queries, cache["model"], dimensions):
        raise ValueError("stale embedding snapshot or query set")
    expected = {key for key, _ in embedding_items(documents, queries)}
    if set(cache["vectors"]) != expected:
        raise ValueError("missing or extraneous embedding identities")
    return {key: unit(value, dimensions) for key, value in cache["vectors"].items()}


def lexical_rank(documents, query):
    counts = {key: Counter(tokens(doc["text"])) for key, doc in documents.items()}
    lengths = {key: sum(count.values()) for key, count in counts.items()}
    average = sum(lengths.values()) / len(lengths)
    terms = set(tokens(query))
    df = {term: sum(term in count for count in counts.values()) for term in terms}
    scores = []
    for key, count in counts.items():
        score = 0.0
        for term in terms:
            frequency = count[term]
            if frequency:
                idf = math.log(1 + (len(counts) - df[term] + 0.5) / (df[term] + 0.5))
                score += idf * frequency * 2.2 / (frequency + 1.2 * (0.25 + 0.75 * lengths[key] / average))
        if score:
            scores.append((score, key))
    return [key for _, key in sorted(scores, key=lambda item: (-item[0], item[1]))]


def vector_rank(documents, vectors, query_id):
    query = vectors["q:" + query_id]
    scores = [(sum(a * b for a, b in zip(query, vectors["d:" + key], strict=True)), key) for key in documents]
    return [key for _, key in sorted(scores, key=lambda item: (-item[0], item[1]))]


def fuse(left, right):
    scores = Counter()
    for ranking in (left[:100], right[:100]):
        for rank, key in enumerate(ranking, 1):
            scores[key] += 1 / (60 + rank)
    return sorted(scores, key=lambda key: (-scores[key], key))


def context_size(context):
    return len(json.dumps(context, ensure_ascii=False, separators=(",", ":")).encode())


def neighborhood(documents, ranking, graph, *, budget, seeds, hops):
    selected, selected_ids, skipped = [], set(), set()
    # Bundle each seed with its bounded linked neighborhood before the next seed.
    for seed in ranking[:seeds]:
        visited = set()
        queue = deque([(seed, 0)])
        while queue:
            key, depth = queue.popleft()
            if key in visited:
                continue
            visited.add(key)
            if key not in selected_ids:
                candidate = selected + [documents[key]]
                if context_size(candidate) <= budget:
                    selected = candidate
                    selected_ids.add(key)
                    skipped.discard(key)
                else:
                    skipped.add(key)
            if depth < hops:
                queue.extend((neighbor, depth + 1) for neighbor in sorted(graph[key]))
    return selected, sorted(skipped)


def benchmark(documents, raw, linked, plan, cache=None, *, budget=None):
    budget = plan["contextBytes"] if budget is None else budget
    if type(budget) is not int or not 128 <= budget <= 16384:
        raise ValueError("context budget outside 128..16384 bytes")
    vectors = validate_cache(cache, documents, plan["queries"]) if cache is not None else None
    rows = []
    for query_id, query in sorted(plan["queries"].items()):
        ranks = {"lexical": lexical_rank(documents, query["text"])}
        if vectors is not None:
            ranks["vector"] = vector_rank(documents, vectors, query_id)
            ranks["hybrid"] = fuse(ranks["lexical"], ranks["vector"])
        # Required evidence is used ONLY below, for evaluation after selection.
        for method, ranking in ranks.items():
            for suffix, graph, hops, seed_count in (
                ("", raw, 0, plan["candidateCount"]),
                ("+seeds-only", raw, 0, plan["seedCount"]),
                ("+raw-links", raw, plan["graphHops"], plan["seedCount"]),
                ("+knowledge-links", linked, plan["graphHops"], plan["seedCount"]),
            ):
                context, skipped = neighborhood(documents, ranking, graph, budget=budget,
                                                seeds=seed_count, hops=hops)
                selected = {doc["id"] for doc in context}
                missing = sorted(set(query["requiredSources"]) - selected)
                boundary = sorted({neighbor for key in selected for neighbor in linked[key]} - selected)
                required = len(query["requiredSources"])
                rows.append({
                    "query": query_id, "method": method + suffix,
                    "seeds": ranking[:seed_count], "context": context,
                    "selected_bytes": context_size(context), "budget_bytes": budget,
                    "skipped_for_budget": skipped, "known_link_boundary": boundary,
                    "oracle_required": query["requiredSources"], "oracle_missing": missing,
                    "oracle_recall": (required - len(missing)) / required if required else None,
                    "oracle_complete": not missing if required else None,
                    "negative_probe": query["negative"], "semantic_quality": "not-evaluated",
                })
    summary = {}
    for method in sorted({row["method"] for row in rows}):
        scored = [row for row in rows if row["method"] == method and not row["negative_probe"]]
        summary[method] = {
            "macro_required_recall": sum(row["oracle_recall"] for row in scored) / len(scored),
            "complete_neighborhood_fraction": sum(row["oracle_complete"] for row in scored) / len(scored),
        }
    return {"documents": len(documents), "corpus_bytes": context_size(list(documents.values())),
            "context_budget_bytes": budget, "seed_count": plan["seedCount"], "candidate_count": plan["candidateCount"],
            "graph_hops": plan["graphHops"], "benchmark_version": "budget-matched-v2",
            "context_fingerprint": hashlib.sha256(json.dumps({
                "documents": documents, "links": {key: sorted(value) for key, value in linked.items()},
            }, sort_keys=True).encode()).hexdigest(),
            "embedding_model": cache["model"] if cache else None,
            "summary": summary, "rows": rows,
            "warning": "Oracle recall is evaluator-only, not a runtime completeness guarantee or semantic accuracy score."}
