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
are rejected. An omission may have an empty candidate-span list; a pass may not. Each span
must be a contiguous substring; separate excerpts must remain separate entries.

Judge output is provisional, not an entailment proof or human ground truth.
Exact quotes validate traceability, not semantic correctness. Human review is
still necessary, especially for unsupported claims, omissions, and ambiguous
wording. An uncertain judgment does not count as a pass. Unsupported findings
remain separate from requirement pass fractions; a fully passing sample needs
all passes **and** no unsupported findings.

Case order is deterministic, and condition order rotates through a Latin square.
Judge order is independently hash-ordered. Calls are stateless. Byte-identical
generation or judging inputs reuse the same success or failure rather than
manufacture a treatment difference through nondeterministic duplicate calls. All repetitions
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

# A separately versioned judge-only audit; no retrieval, links, or answers rerun.
direnv exec . python -m scripts.understanding \
  --audit runs/understanding-live.json --budget-usd 0.10 --max-calls 9 \
  --output runs/understanding-audit.json
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
exclude failures. Submitted calls are checkpointed before network I/O so an
interrupted call is not silently considered unsent. Stage traces contain models,
provider constraints, request/system hashes, usage, cost, and concise statuses.
Parsed rejected model values are retained with known-token redaction for diagnosis;
HTTP headers and raw provider bodies are not logged. An audit hashes its parent
answers, verifies unchanged cases/evidence/generation treatment, preserves parent
statuses, and creates a new measurement—it does not replace the original failures.

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

## First observations — November 22, 2026 (UTC)

The v1 implementation and rubric were pushed in draft PR #7 before the run.
Generation protocol: `65e8d424898dbaed33b70297fb17bffccad739dc0ead0e7643688cdc4e494820`.
A 1,078-document index was built, seven linking calls proposed 33 mechanically
validated discovery links, and all nine understandings were generated. Existing
hand-authored knowledge edges were not used.

| Variant | Vector source recall | Learned-link source recall | Inspection of the resulting understanding |
| --- | --- | --- | --- |
| Payout recovery | 4/7 | 7/7 | Both retained the core ledger/email/manual-versus-scheduler distinction; the additional source identities did not imply proportionally more useful meaning. |
| Archive access | 5/7 | 6/7 | Expansion recovered the staff-only correction. The vector-only answer called application of that exception to visitors ambiguous; the linked answer removed that ambiguity. |
| Telemetry compatibility | 5/7 | 4/7 | Expansion displaced the desktop-only test-suite source. The linked understanding omitted that test-coverage boundary. |

Full-case recall was 7/7 for every variant. All three oracle-scoped full contexts
also fit within 1,800 bytes in this trial; their advantage was relevant evidence,
not a larger actual context window. Averaged across variants, bounded
vector recall was 66.7% and learned-link recall was 81.0%. **The change was not
uniformly positive**, and these are source-identity coverage metrics, not
understanding scores. Link construction and context packing remain experimental;
an edge being useful for discovery does not mean it deserves scarce context
before a higher-ranked material source.

Even the full-case archive answer omitted the detached `Stop.` as unresolved
context, despite receiving it. Better retrieval cannot make a reasoning model
preserve evidence it chooses to ignore.

### Judging failures are part of the result

The initial judge returned IDs instead of citation objects and spliced separate
candidate spans into a single quote. Its first three recorded judgments were
rejected. The harness then interrupted the run during judging; there may have
been one additional in-flight billed call. A separate diagnostic on a previously
unassessed condition confirmed the format problem without regenerating answers.

The v2 **judge-only** audit reused the nine original understandings with unchanged
source evidence and rubric. It changed citation/span formatting, separated the
rubric's supporting IDs from output citations, and clarified that unanswered
uncertainty is not automatically an unsupported assertion. This was a new,
post-diagnostic evaluation method—not a replacement for the original study.
Audit protocol: `ef4ba09c746af4bd0b58561fc8a675caa9abf88491485dd858a6242f55891d44`.

Six of nine audit judgments passed structural/span validation; three did not.
Only one variant had a complete three-condition set of accepted judgments. The
accepted judgments are **not calibrated semantic scores**:

- The judge falsely passed preservation of the missing `Stop.` using unrelated
  uncertainty sentences about visitor arrangements. Both candidate and source
  quotations were real; the claimed semantic relationship was false.
- Some `unsupported` entries described an explicitly stated uncertainty as
  *appropriate* in their own explanations. Their classification contradicted
  their rationale, even after the generic prompt clarification.
- Requirement pass fractions on accepted rows were 100%, but inspection found
  these errors. That number must not be presented as semantic accuracy or as
  confirmation of the hypothesis.

The captured false-positive excerpt is in
[observations.cue](../experiments/understanding/observations.cue). The
[data-only result artifact](../experiments/understanding/results/first-comparison.json)
preserves all nine selected contexts and understandings, available judgments,
link proposals, request/accounting traces, and protocol lineage. It is derived
experimental data, not independent world evidence. Three rejected audit payloads
were not retained by the then-current post-validation code; they were not
resampled. Future runs now retain those parsed proposals and cache identical
failures as failures rather than seeking a better sample.

Logged charges total **$0.04811952**, including the index, original recorded
calls, diagnostic, and judge-only audit; an interrupted in-flight call may add an
unrecorded charge. There were no additional linking or generation calls during
the audit. No case requirement was rewritten to make a model pass.

### Assessment and next experiment

This is **mixed qualitative evidence, not confirmation**. Recovering evidence
helped one ambiguity; expansion hurt another neighborhood; full evidence still
failed to preserve a tiny intervention. Source-count recall can also overstate
loss when several sources express overlapping information. The payout rubric
explicitly allows omitting a redundant retelling, yet its enumerated source set
still includes that retelling. That denominator is not a minimal sufficient
set of facts.

The frozen `Stop.` requirement may itself be too strict for a question-focused
answer when raw evidence is retained elsewhere: preserving an unresolved source
in knowledge/history is different from mentioning it in every answer. The judge
still falsely claimed the candidate addressed it, but that does not establish an
irreversible product-level loss. A future reviewed rubric should separate those
contracts rather than retroactively change this result.

Before claiming better understanding numerically, calibrate the judge on
reviewed pass/fail/uncertain examples—including these false positives—and make
source versus meaning coverage explicit. Then compare context selection policies
on new frozen variants, with human review and repeated samples. Do not tune this
rubric or reroll these answers until they look favorable.

The next [offline review and calibration draft](calibration.md) inspects all nine
saved answers, proposes meaning-level support alternatives, and separates answer
requirements from history retention. It is an unblinded development draft pending
user review, not a replacement for this frozen rubric or a new accuracy score.
