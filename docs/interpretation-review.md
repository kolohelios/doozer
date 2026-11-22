# Interpretation contract: exact review examples

**Review proposal snapshot. See the [separate decision record](../experiments/judgment/interpretation-approvals.cue) for current example approvals. Validation never grants approval.**

This is a reproducible review projection of [`interpretation-review.cue`](../experiments/judgment/interpretation-review.cue) and [`interpretation-examples.cue`](../experiments/judgment/interpretation-examples.cue), not another evidence source or a production IR specification.

Packet SHA-256: `710a4ddce7cc5f4c07a3f009cec0130c347867550a0f0f8cea68aae7525aaaf2`
Policy SHA-256: `ca46c836288278c62308d5cb5cd481f6da738a6d87b1ae2e4b5f3f1fa1929000`

No example or policy is approved by preparing, validating, or merging this packet. Approval must identify the reviewed content or its hashes.

Synthetic development references, not held-out or independently human-authored gold. Each example is a separate scenario with local source/window IDs, not part of one combined evidence pool or a real workplace. No model calls, canonical effects, or retroactive changes to frozen results.

Approval can name all eight examples under this packet hash, or specific example IDs plus the policy hash and their content hashes. Merging this PR is not label approval. Corrections produce new hashes; approval records must remain separate from reviewed content.

## Proposed shared rules

- **meaning-not-layout:** Evaluate recoverable material meaning, provenance, and projection behavior, not exact atom sets, field names, or node counts. Equivalent encodings need not force a hold. A claim of equivalence still needs an inspectable preservation witness; agreement alone is not that witness.
- **uncertainty-owner:** Distinguish what a source says it has not established, what a bounded processed window does not cover, and what an extractor cannot interpret. Record the holder or basis window and the relevant time. Preserve the actual stance: 'not established in these notes' does not itself say the author personally does not know. None is an opposite world fact or a universal claim that nobody knows.
- **preservation-path:** Explicit source qualifications must remain source-linked and recoverable to consumers that need them. A typed condition, linked source act, or reproducible coverage derivation can satisfy this; pertinent projections must expose the material qualification rather than merely archive it. An opaque mixed limitations string that the consumer ignores is not a machine-preservation witness. Mere placement in a limitations field is not itself a semantic error.
- **act-arguments:** Distinguish an act's action object, its about-topic, the prior assertion or act it targets, and any world or normative binding it changes. A single physical binding field is acceptable only if its kind-specific meaning is explicit. A question retains its proposition without asserting it; a stored directive is not a newly assigned task.
- **local-revision:** Withdrawal targets the specified assurance, not permission or all facts in its source. Revocation of an actual grant is a different normative act under the declared authority. Preserve independent support and unaffected facts; a separate live grant cannot be cancelled merely by withdrawing an assurance.
- **frame-and-history:** Bind uncertainty and source coverage to their stated frame. Later evidence may establish a fact without falsifying an earlier source's honest uncertainty. History remains inspectable but need not crowd every answer. Leave only the affected binding unresolved, not all otherwise supported knowledge.
- **shared-contract:** Give every role the same definitions, preservation obligations, and permitted equivalences. Blind extractors to peer outputs and evaluation answers, not to the semantic contract. Reference disagreements and critic reports are proposals, not votes or new world evidence.

## Exact source → proposed meaning pairs

The records below are review notation, not a required storage layout. 'Retains' names material meaning obligations; it does not require one node per obligation. Validators check anchors, frames, ownership, references, and declared coverage, not natural-language entailment or encoding equivalence.

### 01-source-uncertainty: A source's uncertainty is not an opposite date fact

Example SHA-256: `6c65ce342a0ef60b0c09f88dfaebda125066be62d82f9e129dc355648c58d3bc`

**Decision:** Preserve the speaker's stated uncertainty, exact date exclusion, and known venue as distinct meanings.

All dates and names are synthetic. This is a one-day drill; statement time and effective date are different variables.

**Frames:** w1 = s1. Current view: w1. These are bounded supplied snapshots, not global coverage or durable-ingestion guarantees.

**Source s1 — coordinator, said 2030-02-11:**

> The drill venue is Pine annex. I have not established its effective date in these notes. Its effective date is not 2030-02-11, the date of this message.

**Proposed material interpretation:**

- `venue` (assertion; origin=source; basis=w1; about=venue; required): The source reports Pine annex as the drill venue. Anchor: source:s1 “The drill venue is Pine annex.”
- `not-message-date` (assertion; origin=source; basis=w1; about=date; required): The source excludes effective date 2030-02-11, not every other date. Anchor: source:s1 “Its effective date is not 2030-02-11, the date of this message.”
- `speaker-limit` (source-uncertainty; origin=source; basis=w1; holder=coordinator; about=date; required): The coordinator says they have not established the date in these notes; this is not universal ignorance. Anchor: source:s1 “I have not established its effective date in these notes.”

**Acceptable representation alternatives:**

- `separate`: Separate date constraint, venue assertion, and source-uncertainty record with holder and window. Retains: venue, not-message-date, speaker-limit.
- `qualified`: One qualified date record carries the exclusion and source's scoped epistemic statement, alongside the venue. The consumer can recover both meanings without matching a particular node count. Retains: venue, not-message-date, speaker-limit.

**Forbidden inferences:**

- “The drill does not take place on 2030-02-14.” — Excluding 2030-02-11 and lacking an established date do not exclude 2030-02-14.
- “Nobody knows the date, and the venue is unknown.” — The source limits its own establishment in these notes and explicitly gives a venue.

**Pertinent current projection:** Venue: Pine annex. The coordinator has not established the date in w1; 2030-02-11 is explicitly excluded.

**History/recovery boundary:** Retain the source's statement time separately from any effective date.

### 02-window-coverage: A coverage boundary may be represented without a redundant unknown atom

Example SHA-256: `281f412b256717fb836f265983e4e51505fc6845c6b7ae2b13eecc63f0e03caa`

**Decision:** Require recoverable scoped coverage, not a particular epistemic-node layout.

w1 is exactly the supplied processed snapshot, not the complete universe of possible evidence. The setting is scalar within each environment.

**Frames:** w1 = s1. Current view: w1. These are bounded supplied snapshots, not global coverage or durable-ingestion guarantees.

**Source s1 — operator, said 2030-02-12:**

> Quiet-mail is enabled in staging-east. These notes cover staging-east only and provide no finding about production-east. Do not transfer this observation to production.

**Proposed material interpretation:**

- `staging` (assertion; origin=source; basis=w1; about=staging-setting; required): The observation reports quiet-mail enabled in staging-east only. Anchor: source:s1 “Quiet-mail is enabled in staging-east.”
- `coverage` (coverage-limit; origin=source; basis=w1; about=production-setting; required): This note supplies no production-east finding. This is about coverage of w1, not the operator's total knowledge or universal absence of evidence. Anchor: source:s1 “These notes cover staging-east only and provide no finding about production-east.”

**Acceptable representation alternatives:**

- `explicit`: A source-linked coverage-limit record identifies w1 and production-east separately from the staging assertion. Retains: staging, coverage.
- `derived`: Typed source scopes and the bounded-window registry retain the explicit coverage anchor; a reproducible projection derives 'no production finding in w1'. No duplicate unknown atom is required. The qualifier must actually reach the relevant consumer. Retains: staging, coverage.

**Forbidden inferences:**

- “Quiet-mail is disabled in production-east.” — Lack of a production finding is not an observation of either state.
- “No production evidence exists anywhere, or the operator does not know production behavior.” — A processed-window coverage statement does not establish either global absence or personal ignorance.
- “The qualifier appears only in an opaque mixed limitations string ignored by the projection, so the machine-facing representation is complete.” — Field placement is not decisive, but an inspectable recovery/projection path for material coverage is required.

**Pertinent current projection:** Staging-east: enabled. Production-east: not established by w1; do not transfer the staging result.

**History/recovery boundary:** Keep the coverage statement attached to its source/window, not a permanent global unknown flag.

### 03-extractor-limitation: An extractor's unresolved reference is not a source's professed ignorance

Example SHA-256: `7f8ee943aab5d176b37fe6f1cd0bb01233da18982b33d9b15b40c58fdf689097`

**Decision:** Preserve the ambiguous qualifier and reported values; attribute the interpretation limitation to the extractor.

The extractor report below is hypothetical review input, not an actual model call or additional world evidence.

**Frames:** w1 = s1. Current view: w1. These are bounded supplied snapshots, not global coverage or durable-ingestion guarantees.

**Source s1 — organizer, said 2030-02-12:**

> The drill is dated 2030-02-14 and the briefing 2030-02-15. Exactly one of those dates remains provisional; I have not identified which in this note. The venue for both is Aspen room.

**Hypothetical extractor report x1 — extractor, basis w1; not source evidence:**

> I cannot bind the provisional qualifier to a unique date from this packet.

**Proposed material interpretation:**

- `reported-dates` (assertion; origin=source; basis=w1; about=drill-date,briefing-date; required): The source reports drill date 2030-02-14 and briefing date 2030-02-15, subject to the unresolved provisional qualifier. Anchor: source:s1 “The drill is dated 2030-02-14 and the briefing 2030-02-15.”
- `qualifier` (source-qualifier; origin=source; basis=w1; possibleAbout=drill-date,briefing-date; required): One of the two date claims is provisional; the note does not identify which. Do not silently attach the qualifier to both or choose one as settled. Anchor: source:s1 “Exactly one of those dates remains provisional; I have not identified which in this note.”
- `interpretation-limit` (extractor-limit; origin=extractor; basis=w1; holder=extractor; possibleAbout=drill-date,briefing-date; required): The extractor cannot resolve the qualifier target from w1. This does not say the organizer does not know the dates. Anchor: extractor:x1 “I cannot bind the provisional qualifier to a unique date from this packet.”
- `venue` (assertion; origin=source; basis=w1; about=venue; required): Both events have venue Aspen room; uncertainty over the date qualifier does not erase this. Anchor: source:s1 “The venue for both is Aspen room.”

**Acceptable representation alternatives:**

- `alternatives`: Keep a source qualifier with alternative date targets and a separate extractor-origin unresolved-reference report. Retains: reported-dates, qualifier, interpretation-limit, venue.
- `shared-condition`: A shared qualified date group retains the exact reported dates and 'one unidentified date is provisional', with an attributed interpretation-limit annotation. It does not assert that both dates are provisional. Retains: reported-dates, qualifier, interpretation-limit, venue.

**Forbidden inferences:**

- “The organizer says they do not know either date, or both dates are definitely provisional.” — The source supplies both dates and leaves the qualifier's referent unidentified; the extractor's limitation is not a source statement of ignorance.
- “Both dates are confirmed, or all information including the venue must be withheld.” — The first drops a material unresolved qualifier; the second discards unaffected supported meaning.

**Pertinent current projection:** Drill: 2030-02-14; briefing: 2030-02-15. One date is provisional, but w1 does not identify which. Venue for both: Aspen room.

**History/recovery boundary:** The hypothetical extractor report stays derived interpretation metadata, not another corroborating source.

### 04-question-and-directive: An action can be about a date without assigning the date

Example SHA-256: `b212dfdf06b6ec79a95940e4cb6ca59afcc7037c68c9c8a296f1cf4292fc2297`

**Decision:** Separate the question's content, the directive's action object/condition, its topic, and any world effect.

Storing the organizer's request does not assign a new task to a person or to Doozer.

**Frames:** w1 = s1. Current view: w1. These are bounded supplied snapshots, not global coverage or durable-ingestion guarantees.

**Source s1 — organizer, said 2030-02-12:**

> The briefing venue is Aspen room. Is the briefing on 2030-02-16? Please check the calendar before making travel plans; that question is not a confirmed schedule.

**Proposed material interpretation:**

- `venue` (assertion; origin=source; basis=w1; about=venue; required): The briefing venue is reported as Aspen room. Anchor: source:s1 “The briefing venue is Aspen room.”
- `question` (question; origin=source; basis=w1; about=date; required): The proposition 'briefing date = 2030-02-16' is asked, not asserted. Retain which date was asked about. Anchor: source:s1 “Is the briefing on 2030-02-16?”
- `request` (directive; origin=source; basis=w1; about=date; action={"condition": "before making travel plans", "object": "calendar", "verb": "check"}; required): The requested action is checking the calendar before travel plans; date is its topic, not an assigned scalar value. Anchor: source:s1 “Please check the calendar before making travel plans”
- `derived-unknown` (derived-state; origin=derived; basis=w1; about=date; optional): The effective date is unestablished in w1. This can be derived without a separately stored unknown atom; it is not a claim that the organizer is personally ignorant. Anchor: source:s1 “that question is not a confirmed schedule.”

**Acceptable representation alternatives:**

- `separate-arguments`: Separate question content and directive action, with about(date) and no world-date effect. Derive the unknown date when projecting w1. Retains: venue, question, request.
- `typed-topic-link`: A kind-qualified topic binding on the directive is acceptable if every role and consumer knows it means about(date), not date assignment. An extra derived-unknown annotation is also acceptable, not a reason to force disagreement. Retains: venue, question, request, derived-unknown.

**Forbidden inferences:**

- “The briefing takes place on 2030-02-16, or checking the calendar changes its date to that value.” — A question and an action about a date are not assertions or changes of the world date.
- “Any link from the directive to the date binding is intrinsically a material error.” — An explicitly typed about-topic link is legitimate. Ambiguous overloading should be diagnosed as a contract ambiguity, not settled by critic votes.

**Pertinent current projection:** Venue: Aspen room. 2030-02-16 is mentioned in a question, not confirmed; checking the calendar was requested before travel planning. The date is not confirmed in w1.

**History/recovery boundary:** A venue-only answer need not repeat the request, but its content and conditions remain source-linked and recoverable.

### 05-assurance-withdrawal: Withdrawing the only assurance does not revoke permission

Example SHA-256: `3942bfa88bb77be18301779ec886d33278830c802bb4043c7de0f934c1728492`

**Decision:** Target the assurance; distinguish loss of current support from a negative permission fact.

The supplied snapshot contains no separate grant or independent current permission evidence. The coordinator is the declared authority for these fictional notices. A separate live grant, if present, would not be revoked by assurance withdrawal.

**Frames:** w1 = s1; w2 = s1, s2. Current view: w2. These are bounded supplied snapshots, not global coverage or durable-ingestion guarantees.

**Source s1 — coordinator, said 2030-04-10:**

> My assurance is that booked visitors are permitted entry at the Lark session on 2030-04-12. The venue is Hazel room. This is a report of the arrangement, not a new permission grant.

**Source s2 — coordinator, said 2030-04-11:**

> I withdraw the assurance in s1 pending inspection. I am not revoking permission, and I now make no finding that visitor entry is permitted or forbidden. The venue record is unchanged.

**Proposed material interpretation:**

- `assurance` (assurance; origin=source; basis=w1; holder=coordinator; about=permission; required): The coordinator assured permitted visitor entry for this session; this was not a grant and is no longer a current endorsement after s2. Anchor: source:s1 “My assurance is that booked visitors are permitted entry at the Lark session on 2030-04-12.”
- `withdrawal` (assurance-withdrawal; origin=source; basis=w2; about=permission; target=assurance; required): s2 withdraws the assurance, not the underlying permission or unrelated facts in s1. Anchor: source:s2 “I withdraw the assurance in s1 pending inspection.”
- `current-limit` (source-uncertainty; origin=source; basis=w2; holder=coordinator; about=permission; required): The coordinator now supplies no permitted/forbidden finding. With the only assurance withdrawn, current permission is unestablished in w2. Anchor: source:s2 “I am not revoking permission, and I now make no finding that visitor entry is permitted or forbidden.”
- `venue` (assertion; origin=source; basis=w2; about=venue; required): Hazel room remains the supported venue in w2; the change targets only the assurance. Anchor: source:s1 “The venue is Hazel room.”; source:s2 “The venue record is unchanged.”

**Acceptable representation alternatives:**

- `act-target`: An assurance act carries the permission proposition; withdrawal targets that act. Keep the current support gap and venue independently. Retains: assurance, withdrawal, current-limit, venue.
- `endorsement-link`: A source-linked proposition with an assurance/endorsement relation can instead lose that current endorsement; the original proposition and venue history remain reachable. Do not flip its world polarity. Retains: assurance, withdrawal, current-limit, venue.

**Forbidden inferences:**

- “Visitor entry is forbidden, or all facts in s1 are retired.” — The assurance, not permission or venue, was withdrawn.
- “Assurance withdrawal always makes permission unknown even if another valid grant remains current.” — The unestablished result here depends on the stated lack of other current support, not a universal withdrawal rule.

**Pertinent current projection:** Venue: Hazel room. Visitor permission is not established by current support in w2; the earlier assurance was withdrawn, not replaced by a prohibition.

**History/recovery boundary:** The original assurance, its withdrawal, and the unaffected venue stay independently traceable.

### 06-permission-revocation: Revoking an actual grant changes the normative permission

Example SHA-256: `f601726416009adf342301b465a72cfde9df0797e164ab241518c100219fbb47`

**Decision:** Distinguish a permission act from an assurance act and from physical access observations.

The coordinator is stipulated to be authorized for the fictional session, with no later restoration. The scope is this session only.

**Frames:** w1 = s1; w2 = s1, s2. Current view: w2. These are bounded supplied snapshots, not global coverage or durable-ingestion guarantees.

**Source s1 — coordinator, said 2030-04-10:**

> I grant booked visitors entry permission for the Reed session on 2030-04-12. The venue is Willow room. This grant applies only to that session.

**Source s2 — coordinator, said 2030-04-11:**

> I revoke the entry permission granted in s1 for the Reed session. This is a permission change, not merely withdrawal of an assurance. It does not change the venue.

**Proposed material interpretation:**

- `grant` (grant; origin=source; basis=w1; about=permission; affects=permission; required): An authorized session-scoped grant permits booked visitor entry until its revocation. Anchor: source:s1 “I grant booked visitors entry permission for the Reed session on 2030-04-12.”
- `revoke` (revocation; origin=source; basis=w2; about=permission; affects=permission; target=grant; required): The grant is revoked for this session; permission under that grant no longer holds in w2. This is not evidence that a physical door is locked. Anchor: source:s2 “I revoke the entry permission granted in s1 for the Reed session.”
- `venue` (assertion; origin=source; basis=w2; about=venue; required): Willow room remains the venue in w2. Anchor: source:s1 “The venue is Willow room.”; source:s2 “It does not change the venue.”

**Acceptable representation alternatives:**

- `act-chain`: Keep the grant and revocation as an act chain; derive the current session permission from it under the declared authority. Retains: grant, revoke, venue.
- `qualified-permission`: A current permission view can state that the grant is revoked if it links back to the grant/revocation and preserves venue and session scope, rather than replacing history with a bare false flag. Retains: grant, revoke, venue.

**Forbidden inferences:**

- “The coordinator merely became uncertain, all visitor access everywhere is forbidden, or the room is physically locked.” — An explicit scoped normative revocation establishes none of those alternative meanings.

**Pertinent current projection:** Booked-visitor permission under this grant is revoked for the Reed session. Venue: Willow room. No physical-door observation is supplied.

**History/recovery boundary:** Keep the earlier grant as history, not a current conflicting permission alongside the explicit revocation.

### 07-resolved-uncertainty: Later evidence resolves a window, not the truth of an earlier honest limitation

Example SHA-256: `11ee890a3b0f31a94280416d7cb97ee0afdab82cd953a72f330ad0748a2736b5`

**Decision:** Update the affected current binding without leaving permanent fog or erasing uncertainty history.

The drill has one effective date. s2 explicitly supplies the previously missing date for the same drill.

**Frames:** w1 = s1; w2 = s1, s2. Current view: w2. These are bounded supplied snapshots, not global coverage or durable-ingestion guarantees.

**Source s1 — coordinator, said 2030-02-11:**

> The drill venue is Pine annex. I have not established its effective date in these notes. This describes my information as of this note.

**Source s2 — coordinator, said 2030-02-12:**

> I can now establish the drill's single effective date as 2030-02-14. This supplies the date absent from s1. The venue remains Pine annex.

**Proposed material interpretation:**

- `earlier-limit` (source-uncertainty; origin=source; basis=w1; holder=coordinator; about=date; required): The coordinator had not established the date in w1; this remains a historical statement, not current global ignorance. Anchor: source:s1 “I have not established its effective date in these notes.”
- `new-date` (assertion; origin=source; basis=w2; about=date; required): s2 establishes the reported effective date 2030-02-14 for the same drill in w2, distinct from the 2030-02-12 statement date. Anchor: source:s2 “I can now establish the drill's single effective date as 2030-02-14.”
- `venue` (assertion; origin=source; basis=w2; about=venue; required): Pine annex remains the known venue, unaffected by the date update. Anchor: source:s1 “The drill venue is Pine annex.”; source:s2 “The venue remains Pine annex.”

**Acceptable representation alternatives:**

- `framed-condition`: Keep the explicit earlier source condition framed to w1 and derive the established date in w2; no contradiction between those different claims. Retains: earlier-limit, new-date, venue.
- `current-plus-history`: A compact current view gives the new date and venue with a traversable source/revision path to the prior uncertainty. The earlier limitation need not be repeated in every current answer. Retains: earlier-limit, new-date, venue.

**Forbidden inferences:**

- “The date remains unknown forever, s1 is now false, or the effective date is 2030-02-12.” — Later establishment changes current support, not what was established in w1; statement and effective times remain distinct.

**Pertinent current projection:** As of w2, reported effective date: 2030-02-14. Venue: Pine annex.

**History/recovery boundary:** A deliberate history lookup recovers the coordinator's uncertainty in w1 and the source that resolved it; no need to crowd every answer with it.

### 08-local-conflict: A real date conflict does not make an agreed venue unknown

Example SHA-256: `a670d3952d25e961abd6491913153ba7d462f9354fe058faa1bf4af8cbe4a477`

**Decision:** Preserve both current date assertions without choosing by recency or holding unrelated knowledge.

Sources have equal declared authority and refer to the same one-day session. No source establishes supersession or rescheduling.

**Frames:** w1 = s1, s2. Current view: w1. These are bounded supplied snapshots, not global coverage or durable-ingestion guarantees.

**Source s1 — scheduler-a, said 2030-03-01:**

> The one-day session is scheduled for 2030-03-11. Its venue is Maple room. This is our current notice.

**Source s2 — scheduler-b, said 2030-03-02:**

> The same one-day session is scheduled for 2030-03-12. Its venue is Maple room. I have not established that either notice supersedes the other.

**Proposed material interpretation:**

- `first-date` (assertion; origin=source; basis=w1; about=date; required): s1 asserts 2030-03-11 for the session. Anchor: source:s1 “The one-day session is scheduled for 2030-03-11.”
- `second-date` (assertion; origin=source; basis=w1; about=date; required): s2 asserts 2030-03-12 for that same single-day session. Anchor: source:s2 “The same one-day session is scheduled for 2030-03-12.”
- `conflict` (contested; origin=derived; basis=w1; about=date; required): These date assertions conflict without a supported resolution. Recency is not a supersession proof. Anchor: source:s1 “2030-03-11”; source:s2 “I have not established that either notice supersedes the other.”
- `venue` (assertion; origin=source; basis=w1; about=venue; required): Both sources report Maple room. The date dispute does not establish venue uncertainty or independent corroboration by itself. Anchor: source:s1 “Its venue is Maple room.”; source:s2 “Its venue is Maple room.”

**Acceptable representation alternatives:**

- `competing-claims`: Separate date claims and a derived conflict condition, with the venue kept available under its own binding. Retains: first-date, second-date, conflict, venue.
- `qualified-date-group`: A date alternative group preserves both source-linked values and their unresolved incompatibility, without a separate independently maintained contested flag. The venue is still answerable. Retains: first-date, second-date, conflict, venue.

**Forbidden inferences:**

- “The session moved to 2030-03-12 because s2 is newer, or all information including venue must be withheld.” — There is no established move/supersession, and the venue binding is unaffected.
- “The two venue statements prove independent corroboration or a duty to create a resolution ticket.” — Origin independence is not supplied, and uncertainty is not automatically an assigned task.

**Pertinent current projection:** Date unresolved: sources give 2030-03-11 and 2030-03-12 without an established supersession. Venue: Maple room.

**History/recovery boundary:** Retain both date assertions and their context; do not invent a rescheduling event or an intervention queue.
