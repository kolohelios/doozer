# Split meaning judgment, Jev, and vector diagnostics

## Hypothesis

The first [judge pilot](calibration.md#first-pilot-judge-not-reliable-enough)
confused what sources establish with what the candidate actually conveys. Test
whether separating those questions reduces false acceptance, and whether Jev
provides useful agreement/disagreement information. Mathematics supplies
independent diagnostics, not a replacement truth oracle.

This is an adaptation to ten known, user-approved development examples. It is
**not held-out evaluation**, and the new check-card decomposition is proposed,
not separately adjudicated unit-level gold. The original criteria, answers,
source contexts, whole-answer reference labels, and baseline artifact are not
changed. A success here would justify a fresh held-out experiment, not canonical
retirement or unattended semantic acceptance.

## Three signals, deliberately different jobs

For each of the ten saved contrast answers:

1. **Coverage:** `openai/gpt-4.1-mini` receives exact candidate sentences and
   decomposed requirements, but no authoritative sources. It marks each meaning
   conveyed, contradicted, absent, or uncertain and quotes the candidate.
2. **Grounding:** the same generative model receives all exact candidate sentences
   and authoritative sources, but no completeness requirements or coverage output.
   It assesses every sentence as supported, contradicted, unsupported, nonfactual,
   or uncertain. Splitting is deterministic and preserves every non-whitespace
   character, including negation; no generated paraphrase can silently replace it.
3. **Jev:** `typesafe/jev-1.14` receives the original whole-answer criterion,
   candidate, and sources through the Decisions API. It independently chooses
   pass, fail, or uncertain without seeing generative outputs or reference labels.

The coverage cards repeat the meanings being tested, so they are not an entirely
fact-free extraction prompt. Their isolation prevents copying from full source
paragraphs; it does not prove entailment or rule out hallucination from the cards.
The old judge and both generative roles use the same model/provider binding to
avoid confounding this first comparison with a stronger model. The treatment
still changes decomposition, instructions, and number of calls together.

Source quotations, complete check/sentence membership, and candidate spans are
validated mechanically. These checks are not semantic proof. Raw outputs and
failures remain in the result; there are no replacement calls.

The generative result fails on a validated material coverage absence/contradiction
or grounding contradiction/unsupported assertion. It passes only with all meanings
conveyed and every sentence supported or genuinely nonfactual; otherwise it
abstains. The combined result equals Jev and the generative result only when they
agree; disagreement produces uncertainty, never confidence averaging. Correlated
errors remain possible: neither model independence nor calibrated confidence is
assumed. Jev remains optional for the engine, not a new mandatory dependency.

## Mathematics we compute locally

One embedding request covers unique candidate answers, their sentences, check
cards, and source messages using `openai/text-embedding-3-small`, 256 dimensions.
Labels, candidate IDs, and model verdicts are not embedding inputs.

After that call all vector computations are ordinary local mathematics:

- L2 normalization and dot-product cosine similarity.
- For each required meaning, maximum similarity to a candidate sentence.
- For each candidate sentence, maximum similarity to a local source message.
- Similarity between answers under the same criterion, including positive and
  negative contrasts.

A parallel offline **TF-IDF** control uses raw term frequency and
`idf(t) = log((1 + N) / (1 + df(t))) + 1`, followed by L2 normalization. Its fixed
vocabulary uses all unique frozen texts, retains negation and numeric tokens,
and needs no service call. This is lexical geometry, not a semantic embedding.

All scores are **unthresholded diagnostics**. No vector score grants a pass,
resolves disagreement, or establishes a reply referent. High similarity between
contradictory answers is a limitation we want to expose. These authored contrasts
are not controlled single-word minimal pairs; do not attribute a distance change
to one actor/date/negation edit alone. Statement timestamps are not automatically
policy validity dates.

## Execution and bounds

Configuration and stage contracts: `experiments/calibration/split.cue`.
Runner: `scripts/split_judgment.py`.

```sh
# No credentials or network: prepare protocol and local TF-IDF diagnostics.
nix develop --command python -m scripts.split_judgment \
  --output runs/split-prepared.json

# Explicit paid opt-in; existing token is loaded, never displayed.
direnv exec . python -m scripts.split_judgment --live \
  --budget-usd 0.50 --max-calls 40 --output runs/split-live.json
```

There are **31 planned requests**: 20 generative, ten Decisions, one embedding.
A single shared ledger enforces the local budget and call count across all APIs.
The stated $0.50/40-call bounds are ceilings, not spending targets. Request bytes,
provider price filters, fixed provider selection, response size, and transport
timeout are bounded; there are no automatic retries or provider fallback.
Unknown billing stops further requests. Embedding cost may be conservatively
accounted from tokens times the configured provider price ceiling when reported
cost is absent; this is explicitly distinguished from provider-reported cost.
A local budget is not a provider-enforced cap, and interrupted calls may be billed.

Before calls the report freezes every actual request payload, role/provider,
contract, input/source snapshot, approved reference binding, check cards, order,
math policy, implementation hashes, baseline artifact hash, and limits. Each
request identity is checkpointed before sending. Responses, provider metadata,
usage, reservations, invalid outputs, and partial failures are retained with
credential redaction. Existing paths cannot be overwritten or resumed.

Summaries retain all ten planned examples and separate primary from robustness,
with pass/fail/uncertain matrices for generative, Jev, and combined policies.
Invalid and unattempted stages are explicit, not dropped. Review false acceptance,
false rejection, and abstention together. More abstention alone is not better
understanding; agreement on these known examples is not general accuracy.

## First comparison

The [immutable result](../experiments/calibration/results/first-split-judgment.json)
retains the full protocol, actual request payloads, raw responses, dense vectors,
math diagnostics, and accounting. `split-observations.cue` records its hash and
qualitative review. It is derived experimental data, not independent fixture-world
evidence. Preparation and live execution shared protocol
`62b32af99ff0b3c5114d942b06d3759e7ac8d1341c127014cea01429ce196b89`;
the pre-call implementation is commit `bd3e93568c61`.

All **31 planned requests** completed, with no retries, costing **$0.017979816**
as reported by the providers. Jev served `typesafe/jev-1.14-20261014`; both
generative roles served `openai/gpt-4.1-mini`. All costs, including embeddings,
were reported rather than estimated in this run.

| Policy | Correct rejection of bad answers | Correct acceptance of good answers | False rejection | Abstention |
| --- | --- | --- | --- | --- |
| Split generative | 7/7 | 0/3 | 1 | 2 |
| Jev | 7/7 | 3/3 | 0 | 0 |
| Agreement-only combination | 7/7 | 0/3 | 0 | 3 |

These are **observed development counts**, not estimated population rates.
Compared with the old whole-answer judge, false acceptance disappeared on these
known controls, but the combination accepted no good answers. That is a safety
tradeoff, not a finished evaluator. Jev supplies a promising signal worth testing
on new material; ten matches do not prove general accuracy, calibrated confidence,
or statistical independence from the generative model.

### What the separate stages exposed

All ten coverage outputs passed structural checks. Their completeness-only
aggregates matched the ten whole-answer references, including detecting the
manuscript omission without receiving source paragraphs. This does not verify
truth or make every per-card explanation correct: the Harbor bypass-extension
answer also drew an overbroad effects-card rejection.

Grounding still had serious problems:

- **Harbor's good answer:** returned a sentence-keyed object instead of the
  contracted array. It remains invalid; we did not normalize its shape.
- **Maple's good answer:** changed source quotation punctuation/capitalization.
  It remains invalid; we did not loosen quote checks.
- **Good missing-context answer:** called “This answer does not verify that a
  storage system retained the message” unsupported because the world sources
  did not mention storage. This is a valid self-limitation, not a claim that a
  storage operation happened. The narrow nonfactual category may itself be a
  contract-design problem; a future variant should distinguish meta-epistemic
  statements from world claims.
- **Invented-context answer:** still labeled the Maple/annex assertions supported
  even though its sole source contains neither. Another unsupported timestamp
  sentence caused an overall rejection, hiding this local false acceptance.

Preserving intermediate results mattered: whole-answer agreement alone would
have concealed those errors. The combined policy abstained when the generative
result differed from Jev; it did not use Jev confidence as permission to override.

### What the mathematics showed

One batch embedded **65 unique texts**. The correct Maple answer and the wrong
staff-permission-transfer answer had **0.937 dense cosine similarity**. The
correct answer and the manuscript-omission answer scored **0.926**. Overall
similarity therefore cannot certify preservation of a consequential boundary.

For the manuscript requirement, maximum sentence similarity did separate the
correct answer from the omission in this pair:

| Diagnostic | Correct answer | Omission |
| --- | --- | --- |
| Dense cosine | 0.651 | 0.463 |
| TF-IDF cosine | 0.266 | 0.075 |

This suggests useful nomination/coverage diagnostics, not an acceptance threshold.
No thresholds were fitted after seeing these values, and vectors did not influence
any model decision or the combination policy. Next, evaluate Jev on fresh
correspondence and improve grounding's statement types/output structure under a
new frozen protocol, without repairing or resampling these outputs. Include
source-swapped controls with an unchanged candidate and a neutral criterion:
changing the evidence should change the verdict. This helps distinguish genuine
evidence use from recognizing the wording of authored bad answers.

The next [fixed-depth multi-pass Jev investigation](multipass.md) implements those
fresh source-swapped packets, per-claim Decisions questions, stronger generative
audits, re-adjudication, and separate order/repeat controls.
