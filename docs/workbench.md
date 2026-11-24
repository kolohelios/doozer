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

The command reads only the saved `state`, not private evaluator rubrics or model
traces; it caps input at 4 MiB, has no live option, and will not overwrite an
output. The output contains source/claim payloads and is not a privacy-redaction
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
two mechanically valid layouts; no model adherence or semantic improvement has
been measured. The archived v1 protocol remains a rejected result, not a retry.

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
