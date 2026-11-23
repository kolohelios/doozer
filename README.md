# Doozer

**An optimizing compiler for collective knowledge.**

Doozer (called Doozers in the original design documents) is an open-source experiment in autonomous knowledge maintenance: ingest evidence, reconcile it with existing understanding, compact without losing meaning, and make the result discoverable and useful.

This repository begins with two living design documents:

- [Product requirements](docs/PRD.md) — **why** Doozers exists, what it must do, and what success means.
- [Engineering design](docs/EDD.md) — **how** we propose to implement and test it, including open hypotheses.

The [synthetic CUE corpus and model-role experiment guide](docs/corpus.md) define initial expected and forbidden outcomes. Run `nix develop --command just corpus-check` to validate fixture integrity offline; this is not yet a semantic engine evaluation.

The [bounded retrieval experiment](docs/retrieval.md) compares lexical, vector, and hybrid ranking plus explicit-link expansion against a corpus much larger than its evidence budget. Run `nix develop --command just retrieval runs/retrieval-lexical.json` for an offline baseline; real embedding construction is opt-in and cached.

The [retrieval-to-understanding comparison](docs/understanding.md) freezes new held-out cases and compares full-case evidence, bounded vectors, and vectors plus model-proposed links with a fixed reasoning model. Its default command prepares a protocol only; live generation and provisional judging are opt-in.

The [offline meaning review and calibration draft](docs/calibration.md) annotates the nine saved answers without rerunning models or changing the original results. Labels and proposed evidence bundles remain pending user review; run `nix develop --command just calibration` to validate the draft.

The [multi-pass evidence harness](docs/multipass.md) investigates Jev claim decisions, blind generative audits, skeptical review, and re-adjudication using fresh source-swapped packets. Default preparation is offline; model reports remain proposals, not independent evidence or permission to retire knowledge.

The [bounded evidence-update investigation](docs/evidence-expansion.md) adds source-expansion forks, conditional scope/lineage guards, and CUE countermodels. Correct prose can still serialize uncertainty into a wrong machine-facing fact; schema clarity helps but does not establish safe canonical updates. Its source-centric specialist-panel trial adds blind typed extraction, conditional scalar checks, and adversarial shared-error controls—without turning agreement into acceptance. The [interpretation-contract review](docs/interpretation-review.md) contains eight exact meaning-preservation examples and acceptable encoding alternatives, now individually user-approved as development references. The broader policy text is not separately approved as a blanket rule. A fresh [paired transfer trial](docs/evidence-expansion.md#paired-reviewed-contract-transfer) compares the same extractor output with and without panel diagnostics on longer threads, under a shared operational contract grounded in those examples. Its [offline follow-up review](docs/transfer-review.md) proposes two disputed meanings for individual review; both remain pending.

The priority order is **survivability → discoverability → compactness**. A useful one-word correction can matter more than a long discussion; repeated information may legitimately produce no change.

## Status

Early design / exploration. The design documents are v0.4 as of November 21, 2026 and are imported from the starter archive with header whitespace normalized. There is now an experimental [retry-safety workbench](docs/workbench.md): pluggable routing, separate analysis/reasoning roles, CUE stage contracts, lexical retrieval, validated local patches, discovery, and reproducible projections. It is not a durable service or a demonstration that semantic preservation is solved.

## Initial engineering goal

Build a **minimal, testable, end-to-end knowledge-maintenance loop** with synthetic fixtures:

1. Receive and durably identify source evidence.
2. Reconcile new evidence against current understanding, including no-ops and conflicts.
3. Commit changes safely, avoiding duplicate semantic effects on replay.
4. Search/explore current understanding with source links.
5. Produce at least one reproducible projection.

Prefer a narrow vertical slice over prematurely selecting a graph database, message broker, or orchestration framework. AI integration will use **OpenRouter**, with an explicit model selected per experiment; model responses propose changes rather than authorizing them.

## Development and validation

Install Nix with flakes enabled, then run from the repository root:

```sh
nix develop
just validate
```

Or run `nix develop --command just validate` without entering an interactive shell. Optional direnv integration: `direnv allow`.

The flake pins published `kolohelios/kolohelios-nix` and `kolohelios/shaka` inputs. `just validate` runs Shaka preflight (repository audits, workflow validation, spelling and prose checks), whitespace validation, and sandboxed Nix checks. GitHub Actions runs the same command for pushes to `main` and pull requests. These checks validate the repository, **not** the EDD's semantic hypotheses. No live model calls or API credentials are required.

Use Jujutsu (`jj`) for version control and Conventional Commits for change descriptions. No slot projects exist yet; when an executable experiment needs `project.cue`, place it at `<slot>/<project>/project.cue` and use Shaka's generated project justfile/flake workflow. The root flake and justfile are deliberately hand-authored for this docs-first stage.

### OpenRouter setup (opt-in live experiments)

Copy `.env.example` to `.env` and set `OPENROUTER_API_KEY` locally. Direnv loads `.env` through `.envrc` after `direnv allow`. Select models explicitly per experiment/request so runs can compare multiple models; no global `OPENROUTER_MODEL` is required. The [Jev decision probe](docs/jev.md) supports one-request routing experiments; the [workbench](docs/workbench.md) composes separate model roles into a local reconciliation loop. Do not paste tokens into issues, commits, fixtures, or logs.

Keep deterministic fixture tests offline. Live runs must be explicit, bounded by request/token/cost limits, and record model ID, prompt/schema revision, usage, and fixture outcome without recording credentials. Use only synthetic or explicitly authorized inputs: OpenRouter routes requests to external model providers. An API token is not needed for this bootstrap.

### First experiment

Hypothesis: the retry-safety fixture can produce a compact, source-backed explanation without losing the notification exception or manual-replay scope. The seed cases in `corpus/` encode EDD §3, §5, and §14 with expected meanings and forbidden outcomes; review them before using them as an evaluation oracle. Test replay/no-op stability, contradictions, and contextual one-word corrections before expanding the corpus.

Run the local loop offline with `nix develop --command just workbench runs/retry-recorded.json`. Review its live observations before choosing the next role/model comparison: one live run dropped the manual caveat, and a stricter contract improved coverage without yet producing the desired compact reconciliation. Next, add durable ingest and crash/restart behavior only once the local transformations warrant it. Test crash/restart and duplicate delivery; generated handbook/directive text must never become independent corroborating evidence. PostgreSQL versus an embedded transactional store and the implementation language remain open. Follow EDD §13 for the broader evaluation sequence; do not claim semantic preservation from tooling checks alone.

## Working with Pi

Pi reads repository-level `AGENTS.md` as project guidance. Start Pi from the repository root:

```sh
pi
```

Suggested first request:

> Read `docs/PRD.md` and `docs/EDD.md`, particularly the MVP and evaluation sections. Propose the smallest executable vertical slice and a fixture-driven validation plan. Identify assumptions and keep technology decisions reversible. Do not implement the full engine in one step.

Keep the two design documents at stable paths. Git history tracks their revisions; don't create a new versioned document for every edit.

## License

Code and documentation are dual-licensed under **MIT OR Apache-2.0**, at your option, matching kolohelios. See [LICENSE-MIT](LICENSE-MIT) and [LICENSE-APACHE](LICENSE-APACHE).
