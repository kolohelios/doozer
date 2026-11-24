# Corpus and model-role experiments

## Hypothesis and limits

A small evolving corpus can reveal lossy reconciliation before we choose a
storage or transport stack. Success means preserving scoped meaning, exceptions,
provenance, uncertainty, historical discovery, and honest freshness—not matching
one preferred paragraph or shrinking node count.

The baseline CUE files at `corpus/*.cue` contain **synthetic inputs and provisional expected
outcomes**, derived from EDD §3, §5, and §14. Review these expectations before using
them as a benchmark. They describe desired behavior, not measured engine results.
The [local retry-safety workbench](workbench.md) now exercises stage contracts,
reconciliation patches, and projections, with outcome rubrics attached for human
review. There is no automatic semantic grading harness yet. The separate
[opt-in Jev decision probe](jev.md) tests coarse routing labels only.

## Public standards pilot: documents and the discussion behind them

Public standards give us a complementary **development** corpus: real scope
changes, abandoned proposals, objections, clarifications, and released guidance.
They do not replace the synthetic controls or prove general semantic correctness.
The first [external inventory](../corpus/standards/inventory.cue) covers **RFC 7807 → all
eight `draft-ietf-httpapi-rfc7807bis` revisions (00–07) → RFC 9457**. Ten official
text representations were inspected and their exact byte counts/SHA-256 digests
recorded. Future retrieval must match those bytes before use; a changed or
unavailable representation must be reported, not silently rebaselined.
The initial inventory contains metadata only; the first scoped excerpt capture
and offline cutoff preparation are now available below. Neither is a completed
model evaluation.
Its separate `corpus/standards/` package does not relax the closed synthetic
scenario schema. Inspect it with `nix develop --command cue export corpus/standards/inventory.cue`.

Three discussion arcs have public issue/PR locators:

- Relative type URIs: issues 14/64 and PR 20.
- Invalid-object processing: issue 19 and PR 23.
- A proposed Problem HTTP field: issues 35/67 and PR 39.

These are in the [working repository](https://github.com/ietf-wg-httpapi/rfc7807bis)
and have a related [working-group mailing archive](https://mailarchive.ietf.org/arch/browse/httpapi/).
The HTTP-field section appears in drafts 03/04, but not in draft 05 or RFC 9457.
That is an opportunity to test retaining a historical proposal without presenting
it as released guidance. Its omission is **not** proof the field is universally
forbidden, nor does a nearby comment establish why it was removed. The relative
URI arc can test narrower guidance without inventing an absolute prohibition.
Concrete meaning references remain to be reviewed against exact passages.

Before replay, curate one bounded arc with explicit coverage and gaps, including
original comments, replies, feedback, proposal/decision links, and relevant draft
sections—not just a final summary. Preserve proposals and unresolved objections as such. An issue closed,
a PR submitted, or a comment repeated does not establish adoption or consensus.
A released RFC is later evidence with a particular normative scope, **not a truth
oracle**. Draft guidance and still-published guidance may coexist under different
release scopes; document-level obsolescence does not negate every earlier claim.

Replay must freeze exact source versions at explicit cutoffs. In particular:

- A comment's current body may contain later edits: its creation date is not
  proof those bytes were visible then. Preserve capture/update times and exact
  comment/message IDs; mark unrecoverable historical versions unavailable.
- Do not expose later drafts, closure outcomes, final release prose, or evaluator
  interpretations to earlier snapshots. Month-only publication headers are not
  precise event times; Datatracker's record-update time is not publication time.
- Preserve differing statement/publication, reception, effective, and capture
  times. Do not change public dates to fit the synthetic 2026 fixture contract.
- Freeze reader questions and meaning references prospectively, record unknowns,
  and evaluate current guidance, history, qualifications, and useful access—not
  lexical agreement with the final RFC or an authored node count.

### Curated HTTP-field capture and offline cutoffs

The [capture](../corpus/standards/http-field/capture.json) indexes **63 source
records**: five document excerpt sets, all 52 comments and three bodies from
issues 35/67 and PR 39, one review, one inline comment, and the removal commit
message. Exact UTF-8 byte ranges and body/excerpt hashes identify unmodified
technical text. All records remain in the audit denominator, including explicit
nontechnical/privacy omissions and unavailable historical versions. Mailing-list,
HTTP-WG, and issue #56 context is not captured; this is not a complete mailbox.

A scoped reuse review uses IETF Trust TLP 5.0 §3.c.iii for unmodified portions.
The repository contribution notice was checked at a pinned 2021 commit preceding
these contributions. [Separate terms, original notices, and attribution](../corpus/standards/http-field/NOTICE.md)
accompany the excerpts. Public account labels are retained for attribution/context,
not as verified identity or authority. Contact/signature material, a personal URI
example, nontechnical pings/social links, and an unrelated formatting suggestion
are omitted by explicit ranges/statuses, never rewritten as original text.
This does not approve reuse of other sources, model transmission, modified IETF
prose, or relicensing third-party text as MIT OR Apache-2.0.

```sh
nix develop --command python -m scripts.standards_replay \
  --output runs/http-field-prepared.json
```

The [CUE plan](../corpus/standards/http-field.cue) prepares seven dated contexts:
March/September 2022, three stages in January 2023, February 2023, and September
2023. Each contains only eligible excerpts, their own notices/attribution, reader
questions, and honest context gaps. Evaluator meanings and all 63 visibility
cells per checkpoint stay private. Never transmit the entire preparation report.
All proposed references remain **pending human meaning review**; there are zero
planned calls/budget, no live flag, no model/provider, and no semantic score.

Actual availability events matter: draft 05's header is January 26, but the
Datatracker event says January 27 at **02:05:42Z**. The **02:03** context therefore
still withholds it. Comment/issue current bodies are conservatively withheld until
the API's last-update time; earlier versions are unavailable, not reconstructed.
This remains conditional on upstream metadata, not authenticated edit history.
Review submission is not body-edit history; commit time is not push time. The
current review and removal message have no established historical version time
and do not enter earlier contexts merely from those clocks. Flat-thread membership
is not invented as a specific reply. Quoted/echoed positions and successive draft
versions are not independent corroboration.

Public text may already occur in model training: context isolation cannot prevent
parametric knowledge of later outcomes. This is a development corpus, not clean
held-out capability evidence. Complete previews are bounded at 256 KiB; later
ones exceed the existing live adapter's 128 KiB request limit. No truncation or
live adaptation occurs here. Context budgeting and actual maintenance-loop
integration must be reviewed before any separately authorized generation.

Original inspected inputs are retained locally at
`runs/standards-http-field-inputs/`, with their hashes in the capture; that cache
contains unminimized public snapshots and must not be published. The offline
curation recipe is `scripts/curate_http_field.py`, using explicit local inputs and
the recorded curation timestamp (not an inferred source receipt time). Current
upstream bodies may change; reproducing a capture must match the retained inputs,
not silently re-fetch or replace them. Next review the proposed meanings and wire
the source batches into the real workbench rather than add another judging layer.

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

The [bounded retrieval experiment](retrieval.md) adds deterministic adjacent-topic
noise and evaluates required-source coverage under fixed context budgets. Its
embedding inputs exclude these answer rubrics; retrieval coverage is not a score
for semantic reconciliation.

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
