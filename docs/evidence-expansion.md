# Bounded evidence updates and contradiction obligations

## Hypothesis

The [multi-pass investigation](multipass.md) showed why agreement is insufficient:
models can rightly reject an unsupported assertion while wrongly describing it
as contradicted. This experiment tests source expansion and a conditional evidence
compiler, rather than another round of whole-answer votes.

Four synthetic families each have one shared initial understanding, then three
counterfactual source-expansion branches. Initial model outputs are reused across
that family's branches, never resampled to choose a convenient starting state.
References are **proposed controlled expectations, not human-adjudicated gold**.
This is not a demonstration of autonomous canonical maintenance.

## Evidence state is not assertion warrant

Each hypothesis has separate positive and negative witness sets:

| Positive witness | Incompatible factual witness | Packet-relative evidence state |
| --- | --- | --- |
| Absent | Absent | Unestablished |
| Present | Absent | Supported |
| Absent | Present | Opposed |
| Present | Present | Contested |

A negative witness must establish an incompatible fact under matching scope.
Lack of evidence, withdrawal of an assurance, caution against inference, or an
unknown origin is not by itself that witness. These states concern the available
source packet, not universal world truth. Opposing testimony need not be true.
Jev assesses the actual narrative's **warrant** separately: a qualified account of
unestablished or contested evidence can be justified.

The compiler checks source IDs, declared scope, explicit supersession, and witness
structure. An origin guard follows declared lineage: unresolved roots remain
unestablished, known shared roots oppose a distinct-origin assertion, and known
distinct roots support it under the fixture assumptions. Retelling does not
create another origin. This is conditional metadata reasoning, **not automatic
verification of metadata or natural-language entailment**.

Only explicit same-scope supersession changes the current source view. Recency
alone does not settle conflicts; cross-scope supersession is ignored and visible.
Historical sources and spans remain in every subsequent view. These fixtures use
narrow comparison-scope records: the source-level projection is not permission to
retire every independently valid clause in a heterogeneous real document.
Raw proposed states,
filtered current-scope states, provenance-guarded states, and rejected witnesses
are retained separately, never silently substituted into the original model output.

## Controlled families

- **Origin recovery:** a linked run log establishes distinct origins, a shared
  origin, or remains unavailable. Missing lineage must not become a shared-origin
  conclusion.
- **Environment scope:** a deployment record confirms production-west behavior,
  contradicts it, or covers only production-east. Staging cannot supply a current
  production-west witness.
- **Conflict and withdrawal:** a retrieved notice explicitly supersedes the old
  notice, conflicts without supersession, or withdraws an assurance without
  establishing its opposite. The latter leaves no current positive or negative
  availability witness.
- **Parent recovery:** a parent provides both location and date, only location,
  or is unavailable. Preserve newly established partial meaning without inventing
  the remaining date from statement time.

Scope identities and lineage fields are manually declared controlled metadata,
not already-solved text extraction. In particular, the generic exception scope
identifier does not encode the hidden location or date. Hypotheses name possible
facts to evaluate and are explicitly not treated as factual premises.

## A forked, fixed-depth process

Each family first receives:

1. GPT-4.1 initial understanding and witness proposal, using initial sources only.
2. An independent Jev probe of evidence state and narrative warrant.

Each of its three branches then receives:

3. Bounded exact-reference expansion and GPT-4.1 revision.
4. A Jev probe without seeing the prior probe's decisions.
5. A Gemini 2.5 Pro source-span audit and narrative critique.
6. One GPT-4.1 reconciliation using that untrusted audit and original sources.
7. A final Jev probe; no loop until agreement.

The source auditor classifies **every source span for every hypothesis**, not just
the spans the reasoner chose. It sees the proposed narrative but not the reasoner's
witness labels or Jev opinions. Code derives a second evidence ledger from that
audit. An `unclear` audit span is retained explicitly, not promoted to a fact.
Source IDs replace copied quotations; schemas are authored in CUE, specialized to
visible IDs, and compiled back to CUE for local validation.

All model proposals remain derived data, not source evidence. A later valid result
cannot hide an unavailable initial state or audit: complete trajectories are counted
across both shared initial passes and every branch pass. There is no canonical
acceptance, source deletion, or knowledge-retirement path.

## Retrieval is a bounded visibility change

The local executor follows only explicit `references`, `replyTo`, `originFrom`,
`derivedFrom`, and `supersedes` links. Limits are two added documents, two hops,
and 4 KiB of added serialized source data. Logs distinguish missing IDs from
hop/document/byte exhaustion. An unlinked related distractor is never fetched.

Deterministic closure is precomputed and frozen for the controlled experiment;
models see the expanded view only after the shared initial phase. Initial schemas
cannot cite future spans. Catalog bodies and provisional expectations never enter
initial model requests. This is an exact-reference baseline, not vector discovery
or evidence that an unavailable record does not exist elsewhere.

## Execution and boundaries

There are **68 planned calls**: eight shared initial calls plus sixty branch calls,
with local ceilings of 80 calls and $5. Roles are Jev, GPT-4.1, and Gemini 2.5 Pro.
The auditor uses a declared 2,048-token reasoning budget within an 8,000-token
output bound; other generative calls have a 4,000-token bound. Provider fallback
and retries are disabled. The shared ledger reserves actual output bounds and
stops on unknown accounting. Local limits are not provider-enforced spending caps.

```sh
# Freeze only; no credentials or network.
nix develop --command just evidence-expansion runs/expansion-prepared.json

# Explicit paid opt-in; token is loaded without being displayed.
direnv exec . python -m scripts.evidence_expansion --live \
  --budget-usd 5 --max-calls 80 --output runs/expansion-live.json
```

## First preserved run

[`first-evidence-expansion.json.gz`](../experiments/judgment/results/first-evidence-expansion.json.gz)
preserves **68 calls for $0.520824384**, with twelve structurally complete
trajectories. Across fifteen branch hypothesis-state cells, matches to the
provisional expectations were:

| Representation | Matches / 15 |
| --- | --- |
| Expanded generative witness compiler | 8 |
| Expanded Jev evidence probe | 15 |
| Gemini source-audit compiler | 14 |
| Audit-informed generative witness compiler | 9 |
| Final Jev evidence probe | 15 |

These are development contrasts, not estimated population accuracy. The important
failure is **representation divergence**, not simply bad prose. For example:

- The partial parent yields a correct narrative: Oriel annex is known, the date
  remains unknown. Yet the reasoner puts warnings against inventing a date in
  `negative`, which compiles into opposition to May 16.
- The superseding closure yields a correct closed-room narrative. Yet the reasoner
  puts the closed-room witness in `positive`, and the old open-room witness in
  `negative`: polarity relative to its *conclusion*, not the unchanged hypothesis.
  Filtering the historical witness leaves an inverted supported state.
- Both the reasoner and Gemini can put withdrawal into the negative-witness bucket
  despite explicitly recognizing that withdrawal does not establish closure.

Thus a model can understand uncertainty in prose and still serialize it into an
incorrect machine-facing fact. A warrant verdict does not validate proof polarity;
audit feedback does not ensure the next serialization obeys it. The compiler is
not authorized to convert these proposed witness assignments into world facts.

## Separately frozen schema-language control

After observing those failures, a **separate twelve-call control** reuses all twelve
original reconciliation user contexts byte-for-byte, including their original
untrusted audits. Model, provider, temperature, output limit, sources, and compiler
are unchanged. Only schema/instruction language changes: hypothesis-relative
`supports_hypothesis` and `incompatible_fact_spans` replace `positive`/`negative`,
with explicit directional descriptions. Property position is preserved. The slot
adapter renames keys only; raw control output and original outputs stay intact.

This is an adapted development diagnostic, not held-out testing or a clean isolation
of field names from descriptions and instructions. It does not retry or replace the
original run. Its protocol and all actual request bodies are frozen before calls.
It has a $0.50 local ceiling and twelve calls; code checks that combined planned
calls and budget fit the original investigation's 80-call/$5 ceilings. There is no
further repair round, and new narrative warrant is not separately probed. This is
a per-plan check, not a global cross-invocation or provider-side spending lock.

```sh
# Offline by default; --live is a separate explicit opt-in.
nix develop --command python -m scripts.evidence_direction \\
  --output runs/direction-prepared.json
```

The [preserved control](../experiments/judgment/results/first-witness-direction.json.gz)
completed twelve valid calls for **$0.10409**. Compiled matches improved from
**9/15 to 13/15**: four corrections, no regressions. Unknown location/date with an
unavailable parent, unrelated-region evidence, and the reversed closure witness
improved. The remaining failures are the partial parent's unknown date and the
withdrawn assurance. In both, the new narrative correctly says unknown while
`incompatible_fact_spans` still contains epistemic or withdrawal statements.
Clearer language helps, but does not establish reliable semantic serialization.

The investigation stops at **80 calls and $0.624914384 provider-reported cost**.
There is no further repair round. Original and control request/response bodies,
outputs, costs, failures, and reference caveats remain independently inspectable.

## Constructive countermodels and the next proof obligation

[Post-hoc CUE controls](../experiments/judgment/proof-controls.cue) show consistent
possible worlds, not extracted facts or claims about the actual exception:

- A May 16 effective date satisfies `date != May 14` while that date remains
  unestablished in the local packet. “Not the message date” does not exclude
  May 16, and lack of local knowledge does not make the world fact false.
- Access can be available while its prior assurance has been withdrawn. A source
  version/assurance act does not itself set the availability variable to false.
- The same production-east observation permits either production-west value.
  Different scopes are separate variables, not opposing votes.

The controls export concrete satisfying assignments; tests also verify that
same-variable `true`/`false`, or two distinct values for one effective-date field,
produce genuine CUE conflicts. These checks validate consequences of **manually
supplied logical translations**. They do not validate translation of source prose,
solve interval semantics, or permit globally conjoining contradictory sources.

Prefer source-centric extraction of typed facts and acts before hypothesis-relative
proof selection or rendering. The next bounded proof interface should require:

1. A stable target P binding: subject, predicate, scope, value, polarity, and modal
   level. Never silently rebind P to the conclusion of a newly written answer.
2. Separate source acts: world assertion, epistemic limitation, directive,
   withdrawal of assurance, and supersession. Withdrawing permission is not the
   same act as withdrawing an assurance about permission.
3. For an opposing witness, a grounded factual Q plus a checkable incompatibility
   between P and Q under the same binding. `not established(P)` is not `not P`;
   a different date/region must bind its actual value, not borrow the hypothesis's.
4. An explicit unresolved status when narrative, source probe, and compiled witness
   representations disagree. A justified narrative must not authorize a divergent
   machine fact. Preserve the source history and alternatives instead.

CUE constraint compatibility can check a correctly typed proposal; it cannot make
an untrusted semantic extraction correct. Fresh held-out fixtures and reviewed
interpretations remain necessary before any unattended acceptance or retirement.

## Reproduction and artifact boundaries

Protocol snapshots include source windows, hidden catalogs, deterministic retrieval
logs, schemas, reference status, models/providers, prompts, metadata, implementation
hashes, and limits. Every dependent request and response is retained with credential
redaction. Existing paths cannot be overwritten or resumed. Source and proposal
parent hashes make each fork and revision inspectable. No global-current guarantee
follows from evidence in a source window with known unread references.

## Source-centric specialist panel

This trial tests **division of responsibilities, not a vote**. Rather than ask
models to nominate support/opposition relative to a candidate answer, two blinded
roles extract source-centric typed assertions and acts. Code compares their
interpretations; an adversarial role looks for omissions and shared mistakes.

### Fixed roles and information boundaries

1. **Interpreter:** GPT-4.1 extracts a paragraph-anchored ledger from original
   correspondence and a bounded, declared binding vocabulary. It sees no evaluation
   questions, desired values, reference ledgers, or other model interpretations.
2. **Blind verifier:** Gemini 2.5 Pro independently extracts the same kind of ledger
   from identical source context, without the interpreter's output. Its reasoning
   budget is 2,048 tokens within an 8,000-token output bound.
3. **Adversarial auditor:** o3 reads original sources, both untrusted ledgers, and
   necessary mechanical checks. It assesses each role on every paragraph, including
   shared errors. It emits anchored critiques, not replacement facts. Its output
   bound is 8,000 tokens with medium reasoning; no temperature is requested because
   this endpoint does not advertise it.
4. **Deterministic checker/projector:** code checks literal grounding, binding and
   modal operands, declared scope/authority, scalar compatibility, and property-level
   source revision. Rendering exposes the same typed atoms, attributed to a role
   and source, rather than generating new prose with potentially divergent polarity.
5. **Evaluation-only source baseline:** Jev assesses neutral binding/value queries
   using original sources only. Its opinions never enter the panel or adjudicate
   disagreement. Different model families are controls, not independent evidence.

Eight fresh synthetic packets cover assurance withdrawal versus actual permission
revocation, unknown versus established effective dates, genuine conflict versus
property-scoped supersession, a different environment, and a source question mixed
with a directive and an established venue. They have twelve paragraph anchors and
seventeen evaluation queries. Interpretations are **provisional authored development
controls, not human-reviewed or held-out gold**. Optional equivalent annotations
are declared before calls; `other` atoms remain recorded but are not reference-graded.

### Conditional typed consequences

The experimental vocabulary has scalar bindings with supplied subject, property,
scope, time context, admissible canonical values, and source binding allowlists.
These are deliberately curated premises, **not solved entity linking, authority
verification, time extraction, or a production ontology**.

- World assertions contain `eq`/`neq` and a concrete literal present in the cited
  paragraph. Dates must be canonical calendar dates, not borrowed metadata times.
- Local epistemic limitations contain `unknown` with no world value. Questions and
  directives also do not carry world constraints.
- Permission grants/revocations are normative acts, not physical access observations.
  Code interprets their effect only for permission bindings under declared authority;
  revocation requires an interpreted prior grant in the named source.
- Assurance withdrawal removes the targeted prior assertion's current effect, not
  permission itself. Explicit supersession affects only the named binding in a
  source; other material facts in that source remain current.
- Original atoms and source paragraphs remain recoverable even when their current
  effect becomes historical. Rejected atoms are recorded, never silently repaired.

A concrete unequal scalar value can oppose a query; exclusion of another date does
not. Closed finite domains permit an exact complement inference. The checker does
not perform arbitrary theorem proving, alias resolution, interval interpretation,
or verification that the proposed atom really conveys the source paragraph.

### Shared-error controls and evaluation

Each packet also has a **predeclared shared-error audit control**. Two identical
manually authored candidate ledgers contain one mechanically admissible semantic
mutation: an unsupported world assertion, an omitted material atom, or an inverted
date exclusion. These are not actual model outputs. The auditor receives neither
the mutation location nor an indication of the expected response. Control results
are separate from real trajectories; they never repair or replace a model output.

There are **forty fixed calls**, with a local $5 ceiling, no retries, no fallback,
and no correction or consensus round. All dependent request bodies are checkpointed
before submission. Default preparation is offline; local limits are not global or
provider-enforced spending caps, and interrupted calls may still be billed.

Measure each extractor's structural availability, mechanical rejections, material
atom agreement with provisional paragraph references, and derived state comparisons.
Separately measure the auditor's challenges, misses, false challenges, unavailable
assessments, and detection of shared-error controls. A complete evaluation trajectory
includes all five paid stages; actual panel availability is reported separately.
A scalar verdict can match while the underlying ledger omits an epistemic limitation,
so whole-verdict matches are not the only score.

Disagreement, missing stages, mechanical rejection, or an audit concern yields an
explicit unresolved diagnostic. Even unchallenged agreement is labeled
`unchecked-agreement-not-acceptance`: neither a majority nor unanimity is a source
of truth. No canonical changes, source deletion, or retirement are authorized.

```sh
nix develop --command just source-panel runs/panel-prepared.json
# Separate explicit paid opt-in, using a new path; never an automatic rerun:
direnv exec . python -m scripts.source_panel --live \\
  --budget-usd 5 --max-calls 40 --output runs/panel-live.json
```

### Preserved panel trial

[`first-source-panel.json.gz`](../experiments/judgment/results/first-source-panel.json.gz)
preserves **40 calls for $0.372893466**, all with reported accounting and eight
structurally complete evaluation trajectories. No retries or follow-up repair
rounds were performed. The real panel cost $0.28764; shared-error controls cost
$0.08478; the source-only Jev baseline cost $0.000473466.

| Measurement | Interpreter | Blind verifier | Source-only baseline |
| --- | --- | --- | --- |
| Structurally valid packets | 8/8 | 8/8 | 8/8 |
| Paragraph atom agreement with provisional references | 10/12 | 11/12 | Not applicable |
| Mechanically rejected atoms | 1 | 1 | Not applicable |
| Derived query-state matches, after filtering | 17/17 | 17/17 | 17/17 |

The state counts are **not raw model correctness or population accuracy**. The
interpreter inserted a targetless withdrawal into a paragraph that only supplied
an assurance; the verifier added venue-unknown to a statement that left the venue
unchanged. Code rejected both atoms while retaining the raw proposals and source
history. Their removal did not change the seventeen tested state outcomes.

The real auditor challenged two of three discrepancies against provisional atom
references. Both challenged errors had already been rejected mechanically. There
was **no demonstrated incremental real-run state accuracy gain from the auditor**.
It did, however, identify the planted semantic fault in **all eight shared-error
controls**, challenging both identical candidate ledgers, with no false challenges
on unchanged control paragraphs. Saved rationales explicitly identify each planted
fault. These authored controls are not naturally occurring shared model errors;
none occurred against the provisional references in this small real-output batch.

Four packets remained `unchecked-agreement-not-acceptance`; two were held for
mechanical rejections and two for interpretation differences. No packet was
accepted as canonical. The original logs, ledgers, projections, critiques, opaque
provider fields, and all costs remain recoverable.

### What the panel exposed about its own contract

The remaining discrepancy and two apparent false challenges are not settled by
counting judges:

- For the different-environment paragraph, the interpreter placed the explicit
  production coverage limitation in prose limitations/rationale, not a typed
  epistemic atom. The reference requires that atom; the auditor treats the choice
  as stylistic. This exposes a preservation-policy and evaluation-unit mismatch,
  not an independently adjudicated semantic mistake.
- For the question/directive paragraph, both ledgers satisfy the predeclared
  optional-reference variants, but differ on explicit unknown. Exact ledger
  comparison still produces a conservative hold.
- The auditor challenges both calendar-check directives because `binding: b0`
  names an effective-date scalar rather than a reader action. The reference uses
  that binding as an *about-topic* link, not a scalar value assignment. Hence the
  two frozen `false_challenges` are relative to proposed references; they may also
  expose a real schema ambiguity. The control auditor independently raised the
  same concern alongside correctly identifying the planted false date assertion.

**Blind to answers must not mean blind to contracts.** The auditor received the
source context and ledgers, but not the extractor's full instructions. Before
another run, share precise IR semantics across roles, separate a source's expressed
uncertainty from an extractor's limitations, and distinguish an act's action object,
its topic, and any world binding it actually changes. Review which uncertainty
annotations are mandatory versus safely derivable. Do not silently amend the
saved references or reinterpret the original outputs to make the scores improve.

The result supports a bounded specialist panel as an **evaluation and stress-test
tool**, not an always-on production dependency or a consensus acceptance policy.
The next useful evidence is reviewed contracts and fresh held-out correspondence,
not more participants adjudicating these same examples.

### Offline interpretation-contract review — examples individually approved

The [exact eight-example review packet](interpretation-review.md) proposes the
shared contract before another live trial. Its CUE source separates source-stated
uncertainty, bounded-window coverage, and extractor-origin interpretation limits;
act topic links, action objects, prior targets, and world effects are distinct.
Equivalent encodings are judged by recoverable meaning and projection behavior,
not mandatory atom counts. Updated evidence can resolve a current binding while
leaving its earlier uncertainty recoverable in history and unrelated facts usable.

Each example includes exact synthetic source paragraphs, proposed material
interpretations, acceptable representation alternatives, forbidden inferences,
and current-versus-history projection obligations. The rendered Markdown is a
checked projection of CUE, not a separately maintained source of truth. A packet
hash binds policies and all examples; per-example hashes plus the policy hash
support explicit subset approval. Changes to reviewed meanings change the hashes.

The user walked through examples 01–08 and explicitly approved each interpretation.
The [separate decision record](../experiments/judgment/interpretation-approvals.cue)
binds those decisions to their exact content hashes. They are now user-approved
**development references**, not independent held-out gold. The broader policy text
has not been separately approved as a blanket rule. The proposal snapshot stays
unchanged; the checker verifies the decision hashes without granting approval itself.

```sh
nix develop --command just interpretation-review
nix develop --command python -m scripts.interpretation_review --render
```

These commands have no model or approval capability. Tests validate reference and
quote integrity, frames, ownership, act target kinds, and declared preservation
coverage; they do not prove prose entailment or equivalence. Approval comes from
the recorded user decisions, never from validation or merging a PR. The decisions
do not approve a paid protocol, authorize canonical changes, or rescore the previous
panel.

### Paired reviewed-contract transfer

**Hypothesis:** under a common operational contract grounded in the eight reviewed
examples, the panel can flag material errors missed by one extractor plus code
without needlessly withholding unaffected knowledge. Agreement earns no truth
credit. This trial does not causally isolate the contract change from other changes
relative to the original panel trial.

The [shared contract and protocol](../experiments/judgment/reviewed-panel.cue)
and [fresh synthetic threads](../experiments/judgment/reviewed-threads.cue) are
separate from the approved review examples. The new wire grammar and fresh authored
references are **provisional**, not another user approval or independent held-out
gold. All roles see the same contract; extractors see identical original context,
without peers, evaluation queries, reference interpretations, or future messages.
The auditor sees both proposals and mechanical diagnostics, never the references.

Seven threads each have eight multi-sentence messages, including distractions,
nonadjacent reply targets, derived digests, qualifications, and unrelated properties.
Each is independently extracted at a four-message prefix and an eight-message final
window; previous model output is not fed into the next extraction. This measures
paired source-window understanding, not a deployed incremental patch system.
One reply has an explicitly unavailable parent; the gap is reported, never fetched
or guessed into a scope/validity assignment.

| Thread | Material distinction |
| --- | --- |
| Drill date resolution | Earlier source-owned uncertainty becomes historical; question content is not confirmation |
| Regional coverage | Staging/east observations and a missing-parent reply do not establish production-west; backup location survives |
| Unresolved qualifier | Exactly one unidentified provisional date; topic-linked calendar request is not an assignment |
| Withdraw only assurance | Permission becomes unestablished, not prohibited; venue remains usable |
| Independent grant survives | Withdrawing a separate assurance does not revoke a live grant |
| Actual grant revoked | Normative permission under that grant ceases; no physical-door inference |
| Equal-authority date conflict | No recency/repetition resolution; unaffected venue remains available |

There are **14 snapshots, 32 binding assessments, and 32 query cells per extractor**.
Across the seven prefix/final pairs, nine binding-local material signatures are
unchanged, four scalar query states change, and eleven query states stay supported
(with their qualifications). These overlapping views are not independent samples
or independent meaning units.

The fixed schedule is **49 calls, a $5 local ceiling, zero retries**:

- GPT-4.1/OpenAI interpreter: fourteen calls, temperature zero, 8,000 output tokens.
- Gemini 2.5 Pro/Google AI Studio blind verifier: fourteen calls, temperature zero,
  8,000 output tokens including a 2,048-token reasoning budget.
- o3/OpenAI auditor: fourteen real and seven authored-control calls, medium reasoning,
  8,000 output tokens, no temperature parameter.

Every request pins its role's model/provider and disables fallback. The bounds are
128 KiB per request, 1 MiB per response, and a configured 120-second socket timeout
(not a hard wall-clock deadline; see the observed limitation below). These are
local safeguards, not global/provider-enforced spending caps. No unused prior
budget is an instruction to retry or extend the schedule.

Both main arms reuse **the exact same interpreter response and compiled view**:

1. **Single:** deterministic checks flag the affected binding only.
2. **Panel:** also flag unavailable verification, material disagreement, or auditor
   concern. Never substitute verifier facts or silently resolve disagreement.

A verifier-only diagnostic ablation separates comparison from the auditor's added
flags. Even an eligible view is an **untrusted proposal**, not canonical acceptance.
Flagged views, unaffected bindings, and full original history remain inspectable;
there is no publication, deletion, or canonical retirement capability.

[`reviewed_ir.py`](../scripts/reviewed_ir.py) implements the finite experimental
normal form, separate from the original panel's frozen interface. Source-owned
uncertainty, window-derived coverage, and extractor limits have distinct recovery
paths. Each binding's view explicitly exposes source-act links, historical records,
and separately owned extractor limits. Questions retain values without asserting
them. Directives retain an action verb, object, condition, and about-topic. Assurance withdrawal, actual grant
revocation, prior targets, ownership, and binding-local effects are distinct.
Ambiguous prior targets and partial revisions of multi-topic qualifiers are held,
not repaired. Literal/operand/authority checks remain necessary but do not establish
entailment. Bindings, canonical literals, scalar domains, authority groups, source
frames, and origin groups are **manually supplied premises**, not solved discovery,
authentication, or statistical independence.

Reference comparison normalizes equivalent `atoms`/`conditions` placement, identical
duplicates, declared-origin assertion repeats, binary complements, alternative
ordering, and action case/spacing/leading object article. It still distinguishes
source holder/frame, act arguments, and provenance. This bounded equivalence is
not a general semantic oracle. Counts of missing/extra signatures are **binding-local
memberships**; a shared qualifier may contribute to two bindings. `other` atoms and
out-of-vocabulary conversation remain in raw history but are not reference-graded.

Score raw material fidelity separately from mechanically filtered four-state query
results, unsupported/missing polarities, diagnostic flags, unaffected bindings,
state transitions, stage availability, and role/arm cost. A reference-faithful flag
is only a proposed unnecessary hold. A binding-coincident auditor challenge is not
proof that its stated reason identifies the actual discrepancy; inspect its text.
Unavailable stages remain in every planned denominator, with unknown billing
separate from known costs and reserved amounts.

The seven separately authored final-window controls include **three faithful
layout/duplication pairs** and **four identical shared semantic faults**: omit the
new production finding, invent a prohibition after assurance withdrawal, omit an
actual revocation, or omit one origin's conflicting date (including its repeat).
No control label, fault location, expected query, or repair enters the audit prompt.
These controls test sensitivity and conservatism, not naturally occurring shared
error prevalence. They never replace real outputs.

Preparation is offline and rejects an existing output path:

```sh
nix develop --command just reviewed-panel runs/reviewed-prepared.json
# Separate paid opt-in with a new path, only for the authorized frozen trial:
direnv exec . python -m scripts.reviewed_panel --live \
  --protocol-sha256 HASH_FROM_OFFLINE_PREPARATION \
  --budget-usd 5 --max-calls 49 --output runs/reviewed-live.json
```

Protocol snapshots bind role inputs, schemas, source windows, references, controls,
review decision hashes, implementation hashes, provider metadata, and limits.
Live execution requires the exact offline protocol hash, not just an unbound
`--live` flag. Hash matching grants no new interpretation or spending approval.
Earlier experiments and approvals remain unchanged. No retry, repair, fallback,
consensus loop, or resumption is implemented.

### Preserved partial transfer run

[`first-reviewed-transfer.json.gz`](../experiments/judgment/results/first-reviewed-transfer.json.gz)
preserves **21/49 submitted calls**, twenty accounted responses, and one request
without an accountably complete response. Known reported cost is **$0.458809**.
The unaccounted call returned an API-reported **504 timeout**, with a generation ID
but no usage/cost. It retains a **$0.160557 reservation**, not a reported charge.
One separate [read-only billing GET](../experiments/judgment/results/first-reviewed-transfer-billing.json)
returned 404 “Generation not found”; it generated nothing and was not retried.
Actual total billing remains unknown. Twenty-eight role calls were not attempted. The ledger
stopped without retry, replacement, continuation, or use of the remaining budget.
[Observations and hashes](../experiments/judgment/reviewed-observations.cue) bind the
archive to source commit `3bc99cc8d9c1` and protocol `56f768f9…7909f5`.

Only regional coverage, unresolved qualifier, and independent-grant survival were
attempted. The four other families are unavailable, not successes or semantic
misses. The two prefix/final snapshots for each attempted family give six extractor
outputs per role. Full planned denominators remain in the saved summary.

| Stage | Planned | Valid | Invalid report | Failed/unaccounted | Unattempted |
| --- | --- | --- | --- | --- | --- |
| Interpreter | 14 | 6 | 0 | 0 | 8 |
| Blind verifier | 14 | 6 | 0 | 0 | 8 |
| Real auditor | 14 | 4 | 2 | 0 | 8 |
| Authored control auditor | 7 | 2 | 0 | 1 | 4 |

Four of fourteen real-panel snapshots have all three valid reports; three of
fourteen evaluation snapshots also satisfy their control requirement. Availability
is not semantic correctness.

Both extractors match **16/16 available filtered query states**, with sixteen of
thirty-two planned cells unavailable for each role. Raw binding-signature agreement
is **8/16** for the interpreter and **9/16** for the verifier, again with sixteen
unavailable binding units each. Code rejects four interpreter atoms and two verifier
atoms without altering originals. Correct filtered states still hide raw typing,
provenance, and qualification discrepancies; these ratios are not truth accuracy.

All arms use the identical primary ledger. Counts below use **32 planned binding
units**, sixteen with no available primary, and provisional finite signatures—not
independent or adjudicated semantic errors.

| Diagnostic policy | Discrepant flagged | Discrepant unflagged | Reference-faithful flagged | Reference-faithful eligible | Primary unavailable |
| --- | --- | --- | --- | --- | --- |
| Single + code | 7 | 1 | 0 | 8 | 16 |
| Add blind verification | 7 | 1 | 2 | 6 | 16 |
| Add real audit | 8 | 0 | 4 | 4 | 16 |

**The extra full-panel flag is not demonstrated incremental error detection.** Its
cause is an invalid audit report, not a valid critique identifying the primary
coverage-annotation discrepancy. All three valid binding-coincident auditor
challenges concern atoms already rejected by code: two whole-sentence question
values in canonical-date slots and one fabricated negative permission literal.
No filtered-state accuracy benefit was demonstrated in the completed subset.

The known real-panel cost is **$0.422173**, versus **$0.084854** for the same primary
extractions (about five times as much). The verifier-only diagnostic costs
$0.263699. Authored controls add $0.036636 known cost plus the unaccounted request;
they are not included as real-panel protection.

Of nine planned unchanged final-window bindings, five have reference-faithful
primary views and four are unavailable. Single/code and verifier-only diagnostics
leave all five eligible. The full panel leaves three eligible and flags the
unaffected staging setting and backup location because their snapshot's audit is
invalid. Their source-qualified views remain inspectable; no knowledge was deleted.

#### What remains disputed or unavailable

- **Audit reporting ABI:** both regional audit responses return valid JSON with
  faithful labels, but put explicitly harmless observations in `issues`. The frozen
  validator rejects any role issue alongside faithful. The prompt spoke of
  *material* issues while the wire has no severity field. This is a reporting mismatch,
  not evidence that those factual judgments were false. No post-hoc salvage changes
  the saved scores; invalidity flags every binding in the snapshot.
- **Coverage representation:** both extractors add source-uncertainty annotations
  for explicit non-coverage disclaimers that the authored normal form derives as
  window coverage instead. The auditor calls these optional. Scope/ownership and
  the precise epistemic verb must be inspected before calling this an actual
  semantic error; a common instruction alone has not supplied an independent oracle.
- **Directive/topic materiality:** the verifier preserves “do not use its invitation
  as a visitor permission record for another event” from the catering aside. The
  reference treats that aside as outside the Oak-session vocabulary. The final
  auditor challenges the primary omission. This remains an unadjudicated about-topic
  and preservation question, not a proven false challenge or a new task assignment.
- **Controls:** one assessed planted omission is explicitly identified for both
  candidates; the other three faults were never attempted. One faithful qualifier
  placement/duplication control passes, with no challenges on ten assessed faithful
  role-binding comparisons across the two valid controls. The grant-duplication
  control fails at transport; another clean control and three faulty controls are
  unattempted. Unavailable controls are not detection misses.
- **Transport bound:** `urllib`'s timeout limits socket operations, not total request
  duration. A local status poll observed the last submitted checkpoint over 249
  seconds old despite the configured 120 seconds. The API error reports timeout;
  there is no per-call wall-clock trace or provider completion identifying its
  underlying phase or charge. The frozen helper remains
  unchanged; a true wall-clock deadline is future work, not a silent repair.

This partial trial **does not justify an always-on panel** or establish that a panel
cannot help. It shows real cost and availability penalties, a reporting-ABI problem,
and unresolved interpretation/reference choices. Clarify those distinctions offline
and review the disputed source meanings before another separately authorized paid
comparison. Do not retry this run to fill its missing cells. All eight prior example
approvals and all older result archives remain unchanged; canonical acceptance and
retirement remain disabled.

### Offline follow-up: explicit audit severity and meaning review

The prospective [`source-audit-report-v2` contract](../experiments/judgment/audit-report.cue)
now separates **material findings** from **non-material notes**. A faithful role
assessment can include non-material notes without blocking that binding; the notes
remain visible. Material findings require a material-error verdict for each affected
role, and a material-error verdict needs an anchored material finding for that role.
A finding about one binding/role cannot block an unrelated binding/role. Unclear or
unavailable assessments still block their affected role/binding; an unresolved
possible defect must not be disguised as a harmless note.

[`audit_contract.py`](../scripts/audit_contract.py) checks identities, availability,
explicit severity, and verdict/finding consistency, and exposes an **audit-component
signal only**. It cannot clear mechanical/verifier holds, replace primary facts,
validate entailment or severity classification, or accept canonical knowledge.
General limitations remain visible without becoming world facts or automatic
whole-document holds. Tests deliberately show that a wrongly classified or unsupported
claim can remain structurally valid: this is an interface check, not a semantic oracle.

This is **prospective and offline**, not wired into the frozen live runner. No old
response is assigned severity automatically; the two invalid historical audits stay
invalid under their original contract. Requests, costs, availability, scores, and
archives are unchanged. The socket-timeout limitation is also unchanged; no technical
fix here silently alters a completed experiment's implementation.

The [two exact source-meaning proposals](transfer-review.md) address coverage versus
personal ignorance and the invitation-use directive's topic/materiality. They reuse
the existing review notation, with quotes, source metadata, and windows checked
against the immutable archive. Each example has a content hash, acceptable recovery
alternatives, forbidden inferences, and current/history obligations. Review one at a
time; **both remain pending**. Mechanical validation, merging, and the earlier eight
approvals do not approve these proposals, a general policy, or new paid execution.

```sh
nix develop --command just audit-contract
nix develop --command just transfer-review
nix develop --command python -m scripts.transfer_review --render --example 01-coverage-frame
```

These commands have no model, approval, or rescore capability. No paid calls were
made in this follow-up. Semantic decisions require an explicit user response tied
to the reviewed example; they are not inferred from code passing its tests.
