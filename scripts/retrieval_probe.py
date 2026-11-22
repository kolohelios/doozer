"""Offline retrieval benchmark; opt-in OpenRouter embedding index construction."""

import argparse
import json
import os
from pathlib import Path
import subprocess
import tempfile
import time

from scripts.jev_probe import is_number
from scripts.retrieval import benchmark, embedding_items, fingerprint, load_snapshot, unit
from scripts.workbench_models import transport


ENDPOINT = "https://openrouter.ai/api/v1/embeddings"


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(mode="w", dir=path.parent, delete=False) as stream:
        temporary = Path(stream.name)
        json.dump(value, stream, allow_nan=False)
    temporary.replace(path)


def embed(documents, plan, model, *, budget, max_calls, cache_path, sender=transport):
    if not is_number(budget) or budget <= 0 or type(max_calls) is not int or not 1 <= max_calls <= 260:
        raise ValueError("invalid embedding budget or call limit")
    if model != "openai/text-embedding-3-small":
        raise ValueError("this initial adapter supports text-embedding-3-small only")
    token = os.environ.get("OPENROUTER_API_KEY", "").strip()
    if not token:
        raise ValueError("missing OpenRouter token")
    dimensions = plan["embeddingDimensions"]
    rate = float(plan["maxPromptPricePerMillion"]) / 1_000_000
    items = embedding_items(documents, plan["queries"])
    cache = {"version": 1, "complete": False, "model": model, "dimensions": dimensions,
             "fingerprint": fingerprint(documents, plan["queries"], model, dimensions),
             "vectors": {}, "trace": []}
    if Path(cache_path).exists():
        raise ValueError("cache already exists; do not overwrite a paid run")
    batches = [items[start:start + plan["batchSize"]] for start in range(0, len(items), plan["batchSize"])]
    if len(batches) > max_calls:
        raise ValueError("index requires more calls than allowed; no requests sent")
    charged_upper_bound = 0.0
    write_json(cache_path, cache)
    for batch in batches:
        payload = {
            "model": model, "input": [text for _, text in batch],
            "encoding_format": "float", "dimensions": dimensions,
            "provider": {"only": ["openai"], "allow_fallbacks": False, "data_collection": "deny",
                         "max_price": {"prompt": plan["maxPromptPricePerMillion"], "completion": "0"}},
        }
        encoded = json.dumps(payload).encode()
        if len(encoded) > plan["maxRequestBytes"] or any(len(text.encode()) > 4096 for _, text in batch):
            raise ValueError("embedding input byte limit exceeded")
        # Reservation is conservative local accounting, not a provider-enforced cap.
        reservation = (len(encoded) + 4096) * rate
        if charged_upper_bound + reservation > budget:
            raise ValueError("embedding budget cannot reserve the next batch")
        record = {"batch": len(cache["trace"]), "inputs": len(batch), "status": "submitted",
                  "reserved_usd": reservation}
        cache["trace"].append(record)
        write_json(cache_path, cache)
        started = time.monotonic()
        try:
            response = sender(ENDPOINT, payload, token)
            record["latency_seconds"] = round(time.monotonic() - started, 3)
            if not isinstance(response, dict) or response.get("model") not in (model, model.split("/", 1)[1]):
                raise ValueError("unexpected embedding model")
            usage = response.get("usage", {})
            count = usage.get("prompt_tokens", usage.get("total_tokens"))
            if type(count) is not int or count < 0 or usage.get("is_byok"):
                raise ValueError("cannot account for embedding usage")
            cost = usage.get("cost")
            if cost is not None and not is_number(cost):
                raise ValueError("invalid reported cost")
            charge = cost if cost is not None else count * rate
            charged_upper_bound += charge
            record.update({"input_tokens": count, "reported_cost_usd": cost,
                           "accounted_usd": charge, "cost_basis": "reported" if cost is not None else "tokens-times-price-ceiling"})
            if charged_upper_bound > budget:
                raise ValueError("embedding accounting exceeded budget; stop")
            data = response.get("data")
            if not isinstance(data, list) or len(data) != len(batch):
                raise ValueError("missing embedding vectors")
            vectors = {}
            for item in data:
                index = item.get("index") if isinstance(item, dict) else None
                if type(index) is not int or not 0 <= index < len(batch) or index in vectors:
                    raise ValueError("duplicate or invalid embedding index")
                vector = item.get("embedding")
                unit(vector, dimensions)
                vectors[index] = vector
            for index, (key, _) in enumerate(batch):
                cache["vectors"][key] = vectors[index]
            record["status"] = "validated"
        except (ValueError, TypeError, KeyError, OSError, OverflowError):
            record["status"] = "failed-or-unaccounted"
            write_json(cache_path, cache)
            raise ValueError("embedding request failed validation or transport; no retry, response suppressed") from None
        write_json(cache_path, cache)
    cache["complete"] = True
    write_json(cache_path, cache)
    return cache


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--embed", action="store_true", help="explicitly build a paid embedding cache, no retries")
    parser.add_argument("--embedding-model")
    parser.add_argument("--budget-usd", type=float)
    parser.add_argument("--max-calls", type=int, default=40)
    parser.add_argument("--noise", type=int)
    parser.add_argument("--context-bytes", type=int)
    parser.add_argument("--cache", help="new path with --embed; otherwise an existing cache to read offline")
    parser.add_argument("--output", required=True, help="new benchmark report path")
    args = parser.parse_args(argv)
    if Path(args.output).exists():
        parser.error("report already exists; choose a new run path")
    if args.cache and Path(args.cache).resolve() == Path(args.output).resolve():
        parser.error("cache and report paths must be different")
    try:
        if args.context_bytes is not None and not 128 <= args.context_bytes <= 16384:
            raise ValueError("invalid context budget; no requests sent")
        documents, raw, linked, plan = load_snapshot(args.noise)
        cache = None
        if args.embed:
            if not args.cache or not args.embedding_model:
                raise ValueError("explicit model and cache path are required")
            cache = embed(documents, plan, args.embedding_model, budget=args.budget_usd,
                          max_calls=args.max_calls, cache_path=args.cache)
        elif args.cache:
            cache = json.loads(Path(args.cache).read_text())
        report = benchmark(documents, raw, linked, plan, cache, budget=args.context_bytes)
        report["embedding_trace"] = cache["trace"] if cache else []
        write_json(args.output, report)
        print(json.dumps({"report": args.output, "documents": report["documents"],
                          "corpus_bytes": report["corpus_bytes"], "context_bytes": report["context_budget_bytes"],
                          "new_network_calls": len(cache["trace"]) if args.embed else 0,
                          "summary": report["summary"]}, indent=2))
        return 0
    except (ValueError, KeyError, TypeError, OSError, OverflowError, subprocess.CalledProcessError):
        print("Retrieval probe stopped: invalid configuration, snapshot, embeddings, budget, or transport. No automatic retry; inspect any incomplete cache.")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
