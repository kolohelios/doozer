# Jev as one pass in a deeper evidence process

## Hypothesis and limits

The ten [split-judgment controls](judgment.md) suggest Jev is useful, but their
criteria already named the desired meanings. Matching them does not establish
that Jev follows source evidence rather than recognizing answer wording.

This experiment freezes **18 fresh synthetic packets in six families**. Each
family keeps the candidate unchanged across three counterfactual source worlds.
The criterion stays neutral: no source-specific desired answer is included.
Families cover execution path, visitor scope, firmware versus simulation,
effective time, independent origins versus echoes, and epistemic self-limitations.
Sources are paragraph-length messages, not assumed one-word correspondence.

Reference labels are **proposed controlled-fixture expectations**, not newly
user-approved labels or independent human gold. They are frozen before calls and
never rewritten to fit outputs. These are development diagnostics, not a
population accuracy estimate. The older approved calibration set and all earlier
results remain unchanged. Alternative worlds are separate packets, not sources
to combine into one knowledge base.

## Fixed depth, not repeated voting

Every packet receives these seven passes exactly once:

1. **Direct Jev:** whole-candidate assessment from original evidence only.
2. **Claim-level Jev:** multiple typed questions classify each exact candidate
   sentence and nominate a primary source-span anchor. No whole verdict is shown.
3. **Blind analyst:** GPT-4.1 assesses every claim and the whole candidate without
   seeing Jev outputs. It distinguishes world claims, epistemic limits, and
   instructions, and identifies material issues.
4. **Skeptic:** Claude Sonnet 4.5 examines the raw packet and the earlier proposals,
   looking for false acceptance *and* unjustified rejection. It need not disagree.
5. **Jev re-adjudication:** revisits original evidence after the argument audit,
   returning a whole verdict, per-claim relations, and evidence nominations.
6. **Source-order control:** repeats the direct question with source order
   reversed, without seeing any earlier model outputs.
7. **Identical-input control:** repeats the exact direct request once, regardless
   of its result, to expose response variability. It never replaces a result.

There are **126 planned requests**, capped at 140 calls and $5 locally. Caps are
not spending targets. There is no convergence loop, automatic retry, majority
vote, or confidence averaging. Additional passes are arguments to inspect, not
additional independent witnesses. Distinct models do not guarantee independent
errors; even shared explanations can collapse “unknown” into “false.” No result authorizes canonical acceptance, retirement, or a human task.

The source-order control is informative only for packets with multiple sources;
two single-source packets are explicitly marked no-op controls. Repetition and
order sensitivity are reported separately. One repeat is a diagnostic, not a
calibration curve or a statistical replication study.

## Evidence packets and exact references

Candidate sentences are lossless initial claim cards: all non-whitespace content
and negation survive. Sentence splitting is not a general solution to atomic
claim interpretation. Source sentences receive immutable local span IDs.
Generative audits select those IDs instead of copying quotations; the original
text remains reachable. Native Jev questions nominate one anchor, not a complete
proof bundle for a multi-part claim. No selected ID mechanically proves entailment.

The analyst and skeptic use strict provider JSON Schema authored in CUE. The same
specialized schema is imported back into CUE for local validation. Complete claim
membership, source IDs, nonempty rationales, and factual anchors are checked.
Legitimate epistemic statements do not require an irrelevant world-source quote
about a storage operation. Invalid outputs are retained and do not trigger a
replacement call. Later passes see their failure status, not a silently repaired
report.

All passes retain the same original source packet. Earlier model reports live in
an explicitly untrusted proposal section; they never become source evidence or
independent corroboration. Re-adjudication changes, analyst/skeptic disagreement,
and internally contradictory pass judgments are visible rather than collapsed
into an authoritative final score.

Local mathematics reports missing reply targets, explicit echo edges, and declared
origin groups. Different document identities do not establish different origins.
Declared distinct origins in these fixtures mean separate first-hand observations,
not statistical independence or proof of unrelated failure modes.

## Models and current API research

- Jev: `typesafe/jev-1.14`, provider `typesafe`, native Decisions endpoint.
- Blind analyst: `openai/gpt-4.1`, provider `openai`.
- Skeptic: `anthropic/claude-sonnet-4.5`, provider `anthropic`.

Public endpoint metadata snapshots are retained under
`experiments/judgment/metadata/`. The current Decisions reference confirms multiple
typed questions per request. This experiment uses `choice`, including per-claim
relations and span nominations; it does not pretend Jev generates explanations.
The API also documents `noul`, `score`, `box`, and a separate extraction API, which
are not evaluated here. Endpoint metadata lists a 262,144-token Jev context and
$0.042/M input pricing; those are advertised capabilities, not measured quality
or capacity claims from this experiment. Price filters are pinned separately.

## Running and accounting

```sh
# Offline preparation, schema compilation, and packet validation only.
nix develop --command just judgment runs/multipass-prepared.json

# Explicit opt-in; use a new output path and load the existing token safely.
direnv exec . python -m scripts.jev_multipass --live \
  --budget-usd 5 --max-calls 140 --output runs/multipass-live.json
```

The protocol freezes cases, provisional references, schemas, models/providers,
prompts, pass order, request-building implementation, metadata snapshots, and
limits before calls. Dependent request bodies cannot exist before prior outputs;
each actual body and its hash are checkpointed before submission. The pre-call
implementation is preserved separately from results.

One shared ledger accounts for both APIs. Reservations include actual configured
output-token bounds for generative roles. Provider fallback and redirects are
disabled; requests are capped at 64 KiB, responses at 1 MiB, and transport at
120 seconds per call. Missing or unknown billing stops the experiment. A timeout
can still be billed; the $5 local limit is not a provider-enforced cap. No credentials
are printed or stored. Default preparation and all CI tests are offline.

Review the whole evidence trajectory, not merely whether the last pass agrees
with the proposed reference. A later correction can be useful; a later regression
or unresolved disagreement is equally important. Expensive reasoning is warranted
when it improves preservation and auditability, not just because it adds passes.

## First run: source sensitivity and a typing boundary

The [lossless result archive](../experiments/judgment/results/first-multipass.json.gz)
contains all inputs, schemas, actual requests, raw responses, probabilities, costs,
and intermediate proposals. It decompresses to the original JSON byte-for-byte.
`observations.cue` records both compressed and uncompressed hashes. The published
live protocol is `644bc9fa3c01d519f496028129188030f9be2b08d921c666a6d132a57ec76421`;
its pre-call implementation is commit `cfbc5a1277b6`.

All **126 calls** completed with no retries for **$0.2850785** provider-reported
cost. References below remain provisional fixture expectations:

| Pass | Matching whole-reference decisions or proxy | Unavailable/invalid |
| --- | --- | --- |
| Direct Jev | 18/18 | 0 |
| Claim-level Jev proxy | 17/18 | 0 |
| Blind GPT-4.1 audit | 18/18 | 0 |
| Claude Sonnet skeptic | 12/18 | 6 |
| Jev re-adjudication | 18/18 | 0 |

The unchanged candidates received different appropriate verdicts under the six
families' changed sources. This provides evidence of source sensitivity beyond
candidate-wording recognition on these controls. It does not establish broad
accuracy, calibration, reliable performance on longer threads, or statistical
independence of repeated conditions. There are six families, not 126 independent
evaluation examples.

Direct and re-adjudicated **whole verdicts never changed**. We therefore observed
no whole-verdict accuracy gain from the deeper process on this set. Its value was
exposing a finer-grained boundary and missing audit coverage:

- For `epistemic-scope/v1`, claim-level Jev classified “Its location and effective
  date are not established here” as `not-established`, which the atom compiler
  interprets as an unsupported assertion. Both valid generative audits treated
  this as a warranted epistemic limitation. Re-adjudication selected `meta`.
  The whole verdict was already pass, and the relation confidence remained low
  (0.42 before, 0.40 after). This is a typing/taxonomy problem, not proof that an
  extra argument pass reliably repairs semantic reasoning.
- Claude returned `content_filter` / native `refusal`, with no completion tokens,
  on six benign packets. Their input charges total **$0.042681** and remain in the
  run cost. The cause is not established. We did not enable fallback, retry, or
  reword requests to obtain replacements.
- Among valid analyst/skeptic pairs there were **12 agreements and no differing
  whole verdicts**. Six pairs were unavailable, not semantic disagreements. The
  raw summary's `analyst_skeptic_disagreements` field includes status differences;
  do not interpret those six entries as opposing substantive assessments.

A more consequential qualitative warning appeared in `independent-evidence/v3`.
The second note says it **may** be a retelling; its origin is unknown. The analyst,
valid skeptic, and Jev recheck all labeled the independence assertion
`contradicted`, while explaining that there was no evidence of a separate drill.
Rejecting that unsupported assertion is appropriate, but lack of evidence is not
proof that the two notes share one origin. The packet math shows one declared
origin, one source with unknown origin, and no echo edge. Do not compile this
label into “no second drill occurred.” The relation taxonomy needs a separate
proof obligation for an incompatible world fact versus an unjustified assertion.
This is qualitative review, not an independently adjudicated per-claim score.

Only **12 trajectories** had all seven stages valid. Matching whole-answer labels
must not conceal that relation-level problem or six unavailable critiques. Stronger models plus strict structured
outputs and exact span selection produced valid reports without copied-quotation
errors, but those design changes and models were not isolated experimentally.

All 18 identical-request controls preserved their verdicts. All 16 informative
source-order controls did too; two single-source packets were no-op order tests.
These counts do not imply identical probability distributions.

### Local probability mathematics

The [post-hoc diagnostics](../experiments/judgment/results/probability-diagnostics.json)
compute Shannon entropy and Jensen–Shannon divergence in bits, entirely offline:

```sh
nix develop --command python -m scripts.judgment_math \
  experiments/judgment/results/first-multipass.json.gz \
  --output runs/multipass-probabilities.json
```

Raw probability vectors are preserved. Rounded vectors are normalized only for
these calculations; confidence is never substituted for missing probabilities.
Label iteration is sorted for reproducibility. There are no fitted thresholds
and these diagnostics did not influence any call or verdict.

- Maximum identical-repeat divergence: **0.0063 bits**.
- Maximum source-order divergence: **0.0152 bits**.
- Direct positive-versus-contradictory-source divergence: **0.572–0.960 bits**
  across the six fixed-candidate families.
- The retyped epistemic claim's entropy **increased from 1.292 to 1.464 bits**.

Thus source changes moved the output distributions much more than the observed
controls, but a selected category changing after audit did not remove ambiguity.
These are exploratory diagnostics, not calibrated truth probabilities or a
causal estimate of order effects from one repeat per packet.

The initial preview encoded a default integer budget `5`, while the explicit live
CLI encoded `5.0`. Scientific inputs and effective limits were equal, but those
JSON representations produced different digests. The live protocol was still
frozen before calls. Future preparation normalizes budgets; the archived protocol
and outputs are unchanged.

## What this suggests for the harness

Deep should mean a sequence of **typed, auditable transformations**, not more votes:
source structure and provenance → candidate acts and claims → source relations →
argument audit → bounded source expansion when justified → reconciled proposals.
Keep world assertions, warranted uncertainty, and method/self-limitation statements
distinct. Preserve unresolved arguments and unavailable stages even when the last
model supplies a decisive verdict.

Next, exercise genuine source conflicts and warranted uncertain answers, longer
distracting conversations, and source expansion with explicitly bounded context.
Those cases are more informative about the need for depth than repeatedly judging
these clear controls. Do not adopt a consensus loop or let the last pass become
permission to retire knowledge.

The next [bounded evidence-update experiment](evidence-expansion.md) introduces
shared initial states, source-expansion forks, separate support/opposition witness
sets, and conditional provenance/scope guards.
