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
errors. No result authorizes canonical acceptance, retirement, or a human task.

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
can still be billed; the $5 local limit is not a provider-enforced cap. No tokens
are printed or stored. Default preparation and all CI tests are offline.

Review the whole evidence trajectory, not merely whether the last pass agrees
with the proposed reference. A later correction can be useful; a later regression
or unresolved disagreement is equally important. Expensive reasoning is warranted
when it improves preservation and auditability, not just because it adds passes.
