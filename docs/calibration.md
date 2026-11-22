# Draft meaning review and judge calibration

## Scope and status

This is an **offline, unblinded draft inspection**, not an independent human
adjudication or a new model-quality score. It reviews all nine saved answers from
PR #7 against their immutable source snapshots. No answers, original checks,
results, or previous scores are rewritten. No embeddings, generation, or judging
calls are made.

The hypothesis here is about measurement: counting source identities can mistake
redundancy for missing meaning. Propose small, scoped meanings and alternative
support bundles, then separately inspect whether an answer actually preserves
them. Quote and pointer checks establish traceability, not semantic entailment.

These definitions were written after inspecting the saved outputs. Their counts
are diagnostic, not a preregistered performance estimate.

Everything in `experiments/calibration/` remains `pending-user-review`, including
12 development calibration examples. `semanticScoringEnabled` is false. Merging
the machinery does not approve the labels or make this development set held-out
judge gold. There is no judge execution or approval command in this tool.

## What was reviewed

The CUE files contain:

- **11 proposed required answer meanings**, plus conditional guards and a separate
  history-retention obligation: 17 units in total.
- **51 draft assessments** covering the applicable units for all nine answers.
- **12 calibration examples** spanning supported guidance, unsupported certainty,
  unjustified ambiguity, legitimate uncertainty, omission, criterion mismatch,
  and genuinely unsettled consumer contracts.

Each assessment has a reason and, where the claim is present, an exact quote at a
JSON pointer into the saved answer. Missing meanings are assessed against the
whole answer, not a fabricated quote. Candidate spans cannot point only at a
source quotation in a citation object. Each unit and example also links to
verbatim authoritative case-source spans.

The source JSON artifact is bound by SHA-256. Reusing a similar source from a
different case, silently modifying the artifact, omitting assessments, misquoting
an answer/source, or using an unanchored No as a support bundle fails validation.
These checks do not determine whether a draft semantic label is right.

## Meaning support is not a document-count score

`meanings.cue` gives required meanings one or more proposed `allOf` support
bundles. A bundle is available only when all named source spans are present;
contextual replies must include their target. Examples:

- The Orchid command documentation directly says the scheduler does not read
  the manual switch. Alternatively, the proposal plus its contextual No support
  the stated rejection. The second pair is not necessary when the direct
  implementation boundary is already present, and it is not proof of every
  runtime side effect.
- Normal Cedar catalog access needs the standing policy and date-bound context,
  not the policy alone. The manuscript restriction is a different meaning.
- Quill's desktop-only suite coverage needs the suite description. A generic
  objection to monitor safety does not identify what the suite actually tests.

Availability under these draft definitions:

| Variant | Full | Vector | Vector + learned links |
| --- | --- | --- | --- |
| Payout required answer meanings | 4/4 | 4/4 | 4/4 |
| Archive required answer meanings | 3/3 | 3/3 | 3/3 |
| Telemetry required answer meanings | 4/4 | 4/4 | 3/4 |

These are **proposed-support availability counts**, not accuracy or proof that a
bundle is minimal, complete, or logically sufficient. Conditional guards and
history obligations do not inflate the answer denominator. Do not average these
numbers into a semantic performance claim while labels/bundles are unapproved.

This view does not replace the original source-recall metric. It shows why its
67% → 81% change was not itself evidence of better understanding. Two variants
already had support for the main answer meanings in their vector context. Link
expansion then lost the suite-scope meaning in telemetry.

## Findings to adjudicate

| Saved output | Draft finding |
| --- | --- |
| Payout/full | Correct architecture and manual mitigation, but “automatic retries will send email” asserts more certainty than lack of this switch and one incident establish. |
| Payout/vector | Preserves the same core meanings with fewer source identities and uses the appropriately bounded “may be sent.” |
| Payout/vector-links | Preserves the core guidance, but source-independence semantics cannot be established merely by counting its two incident/retelling citations. |
| Archive/full | Includes the material procedure in the whole answer; its first directive alone omits annex check-in. Whether that directive must be standalone is unresolved. |
| Archive/vector | Correct main procedure, but invents ambiguity about extending a staff-only exception despite already receiving the staff-only observation and visitor escort notice. |
| Archive/vector-links | Makes that staff boundary explicit. This is consistent with a useful clarification, but the earlier context already had sufficient evidence; retrieval is not the sole explanation. |
| Telemetry/full | Retains the suite and rollout boundaries; “conditionally safe for desktop” needs review as shorthand versus an unjustified safety inference. |
| Telemetry/vector | Retains all four proposed answer meanings without needing the later objection pair. |
| Telemetry/vector-links | Omits the desktop-only test boundary, whose source was absent from generation context. This is an end-to-end omission, not proof that the reasoner ignored a supplied fact. |

An uncertainty is not automatically a hallucination. The current documentation
does not establish whether the scheduler limitation is permanent; saying that
this is unknown is legitimate. Conversely, a received staff-only exception plus
an explicit visitor escort notice should not create uncertainty about whether
staff practice authorizes unescorted visitors. The calibration examples keep
these two cases distinct.

The captured judge's false Stop pass is tested as **criterion attribution**:
unrelated uncertainty sentences do not establish that an answer addressed Stop.
That does not imply that every question-focused answer must mention the detached
intervention. The old frozen rubric is left unchanged; the draft separates
answering from future knowledge/history retention instead of retroactively
turning old failures into passes.

## Decisions needed before promoting labels

1. **Answer versus retained knowledge:** should an answer mention an unrelated,
   unscoped Stop, or should preservation be tested only in the inbox/history/IR?
   Proposed default: retention is a separate contract and is not assessed from
   these answer-only artifacts.
2. **Standalone directives:** must each directive contain every required step, or
   may it be a reminder embedded in a complete cited answer? The archive example
   contains the step in claims but not in its first directive.
3. **Safety inference:** is “conditionally safe for desktop clients” acceptable
   shorthand for limited test evidence, or should it remain a scoped test result?
4. **Dependent citations:** what output metadata demonstrates shared evidentiary
   origin? Two citations are neither automatically two independent proofs nor
   proof that lineage was preserved.
5. **Support alternatives:** approve or revise the proposed source bundles,
   especially inferring normal access from standing policy plus a one-day notice.

These are evaluation-contract questions, not new product task queues or requests
to resolve every uncertainty in the knowledge engine. The draft intentionally
uses `uncertain` / `not-assessed` rather than manufacture consensus.

## Inspect it without model calls

```sh
nix develop --command just calibration

# New paths only; the packet includes sources, all nine original answers,
# proposed support bundles, draft labels/reasons, and exact annotation spans.
nix develop --command python -m scripts.calibration \
  --output runs/calibration-draft.json --packet runs/calibration-review.md
```

The packet is a reproducible view, not another authoritative copy to maintain.
The CUE annotations and original result JSON are the owned, versioned inputs.
Existing files are never overwritten. A token in the environment changes nothing;
the command has no live mode and does not read credentials.

The JSON export separates `draft_expected` / `draft_reason` / provenance from each
sample's `judge_input`. Only that label-blind payload would be appropriate input
for a future judge test; never send the whole report or the expected label. Each
sample is marked development data, not a new held-out evaluation set.

Next, review these annotations and resolve the uncertain contracts in a visible
versioned change. Only then freeze an approved calibration version, test judge
false positives/negatives/abstentions against it, and use separately authored
held-out cases for performance claims. No further paid calls are justified by
this draft alone.
