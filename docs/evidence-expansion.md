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
