# Larger reviewed-contract paired comparison

## Hypothesis and scope

The prospective extraction/projection contract and severity-aware audit ABI
should reduce representation-only disagreements without hiding material stance,
scope, or revision errors. Measure the extra diagnostic flags and holds from a
blind verifier and source auditor on **the same primary output**, along with
availability, raw differences, transitions, and cost. Agreement is not truth.

This is a new synthetic development experiment, not a continuation of the
partially attempted 49-call trial. Its original results and invalid audits remain
unchanged. The ten previously reviewed examples remain development references;
neither the shared policy nor these twelve new authored references receive
blanket human approval. Canonical acceptance, publication, deletion, retirement,
and substitution of verifier facts remain disabled.

## Frozen design

- Twelve fresh threads, sixteen messages each; independent eight- and
  sixteen-message checkpoints: 24 snapshots and 192 distinct source messages.
- Three real calls per snapshot: GPT-4.1 / OpenAI interpreter, Gemini 2.5 Pro /
  Google AI Studio blind verifier, o3 / OpenAI source auditor.
- One final-window o3 control call per thread: four faithful equivalence pairs
  and eight identical shared faults. Controls are authored, not real outputs.
- **84 fixed calls, $5 local ceiling, zero retries, fallback, or repair.** A
  credit top-up neither raises the ceiling nor resumes a stopped run. Unused
  budget is not authorization for extra calls. The local ceiling does not reserve
  credits or establish an account-wide spending cap.
- Each request pins its model, provider, price ceilings, and 8,000 output tokens.
  Fresh public endpoint GET snapshots are frozen with the protocol; they are
  availability observations, not reservations or guarantees of future service.
- The explicitly selected transport is `deadline_transport.ledger_sender`:
  300-second absolute local wait including worker startup, 128 KiB request,
  1 MiB captured response. Termination does not cancel provider work or prove
  billing. Cleanup is bounded best effort, not a real-time OS guarantee.
- Stop without retry on unaccounted submission, unknown billing, or exhausted
  local budget. Preserve reservations, raw response/error bodies, unavailable
  stages, and every planned denominator. Accounted invalid outputs stay invalid;
  later scheduled roles still run if accounting and limits permit.

`scale-plan.cue` supplies the common source envelope and schedule;
`scale-cases.cue` supplies original paragraphs, scoped bindings, provisional
interpretations, query expectations, and control mutations. The checked Python
manifest freezes these values, schemas, shared contracts, source/script hashes,
review decisions, provider snapshots, ordering seed, and normalized limits before
any paid call. Both extractors receive byte-identical messages; only their
requested model/provider and generation parameters differ. No extractor receives
peer outputs, query hypotheses, reference labels, controls, or future messages.
Auditors receive the original window, common contract, untrusted proposals,
availability, and mechanical rejections/lowerings—not reference labels or control
identity. Frame, authority, identity, lineage, finite domains, and topic links are
manually supplied premises, not autonomously discovered facts.

### Families and predeclared controls

| Family | Final-window control |
| --- | --- |
| Hunch followed by observation | Turn attributed speculation into a world assertion |
| Environment-specific coverage | Add an east observation to a west binding; the filtered state stays correct |
| Personal ignorance | Add a negative world assertion from a personal unknown |
| Source-note date gap | Omit an optional explicit coverage note; derived coverage and recovery remain |
| Withdraw only an assurance | Add a prohibition unsupported by withdrawal |
| Independent grant survives | Move a topic-linked invitation warning to a direct about-binding |
| Actual grant revocation | Omit the targeted revocation |
| Equal-authority conflicting dates | Omit one declared-origin group's date assertions |
| Property-local date correction | Duplicate original date and venue atoms |
| Question is not confirmation | Add a world assertion from the question |
| Exactly one unidentified provisional date | Move and duplicate the qualifier in `conditions` |
| Physical door is not permission | Add a prohibition from a question about permission |

Every control is schema-valid and mechanically admissible before execution.
Planted faults affect only the declared binding under the authored operational
profile; clean alternatives must match that profile. This checks experimental
construction, not a model's ability to interpret natural language.

## Projections and scoring

The runner explicitly adopts `meaning_projection`, its native CUE schema
importer, and `source-audit-report-v2`; it does not modify historical runners.
Speculation remains attributed but contributes no world witness. Typed personal
conditions, questions, exactly-one qualifiers, narrow revision targets, original
sources, and procedure recovery paths remain inspectable. Successful procedure
annotations lower through declared topic links without replacing the proposal.
Both fact and evidence-use views are saved. Projection checks verify conditional
preservation, not extraction completeness or entailment.

Report all 72 binding/query units per extractor and 72 binding assessments per
policy, including unavailable ones. Policies are primary plus mechanical checks,
then the same primary plus blind verification, then the same primary plus the real
auditor. Controls never enter the real policy masks. Material/unclear/unavailable
audit concerns add binding-local holds; non-material notes remain visible without
blocking. Audit output cannot clear other checks or add facts.

The finite comparison profile normalizes only declared equivalences: placement,
identical duplicates, binary complements, declared-origin world repeats,
qualifier ordering, directive case/spacing/leading object article, direct versus
lowered procedure placement, and repeated same-actor/same-origin directives.
Attributed hunches and personal frame/holder are material. Explicit source-note
coverage nodes are optional under the derived view and are reported separately;
this does **not** establish that every proposed note is semantically correct.
Raw proposals, quotations, source windows, lowerings, and rejections survive.

Raw profile differences, omitted/extra memberships, and filtered scalar states
are separate. A correct scalar state can conceal wrong scope/provenance.
Reference-profile matching is not established semantic fidelity. Likewise,
profile-matching flags are proposed unnecessary holds, not adjudicated harm.
Binding-coincident material auditor findings require inspection of their actual
reasons before claiming incremental valid detection. The report preserves those
reasons and separately reports ungraded note differences. Qualitative review
must not silently repair or rescore the frozen authored references.

Report prefix/final changes, unchanged material profiles, affected versus
unaffected eligibility, role/arm cost, control availability, and full planned
counts. A missing control is unavailable, not a detection miss. A valid structured
audit is not necessarily a correct audit. These authored families and controls
are not calibrated independent gold or an estimate of production error rates.

## Offline preparation and explicit execution

```sh
nix develop --command just scale-panel runs/scale-prepared-NEW.json
```

Preparation, tests, and CI make no network or generation calls. Live execution is
separate, requires credentials and the exact prepared `--protocol-sha256`, and
uses a new output path. The runner refuses changed/attempted reports and existing
output paths. No resume option exists. Public endpoint preflight was an explicit
read-only action outside the offline preparation path; it is not repeated by the
runner. A later changed implementation produces a different protocol digest.
