# Does better retrieval produce better understanding?

## Frozen hypothesis

With the reasoning model, provider, prompt, and sampling settings fixed, higher
material-evidence coverage should improve preservation of scope, exceptions,
uncertainty, and provenance. Measure two links separately:

1. Did retrieval supply the enumerated material sources?
2. Did the model use its supplied evidence to produce a faithful understanding?

More retrieved sources are not automatically better. Redundancy, misleading
neighbors, and a model ignoring a present caveat can break the second link.
The strongest useful result would be bounded retrieval matching the full-case
control on fresh variants—not merely citing more documents.

## Cases and conditions

`experiments/understanding/cases.cue` contains three newly authored variants:
Orchid payout recovery, Cedar archive access, and Quill telemetry compatibility.
There are 21 synthetic source artifacts and 14 provisional meaning-level checks.
They were not used in prior model runs, but are author-created variations, not
an independently curated or statistically representative holdout set. Review
the rubric before treating it as a benchmark.

All held-out source identities are opaque and globally unique. The global index
contains the earlier corpus, 1,024 adjacent-topic distractors, and these sources.
Only source text and query text go to the embedding model. Expected source sets,
case partitions, and outcome labels do not go to retrieval or generation.

Three primary evidence conditions:

- **Full:** every source from the target case. This is an *oracle-scoped relevant
  evidence control*, not the whole global corpus and not a deployable retriever.
  It is exempt from the bounded evidence byte cap.
- **Vector:** greedily fill the evidence byte budget from up to 100 cosine-ranked
  candidates, without relationship expansion.
- **Vector + links:** four vector seeds, expanded up to three hops through raw
  reply metadata and model-proposed relationships, under the same byte budget.

A raw-links-only retrieval diagnostic is also reported without extra generation
calls. Existing hand-authored knowledge links are deliberately ignored. Source
metadata, anchors, reply targets, and event times count against the 1,800-byte
bounded evidence budget. Selected sources are sorted by identity for every arm,
so presentation rank order is not an additional treatment. Query wording is
identical across the three conditions.

## Relationship construction without the expected graph

Before query answering, the linker processes incoming source identities in
batches of three. For each incoming source, it sees four vector neighbors and
explicit reply neighbors from the global index. It does not receive the user
query, case partition, or rubric. Batches are sorted opaque identities, not
fixture groups. This models a small new-source linking pass, not a scalable
ontology induction system.

The model may propose at most two useful links per source with exact quotations
from both endpoints. Unknown endpoints, fabricated spans, duplicate pairs, and
links outside the supplied candidates are rejected. Invalid batches are retained
as failures, not retried until they look good. Empty link output is allowed.
These are **proposed discovery links**, not verified agreement/contradiction or
canonical truth. Generated relationship labels/rationales are not sent to the
reasoner: only the selected raw source records are, isolating evidence selection
from extra model-written coaching.

## Fixed generation, blinded provisional evaluation

The CUE plan pins a separate role assignment:

| Role | Model | Provider constraint |
| --- | --- | --- |
| Link construction | `openai/gpt-4.1-mini` | `openai` |
| Understanding synthesis | `deepseek/deepseek-v3.2` | `deepinfra/fp4` |
| Provisional semantic judge | `openai/gpt-4.1-mini` | `openai` |

Assignments are per experiment, not global defaults. The reasoning model uses
one generic prompt, JSON/CUE output contract, temperature zero, and output limit
across all conditions. Source text is untrusted data. Its response contains a
compact summary, scoped/source-linked claims, bounded directives if justified,
and uncertainties. It is **not** a canonical patch or production knowledge write.

After every generation has finished, the judge receives the question, candidate
understanding, full case evidence plus any additional cited sources, and the
same rubric. It is not given arm, model identity, retrieval scores, candidate
pool, or generation context size. It returns pass/fail/uncertain per requirement,
exact supporting source quotes, exact candidate spans for passes, and separately
identified unsupported statements. Missing/invented checks and fabricated quotes
are rejected. An omission may have an empty candidate quote; a pass may not.

Judge output is provisional, not an entailment proof or human ground truth.
Exact quotes validate traceability, not semantic correctness. Human review is
still necessary, especially for unsupported claims, omissions, and ambiguous
wording. An uncertain judgment does not count as a pass. Unsupported findings
remain separate from requirement pass fractions; a fully passing sample needs
all passes **and** no unsupported findings.

Case order is deterministic, and condition order rotates through a Latin square.
Judge order is independently hash-ordered. Calls are stateless. Byte-identical
generation or judging inputs reuse the same sample rather than manufacture a
treatment difference through nondeterministic duplicate calls. All repetitions
and reuse are recorded. Temperature zero does not freeze vendor weights or make
an API deterministic.

## Run it

```sh
# Default: freeze the protocol only. No network, generation, or fake quality score.
nix develop --command just understanding runs/understanding-plan.json

# New held-out index; no reasoning/judging calls in this phase.
direnv exec . python -m scripts.understanding --embed \
  --budget-usd 0.02 --max-calls 40 \
  --cache runs/understanding-vectors.json --output runs/understanding-index.json

# Execute the fixed comparison using the versioned role assignments above.
direnv exec . python -m scripts.understanding --live \
  --budget-usd 0.20 --max-calls 30 \
  --cache runs/understanding-vectors.json --output runs/understanding-live.json
```

Use new report/cache paths. `--noise` must match the index construction. Override
role assignments with `--reason-model` / `--reason-provider`, `--link-model` /
`--link-provider`, or `--judge-model` / `--judge-provider`; each change produces a
new protocol. This experiment requires a different judge model from the reasoner.
The initial embedding adapter remains `openai/text-embedding-3-small` at 512
dimensions. No Jev call is needed for this particular comparison.

Before any live calls, the report freezes source snapshot, raw graph, case
partitions, rubric, prompts, sampling parameters, role/provider bindings, CUE
contract hash, and implementation hashes. The protocol has a SHA-256 identifier.
No rubric is adjusted after observing results. All local artifacts live under
ignored `runs/`; compact observations can be added to the versioned experiment
without changing the protocol's inputs or code.

There are at most seven link calls, nine generations, and nine judgments with
these cases; identical inputs can reduce that. Embedding calls have a separate
budget. There are no automatic retries or replacement samples. Unknown/BYOK
billing and transport failures stop the run; invalid known-billed outputs remain
explicit failures. Summaries show planned versus judged counts, status counts,
and only complete three-condition pairs for paired comparisons—never silently
exclude failures. Stage traces contain models, provider constraints, request and
system hashes, usage, cost, and concise statuses, not credentials or raw bodies.

Rate filters, request/output limits, call limits, and local reservations are not
a provider-enforced total-spend guarantee. Use a limited-credit OpenRouter key.
The existing Python transport has a 30-second timeout and refuses redirects;
timeouts can still be billed. CI uses controlled vectors, abstaining fake model
responses, and uncertain fake judges to test mechanics, not confirm the hypothesis.

## Interpreting the result

Compare per-case enumerated-source recall with provisional rubric results, not
just arm-wide averages. Missing an enumerated source does not necessarily mean
missing its meaning: another source may independently provide it. Conversely,
complete enumeration does not prove all relevant evidence was enumerated. The
rubric can be incomplete or overly strict; preserve that limitation rather than
quietly editing it to fit output.

Three variants, a single sample per distinct input, author-written rubrics, and
an automated judge cannot statistically establish the hypothesis. This tests
one-shot understanding synthesis, not autonomous history-preserving compaction,
incremental convergence, or safe bounded-context retirements. Keep the workbench's
preservation envelope and canonical commit safeguards unchanged until broader
human-reviewed evaluation warrants altering them.
