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
