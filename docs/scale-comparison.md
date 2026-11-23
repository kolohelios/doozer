# Larger reviewed-contract paired comparison

> Completed, with protocol limitations: the shared prompt omitted the older base
> contract, and authored rationale text could identify controls. This is not a
> clean full-contract or blinded-control confidence result. The original protocol,
> prompts, responses, invalid outputs, and scores remain unchanged below.

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
requested model/provider and generation parameters differ. The actual shared
`common_contract` is `meaningContract` v2 alone: the older `reviewedContract`
rules/wire were not composed into it. Thus "common" does not mean the intended
complete base-plus-extension contract. No extractor receives
peer outputs, query hypotheses, reference labels, controls, or future messages.
Auditors receive the original window, actual common wire, untrusted proposals,
availability, and mechanical rejections/lowerings—not expected verdicts or fault
labels. However, control rationale text says "Authored development
interpretation, not a model response or human gold," leaking authored origin.
Do not describe the controls as cleanly blinded. Frame, authority, identity, lineage, finite domains, and topic links are
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

## Frozen execution result

The [lossless archive](../experiments/judgment/results/first-larger-transfer.json.gz)
contains the complete prepared manifest, 84 exact request payloads, 84 native
responses, transport/accounting records, compiled views, failures, and original
summary. [CUE observations](../experiments/judgment/scale-observations.cue) bind
its hashes and counts. Ignored originals remain under `runs/scale-*-01.json`.

- Protocol: `4fc33b638aa8c104124c4f9f90fdd23b9ef26c1c929c07025099f6aece688ff7`
- Source: `f5220378a22fde838ef1aa32b4af77aa72027139`
- Archive: `9e29a682a37956595b1b08c67377fdf53f1c37ea59c7259d90c703b416518575`
  (1,341,955 bytes).
- Original JSON: `a8b114e8a086a6f107d36b41c02f71121a300e5c806a16228c86f09e025f5929`
  (10,871,970 bytes).

**84/84 submitted and accounted; $2.527731 reported cost; no unknown billing,
retries, or extra calls.** All 24 real snapshots and 12 controls were attempted;
20 real snapshots have all three valid role outputs. Primary: 22/24 valid;
verifier: 23/24; real auditor: 23/24; controls: 12/12. Unused budget is not spent.

| Extractor | Available / planned cells | Scalar matches | Profile matches |
| --- | ---: | ---: | ---: |
| Primary | 66 / 72 | 62 / 66 | 38 / 66 |
| Verifier | 69 / 72 | 69 / 69 | 54 / 69 |

The primary has four missing-support scalar outcomes among available cells,
not unsupported support or spurious opposition. It has 11 missing and 48 extra
profile memberships, versus zero missing and 25 extra for the verifier. These
memberships overlap, include rejected proposals, and are not independent error
counts. The 36/6 mechanical rejections and 19/16 note-difference snapshots remain
separate. Profile counts are **not** adjudicated meaning accuracy: for example,
the verifier's extra Grove `venue != storage bay` membership corresponds to an
explicit source exclusion omitted from the provisional reference. That reference
is not repaired or rescored here.

All policies have 72 planned bindings, six unavailable primary cells, 28
profile-discrepant primary cells, and 38 profile-matching primary cells:

| Policy | Discrepant flagged / unflagged | Matching flagged / eligible |
| --- | ---: | ---: |
| Single + checks | 19 / 9 | 0 / 38 |
| Add blind verifier | 28 / 0 | 7 / 31 |
| Add real auditor | 28 / 0 | 11 / 27 |

The auditor adds **zero newly flagged profile discrepancies** over blind
verification and four holds on profile-matching final-window bindings. Two holds
arise from objections to an omitted original location atom despite a surviving
same-origin repeat. Two follow an invalid audit. This does not prove that every
profile-matching interpretation is correct or every extra hold unjustified.

All seven authored query changes match at both checkpoints. Of 24 unchanged
material profiles, 19 have matching primary final interpretations; single keeps
19 eligible, blind verification 18, full panel 14. The other five remain
profile-discrepant rather than disappearing from the denominator.

Known role costs: primary **$0.521790**, verifier **$1.143845**, real auditor
**$0.639966**, authored controls **$0.222130**. The real panel costs $2.305601,
about **4.42 times** primary alone. Controls are excluded from that arm comparison.

### Protocol limitations and retained failures

1. **Incomplete contract composition.** The actual shared prompt contains only
   the prospective projection wire, not the older base semantic rules/wire.
   Extractors get their constructor schema, but the auditor gets only its audit
   schema and the short common wire. In particular, it is not told the full
   grant-none/null lowering contract. Two unaffected staff grants in faulty
   controls receive material challenges for `value=null`, although the frozen
   compiler requires that operand and derives permitted status from `kind=grant`.
   These four role-specific proposed false challenges cannot be attributed solely
   to reasoning quality under a fully shared contract.
2. **Authored-origin cue.** Control entry rationales explicitly identify authored
   development interpretations. Expected verdicts and planted-fault labels stay
   hidden, and real extractors remain peer/reference/future-blind, but the
   controls are not cleanly origin-blinded. All eight planted faults receive
   both-role material challenges; do not treat 8/8 as a calibrated detection rate.
3. **Report availability.** Two primary outputs have empty evidence arrays in
   extraction limits. The JSON schema permits those arrays; the stricter
   conditional validator rejects the reports. Both claim no location record for
   visitor-scoped subjects; the authored binding scope intends the event venue.
   Those subject labels and interpretations are unreviewed, not settled by model
   agreement. One verifier output ends with `finish_reason=length`. One audit
   repeats `m13` in an evidence list and remains invalid. No deduplication,
   partial promotion, token increase, or regeneration rescues these reports.
4. **Meaning versus operational profiles.** In the Iris prefix, the auditor
   demands an extra world inequality from “It is not another proposed date for
   the workshop,” a source-scope disclaimer in a separate briefing record. A
   world inequality might follow from the workshop's own date elsewhere, but
   that does not make the briefing disclaimer an independent world witness.
   Other extra exclusions, such as the explicit Grove venue exclusion, may be
   legitimate reference omissions. Original scores and disputed meanings remain
   visible rather than being silently relabelled.

This result supports keeping scalar outcomes, typed interpretation, provenance,
ABI availability, and diagnostic cost separate. It does not demonstrate safe
acceptance or a worthwhile always-on auditor. **Before another paid trial, fix
and inspect common-contract composition and control cues offline**, explicitly
handle the schema/validator gap, and review disputed meanings individually.
Do not resume, repair, or spend the remainder of this run's budget.
