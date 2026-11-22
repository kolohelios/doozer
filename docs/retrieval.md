# Retrieval beyond the evidence-context budget

## Hypothesis and setup

Vectors can find related knowledge despite vocabulary differences, but a short
correction or distant exception may need explicit relationship traversal. Measure
material evidence coverage separately from generation quality before removing
the workbench's small-corpus preservation envelope.

`experiments/retrieval/` holds a CUE plan, deterministic distractor templates,
supplied knowledge links, and captured observations. The snapshot combines all
33 source artifacts in the five seed scenarios with 1,024 archive memos. It is a
static snapshot, not a streaming simulation: there are no future/pending sources
relative to a checkpoint. The distractors are synthetic adjacent-topic workshop
memos, not private conversations. The resulting 1,057 documents occupy 838,151
serialized bytes—about 327 times the default **2,560-byte evidence budget**.
This measures a bounded retrieval context, not a particular model's maximum
context window. Byte counts are not token counts; downstream callers still need
to reserve space for instructions, current state, and output.

The embedding adapter uses OpenRouter's Embeddings API with
`openai/text-embedding-3-small` and 512 dimensions. It embeds **source text only**,
not expected source IDs, query labels, scope annotations, graph links, or outcome
rubrics. Queries are embedded in the same space. A local exact cosine scan is
enough for this experiment; no vector database, broker, or ANN index is needed.
Long-source chunking and context-enriched/thread-aware embeddings remain future
comparisons; this first adapter rejects individual texts over 4,096 UTF-8 bytes.

## What is compared

There are six positive queries with provisional required source sets, plus an
unknown-payment question that must not be scored as vacuously complete. The
retriever never sees required source sets. Evaluation joins them after selection.
These are familiar seed-fixture queries, **not a held-out benchmark**.

Three ranking methods:

- **Lexical:** a small BM25 baseline with simple suffix normalization.
- **Vector:** normalized cosine similarity over real embeddings.
- **Hybrid:** equal-weight reciprocal rank fusion, constant 60, over the first
  100 results from each method. No weights were tuned to the outcome labels.

Each has four arms, all with the same serialized evidence budget:

1. **Plain:** greedily pack whole source records from up to 100 ranked candidates.
2. **Seeds only:** pack only the first four, as an explicit top-k control.
3. **Raw links:** take four seeds and expand up to three hops through source
   `replyTo` and `derivedFrom` links.
4. **Knowledge links:** also traverse the supplied, source-scoped EDD relations.

Seeds are bundled with their breadth-first neighborhoods before the next seed.
Oversized records are skipped, never truncated mid-source. Returned source
records retain event times, reply targets, derivation references, anchors, and kind; this
metadata counts against the same context budget. Each seed gets its
own traversal depth limit. The graph is traversed bidirectionally for discovery;
that does **not** make support, authority, or derivation symmetric.

The knowledge links are authored inputs standing in for relations maintained by
a future reasoning pipeline. Their endpoints are validated, but this experiment
does not discover them or establish that they would exist in a fresh system.
The raw-link ablation makes that assumption visible. There are no automatic
same-scenario links that hand the retriever an entire answer set.

We retained seeds-only controls and added budget-filling unlinked baselines so
link expansion is not merely compared against an artificially small context.
Packing order and candidate limits are experiment parameters, not an optimal
context-selection algorithm. More bytes need not monotonically improve results
with greedy whole-document packing and many near-duplicate distractors.

## Run it

```sh
# Offline lexical arms, no credentials or network even if a token is present.
nix develop --command just retrieval runs/retrieval-lexical.json

# Explicit paid construction: choose a new cache and report path.
direnv exec . python -m scripts.retrieval_probe --embed \
  --embedding-model openai/text-embedding-3-small \
  --budget-usd 0.02 --max-calls 40 \
  --cache runs/retrieval-vectors.json --output runs/retrieval-live.json

# Reuse the same index offline with another evidence budget. No new model calls.
nix develop --command python -m scripts.retrieval_probe \
  --cache runs/retrieval-vectors.json --context-bytes 512 \
  --output runs/retrieval-512.json
```

`--noise` changes corpus size; changing it requires a matching embedding cache.
Caches bind to model, dimensions, document identities/text/anchors, and query
texts. Changing expected labels or retrieval budgets does not require new
embeddings. Temporal/relationship metadata is reloaded and included in a separate context
fingerprint; changing relationships does not require rebuying unchanged text
vectors. Missing vectors, invalid dimensions, nonfinite/zero vectors, stale
inputs, duplicate batch indices, and incomplete caches are rejected. Caches and
reports live under ignored `runs/`; they must use distinct paths and paid caches
are never overwritten. A failed construction leaves an explicitly incomplete
cache and trace for inspection, with no automatic resume or retry.

The initial adapter is deliberately restricted to this embedding model. Other
models may need different dimensions, input types, or limits; add and test an
adapter rather than assuming chat and embedding models are interchangeable.

Live requests allow only the OpenAI provider, disallow fallback and non-transient
data collection, use a $0.03/M prompt-token price ceiling, and have byte caps and
30-second network timeouts. There is an upfront call-count check and conservative
per-batch budget reservation. Reported cost is used when available; otherwise
accounting explicitly uses observed input tokens times the price ceiling, not
zero. BYOK/unknown usage stops the run. These are **not provider-enforced total
spending guarantees**; use a limited-credit key. A timeout can still be billed.
No secret is written to the index, report, or trace. Only synthetic text is sent.

References: [OpenRouter RAG guide](https://openrouter.ai/docs/cookbook/evaluate-and-optimize/rag),
[embedding SDK contract](https://openrouter.ai/docs/client-sdks/python/sdks/embeddings/README.md),
and [model endpoint metadata](https://openrouter.ai/api/v1/models/openai/text-embedding-3-small/endpoints).

## First observations — November 22, 2026 (UTC)

One index build made 34 requests, embedded 125,661 input tokens, and reported a
total cost of **$0.00251322**. Sum of network-call wall times was 19.845 seconds.
All subsequent benchmark/byte-budget runs reused that cache without network.
Compact captured metrics and representative misses are versioned in
[observations.cue](../experiments/retrieval/observations.cue).

At 2,560 bytes, using budget-filling unlinked baselines:

| Ranking | Unlinked recall / complete | Raw-link recall / complete | Supplied-knowledge-link recall / complete |
| --- | --- | --- | --- |
| Lexical | 27.8% / 0 of 6 | 45.8% / 2 of 6 | 66.7% / 4 of 6 |
| Vector | 65.3% / 1 of 6 | 79.2% / 3 of 6 | 100% / 6 of 6 |
| Equal-weight hybrid | 36.1% / 0 of 6 | 45.8% / 2 of 6 | 66.7% / 4 of 6 |

Recall is the unweighted mean of each positive query's required-source recall.
“Complete” means every **enumerated required source** was present—not every
relevant fact in the corpus. The negative query is excluded from those averages.
No precision/relevance labels were collected for other candidates.

Important failures and caveats:

- Vector-only missed the contextual `No.` in automatic-retry guidance, even with
  extra ranked candidates filling the budget. Explicit reply/knowledge traversal
  recovered it. Textual similarity alone did not preserve a material correction.
- Hybrid fusion let repetitive archive memos dominate the human-approval and
  reception queries. It was worse than vector-only; combining scores is not an
  automatic improvement. Near-duplicate-heavy templates limit generalization.
- At 512 bytes, vector plus supplied links fell to 61.1% recall and only 1/6 complete
  sets. At 1,024 bytes it reached 95.8% recall and 5/6 complete sets, still missing
  the permission-change correction for the human-approval query. It reached 6/6 at 2,560 and 4,096 bytes.
- The hybrid human-approval failure had an **empty known-link boundary** while
  missing every required policy source. No discovered dangling edge is not proof
  that retrieval found the relevant neighborhood.
- At 1,024 bytes, some vector/link contexts contained all enumerated required
  sources but still omitted other known adjacent sources. Oracle rubric coverage
  and graph-boundary coverage are distinct, neither a global completeness proof.

Reports contain selected source records, budget skips, known uninspected linked
sources, and evaluator-only missing-source lists. They deliberately do not emit a
runtime “safe to rewrite” flag. The unknown-payment query may retrieve related
retry evidence; that must not become an invented payment answer.

## What this establishes—and does not

This supports vector retrieval as a useful candidate-discovery layer and shows
why relationship expansion deserves a separate role. It does not establish
semantic equivalence, calibrated retrieval confidence, automatic relation
construction, safe compaction, or the PRD's success. No downstream answer or
knowledge patch was generated or scored in this experiment. CI's vectors are
controlled test values for mechanics, not substitute semantic embeddings.

The existing workbench still retains its full active-claim preservation envelope.
The [paired understanding experiment](understanding.md) now defines fresh variants
and compares the resulting understanding under fixed role assignments, including
links proposed without the expected graph. It does not enable canonical rewrites.
Next, test held-out wording and genuinely distinct distractors, compare thread-
aware embeddings/diversity/reranking, and feed bounded contexts into the same
reasoning-role comparison. Test missed evidence and stale-neighborhood revisions
before permitting bounded-context retirements. Do not remove preservation checks
or add pgvector/JetStream merely because this synthetic retrieval result is good.
