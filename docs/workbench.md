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
counterexample. This does not scale indefinitely. The separate [bounded retrieval benchmark](retrieval.md)
now compares real embeddings and link expansion against the lexical baseline;
it does not yet replace this workbench's preservation envelope. Projection is
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

The next section returns to qualification/retirement and the end-to-end local
loop, rather than adding another judge. Broader semantic evaluation and held-out
cases are still required before attaching this loop to a real durable inbox or
outbox.

## Executable maintenance and recovery — offline

**Hypothesis:** scoped amendments and a many-to-one consolidation can reduce live
redundancy while preserving the authored notification exception, manual-only
mitigation, contextual automatic-retry correction, evidence, and historical
access. Compare reader views after every round, not just the final node count.
This addresses the local transformation/recovery portions of PRD §9 and EDD §13;
it does not complete the autonomous or durable-service requirements.

```sh
nix develop --command just retry-maintenance runs/retry-maintenance-NEW.json
```

This uses the existing eight-step retry fixture and recorded patch proposals,
then adds one **source-free maintenance pass** from
[`maintenance.cue`](../experiments/workbench/maintenance.cue). It does not invent
an incoming message merely to trigger consolidation. The two current retry
explanations are combined with their existing text and union of original
citations; both prior claim IDs retire to the combined explanation. The detached
Stop remains separately recoverable and does not become a global revocation.
Handbook and agent-context projections contain the same scoped assertions and
source anchors; neither is independent corroboration.

The append-only comparison receives the **same additions and accounting**, with
only retire operations removed. This is a controlled patch ablation, not an
independent model-generated summarization baseline. At manual mitigation there
is one active maintained claim versus four appended claims; after contextual
correction/echo there are three versus six. After the explicit consolidation
there are **two versus seven**, with the same seven immutable historical claim
payloads and the same original received/processed sources. Claim word totals,
active source IDs, projections, and six fixed lexical reader probes are recorded
for all nine rounds. These are structural diagnostics, not semantic accuracy or
a quality-adjusted compression score. Required/forbidden meanings remain
separate, with judgment explicitly pending human review.

### Local APIs and boundaries

- `maintain(state, patch, analysis, route)` applies an explicit source-free patch
  atomically in the isolated local state. Accounting must be empty; only already
  processed evidence is eligible. It cannot mark a pending source processed.
  Ingestion retains its existing nonempty, distinct-source batch requirement.
  A maintenance proposal with no operations makes no state, revision, or journal
  change. The coordinator chooses this mode; it is not a new model patch opcode.
- `historical_view(state, position)` reconstructs the knowledge/processing view
  after a journal prefix. **Positions are not semantic revisions:** a dependent
  no-op advances processing without changing the semantic revision. This does
  not reconstruct the full historical receipt timeline.
- `restore(state, {baseRevision, targetPosition, reason})` appends a compensating
  local recovery event. It restores that prefix's active claims, redirects, and
  processing positions, while retaining **all** received sources, immutable
  claim history, and the entire existing journal. Later received sources become
  pending again, visible to discovery. The current revision increases rather
  than resetting and accidentally making a stale patch current. This is whole
  prefix recovery, not selective semantic undo or source erasure.
- `replay(state, position, base_revision=...)` revalidates one exact prior patch
  against its original material preconditions. It may reactivate only identical
  historical claim payloads; ordinary proposals still cannot reuse claim IDs.
  Different content, changed neighborhoods, stale revisions, or restore events
  are rejected. Each replay is recorded with its origin position; sources are not
  fetched and models are not called. New schema/reference validation still runs.

The demonstration restores the pre-mitigation view, then replays the remaining
source patches and the maintenance pass. Active claims, redirects, processed
positions, immutable history, and rendered handbook text recover exactly; the
new revision and appended recovery/replay journal remain different, as intended.
Both projections disclose their processed/received source counts and explicitly
warn when received material remains unreconciled. Coverage can change on an echo
or projection receipt without changing the active knowledge or its revision.
Later-only claims remain inspectable in history during rollback rather than
being falsely redirected to an earlier conclusion. Legacy artifacts without the
new recovery metadata are rejected for recovery, not silently reconstructed or
rescored. Old inspection remains available.

Discovery now also searches the former wording and scopes of redirected claims.
For example, “implementation” can reach the current retry explanation through
its historical database-write claim, even though that word is absent from the
current text. Hits show `historical_matches` separately and return the **current**
claim, not obsolete guidance disguised as current. Reader probes are lexical
candidate lookup, not generated answers or a demonstration of general fuzzy
understanding. Results expose pending inputs, processed-source coverage, and the
boundary that no local match does not establish global absence.

**Critical limit:** the patches and consolidation are hand-authored playback,
not a model autonomously discovering a correct maintenance plan. A deliberate
counterexample retains every citation and passes the reference gate while
replacing the conclusion with “All retry paths are safe.” Its unchanged node
count and source coverage do not make it correct. Tests preserve this failure
rather than introducing a fixture-specific keyword oracle. The new loop makes
maintenance, discovery-path retention, and recovery executable; it does not
solve semantic validation. No paid calls, external knowledge publication,
durable ACKs, crash recovery, concurrency isolation, or new semantic approvals
are implied.

## One maintenance proposer checkpoint — offline protocol

The next question is whether a model can **choose** warranted maintenance, not
merely whether the engine can apply a known patch. The prospective protocol in
[`proposer.cue`](../experiments/workbench/proposer.cue) and
[`maintenance_proposer.py`](../scripts/maintenance_proposer.py) prepares one
checkpoint immediately before the authored consolidation. Its hypothesis is
that original evidence plus the current working view and exact patch interface
are sufficient to propose a useful consolidation, amendment, or justified no-op.
The fixture is reused synthetic development material, not independent held-out
gold. No proposal is generated by this offline command.

```sh
nix develop --command just maintenance-proposer runs/proposer-prepared-NEW.json
```

The prospective proposer receives only:

- Static instructions and the exact CUE `#MaintenancePatch` contract.
- The current revision and three active, untrusted working assertions.
- Processed original sources with their available scope, time, reply, and
  projection-lineage metadata.
- Reserved historical claim IDs and existing alias routes, so identity reuse
  and broken old references need not be guessed.

It receives **no authored consolidation patch, target ID/text, expected node
count, evaluation rubric, reader queries, old patch journal, or later sources**.
The context is built through an explicit allowlist, with canary tests for those
boundaries. `proposer_messages(prepared)` is the sole prospective model input.
**Do not transmit the complete manifest:** it deliberately retains private state,
source construction history, and evaluator rubrics for local inspection.

The response is one unmodified JSON `#MaintenancePatch`. Accounting is closed
empty because this is source-free maintenance. New revisions use fresh claim
IDs and add/retire operations; `operations=[]` is available without a forced
merge or target claim count. The adapter derives bookkeeping analysis from added
assertions, or current assertions when there are no additions. That is explicitly
not another model opinion, fact substitution, hidden repair, or semantic check.

A saved raw proposal can be inspected without generating or retrying it:

```sh
nix develop --command python -m scripts.maintenance_proposer \
  --prepared runs/proposer-prepared-NEW.json \
  --proposal runs/saved-patch.json --output runs/proposer-inspected-NEW.json
```

Inspection checks the manifest digest and current implementation/contract hashes,
then applies the proposal only to a **copied, isolated fixture state**. It records
raw input bytes, the parsed proposal when available, contract/precondition
rejection or application status, before/after reader probes and projections,
historical/current reference pairs, and the pending meaning-review checklist.
Malformed JSON, duplicate members, non-finite numbers, excessive nesting, stale
revisions, fabricated quotes, lost source paths, and reused identities are not
repaired. No-op application remains pending semantic review; its recovery test
is correctly marked unexercised because nothing changed.

For a nonempty applied patch, rollback and exact replay use **that actual saved
proposal**, not the authored target. Recovery verifies the material view while
retaining the proposal's claim history and newer journal revisions. The input
file and prepared state are never overwritten. Captures are bounded at 1 MiB;
an oversized input is rejected with an explicitly incomplete prefix, and the
unchanged original file must remain available. Prompt and nesting limits are
also explicit. These are local response bounds, not a provider billing policy.

All mechanically applicable proposals—including different layouts/IDs and a
citation-complete false universal safety claim—remain **pending human meaning
review**. Correctness is not target-patch equality, valid JSON, successful
rollback, or a smaller claim count. The evaluator must inspect the notification
exception, manual/automatic distinction, contextual No, detached ambiguity,
source dependence, useful discovery paths, and whether change/no-op was justified.
This does not install a per-change human approval queue in the future product;
it is review of this experimental evaluation result.

The artifact has **zero planned calls, zero budget, model/provider unset, no live
option, and no execution authorization**. A later live experiment requires an
explicit model/provider, inspected exact request, call/cost/transport bounds,
lossless accounting/response capture, and separate authorization. Prior spending
approvals do not carry forward. No paid generation or semantic-quality result is
claimed by preparing this protocol or exercising its inspector with authored
unit-test inputs.

## Bounded one-call adapter

`just maintenance-call runs/proposer-call-prepared-NEW.json` now prepares a
separate, proposed live envelope around exactly the messages above. Preparation
remains offline and credential-free. It neither submits the request nor grants
execution permission. The proposal is:

- **One** `openai/gpt-4.1` call through **OpenAI**, temperature 0, JSON-object
  response, at most 8,000 output tokens.
- **$0.15 local ceiling**, price filters of $3/M input and $9/M output tokens;
  the byte-based reservation is printed before execution. This is not a provider
  or account-wide cap or a guarantee of the eventual bill. Reported overruns
  remain known charges and stop, not permission to submit again.
- Existing absolute-deadline transport explicitly selected: **120 seconds**
  including worker startup/connect/read, 128 KiB request and 1 MiB response
  bounds. Bounded best-effort cleanup is not a real-time OS guarantee; local
  termination does not cancel provider work or establish billing.
- No retries, fallback, resampling, repair, second opinion, or automatic use of
  unused budget. Unknown billing retains its reservation and stops.

The live envelope freezes the offline checkpoint, exact OpenRouter operation,
price/token/call/byte/deadline bounds, implementation/toolchain hashes, and a
historical public endpoint observation. That cached observation is **not** a
fresh availability check; preparation makes no metadata or account requests.
The API request contains only the blind proposer messages, never the private
checkpoint/report or evaluator metadata. A returned model must match the pinned
name or a dated version—not a different family member such as GPT-4.1 Mini.

Execution is a separate explicit command **only after the operator authorizes
this exact one-call scope and frozen hash**:

```sh
# NOT an instruction or authorization to run this while reviewing the PR.
# Load the key through the operator's normal secret/environment mechanism.
nix develop --command python -m scripts.maintenance_call \
  --live --prepared runs/proposer-call-prepared-NEW.json \
  --protocol-sha256 EXACT_APPROVED_HASH --output runs/proposer-call-live-NEW.json
```

A local exclusive receipt under
`runs/maintenance-proposer-attempts/<protocol-hash>.json` claims the attempt before
submission. Completed/stopped reports cannot resume; a fresh output path or a
fresh copy of the same prepared artifact cannot silently reuse that hash in the
same workspace. Missing credentials do not consume a receipt. Once claimed, even
a pre-submission interruption does not automatically release it. The receipt is
not proof of billing, durable crash recovery, distributed exactly-once execution,
or a global limit across copied workspaces. Do not delete it to retry under the
old approval; a further attempt needs explicit new authorization and protocol.

The ledger checkpoints the available complete native response object, token/cost
accounting, and transport diagnostics **before inspection**. Captured HTTP-error
bodies retain credential-redacted bytes with status/truncation metadata. No
response is claimed recoverable if a killed worker never captured it. This does
not promise byte-identical HTTP formatting for successful parsed JSON responses;
the native model content string and response fields remain available unchanged
apart from credential redaction.

There is exactly one inspection of the actual returned model text. Refusal,
length termination, wrong model, multiple choices, malformed patch, failed
application, or inspector failure are retained without replacement. Successful
local application/no-op and recovery still leave semantic review pending and
canonical acceptance false. The inspector's own `network_calls: 0` refers only to
that offline inspection; the parent ledger reports the submitted paid call.

Mocked tests cover known and unknown accounting, deadline/HTTP failures,
response-before-inspection persistence, duplicate-attempt refusal, incorrect
model variants, invalid patch text, inspector failure, and a citation-complete
false conclusion. These are adapter tests, **not model observations**. Preparing
or merging the envelope does not authorize spending; the separately authorized
execution below is retained as an observation, not a change to those tests.

## First authorized proposer response — November 23, 2026

The [lossless archive](../experiments/workbench/results/first-maintenance-proposer.json.gz)
contains the exact frozen request/private checkpoint, complete native response
object and accounting/transport metadata, original model text, and inspection.
[`proposer-observations.cue`](../experiments/workbench/proposer-observations.cue)
binds its hashes, cost, and outcome. The local original is
`runs/proposer-call-live-01.json`; its one-shot receipt remains consumed.

The user instructed execution in reply to the explicit one-call approval
question. No permission was inferred from PR merge alone. The merged code was
checked against the exact prepared hash before submission:

- Protocol: `42e951b2de3d064265c8518aee521c2896a3a5bd0cd06e90db94dcd6ccd83e03`.
- Archive: `b33d871334ce6cadd417cfcd066de2d313c7084e8b8f86b444ac44576524fbb9`
  (25,459 bytes); original JSON:
  `6c4ffd7ef055a30dcf3abc2b1e5f60ce4776821f0234029b94f935ad3e306adc`
  (265,223 bytes).
- Preparation source `5946f6532b31b722ee8c87defc3cd5fdf0c051e1`; verified merged
  execution base `2d427f468c22ac0cd19c197b27250a93e437a61b`. The archive's
  `source_commit` is the preparation source, not a new execution-commit claim.

**One submitted/accounted GPT-4.1/OpenAI call; $0.004806 reported cost; zero
unknown billing or retries.** Native usage is 2,035 prompt and 92 completion
tokens. The single transport attempt received its response in about 1.54 seconds
within the 120-second absolute bound. The $0.123036 initial reservation settled
to the reported charge. No further proposal, judge, repair, billing lookup, or
provider/account check was made; the remaining budget is not transferred.

### Actual choice: no-op

The unmodified patch has `baseRevision: 5`, `operations: []`, `accounting: {}`.
Its complete rationale is:

> No new sources are being ingested, and the current claims accurately reflect
> the distinctions, uncertainties, and evidence present in the supplied sources.
> Each claim is scoped and attributed appropriately, with ambiguity and
> boundaries preserved where the evidence is inconclusive or contextually
> limited. No consolidation, amendment, or retirement is warranted at this
> checkpoint.

The three working claims therefore remain separate:

1. Database-write deduplication, duplicable notification side effects, and the
   documented manual-replay mitigation, with the broad guidance historical
   rather than a blanket guarantee.
2. The contextual No rejecting the proposed automatic-retry extension, without
   revoking database-write deduplication.
3. The detached Stop with unknown referent, without a global revocation or task.

Application is mechanically valid in the isolated copy. Before/after state,
source/evidence history, aliases, reader probes, projections, revision, and
journal are identical. Recovery is **`not-exercised-no-change`**, not counted as
a successful nontrivial rollback/replay. Semantic judgment remains
**pending-human-review** and canonical acceptance remains false.

This is neither a demonstrated compaction nor an automatic failure to match the
authored two-claim layout. A justified no-op was explicitly permitted. The
rationale asserts fidelity but does not give a detailed account of whether
consolidation would improve usefulness or discovery. Lack of new sources alone
cannot establish that source-free maintenance is unwarranted. The narrow review
question is whether keeping the scoped explanation and automatic-retry boundary
separate is useful here—not whether the output matches a target node count.
One reused authored-development checkpoint cannot establish general proposer
accuracy, and this result does not show model-selected amendment or retirement.
