# Jev: first live decision probe

## Hypothesis

`typesafe/jev-1.14` can distinguish a meaningful tiny correction, exact replay,
and an intervention with no recoverable referent. This is a routing experiment,
not a semantic reconciliation engine or permission to write knowledge.

Jev is a direct structured-decision model, not `typesafe/jev-router`. OpenRouter
exposes it through `POST https://openrouter.ai/api/alpha/decisions`. It accepts
`state` plus typed `questions` and returns typed `answers`; do not assume it is
an ordinary chat model or attempt to obtain generated prose from it.

References checked for this implementation:

- [Jev 1.14 model page](https://openrouter.ai/typesafe/jev-1.14)
- [Decisions API reference](https://openrouter.ai/docs/api/api-reference/alphadecisions/submit-a-decisions-request)
- [TypeSafe SDK / System One compatibility](https://openrouter.ai/docs/guides/community/typesafe-sdk)
- [Model endpoint metadata](https://openrouter.ai/api/v1/models/typesafe/jev-1.14/endpoints)

The general Models API defaults to other output modalities and did not list the
model in the initial lookup. Use the model-specific endpoint metadata or filter
for `output_modalities=decisions`. Alpha API shapes may change.

## Run it

The CUE configuration in `experiments/jev/probes.cue` pins this experiment's
model, question, criteria, limits, and five provisional labels. It does not
introduce a global model setting. Cases reference existing source identities and
checkpoints in the corpus, rather than duplicating source conversations.

```sh
# Safe default: inspect one request, no credentials or network required.
nix develop --command python scripts/jev_probe.py contextual-no

# Explicit live call: direnv loads the token from ignored .env.
direnv exec . python scripts/jev_probe.py contextual-no --live
```

Other case IDs are `duplicate-incident`, `detached-stop`, `pending-incident`, and
`older-positive`. Each invocation selects exactly one case and makes at most one
request. Exit code 0 means preview success or agreement with the provisional
label; 1 means disagreement; 2 means validation/transport failure. A refusal is a
failure, not an authorized action. To compare all cases, run them deliberately
one at a time; there is no automatic paid sweep.

Allowed decisions:

- **analyze:** new meaningful evidence, including a context-resolvable correction,
  needs scoped analysis; this does not authorize a commit.
- **no-op:** all incoming source identities were already processed.
- **retain-ambiguity:** preserve an intervention whose target is not recoverable.

No-op detection from identical processed IDs has a deterministic baseline. We do
not need an LLM for that in production; the case is a calibration/control probe.
These three choices are deliberately coarse and do not evaluate actual patches.

## Boundaries and cost

The runner allowlists received source fields and passes prior processing
identities, incoming identities, and same-batch context. Expected labels/reasons,
scenario titles/tags, future sources, and corpus answer rubrics stay outside the
request. `pending-incident` specifically checks that received is not confused
with processed. API response confidence is diagnostic, not calibrated truth.

Live requests require `--live` and an environment `OPENROUTER_API_KEY`. The script
never reads `.env` itself or prints credentials. It sends only synthetic text,
allows only the TypeSafe provider, disallows fallback and non-transient provider
data collection, refuses redirects, caps request data at 16 KiB and responses at
1 MiB, and uses a 30-second network timeout. It makes no automatic retries:
a timed-out call can still be billed. Errors suppress raw provider response
bodies. The runner cannot commit patches, invoke tools, or call another model.

The configured price filters are **$0.05/M prompt tokens and $0/M completion
tokens**. Endpoint metadata at initial discovery listed $0.042/M input tokens
and zero completion-token price. These are routing price filters, **not a hard
total-spend cap**; provider token accounting includes question/structural overhead.
Use a dedicated OpenRouter key with a small credit limit for a provider-enforced
budget. Missing response cost is reported as unknown, not zero; BYOK costs can
exclude underlying provider charges. Do not infer a hard token limit from the
request byte limit.

## First observation

One live synthetic request, on November 22, 2026 (UTC):

| Case | Served model | Decision | Confidence | Wall latency | Tokens in/out | Reported cost |
| --- | --- | --- | --- | --- | --- | --- |
| `contextual-no` | `typesafe/jev-1.14-20261014` | `analyze` | 0.88 | 0.295 s | 1280 / 47 | $0.00005376 |

Prompt revision: `triage-v1`. Canonical request JSON SHA-256:
`a4af2238b9eaee1dd97be2a766e0d5692c8cb75d756f4d8ae68d94ed2e40521a`.
The response indicated no BYOK billing. This matched the provisional label for a
reply rejecting automatic application of a manual mitigation. It is one smoke
test, **not an accuracy, calibration, or latency benchmark**. No engine effect
was authorized. Repeated calls may differ and incur additional charges.

Offline CI tests request isolation, scheduling, response validation, refusals,
price/provider filters, preview behavior, and sanitized failures with mocked
transport. It does not call OpenRouter, even when a token is present. Next,
review the labels, compare negative/ambiguous cases, and test controlled role
assignments before attaching decisions to any real reconciliation pipeline.
