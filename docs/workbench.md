# Retry-safety reconciliation workbench

## Hypothesis

Separate routing, analysis, retrieval, and reasoning behind explicit contracts;
then inspect whether resulting knowledge preserves the corpus outcomes. A model
returning valid JSON is not evidence of semantic preservation. Jev is an optional routing candidate;
it does not perform all roles or authorize commits. Live runs default to a
network-free rules router; opt into Jev with `--router jev`.

This is a single-process, synthetic-data experiment. It has no database, broker,
embedding model, multiuser service, external publication, or durable-ingest ACK.
Canonical effects are confined to the selected local run artifact.

## Pipeline and contracts

`experiments/workbench/contracts.cue` defines the boundaries:

| Stage | Responsibility | Output |
| --- | --- | --- |
| Receipt (code) | Stable source identity; preserve text, scope, event time, anchors, and lineage | Local received sources, distinct from processed sources |
| Routing (rules or optional Jev) | Analyze or retain ambiguity; exact processed-identity replay is skipped by code | `#Route` |
| Analysis (explicit chat model) | Source-linked assertions, exact quoted spans, scoped attribution | `#Analysis` |
| Retrieval (code baseline) | Rank active claims by lexical overlap and explicit evidence links | `#Retrieval` |
| Knowledge reasoning (explicit chat model) | Minimal add/retire patch, rationale, revision precondition, per-source accounting | `#Patch` |
| Commit gate (code) | Validate contracts and references against a copy; publish all effects or none | Versioned claims, source processing positions, history, redirects, journal |
| Discovery/projection (code) | Search with source anchors and pending inputs; render the same claims into handbook and agent context | `#Projection` and discovery snapshots |
| Review (evaluator-side) | Join actual views to corpus required/forbidden outcomes after model stages finish | Structural checks and an explicitly pending semantic judgment |

Models receive only eligible source fields, processing identities, current
claims, and preceding stage outputs. They do not receive corpus rubrics,
scenario titles/tags, future sources, or checkpoint IDs. Step IDs are used only
by recorded playback and local trace records. Source text stays user data, not
system instructions. Live JSON is validated against CUE, never executed as CUE.

Retrieval is not adjudication. For this tiny corpus every active claim also
travels in a preservation envelope, so retrieval cannot hide an inconvenient
counterexample. This does not scale indefinitely; compare embeddings against
the lexical baseline before adding another model or index. Projection is
currently deterministic: both outputs reuse the same scoped claim text and
citations. Agent context is not an independently invented mandate or an edited
repository `AGENTS.md`.

## Run and inspect

```sh
# No token, network, or paid models. Use a new output path for every run.
nix develop --command just workbench runs/retry-recorded.json

# Search or follow a retired reference without model calls.
nix develop --command python -m scripts.workbench \
  --inspect runs/retry-recorded.json --query notifications --reference retry-guidance

# Separate role assignments; same model in both roles is allowed for comparison.
# Start with the first checkpoint (three calls at most).
direnv exec . python -m scripts.workbench --live --router jev \
  --analysis-model openai/gpt-4.1-mini \
  --reasoning-model deepseek/deepseek-v3.2 \
  --budget-usd 0.10 --max-calls 3 \
  --through expressed-guidance --output runs/retry-live-first.json
```

Omit `--through` for all eight checkpoints and allow up to 18 calls. To test
through the manual mitigation, use `--through scoped-mitigation --max-calls 12`.
Explicit model IDs are per run, not global environment configuration. The
model suggestions above are trial assignments, not selected production defaults.
Use `--router rules` (the default for live runs) to omit routing API calls while
keeping the analysis/reasoning assignments unchanged. At the current coarse
granularity, all fresh sources still go through analysis: Jev supplies a routing
signal but has not demonstrated saved downstream calls or better final knowledge.
It may not earn its extra cost here. Compare routers on the same input sequence
before adding more routing decisions or making Jev a production dependency.

A provider lacking JSON response support, privacy eligibility, or the configured
price tier will fail rather than falling back silently.

The artifact contains `state`, `snapshots`, `trace`, and `evaluation`. Read the
handbook/agent views and compare each `evaluation.required` and `.forbidden` item
with `.actual`. `semantic_judgment` deliberately remains `pending-human-review`.
Inspect `state.journal` for before-views, accepted analyses, patches, accounting,
and rationale. Retired IDs resolve through `state.redirects`; original claims
remain in `state.history`. Discovery snapshots include received-but-unprocessed
source IDs and distinguish no lexical match from a universal claim of absence.

`runs/` is ignored and contains only local experimental artifacts. The output
file must not already exist. Snapshots are atomically replaced after receipt and
successful steps, and a failed model stage preserves the last valid state plus
available trace. This is not fsync-backed crash durability, a resume protocol,
or a claim that ingestion/processing is exactly-once.

## Mechanical safeguards and limitations

The gate rejects stale revisions, reused claim IDs, fabricated quote spans,
unavailable/pending citations, projection-as-corroboration, orphaning retirements,
and replacements that drop old source discovery paths. It retains all old
claims unless explicitly retired with a surviving replacement. New sources must
have per-source accounting: either surviving claims cite them, or an explicit
dependent no-op cites prior processed evidence supporting surviving claims.
A router's no-op cannot silently mark a new source processed; new evidence still
passes through analysis/reasoning. Unchanged source redelivery skips model calls.

These safeguards do **not** prove that quoted evidence entails a claim, that a
scope is correctly inferred, or that a declared dependent no-op is semantically
justified. A patch can remain structurally valid and materially poor. Keep the
outcome rubric separate from the engine, review real failures, and do not report
structural checks as a model-quality score.

Live calls are opt-in and have no automatic retries. Request/response byte caps,
30-second network timeouts, call limits, explicit token output limits, provider
privacy preferences, and routing price filters bound the experiment. The plan
filters chat rates to $1/M prompt and $4/M completion tokens, and Jev to $0.05/M
prompt and zero completion price. A conservative local cost reservation is made
before each call; unknown cost, BYOK billing, or budget exhaustion stops further
calls. **This is not a provider-enforced total-spend guarantee.** Use a dedicated
OpenRouter key credit limit for that. Timeouts or failed requests can be billed.
Credentials, raw provider bodies, and hidden reasoning transcripts are not logged.

## Initial live observations — November 22, 2026 (UTC)

Both runs used Jev 1.14 for routing, GPT-4.1 Mini for analysis, and DeepSeek V3.2
for knowledge reasoning. Each stopped after the fifth checkpoint (manual
mitigation): four processing batches, twelve network calls. The received-only
checkpoint used no models. They are unreplicated smoke tests, not benchmarks.

| Prompt/contract | Reported total cost | Sum of network-call wall times | Observation |
| --- | --- | --- | --- |
| `retry-slice-v1` | $0.00566076 | 98.744 s | Analysis extracted the manual-replay mitigation, but reasoning omitted it and incorrectly called the incoming sources already processed. The initial gate accepted the patch. |
| `retry-slice-v2` | $0.005672781 | 96.499 s | Mandatory per-source accounting retained all six received source identities, including the manual mitigation. The model mostly appended separately attributed claims rather than reconciling the broad guidance into a compact qualified live explanation. |

Compact captured observations, including the actual failed v1 patch, are
versioned in [observations.cue](../experiments/workbench/observations.cue).
The v1 failure motivated the v2 accounting contract and regression tests. We did
not change the expected corpus outcomes to make the model pass. The v2 run
improved traceable coverage but **does not establish the desired semantic
reconciliation**: broad expressed guidance still appears alongside its caveats
instead of being explicitly retired/qualified in the live representation. This
is an open model/prompt/IR experiment, not a solved compiler pass. The two local
artifacts are `runs/retry-live-01.json` and `runs/retry-live-02.json`; no later
contextual-correction or echo/projection live checkpoints were tested in these runs.

Offline playback in `recorded.cue` is hand-authored, not captured model output.
It demonstrates all eight checkpoints, five material revisions, replay stability,
source-backed scoped projections, and recoverable historical references. Tests
also exercise the live transport path with mocked separate models, invalid
patches, leakage checks, and budget failures; CI makes no network calls.

Next: review the live views against the rubric, compare reasoning-role
assignments on the same checkpoint sequence, and evaluate qualification/retirement
rather than merely counting cited sources. Add broader semantic evaluation and
held-out cases before attaching this loop to a real durable inbox or outbox.
