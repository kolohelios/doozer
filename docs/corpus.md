# Corpus and model-role experiments

## Hypothesis and limits

A small evolving corpus can reveal lossy reconciliation before we choose a
storage or transport stack. Success means preserving scoped meaning, exceptions,
provenance, uncertainty, historical discovery, and honest freshness—not matching
one preferred paragraph or shrinking node count.

The CUE files in `corpus/` contain **synthetic inputs and provisional expected
outcomes**, derived from EDD §3, §5, and §14. Review these expectations before using
them as a benchmark. They describe desired behavior, not measured engine results.
The [local retry-safety workbench](workbench.md) now exercises stage contracts,
reconciliation patches, and projections, with outcome rubrics attached for human
review. There is no automatic semantic grading harness yet. The separate
[opt-in Jev decision probe](jev.md) tests coarse routing labels only.

## Initial cases

| Scenario | Main probes |
| --- | --- |
| Retry safety | Six-round scope refinement; delayed reconciliation; replay; contextual No; ambiguous Stop; incident echo; generated handbook feedback |
| CNPG/RDS | Capability versus local evidence; workload/failure-model boundaries; older positive evidence arriving after a newer failure |
| Breaking changes | Strict-consumer exception; paraphrase compaction; incomplete test coverage; migration order; behavior versus schema |
| Code review | Policy versus practice; contested proposal; model assistance versus human approval; repo/risk/effective-date boundaries |
| Visitor access | Nonengineering procedure; date-bounded location exception; correction that preserves the underlying obligation |

There are five scenarios and nineteen checkpoints. This is a seed corpus, not
complete EDD coverage. Crash recovery, transactional outbox, stale concurrent
patches, durable-before-ack, edited projection reingestion, actual merge/split
reference traversal, and event-order convergence need executable engine tests.
One out-of-order schedule is not evidence of convergence across permutations.

## Data contract

- `sources` maps stable fixture-local identities to text, anchors, event time,
  kind, and scope. These are not a proposed database schema or ontology.
- `replyTo` preserves conversational context, not an assertion of corroboration.
  `derivedFrom` records projection lineage; generated material is not independent
  evidence. All anchors use `fixture://` and contain no company data.
- Each ordered step distinguishes `receive` from `reconcile`. Repeating a source
  identity means redelivery, not an independent source. Arrival order need not
  match `saidAt`; ingestion and validity times must not be inferred from it.
- `expect.must` contains scoped meaning-level obligations with supporting source
  IDs. `mustNot` records catastrophic or material conclusions and why they fail.
  A checkpoint's rubric applies to that snapshot, not forever after supersession.
- `pending` is the exact received-but-unprocessed set. Query rubrics can describe
  supported, insufficient, conflicted, pending, or absent answers. These labels
  are test expectations for answers, not canonical epistemic-state columns.
- `equivalentTo` requires material semantic equivalence with an earlier snapshot,
  not byte identity or identical internal graph shape. Provenance may gain a
  dependent retelling without gaining an independent evidentiary origin.

CUE enforces structure, nonempty outcomes, synthetic markers, and reference
membership. Small Python standard-library tests enforce schedule integrity,
lineage acyclicity, unique identities, and evidence availability. Mutation tests
prove malformed fixtures are rejected. **None of these checks prove that a model
preserves meaning.**

```sh
nix develop --command just corpus-check
nix develop --command just corpus-export   # JSON, including the answer rubrics
nix develop --command just validate        # same offline gate as CI
```

Future runners must send only received source inputs and allowed processed
context to the system under test—not `expect`, tags, scenario titles, future
sources, or the full exported corpus. Keep expected outcomes evaluator-side.
Score required and forbidden outcomes individually with evidence citations;
compare against an append-only summary baseline. Do not trust a model's own
claim that it passed. Human-calibrate any semantic judge and preserve failures
rather than tuning the rubric to fit an attractive answer.

## Model roles: execution hypotheses, not a mandatory chain

OpenRouter is the integration boundary. Choose explicit model IDs per role and
run; compare assignments rather than setting one global model. The first
[bounded Jev experiment](jev.md) uses `typesafe/jev-1.14` through OpenRouter's
Decisions API; it is separate from `typesafe/jev-router`.

| Role | Input and responsibility | Boundary |
| --- | --- | --- |
| Triage/router | Source context and processing budget; choose relevant analysis paths or a justified no-op | Cannot discard durable evidence or dismiss a tiny intervention merely because it is short |
| Analysis | Recover assertions, referents, temporal/conditional scope, source spans, and ambiguity | Structured interpretations, not canonical facts or inferred agreement |
| Vectorization/retrieval | Embed text for candidate discovery; combine with lexical and historical-reference retrieval | Similarity proposes neighborhoods; it never proves equivalence or contradiction |
| Knowledge reasoning | Inspect source-backed neighborhood and propose a minimal patch, no-op, or unresolved interpretation | Preserve exceptions, counterevidence, lineage, and history; no invented decisions |
| Patch evaluator | Compare a proposed transformation with its cited evidence, preservation rules, and current revision | Structured accept/reject/retry recommendation with concise evidence-linked reasons; not unchecked write authority |
| Commit gate (code, not a model) | Validate CUE-shaped patch data, reference/scope rules, idempotency, and revision preconditions | Atomic commit or explicit rejection/retry; a stale patch must not overwrite newer meaning |
| Discovery/projection | Explain the processed snapshot with citations, applicability, and lag; emit bounded handbook/directive views | Must not over-answer, hide backlog, or turn derived output into independent support |

These roles may share a model, run in parallel where safe, or be bypassed when
unnecessary. Start with one proposer and deterministic validation; add a separate
model evaluator only if paired corpus runs show a benefit worth its cost. A
stronger judge can share the proposer's blind spots. Compare independent role
assignments and include intentional failures and no-op cases. Decision-making
here means bounded engine actions—not deciding a team's policy or architecture.

Record inspectable **decision records**, not hidden reasoning transcripts:
source identities/spans, role, explicit model ID, prompt/schema revision,
neighborhood revision, proposed operations, concise rationale and evidence,
validation results, disposition, retries, latency, usage, and cost. Never record
credentials. Untrusted source text must remain data, not model instructions.
Live tests must be opt-in, cost-bounded, and limited to authorized inputs;
offline CI uses no API token. Embeddings require an embedding-capable endpoint,
not an assumption that every chat model can vectorize.

## Storage and transport: delay the commitment

The local workbench uses files and deterministic recorded responses by default,
not a broker. The next durable slice can use an embedded transactional store or
PostgreSQL for inbox, revisioned changes, and outbox. PostgreSQL is attractive
when testing transactions and concurrent workers; it is not yet a dependency.

Add NATS/JetStream only when experiments demonstrate a need for durable fan-out,
independent consumers, or replay outside database dispatch. It does not replace
canonical evidence/history or solve semantic reconciliation. Keep the EDD's
at-least-once, idempotency, stale-revision, and eventual-freshness contracts
independent of that choice. No deployment scaffolding is needed for this corpus.
