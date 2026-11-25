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

### Subsequent layout clarification — November 24, 2026

The user clarified: “the automatic-retry restriction doesn't need to stay
separate.” The separate `layoutReview` in the CUE observations binds that narrow
clarification to the archived checkpoint. Integration into the main explanation
is permitted if the restriction, context, evidence, and useful access paths
survive; it is not a mandate for one exact merger or node count. This does not
approve the model's no-op rationale or all current claims. The original archive,
run outcome, and pending meaning judgment remain unchanged. PRD v0.5 §7 and EDD
v0.5 §3.5 carry the corresponding design clarification.

## W3C PROV projection — experimental interchange, not a new ontology

A read-only [PROV-O/JSON-LD exporter](../scripts/provenance.py) maps existing local
records onto [W3C PROV](https://www.w3.org/TR/2013/NOTE-prov-primer-20130430/)
([PROV-O recommendation](https://www.w3.org/TR/2013/REC-prov-o-20130430/)). The
hypothesis is that standard provenance vocabulary can describe the current
lineage without collapsing evidence, assertions, activities, and projections or
creating a second independently maintained graph. The JSON-LD is recomputed,
not canonical storage; this does not adopt RDF/OWL as the semantic engine.

| Existing record | Projection | Boundary |
| --- | --- | --- |
| Received source version | `prov:Entity` | Retains its record, source kind, and statement time; not an independent-witness verdict |
| Exact citation excerpt | Entity `prov:wasQuotedFrom` source | Quotation is mechanically checked; no invented occurrence offsets |
| Immutable assertion record | Entity with `doozer:cites` excerpt references | Citation is not proof of entailment or the proposer's actual derivation |
| Journal patch/restore commit | `prov:Activity` using recorded inputs | Describes local commit, not an invented model reasoning event |
| Each journal-prefix snapshot | `prov:Collection` of active assertion entities | Processing-only events can change snapshots without semantic-revision increments |
| Handbook/agent context | Derived projection entity | Never independent corroboration |
| Responsible person/organization/software | `prov:Agent`, when recorded | Optional source attribution yields `wasAttributedTo`; activity actors remain absent unless recorded |

PROV entities here are **versioned artifacts/records**, not a replacement for
Doozer's domain entities or scoped epistemic interpretation. Dataset-scoped,
content-addressed IRIs keep representations distinct; hashes identify normalized
JSON records, not original HTTP serialization. A paraphrased assertion is
not marked `wasQuotedFrom`; only its literal excerpts are. Existing declared
source derivations are carried as recorded provenance, not authenticated facts.
Replies remain a separate contextual relation, not inferred agreement or
independent support. Unavailable reply/derivation parents remain explicit source
IDs without fabricated records.

Source `attributedTo` metadata contains an identifier, label, and basis. `receive`
preserves it immutably; changing attribution under an existing source ID is rejected.
The exporter records the declared source agent without assuming a legal identity,
WG role, authority, or assertion truth. This is distinct from the assertion's
`expressed`/`observed`/`inferred` stance and from who committed a patch. The curated
public-comment test uses the account association reported by GitHub, not an
inferred activity actor or a new actor registry.

Every prefix retains its active membership, processing positions, and alias
metadata. Restore appends a new collection revision derived from its selected
historical snapshot. Replay reuses the original immutable assertion entities;
it does not generate them a second time. Retirement removes active membership,
**not the historical entity**: the exporter does not misuse PROV invalidation to
claim that evidence or assertions ceased to exist. Statement time is not mapped
to generation/receipt/effective time, and missing actors/timestamps are not guessed.
Legacy missing recovery metadata fails rather than inventing a past.

```sh
nix develop --command just workbench runs/prov-input.json
nix develop --command python -m scripts.provenance \
  --input runs/prov-input.json --dataset-id synthetic-retry-development \
  --output runs/retry-provenance.jsonld
```

For a durable inbox, use `--db runs/inbox.sqlite` instead of `--input`. The
exporter takes one read-only SQLite snapshot and does not refresh the cached
projection. It exports the same graph as the snapshot artifact for the same
dataset ID and title. With either input, `--at-position N` limits the graph to
records known through that reconciliation prefix. Later source payloads and
claims are omitted; snapshots and retained records keep their IDs. The rendered
views mark historical intake and pending coverage as unknown. This is not a
source-time cutoff or a privacy-redaction filter.

The command reads only workbench state, not private evaluator rubrics or model
traces. It caps the artifact or serialized inbox state at 4 MiB, has no live
option, and will not overwrite an output. The output contains source/claim payloads and is not a privacy-redaction
filter: retain the input's handling restrictions. Its inline context requires no
network lookup. RDFLib in the pinned shell/CI parses the
result as JSON-LD/RDF; tests check entity separation, membership/history,
source paths, restore/replay identities, and no source-state mutation. These
checks do **not** establish full PROV constraint conformance, semantic correctness,
authenticated provenance, authority, or reliable autonomous maintenance.

This is a final-state provenance view, **not** a historical model-input filter:
received-but-pending sources and historical payloads may appear, and the journal
does not record past receipt times. Do not hand a full graph to an earlier replay
checkpoint. The [public standards pilot](corpus.md#public-standards-pilot-documents-and-the-discussion-behind-them)
now has explicit conditional source-version/cutoff previews for one captured arc;
meaning review, context budgeting, and maintenance-loop integration still precede
model evaluation. The preparer is not an ingestion/acceptance or live-call adapter. Reingestion must retain projection lineage, not promote
an exported graph or handbook to new independent testimony.

## Bounded standards batches in the local maintenance loop

The [standards adapter](../scripts/standards_maintenance.py) now connects eligible
public-source versions to `receive`, the existing atomic `commit`/`maintain`
gate, projections/discovery, and actual prefix restore/exact replay. It prepares
one artifact per ingestion batch and inspects a saved raw patch offline; it does
not generate one. Authored test responses exercise real intake, amendment through
add/retire, alias access, source-free no-op, and processing-only rollback/replay.
These are mechanical integration tests, not model-selected maintenance results.

```sh
nix develop --command python -m scripts.standards_maintenance \
  --checkpoint checkpoint-02 --source-id draft-04 \
  --output runs/standards-batch.json
# After a raw JSON #Patch has been saved separately (no generation here):
nix develop --command python -m scripts.standards_maintenance \
  --prepared runs/standards-batch.json --proposal runs/saved-patch.json \
  --output runs/standards-inspection.json
nix develop --command python -m scripts.standards_maintenance \
  --checkpoint checkpoint-06 --state runs/standards-inspection.json \
  --source-id draft-05 --output runs/standards-next-batch.json
```

Preparation receives **all eligible retained artifacts into a copy**, preserving
unknown/missing context separately. Each artifact remains one source identity:
its fragments are not independent witnesses. Source `excerpts` retain original
UTF-8 ranges/hashes; `origin` retains version/capture identity, conditional
availability, attribution, scope kind, and separate terms/notices. Statement time
is copied only when known; availability is not invented as statement/receipt time.
The joined `text` field is an index only. It never enters model input, and the
core quote gate requires a quotation to match wholly within one retained excerpt,
not across an omitted gap. Source identity reuse cannot alter this metadata.

Without `--source-id`, ingestion picks the oldest eligible unprocessed version
then stable ID—not the shortest message or a semantic importance score. Use
`--maintenance` explicitly for a source-free patch over existing processed
knowledge. No pending input means idle, not a verdict that consolidation is
unnecessary. Redelivery cannot duplicate receipt or processing. Later sources in
retained state cause an earlier-cutoff preparation to fail; restore does not
magically erase knowledge of receipt or produce a historically blind input.

Only `model_messages(prepared)` is prospective model input. It protects **every
current assertion and every complete retained source excerpt cited by it**, plus
one incoming artifact, aliases/reserved IDs, and honest processing/context gaps.
Other pending text stays local and unreconciled; omitted processed text cannot be
cited by guessing an ID/quotation. The 128 KiB message bound fails explicitly if
the protected envelope cannot fit; there is no silent claim/source truncation or
fake no-op. This is a message-byte limit, not a whole-HTTP/token/provider cost cap.
No current live adapter adopts these messages automatically.

The original seven source meanings remain approved only for their original full
cutoff contexts. They and their bindings stay evaluator-side; that approval is
**not transferred to a partial working view or saved patch**. New framing/output
utility remains unreviewed. All calls/budgets are zero and model/provider are null;
there is no live flag or external publication/acceptance.

Inspection reuses strict saved-JSON decoding and the existing patch ABI. It checks
revision, exact incoming accounting, shown references, source fragments, and
retirement source/access paths without repairing output. Derived analysis is
adapter bookkeeping from additions/current assertions, not another reasoning or
judging call. Each applicable changed material view exercises its own restore and
replay. An ingestion no-op that advances processing is **processing-only**, not a
source-free no-change: its processing positions also need recovery. Genuine
source-free no-change leaves revision/journal untouched and recovery unexercised.
Public projections use the HTTP domain title and retain cited source attribution,
separate terms, and original notices; provenance can render the same titled view
with `--projection-title 'HTTP problem details'` (its legacy default is unchanged).

Known limitations remain explicit: the inherited accounting ABI has represented
and dependent-no-op dispositions, not a general first-source irrelevance mode.
Unsupported empty-view/no-op proposals are rejected rather than inventing a fact
or pretending to process them. Citation-complete false prose (the test says “All
HTTP headers are now forbidden”) still passes the mechanical gate and recovery.
Semantic judgment stays pending and external acceptance false. This is isolated
local state, not durable intake, concurrent/crash-safe service operation, a full
seven-checkpoint semantic run, or evidence of autonomous correctness.

### Draft version update request preview

`python -m scripts.standards_request --state runs/standards-batch-inspected-03.json --output runs/standards-request-preview.json`
(in the pinned devshell) freezes an offline request for draft 05 against an
operator-supplied, already processed draft-04 view. The authored baseline is not
a semantic endorsement. The exact payload includes the protected current view
and one incoming artifact, not private evaluations, the entire received-source
store, or later releases. No live runner accepts this report.

On the authored demonstration state, the full serialized body is 58,625 bytes.
The proposal pins GPT-4.1 via OpenAI on OpenRouter, with no fallback or retries,
a 4,096-output-token limit, a 128 KiB body ceiling, and a $0.26 local budget.
Using body bytes plus 8,192 as a padded input proxy and the pinned price filters
reserves $0.237315 for this request. This is not a measured token count, bill
prediction, or provider-wide cap. The preview makes zero calls.

Before execution, review the exact excerpts and notices, authorization for
transmission to both services, and retention/training and routing terms for
this endpoint. The payload's `data_collection: deny` filter does not by itself
prove zero retention or grant transmission rights. A later executable protocol
must enforce request/response/time/accounting bounds and receive explicit
hash-bound spending approval. The behavioral question is whether the proposal
updates the working-draft guidance without erasing historical access or
inventing a universal prohibition; successful parsing or replay alone is not a pass.

### Synthetic guide revision trial

Prepare with `nix develop --command python -m scripts.maintenance_call --revision-update --output runs/synthetic-revision.json`.
The fixed fictional guide supersedes its first revision and omits an optional
procedure. The model sees both versions and the current working view, but not
the evaluator's questions. Review whether the proposal distinguishes current
guidance, historical access, and omission versus prohibition. No particular
layout is required. Saved output uses the local batch inspector; successful
application and replay do not settle meaning.

The proposed call is one GPT-4.1 request through OpenRouter to OpenAI, with a
$0.10 local limit, at most 4,096 output tokens, and no retry or fallback. The
existing runner requires exact-hash opt-in and a new output file; preparation
and PR merge do not authorize execution. The public standards preview remains
non-executable and is not used in this trial.

The separately authorized trial submitted **one call for $0.003900** (766 input
and 296 output tokens), with no retries or unknown billing. The [unaltered run
archive](../experiments/workbench/results/first-synthetic-revision.json.gz) is bound
to protocol `5f51e85e8bc551505e1b0952f8997b5175cb26bba39444b0ef840e53224bab1c`.

The rationale noticed supersession, omission, the new ledger step, and the
unchanged deadline rule. The patch, however, proposed no additions and attempted
to retire `marker-procedure` with an empty replacement. It keyed intake accounting
by that claim ID rather than `guide-two`, listed no surviving claims, and cited
the incoming source as a dependent-no-op basis (which must be processed already).
The empty replacement and claim list violate the patch schema; the other defects
would fail commit checks. The inspector rejected the original patch before commit.
Revision 1 remained unchanged, `guide-two` stayed pending, and recovery was not
exercised. The rationale is not a successful update, and no correction or
replacement was attempted.

The prospective `synthetic-revision-update-v2` protocol keeps the same evidence,
working view, schema, and commit gate. It explains the cross-record rules that
CUE's exported shape does not express: incoming source keys, surviving claims,
processed evidence for dependent no-ops, and source-preserving replacements.
It explicitly allows add-only patches. Offline controls exercise violations and
two mechanically valid layouts. The archived v1 protocol remains a rejected
result.

The separately authorized v2 request cost **$0.004838** (963 input and 364 output
tokens), with no retries or unknown billing. The [run archive](../experiments/workbench/results/second-synthetic-revision.json.gz)
retains the response unchanged under protocol
`9dd2e54d8a2f1dd07d0ea6e800de7249bfdfece986f8dc55b618f10f864e4678`.
Unlike v1, v2 used the incoming source as the accounting key and supplied two
add operations. One attempted to add `marker-procedure`, an ID already in use.
The patch passed the schema but failed the immutable claim identity check. The
entire patch was rejected: neither addition was committed, the incoming guide
stayed pending, and recovery and semantic evaluation were not exercised.
One response per version does not establish a causal improvement; neither
version completed the update. No patch was repaired or resubmitted.

The prospective v3 protocol assigns checkpoint-local references. An `add` must
use one of four offered `new-*` slots; a retirement target must be a shown
`existing-*` reference. Accounting and replacement operands may refer to shown
existing claims or slots actually used by an add. Unknown, unused, or duplicate
add slots are rejected, not reassigned. The private map deterministically picks
fresh persistent IDs outside current claims, history, and redirects. Unused slots
have no persistent effect. Only declared claim operands are translated: source
keys, quotations, prose, operation order, and reasons remain unchanged. The
inspector retains the original proposal and the translated patch separately.
Commit still checks revision, citations, accounting, and retirement paths; exact
replay uses the translated journal entry. This prevents the observed identity
collision for valid slot operands; it does not judge meaning or reprocess either
archived response.

The authorized v3 trial made one call for **$0.004744** (1,052 input and 330
output tokens), with no retries or unknown billing. The [v3 archive](../experiments/workbench/results/third-synthetic-revision.json.gz)
records the original proposal and translation. The model used one new slot to
add the revision 2 ledger and deadline guidance. The patch applied in isolation,
processed both guides, and exercised successful restore and exact replay.

The original procedure remained an active, explicitly revision 1 claim; the
revision 2 claim says it supersedes revision 1 and does not infer a marker ban.
Both entries remain in the projection. This is a model-selected, applicable
add-only update with historical access—not consolidation, a current-only view,
or proof that readers will interpret the two entries correctly. Semantic review
remains pending. One run does not establish general reliability.

To find a scope label without knowing it in advance, use the offline reader's
`--find-scopes` mode:

```sh
nix develop --command python -m scripts.workbench \
  --inspect runs/synthetic-revision-v3-live-01.json \
  --find-scopes --query 'dispatch deadline'
```

On the saved v3 report, this lists both guide revisions and their matching claim
IDs, without ranking or selecting a revision. `ledger` lists only revision 2, but
still does not select it. The search matches terms in active claim text and scope
labels, not historical aliases or pending sources. No match is local to that
search and snapshot, not evidence of absence. To inspect historical material,
use normal discovery or explicit reference lookup.

Then select an exact claim scope to view its guidance:

```sh
nix develop --command python -m scripts.workbench \
  --inspect runs/synthetic-revision-v3-live-01.json \
  --scope 'Lantern Dispatch Guide, revision 2' --query ledger \
  --reference marker-procedure
```

The revision 2 projection shows the ledger and deadline guidance with its
source, not the revision 1 procedure. The explicit reference returns the old
payload separately; its active target is suppressed if outside the requested
scope. A search in revision 1 still finds the old procedure. An unknown label
produces no hits or projected claims rather than falling back to mixed guidance.
Scope matching uses exact stored labels, not inferred applicability, and a
matching label can omit relevant cross-scope qualifications. Coverage still
reports the whole local snapshot. Unscoped views remain unchanged, and this
read-only filter neither retires claims nor establishes what is current.

Use `--claim-evidence claim-slot-1` with the saved report to read the exact
revision 2 quotation and anchor; `--claim-evidence marker-procedure` reaches the
revision 1 quotation. A source comparison shows that revision 2 directs
completed counts to the shared ledger and leaves the deadline rule unchanged.
It supersedes revision 1 and omits the old optional second-count procedure,
but it does not ban markers. The archived patch preserves these distinctions
when read by revision. Both claims still appear in the unscoped view, which
is not a current-only answer. This observation does not change the archived
judgment or establish reader comprehension.

## Durable local source inbox

`scripts.source_inbox` records validated immutable source versions in a local
SQLite database. Row presence is pending membership: there is no separate event
that could be lost between storing the payload and recording work to do. Receipt
returns only after commit in rollback-journal mode with `synchronous=EXTRA` and
a directory sync. This relies on SQLite and a local filesystem honoring syncs;
tests exercise process and transaction failures, not hardware power loss.
Identical redelivery returns the same position; a changed record under the same
ID fails. Positions are local intake order, not publication or effective time.

```sh
nix develop --command python -m scripts.source_inbox --db runs/inbox.sqlite \
  receive --source-id synthetic-note --source runs/source.json
nix develop --command python -m scripts.source_inbox --db runs/inbox.sqlite \
  snapshot --output runs/inbox-snapshot.json
nix develop --command python -m scripts.workbench --inspect runs/inbox-snapshot.json
```

The source JSON requires `kind`, `text`, `anchor`, and `scope`; the input size
limit is 256 KiB. Use synthetic data, and keep the database and snapshots in
ignored `runs/`. `received-pending` describes the original intake acknowledgment,
not the source's current processing status. Inspect the snapshot for that status.

For a local thread import, pass an ordered JSON array of `{source_id, source}`
records to `receive-batch --sources runs/thread.json` instead of `receive`.
The batch accepts up to 64 records and 1 MiB total, with the same per-source
limit. All records commit in one transaction. A conflicting ID aborts the whole
batch, and identical redelivery reuses the original positions. Receipts are
returned in input order, which may differ from intake order on redelivery.
Batch intake does not run reconciliation.

Use `pending --limit 20` on the same inbox to see pending IDs in intake order,
without source payloads. The report includes the total pending count, whether
the list is truncated, and both positions from one read transaction. Projection
refresh does not clear pending work; reconciliation can clear it, and restore
can return it to pending.

To prepare a local reconciliation batch from that list, run
`source_inbox --db runs/inbox.sqlite prepare-batch --source-id ID` (repeat
`--source-id` for additional pending records). This read-only view includes
selected source payloads, active claims and their cited sources, and the count of
other pending records without their text. The 128 KiB envelope fails rather than
trimming evidence. Uncited sources are omitted, so this is not a completeness
claim. Keep the output local.

Copy `commit_binding` into the top level of a saved commit request alongside
`patch`, `analysis`, and `route`. Its optional state digest rejects a changed
snapshot inside the transaction, even when only a new receipt arrived. It is a
freshness check, not a semantic verdict or a restriction on what a commit may
cite. Existing commit requests without the digest still work.

For a read-only preview, save the preparation and pass it to
`inspect-batch --prepared runs/batch.json --proposal runs/proposal.json`, where
`proposal.json` contains `patch`, `analysis`, and `route`. Inspection checks the
preparation against the current inbox, runs the existing commit checks in a
copy, and rejects citations to sources not shown in the preparation. It returns
before and after projections, the exact `request`, and an inspection hash.
Nothing is committed by inspection. To apply the reviewed inspection without
copying its request by hand:

```sh
nix develop --command python -m scripts.source_inbox --db runs/inbox.sqlite \
  apply-batch --inspection runs/inspection.json --sha256 INSPECTION_HASH \
  --operation-id reviewed-batch
```

The hash detects changes to the reviewed report; the existing transaction checks
the state binding and revalidates the request. The preview is not a semantic
verdict or an authenticated approval, and it does not change the standalone
commit contract.

To watch the whole handoff on a disposable synthetic inbox:

```sh
nix develop --command python -m scripts.watch_workbench --prepared-batch --step
```

The demo pauses after receipt and again after inspection. Both pauses show the
same pending batch. Only explicit apply commits the authored proposal, after
which the demo refreshes the reader projection. No model calls are made.

### Durable saved-patch commit

```sh
nix develop --command python -m scripts.source_inbox --db runs/inbox.sqlite \
  commit --operation-id apply-note --request runs/reconciliation.json
```

Supply a JSON envelope with `base_position` (the snapshot's
`reconciliation_position`, initially zero), `patch`, `batch`, `analysis`, and
`route`. The existing workbench validator checks the saved ingestion patch.
A transaction writes its resulting state, including processed source IDs and
journal, together with an operation receipt. Exact redelivery returns the original
receipt; reusing the operation ID for a different request is an error. A new
commit advances the position even for processing-only changes, so a stale
position cannot pass merely because the semantic revision stayed the same.

Snapshots read both parts together; newly received material remains pending until
committed. This is an operator-driven local path, not a judge of semantic
correctness. It holds a writer lock during validation and rewrites the compact
workspace snapshot, so it is not a scalable persistence design. There is no
network listener or dispatcher.

### Durable source-free maintenance

Use `python -m scripts.source_inbox --db runs/inbox.sqlite maintain --operation-id combine-claims --request runs/maintenance.json`
inside the pinned devshell. The envelope contains `base_position`, `patch`,
`analysis`, and `route`, with no `batch`. The patch must have empty accounting
and may cite only already processed sources. A successful change commits a
journal entry and operation receipt, shows up as `Maintained` in the watch, and
makes the reader projection fall behind without moving the intake position.

A valid empty patch returns `no-change` without a receipt, new position, or
journal entry; it does not reserve the operation ID. Nonempty changes use the
same idempotency, restore, and replay path as ingestion patches. Old claim
payloads and references remain available. Validation does not establish that
a consolidation preserves meaning.

To review a saved patch without hand-copying an envelope, use the offline handoff:

```sh
nix develop --command python -m scripts.maintenance_handoff --db runs/inbox.sqlite \
  prepare --output runs/prepared-maintenance.json
# Supply a saved patch separately; prepare does not generate one.
nix develop --command python -m scripts.maintenance_handoff --db runs/inbox.sqlite \
  inspect --prepared runs/prepared-maintenance.json --patch runs/patch.json --output runs/inspection.json
nix develop --command python -m scripts.maintenance_handoff --db runs/inbox.sqlite \
  apply --inspection runs/inspection.json --sha256 INSPECTION_HASH --operation-id reviewed-maintenance
```

Preparation includes all active claims and the processed sources they cite, not
pending text or uncited sources. It reports pending coverage as a count and fails
rather than trimming the context at its message-byte bound. The preparation is
an offline preview, not a live request or spending authority. When inspecting
with `--prepared`, changed state, changed messages, or citations to withheld
sources are rejected. Prepared proposals use temporary references for existing
claims and four offered slots for additions. Doozer allocates persistent IDs and
translates claim references only; the inspection retains both the original
proposal and the translated commit request. Apply verifies the translation again
before entering the durable gate. Direct inspection without a preparation still
accepts patches with explicit persistent IDs.

Inspection checks the exact saved patch in an isolated copy and shows before and
after projections. For a change, it rehearses restore and exact replay in the
same isolated copy, checking material state and retained history. A no-op skips
recovery. Inspection writes no database state and does not evaluate meaning:
an authored patch that reverses the greenhouse fan instruction while keeping
its citations still passes mechanical inspection and recovery.

Add `--query 'circulation fan' --scope 'east greenhouse evening closure'` to
`inspect` to record the same lexical search before and after. Drop `--scope`
for unscoped results. The comparison shows actual claims and citation anchors,
not an automatic judgment, and never enters the model prompt. It is included in
the local inspection hash but not in the commit request.
The inspection file contains claim text and evidence; keep it local. Apply requires
the reviewed hash and revalidates through the durable maintenance gate. A new
receipt, intervening reconciliation, or change to the gate invalidates the
handoff. The state check runs inside the write transaction. The hash binds the
inspection to a logical snapshot, not an authenticated reviewer or physical
SQLite file. Existing saved-patch commands remain available; this workflow does
not grant publication or model-call permission.

For a deterministic baseline, preview exact duplicate retirements without a
model or saved proposal:

```sh
nix develop --command python -m scripts.maintenance_handoff --db runs/inbox.sqlite \
  duplicates --output runs/duplicates-inspection.json
```

Only active records identical in every field except ID are grouped. Citation
order, wording, scope, and attribution must match; identical text from a
separate source is not a duplicate. The first ID in lexical order stays active.
The existing hash-bound `apply` command can persist the preview, retaining old
IDs and original records in history. If nothing matches, no inspection file is
written. This is exact-record cleanup, not a finding about semantic equivalence
or whether other maintenance is warranted.

To opt in to one bounded exact-duplicate cleanup without saving a separate
inspection file:

```sh
nix develop --command python -m scripts.maintenance_handoff --db runs/inbox.sqlite \
  compact-duplicates --max-retirements 2
```

The command inspects and rehearses recovery before committing through the same
snapshot-bound gate. If the limit would be exceeded, it refuses the whole
cleanup. A stale snapshot fails without retry. Running again on the unchanged
result is a no-op with no new receipt. This command does not apply model proposals
or refresh the reader projection.

Watch the real cleanup and recovery in a disposable greenhouse inbox:

```sh
nix develop --command python -m scripts.watch_workbench --exact-duplicates --step
```

The demo labels the authored setup separately, runs the deterministic cleanup
twice, then restores and exactly replays the first cleanup. The repeat has no
receipt. Each stage shows durable events and the active east-scope IDs; the
demo does not touch the live trial inbox or call a model.

### Synthetic inbox proposal trial

```sh
nix develop --command python -m scripts.maintenance_call \
  --inbox-trial runs/trial.sqlite --output runs/trial-prepared.json
```

This offline command seeds a new inbox with the checked-in append-only retry
fixture and freezes a maintenance request for its six active claims. Only the
prepared messages enter the payload. The runner reconstructs the fixed synthetic
checkpoint before accepting it; arbitrary inboxes are not eligible for this trial.

Use `--inbox-case closure` to prepare a distinct synthetic greenhouse fixture.
Two east-greenhouse claims describe complementary closure steps; the west
instruction differs and must remain separately scoped. The authored comparison
combines only the east claims while preserving both old references, both scopes,
and the original evidence. The comparison and reader checks are not part of the
request. A model-selected patch need not match the authored layout, and a
mechanically valid patch or no-op does not settle reader usefulness.

The offline closure control preserves both east instructions and the distinct
west instruction in scoped search, with exact source quotes and old IDs still
reachable. A reversed east fan instruction also passes inspection and replay
but contradicts its cited quote. The control test checks actual durable apply,
restore, and replay receipts using the same watcher as a local operator:

```sh
nix develop --command python -m scripts.watch_workbench --db PATH_TO_DISPOSABLE_INBOX
```

This is authored-control evidence, not a model result.

The first authorized closure trial made one GPT-4.1 call for **$0.003128**
(964 input and 150 output tokens), with no retry or unknown billing. It returned
a mechanically valid no-op. The rationale correctly distinguished the two east
steps and the opposite west fan instruction, but treated distinct actions as a
reason not to combine their presentation. It did not explain a reader benefit
that required keeping two east claims, and lack of new intake does not rule out
source-free maintenance. All three scoped instructions and source quotations
remained reachable; no reader improvement or model-selected consolidation was
demonstrated. Nothing was applied, and restore and replay were not exercised
for the no-op. The original response and accounting are preserved locally in
`runs/bird-closure-live-01.json`. The [review record](../experiments/workbench/results/first-inbox-closure.json)
contains the exact response text and selected accounting fields; an offline
regression test reproduces the no-op from that response. To see the actual receipt history, substitute
`runs/bird-closure-01.sqlite` in the watcher command above: only the seed
reconciliation appears, not a maintenance commit.

One GPT-4.1 call via OpenRouter to OpenAI is proposed, with a $0.10 local limit,
4,096 output tokens, and no retry or fallback. Preparation does not authorize a
call. The existing runner requires separate approval and exact-hash opt-in. It
inspects any returned patch against the frozen snapshot in memory, without
writing to the inbox. Durable apply remains a distinct explicit operation using
the inspection and its hash. A valid patch or no-op is not a semantic pass.

The [first authorized inbox trial](../experiments/workbench/results/first-inbox-maintenance.json.gz)
made one call for **$0.004376** (1,920 input and 67 output tokens), with no retries
or unknown billing. The response proposed an empty operations list but omitted
required `accounting: {}`. Inspection rejected it, recording a missing-key error;
this is not an accepted no-op. The rationale partly invoked the absence of new
sources and did not address whether the six claims could usefully be consolidated.
No semantic verdict, repair, or durable apply followed. The trial inbox remained
byte-for-byte unchanged.

Prepared proposals now omit `accounting` entirely. The inspector preserves the
raw proposal and adds empty accounting to the separate canonical workbench
patch. Direct inspection of a saved canonical patch still requires explicit
empty accounting. The format change is prospective; it does not change the
archived rejection or authorize another call.

The [second authorized inbox trial](../experiments/workbench/results/second-inbox-maintenance.json.gz)
used the same six claims and nine synthetic sources with the revised proposal
format. One call cost **$0.004094** (1,811 input and 59 output tokens), with no
retries or unknown billing. The empty operations list passed isolated inspection,
and the projected state did not change. The rationale asserted that the claims
were accurate but did not address whether overlapping claims could be combined
without losing useful distinctions. This is a mechanically valid no-op, not a
semantic verdict or evidence of consolidation. Nothing was applied; the durable
inbox remained byte-for-byte unchanged.

Prepared requests also carry one hop of recorded reply context for cited
sources. If a parent is already in `sources`, it is not repeated. Otherwise a
processed parent's retained passages are labeled as context only and are not
eligible citations for this proposal. Pending and missing parents are marked
without text. The same request byte limit applies; nothing is silently trimmed.

Prepared requests include `evidence_overlap`: pairs of temporary claim
references that cite the same processed source, with shared source and exact
quotation counts. The preview shows at most eight pairs, sorted by exact
quotation count, then shared source count, then reference. It reports truncation
and skips comparison above 32 claims without removing claims or evidence. The
three- and six-claim retry views yield one and seven pairs, respectively. Even an
identical quotation can support distinct claims; the hint neither adds evidence
nor recommends a merge. The proposer is asked to weigh reader usefulness and
explain a no-op.

The [third authorized inbox trial](../experiments/workbench/results/third-inbox-maintenance.json.gz)
used the same checkpoint and added those seven comparisons. One call cost
**$0.005494** (2,095 input and 163 output tokens), with no retries or unknown
billing. The proposal passed isolated inspection as a no-op. Unlike the previous
rationale, it named a pair and distinguished the incident account from guidance
on manual replay and execution paths. That is a more specific rationale, not
proof that keeping the claims separate best serves readers or that the hints
caused the difference. No semantic verdict or durable apply followed. The inbox
checksum was unchanged.

An offline comparison applied the existing authored consolidation to a copy of
that same six-claim checkpoint. It combined the execution-path explanation and
its automatic-retry restriction into one entry, leaving the separate production
incident account and detached “Stop” untouched. The `manual replay` search went
from two hits to one. Unscoped `automatic retries` search and both old claim IDs
still reached the combined entry, with the original wording and citations
retained. But exact-scope search under `automatic-retries` went from one hit to
none: the new entry has a broader scope label. This is a concrete access cost of
this authored layout, not a verdict that the model's no-op was warranted. It
also doesn't test merging the specific pair named by the model. Neither archive
nor any durable inbox was changed.

If you know the former scope but not the claim ID, look it up explicitly in a
saved state artifact:

```sh
nix develop --command python -m scripts.workbench --inspect runs/retry.json \
  --scope-history automatic-retries
```

`--scope-history` lists inactive assertions under that exact label, with their
original citations and source anchors. A current reference, when present, shows
its own scope rather than implying that it applies to the former scope. The
lookup does not change active search, scope suggestions, or projections.

Maintenance inspection now reports `scope_impact`: exact labels that would be
added or disappear from active search, and historical claim IDs for lost labels.
The terminal demo shows the count before applying a patch, then actually looks
up the inactive records in the durable inbox by former scope. This is a structural
comparison, not a semantic verdict or a claim that history replaces active access.

To read the durable inbox directly, without exporting an artifact:

```sh
nix develop --command python -m scripts.source_inbox --db runs/inbox.sqlite \
  discover --query 'automatic retries' --find-scopes
nix develop --command python -m scripts.source_inbox --db runs/inbox.sqlite \
  discover --scope-history automatic-retries
```

`discover --query ... --scope LABEL` restricts current search to that exact
label. Results include the intake and reconciliation positions from the same
read-only snapshot and list pending source IDs. Search does not wait for or
refresh the cached projection, and pending source text is not searched.

Follow a search hit's exact claim ID to its evidence:

```sh
nix develop --command python -m scripts.source_inbox --db runs/inbox.sqlite \
  evidence --claim automatic-retry-boundary
```

This read-only lookup labels active and historical claims separately. It returns
recorded quotations and source anchors, plus one hop of recorded reply context.
Processed parents show their retained passages; pending and missing parents are
reported without text. Declared `derivedFrom` links are listed separately from
reply context, with anchors and kinds for processed inputs and status only for
pending or missing ones. Neither kind of link is an additional citation or an
entailment verdict, and a missing derivation link does not imply independence.

Go the other way from a source ID to its direct citing claims:

```sh
nix develop --command python -m scripts.source_inbox --db runs/bird-closure-01.sqlite \
  source-usage --source-id note
```

The report separates active and historical claim IDs, gives a processed
source's anchor, and distinguishes pending from unknown sources. It does not
count reply or derivation links as citations. Use `--at-position N` to limit the
lookup to a recorded reconciliation prefix, not reconstruct historical intake.

Follow a citing claim's recorded membership and reference changes with
`claim-timeline --claim ID` on the same inbox. It lists only positions where
that ID became active, became inactive, or resolved to a different claim. Use
`watch_workbench --db PATH --explain POSITION` for the recorded transition's
rationale. The timeline does not infer source-time validity or show claim text.

If you already know the exact scope, browse all its active claims without
choosing search terms:

```sh
nix develop --command python -m scripts.source_inbox --db runs/bird-closure-01.sqlite \
  browse --scope 'east greenhouse evening closure'
```

This shows both east steps and their citations without merging them or returning
the west instruction. An unknown label returns no claims; browsing does not
select a scope, infer applicability, or refresh the cached projection.

`discover`, `browse`, and `evidence` accept `--at-position N` to read a recorded
reconciliation prefix without restoring the inbox. For example:

```sh
nix develop --command python -m scripts.source_inbox --db runs/inbox.sqlite \
  discover --query 'automatic retries' --at-position 4
```

Position zero precedes the first reconciliation. Later claims and source text
are withheld; a linked input with no record in the prefix is `not-in-prefix`,
not known missing at that time. Intake and pending coverage are `null` because
reconciliation history cannot reconstruct receipt order. This is a local journal
view, not a source-time or public-availability cutoff.

To run the same search at two positions in one read-only snapshot:

```sh
nix develop --command python -m scripts.source_inbox --db runs/inbox.sqlite \
  compare --query 'automatic retries' --scope automatic-retries \
  --from-position 6 --to-position 7
```

Both searches use the same exact scope (or both are unscoped if omitted). The
report includes both sets of hits and lists IDs gained or lost. A changed hit is
an access difference, not a verdict about meaning or applicability. The command
never restores the database or reconstructs historical intake.

### Durable restore

Use `python -m scripts.source_inbox --db runs/inbox.sqlite restore --operation-id undo-note --request runs/restore.json`
inside the pinned devshell. The envelope contains `base_position` (the current
reconciliation position) and `request` (the workbench restore object with
`baseRevision`, `targetPosition`, and `reason`). `targetPosition` is a journal
prefix, not a semantic revision. A successful restore appends a compensating
entry, preserves source receipts and historical claims, and can put previously
processed sources back into pending. It advances the reconciliation position so
the cached projection reports `behind` until refreshed.

An identical restore redelivery returns the original receipt. A stale, invalid,
or no-change restore writes no receipt or journal entry. Restore and saved-patch
operations share the operation ID namespace. Resubmitting the original patch's
operation ID returns its original receipt and does not undo the restore.

### Watch the recorded fixture

```sh
nix develop --command python -m scripts.watch_workbench --step
```

Press Enter between rounds, or omit `--step` for continuous playback. The demo
uses a fresh temporary inbox and prints durable receipts, recorded patch proposals,
commit acknowledgments, pending evidence, and actual handbook diffs. Watch the
incident sit pending, a redelivery produce no new commit, and the contextual
“No.” arrive in its own round. A rejected proposal stops playback without a
commit line. This is a synthetic demonstration of the local pipeline, not a
live model trace. The temporary inbox is removed when playback exits.

Add `--maintenance` to continue after ingestion. Watch three active claims
become two, see a recorded no-op leave the view unchanged, then restore the
three-claim view and replay the consolidation. Consolidation and the no-op go through the prepared proposal handoff. The demo
shows the temporary references and the inspected claim count before applying the
patch. In step mode it pauses before consolidation is applied. All four rounds
use the durable inbox APIs and show the resulting reader view or diff. The intake position
stays fixed. This is authored playback, not a model choosing to consolidate.

### Watch an existing inbox

```sh
nix develop --command python -m scripts.watch_workbench --db runs/inbox.sqlite --follow
```

This opens the database read-only. It lists durable source receipts, patch
commits, processing-only commits, restores, and replays, and reports cached
projection freshness. It prints identifiers and positions, not source or claim
text. Omit `--follow` for one snapshot. The follow cursor is session-local:
restarting lists existing records again. Intake and reconciliation have separate
position order; the display does not guess how they interleaved. Projection
refreshes between polls may coalesce. Saved patches rejected by the local
validator produce a separate durable attempt record with the operation ID and
base reconciliation position. It omits the patch, source text, and validator
message; the submitting command still reports the error. A rejection does not
advance reconciliation or invalidate a projection. In-flight work, stale
requests rejected before patch validation, recovery errors, and storage
failures are not recorded by this path.

To inspect a reconciliation position from the watch output:

```sh
nix develop --command python -m scripts.watch_workbench --db runs/inbox.sqlite --explain 2
```

The JSON includes the recorded reason, added and removed claims with citations,
redirect changes, processed or reopened source IDs, and their source anchors.
Restore reports its target journal prefix; replay points to the original patch's
reconciliation position. The changes come from the two journal prefixes around
the selected transition, not from comparing against today's state. This is
recorded rationale, not a verdict, and it does not reconstruct which unrelated
sources had arrived at the time. Unlike the default watch, this opt-in view
includes claim text and quotations.

### Recorded dispatch

`nix develop --command python -m scripts.recorded_dispatch --db runs/inbox.sqlite`
advances an existing inbox by one reconciliation batch from the checked-in
synthetic retry fixture. Populate the inbox using that fixture's source IDs and
records. The driver rebuilds the offline reference journal, checks that the
inbox matches its prefix, and uses the existing durable commit path for the next
batch. It reports missing batch sources without changing state and returns
`complete` once all recorded transitions are committed. Receipt order need not
match reconciliation order.

Add `--max-steps 3` to drain up to three ready batches in one invocation.
It prints each durable receipt as a JSON line, then reports `step-limit`,
`waiting-for-sources`, or `complete`. If reporting stops after a commit, a new
invocation starts from the durable journal, not the last printed receipt.

Add `--wait-seconds 10` to poll for missing receipts. The optional wait window
starts when the drain begins checking batches, has a maximum of 60 seconds, and
does not reset between batches. If the window closes while waiting, the drain
reports `wait-expired` with the last observed missing IDs. This bounds polling,
not an in-progress commit or projection refresh. Without the flag, the drain
returns immediately on missing evidence.

Add `--refresh-projection` alongside `--max-steps` to catch up the reader
projection once the drain stops, even when it commits zero batches. The summary
reports projection positions, not projected text. Projection refresh is a separate
transaction: a failed refresh leaves reconciliation intact, so a later run can
catch up without recommitting completed batches.

This is fixture playback, not a general worker: unknown or changed source
records and divergent journal history are rejected. It does not run in the
background, retry failed commits, call a model, or publish externally.

### Durable exact replay

Use `python -m scripts.source_inbox --db runs/inbox.sqlite replay --operation-id redo-note --request runs/replay.json`
inside the pinned devshell. The envelope contains `base_position` (current
reconciliation position), `base_revision` (current semantic revision), and
`journal_position` (the zero-based index of the original patch entry, not its
receipt position). Use a fresh operation ID for a new replay. Doozer revalidates
the recorded patch against its original material preconditions; a restore entry
or divergent working view is not replayable. The transition and its receipt
commit together. Exact redelivery has no further effect, and the cached
projection stays behind until refreshed. Replay does not call a model.

### Local projection catch-up

```sh
nix develop --command python -m scripts.source_inbox --db runs/inbox.sqlite projection
nix develop --command python -m scripts.source_inbox --db runs/inbox.sqlite refresh-projection
```

The commit receipts already written with reconciliation state serve as durable
invalidation markers. The local projection consumer tracks both reconciliation
and intake positions, so receipt alone can make its coverage stale. `projection`
reports `missing`, `behind`, or `caught-up` with cached and available positions
from one read transaction. `caught-up` does not mean all inputs were reconciled;
the projected coverage still reports pending evidence. A cached render from an
older renderer version is `behind` even when both positions match. Claims render
in ID order, independent of the order in which the state was loaded.

`refresh-projection` coalesces outstanding changes into the latest local view
and commits the rendered projection and its positions together. Failed refreshes
leave the old projection and positions intact. Refreshing an unchanged snapshot
does not regenerate it. This is a pull-based local outbox equivalent for one
regenerable view, not per-event delivery or an external publication mechanism.

## Same-evidence working-view contrast

To test whether the proposer distinguishes useful maintenance from unnecessary
rewriting, reuse the existing checkpoint builder, one-call adapter, and saved
proposal inspector. No new judge or evaluation service is introduced.

`proposerContrast` in `proposer.cue` defines two views **before** the authored
consolidation pass:

- `case-a`: the maintained view with three active claims.
- `case-b`: the append-only patch ablation with six active claims.

Both have identical received/processed sources (eleven records), revision,
historical claim payloads, and reserved IDs. The three current assertions are
an unchanged subset of the six. Current membership and alias routes differ as
legitimate representation state; no new observation or source is invented to
make the contrast. The six-claim view is not the seven-claim result after adding
the authored consolidation. That target is never applied or shown here.

Both receive **byte-identical system instructions and output contract**, updated
for PRD/EDD v0.5: no new sources alone is not a no-op justification, restrictions
may be integrated without losing meaning/access, neither separation nor merger
is automatically preferable, and usefulness needs explanation. Public user
context differs only in current assertions and existing aliases. Cell labels,
construction descriptions, expected input counts, evaluator queries/rubrics,
prior model output, authored targets, and future sources remain outside model
messages. Input membership counts validate experimental construction, never a
required output count. These are reused authored development views, not held-out
cases or a calibrated estimate of proposer accuracy.

```sh
# Offline, credential-free, no request or account/provider lookup.
nix develop --command just maintenance-contrast runs/maintenance-contrast-NEW.json
```

The parent manifest freezes both child requests, their exact hashes and private
checkpoints, the shared instructions, construction assumptions, and fixed order
(`case-b`, then `case-a`). The proposed live envelope is **two GPT-4.1/OpenAI
calls, $0.30 total locally, at most $0.15 per child, no retries or fallback**.
The existing per-call 8,000-output-token, 120-second absolute local wait,
128 KiB request, and 1 MiB response bounds remain. All price/accounting and
provider-cancellation caveats above still apply. The requests are independent:
neither receives the other view or its proposed answer.

**No paid call is authorized by preparation or merge.** After separate approval
of the exact parent hash and two-call scope, the existing adapter can execute:

```sh
# Only after explicit authorization; not an instruction to run during review.
nix develop --command python -m scripts.maintenance_call --contrast --live \
  --prepared runs/maintenance-contrast-NEW.json \
  --protocol-sha256 EXACT_APPROVED_PARENT_HASH --output runs/contrast-live-NEW.json
```

The parent coordinator delegates only the two frozen requests to the one-call
runner. Parent and child receipts prevent accidental duplicate execution in the
workspace; extracted children refuse standalone execution through the normal
CLI. A transport/accounting failure or reported child overrun stops the pair;
the unattempted denominator remains visible and cannot be filled by resuming or
spending the other child's allowance. An accounted invalid output remains
invalid, while the other fixed request may still run. No response is regenerated,
repaired, judged by another model, or passed to the peer. Existing local receipt
and crash-durability limitations remain; copying workspaces is not a global cap.

Both actual outputs must be reviewed independently for warranted action/no-op,
material scope and qualifications, source independence, old access paths, and
reader usefulness. A coherent input need not produce no-op, and a redundant input
need not hit a fixed count. Mechanical acceptance, smaller graphs, recovery
success, or asymmetric outputs do not themselves establish appropriate behavior.
Known-invalid and unavailable outputs remain distinct from semantic failures.
Nonempty applicable patches use their own initial state for rollback/replay;
no-op recovery remains unexercised.

Offline tests cover same-evidence/current-view invariants, v0.5 prompt parity,
private/future/prior-output canaries, two independent mocked inspections,
nonempty patch recovery, known-invalid continuation, unknown-billing stop,
parent/child authorization and duplicate-attempt guards, and CLI no-clobber.
They do not constitute a generation result. The original one-call no-op archive
and its pending meaning judgment are unchanged; no previous budget is reused.

### Authorized contrast result — November 24, 2026

After the user explicitly approved the fixed two-call scope, both requests ran
from the exact prepared parent hash. PR #28 was still open; spending permission
came from the direct approval, not merge. The [lossless result archive](../experiments/workbench/results/first-maintenance-contrast.json.gz)
and [CUE observations](../experiments/workbench/contrast-observations.cue)
retain both requests/private checkpoints, native responses, accounting,
transport metadata, original patch text, and unchanged-state inspections.
The local original is `runs/maintenance-contrast-live-01.json`.

- Parent protocol: `a6950b007760bb4971d53afa30323bacfdff036fcfafdaf6794228f0855e2e9e`.
- Frozen source: `85f9392e27f20ae6e9d2d4dc707723b06d945929`.
- Archive SHA: `783d037053a552bd6f877301af76d3f837aa2c2609f3cb0dd0a288964c9244c7`
  (76,972 bytes); original JSON SHA:
  `8fbc3f24a931b379c34031bae1aab93740db5a42e62208a9306056dbb1f66886`
  (853,975 bytes).

**Two submitted/accounted GPT-4.1/OpenAI calls, $0.011594 reported cost total,
zero retries or unknown billing.** Fixed order was `case-b`, then `case-a`.
No additional proposal, repair, judge, provider/account query, or billing lookup
was used. Parent and child receipts remain consumed; unused budget is not spent
or transferred.

| View | Active claims before → after | Reported cost | Input / output tokens | Actual choice |
| --- | ---: | ---: | ---: | --- |
| case-b, append-only | 6 → 6 | $0.006144 | 2,472 / 150 | No-op |
| case-a, maintained | 3 → 3 | $0.005450 | 2,129 / 149 | No-op |

Both returned `baseRevision: 5`, empty accounting, and no operations. Both give
this exact sentence in their otherwise distinct rationales:

> No new synthesis, clarification, or consolidation is warranted without
> additional evidence or a change in interpretive context.

The full rationales remain in the archive and CUE record. The six-claim response
says retaining the current structure best serves readers by keeping attributions,
scope boundaries, and recoverable evidence paths; it does not identify particular
overlap and compare the utility of an alternative current view. The three-claim
response likewise emphasizes fidelity and avoiding unwarranted changes.

Both are mechanically valid no-ops. Each complete local state, including claims,
citations, source/claim history, aliases, projections, reader probes, revision,
and journal, stays exactly unchanged. Both recovery results remain
`not-exercised-no-change`. Semantic usefulness and fidelity remain **pending human
review**, not automatically passed because citations survived or nothing changed.

**The desired selective-maintenance behavior was not demonstrated:** there is no
model-selected consolidation, amendment, or retirement in either view. Both
responses condition consolidation on extra evidence/context despite the common
v0.5 instruction that lack of new sources alone does not justify no-op. This is
a concrete objective/representation-maintenance concern to investigate offline,
not proof of general model incapacity or a calibrated semantic failure label.
Same actions also need not have equal utility across inputs. The experiment
allows no-op and does not force the redundant view to hit a target count; whether
retaining its overlap is justified remains a meaning/usefulness review.

No prompts, reference meanings, proposals, or archived scores were repaired or
rescored after seeing the result. The original one-call no-op and the user's
narrow permission to integrate the automatic-retry restriction are unchanged.
A further attempt requires a fresh, inspected protocol and separate approval;
these results do not license resampling until a merger appears.
