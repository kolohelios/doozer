# Doozer

**An optimizing compiler for collective knowledge.**

Doozer (called Doozers in the original design documents) is an open-source
experiment in autonomous knowledge maintenance: ingest evidence, reconcile it
with existing understanding, compact without losing meaning, and make the result
discoverable and useful.

This repository begins with two living design documents:

- [Product requirements](docs/PRD.md) — why Doozer exists, what it must do,
  and what success means.
- [Engineering design](docs/EDD.md) — how we propose to implement and test
  it, including open hypotheses.

The priority order is **survivability → discoverability → compactness**. A useful
one-word correction can matter more than a long discussion; repeated information
may legitimately produce no change.

## Status

Early design / exploration. The design documents are v0.4 as of November 21,
2026 and are imported from the starter archive with header whitespace normalized.
There is no engine implementation yet. Development infrastructure and licensing
will be introduced in a separate pull request.

## Initial engineering goal

Build a minimal, testable, end-to-end knowledge-maintenance loop with synthetic
fixtures:

1. Receive and durably identify source evidence.
2. Reconcile new evidence against current understanding, including no-ops and
   conflicts.
3. Commit changes safely, avoiding duplicate semantic effects on replay.
4. Search/explore current understanding with source links.
5. Produce reproducible projections without creating circular evidence.

Prefer a narrow vertical slice over prematurely selecting a graph database,
message broker, or orchestration framework. Read `docs/PRD.md`, `docs/EDD.md`,
and `AGENTS.md` before implementing product behavior. Keep the design documents
at stable paths and revise them in place rather than creating versioned copies.
