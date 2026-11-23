# Transfer disputes: proposed meanings

**Pending user review. Zero paid calls; validation and merging grant no approval.**

Generated from [`transfer-review.cue`](../experiments/judgment/transfer-review.cue), using the existing interpretation-review notation. Original sources are checked against the immutable partial-run archive, not model verdicts. Earlier approvals and frozen scores are unchanged.

Packet SHA-256: `fcbaebd37bc47fa9789b879b54450344d6c9b8cbf2994d246e4236078ab20468`
Policy SHA-256: `2fab286273e107488cc9d0853431ded53a6b03fba16ab1f74137b297e92995d7`

Review these examples one at a time. Neither preparation, validation, merging, nor earlier example approvals approves these proposals. Decisions must identify the exact example content; there is no approval-writing or model capability here.

Post-hoc development review of two disputes exposed by the partial transfer run. Not held-out gold, a rescore, a new paid protocol, blanket policy approval, or permission for canonical effects. The audit-report ABI is separate from semantic reference approval.

Approve, reject, or amend one example at a time. Each example hash binds its full sources, proposed meanings, alternatives, projections, and archive context. No decision for one example applies to the other. These are semantic proposals, not new mandatory atom layouts. Mechanical checks verify anchors and declared recovery, not entailment or actual equivalence.

**Proposed scope rule — meaning-before-wire:** Decide source meaning, relevant consumer recovery, and forbidden inferences before selecting field names. Equivalent encodings need inspectable recovery paths. A model verdict or an atom count cannot establish either fidelity or loss.

## 01-coverage-frame: A report's coverage is not its author's personal ignorance

Example SHA-256: `e2c6dc4386fedeacfbeb500d4724f3f4d02123ff7b8a34557b2848553b8a203c`

**Decision:** Pending: preserve the bounded no-finding qualification without inventing a person's knowledge state; allow explicit or derived coverage with the same consumer meaning.

Exact four-message prefix from the archived regional thread, before the later production record. The east observation is a separate scope; the digest is a declared derivative of m1. Speaker attribution is not automatically an epistemic knowledge holder.

**Frozen context:** `regional-coverage/w0`; current window `w0`. Archive SHA-256: `3b95db71031ef55fc10772a6644376e5435f90ea85785d210e4d46ecd5beace4`.

### Exact sources

**Frames:** w0 = m1, m2, m3, m4.

**Bindings:** staging-west-quiet-mail, production-west-quiet-mail, production-west-backup, production-east-quiet-mail.

**m1 — Tess, 2031-07-18T09:00:00Z** (declared authority `operations`, origin `staging-run`, reply `None`, derived from []):

> For the staging-west export scheduler on 2031-07-20, quiet-mail is enabled. This observation covers staging-west only and supplies no production-west finding in these notes. A similar option name is not a reason to transfer the result between environments.

**m2 — Tess, 2031-07-18T09:10:00Z** (declared authority `operations`, origin `backup-record`, reply `None`, derived from []):

> The production-west export backup is stored at Sable vault. That is a location record, separate from the scheduler's quiet-mail setting. The backup record is not a test of notification behavior.

**m3 — Lee, 2031-07-18T09:20:00Z** (declared authority `other-region`, origin `east-run`, reply `None`, derived from []):

> In production-east, quiet-mail is disabled for the export scheduler. That report concerns the east region, not production-west or staging-west. I copied the subject line into this conversation because the option names look alike.

**m4 — Draft, 2031-07-18T09:30:00Z** (declared authority `projection`, origin `staging-run`, reply `None`, derived from ['m1']):

> This digest repeats the staging observation from m1. It is not a production deployment record and does not create another independent test. Its shortened heading should not override the source's environment scope.

### Proposed interpretation

- **staging:** Tess reports quiet-mail enabled for staging-west on 2031-07-20, not for every environment.
  Review fields: `{"about": ["staging-west-quiet-mail"], "affects": [], "holder": null, "id": "staging", "kind": "assertion", "origin": "source", "possibleAbout": [], "required": true, "target": null, "window": "w0"}`. Anchors: source:m1 “For the staging-west export scheduler on 2031-07-20, quiet-mail is enabled.”
- **report-limit:** Tess explicitly limits this observation to staging-west and reports no production-west finding in these notes. Keep the speaker attribution and source-note frame; do not turn it into Tess personally not knowing the production value.
  Review fields: `{"about": ["staging-west-quiet-mail", "production-west-quiet-mail"], "affects": [], "holder": null, "id": "report-limit", "kind": "coverage-limit", "origin": "source", "possibleAbout": [], "required": true, "target": null, "window": "w0"}`. Anchors: source:m1 “This observation covers staging-west only and supplies no production-west finding in these notes.”
- **backup:** The production-west backup is at Sable vault; this independent property remains usable.
  Review fields: `{"about": ["production-west-backup"], "affects": [], "holder": null, "id": "backup", "kind": "assertion", "origin": "source", "possibleAbout": [], "required": true, "target": null, "window": "w0"}`. Anchors: source:m2 “The production-west export backup is stored at Sable vault.”
- **east:** Lee reports quiet-mail disabled in production-east. This is not a finding for production-west or staging-west, and no validity date is borrowed from the other region's observation.
  Review fields: `{"about": ["production-east-quiet-mail"], "affects": [], "holder": null, "id": "east", "kind": "assertion", "origin": "source", "possibleAbout": [], "required": true, "target": null, "window": "w0"}`. Anchors: source:m3 “In production-east, quiet-mail is disabled for the export scheduler.”; source:m3 “That report concerns the east region, not production-west or staging-west.”
- **west-view:** The production-west setting is unestablished within this supplied prefix, neither enabled nor disabled on its evidence. This is bounded coverage, not global absence or anyone's personal ignorance.
  Review fields: `{"about": ["production-west-quiet-mail"], "affects": [], "holder": null, "id": "west-view", "kind": "derived-state", "origin": "derived", "possibleAbout": [], "required": true, "target": null, "window": "w0"}`. Anchors: source:m1 “supplies no production-west finding in these notes”; source:m2 “The backup record is not a test of notification behavior.”; source:m3 “not production-west or staging-west”; source:m4 “It is not a production deployment record and does not create another independent test.”

### Acceptable recovery paths

- **explicit-coverage:** A source-linked coverage condition records no-finding-in-this-note, attributed to Tess as speaker, with the relevant environment and basis window. The current consumer receives that condition; no personal-ignorance claim is added. Source attribution is retained without making Tess the holder of a broader unknown world proposition. Retains: staging, report-limit, backup, east, west-view.
- **derived-coverage:** The original explicit scope clause remains anchored and the consumer derives no production-west finding from the identified four-message window and its scoped assertions. No extra unknown atom is required. A legacy holder/unknown encoding is equivalent only if its inspectable contract and projection retain this note/report frame, not a person's ignorance; the field name alone proves neither correctness nor error. Retains: staging, report-limit, backup, east, west-view.

### Forbidden inferences

- “Tess or Lee personally does not know production-west's setting.” A report's scope and lack of a finding do not establish its author's overall knowledge.
- “Production-west is disabled because east is disabled, or enabled because staging is enabled.” Different scoped variables do not transfer support or opposition.
- “No production-west finding exists anywhere, or the repeated digest independently confirms staging.” Coverage is bounded; a declared derivative supplies no new independent observation.
- “A source-uncertainty label alone settles whether a ledger is wrong.” Inspect its actual stance, source-note frame, attribution, and consumer projection. Approval of this meaning does not rescore old fields.

**Pertinent current projection:** Staging-west enabled for the stated date; production-west not established in this four-message prefix; backup at Sable vault. Mention the coverage bound where the production setting is requested. East remains a separate report, not a west finding.

**History/recovery:** Recover all four messages, the exact scope clause and author attribution, and the digest's derivation from m1. A later finding may change the current west view without falsifying this earlier coverage bound. This example approves no later-window interpretation.

## 02-invitation-directive: A warning about using evidence is not a permission assignment

Example SHA-256: `b6e5cd86167e44bc7c6b455b6e1d4672d2f0d58ab58122809ceeb8eb57ae2139`

**Decision:** Pending: preserve the invitation-use warning as a source directive about evidence reuse, with a relevant recovery path; do not require it in every unrelated answer or convert it into prohibition.

Exact eight-message Oak-session thread. The catering invitation belongs to another meeting. The warning's action object is that invitation, its condition is use as permission evidence for another event, and its topic may be an evidence-use procedure linked to the Oak permission question.

**Frozen context:** `independent-grant-survives/w1`; current window `w1`. Archive SHA-256: `3b95db71031ef55fc10772a6644376e5435f90ea85785d210e4d46ecd5beace4`.

### Exact sources

**Frames:** w0 = m1, m2, m3, m4; w1 = m1, m2, m3, m4, m5, m6, m7, m8.

**Bindings:** oak-permission, oak-venue, permission-evidence-use.

**m1 — Gale, 2031-09-18T09:00:00Z** (declared authority `session`, origin `grant-register`, reply `None`, derived from []):

> I grant booked visitors entry permission for the Oak session on 2031-09-21. The venue is Oak hall. This is an actual session-scoped grant, not merely an assurance about some other authorization.

**m2 — Hal, 2031-09-18T09:10:00Z** (declared authority `participant`, origin `other-meeting`, reply `None`, derived from []):

> The catering meeting has a different attendance list. It is not the Oak session. Please do not use its invitation as a visitor permission record for another event.

**m3 — Gale, 2031-09-18T09:20:00Z** (declared authority `session`, origin `inspection-assurance`, reply `None`, derived from []):

> My separate assurance is that booked visitors are permitted entry for the Oak session. This reassurance is not a second grant. The grant already issued in m1 remains a distinct record.

**m4 — Draft, 2031-09-18T09:30:00Z** (declared authority `projection`, origin `grant-register`, reply `None`, derived from ['m1']):

> This is a projection of the grant in m1. Repeating the permission does not issue it again or provide independent corroboration. The venue information is inherited from that same source.

**m5 — Hal, 2031-09-19T09:00:00Z** (declared authority `participant`, origin `other-revocation`, reply `None`, derived from []):

> A different coordinator revoked a permit for the catering meeting. That revocation concerns the other event, not the Oak session or the grant in m1. I am separating the two conversations because their subject lines were similar.

**m6 — Ira, 2031-09-19T09:10:00Z** (declared authority `participant`, origin `permission-question`, reply `None`, derived from []):

> Are booked visitors permitted entry for the Oak session? I am asking about that session, not granting permission myself. My question does not replace the existing source records.

**m7 — Gale, 2031-09-19T09:20:00Z** (declared authority `session`, origin `grant-register`, reply `m3`, derived from []):

> I withdraw the assurance in m3. This withdraws only that endorsement; I do not revoke the grant in m1. The venue remains Oak hall.

**m8 — Draft, 2031-09-19T09:30:00Z** (declared authority `projection`, origin `grant-register`, reply `None`, derived from ['m1', 'm7']):

> This digest derives the session view from the grant and the assurance withdrawal. It is not a new grant or a revocation. Its existence does not change which original acts remain current.

### Proposed interpretation

- **grant:** Gale issues the actual booked-visitor entry grant for the Oak session on 2031-09-21 under the supplied fixture authority.
  Review fields: `{"about": ["oak-permission"], "affects": ["oak-permission"], "holder": null, "id": "grant", "kind": "grant", "origin": "source", "possibleAbout": [], "required": true, "target": null, "window": "w0"}`. Anchors: source:m1 “I grant booked visitors entry permission for the Oak session on 2031-09-21.”
- **venue:** The session venue is Oak hall and remains unaffected by the permission correspondence.
  Review fields: `{"about": ["oak-venue"], "affects": [], "holder": null, "id": "venue", "kind": "assertion", "origin": "source", "possibleAbout": [], "required": true, "target": null, "window": "w0"}`. Anchors: source:m1 “The venue is Oak hall.”
- **warning:** Hal instructs readers not to reuse the catering meeting's invitation as permission evidence for another event. Preserve the source request; it neither assigns permission nor creates a new task. A link to the Oak permission topic is legitimate if it is explicitly about-topic, not a scalar effect.
  Review fields: `{"about": ["permission-evidence-use"], "action": {"condition": "as a visitor permission record for another event", "object": "catering meeting invitation", "verb": "do not use"}, "affects": [], "holder": null, "id": "warning", "kind": "directive", "origin": "source", "possibleAbout": [], "required": true, "target": null, "window": "w0"}`. Anchors: source:m2 “The catering meeting has a different attendance list. It is not the Oak session. Please do not use its invitation as a visitor permission record for another event.”
- **assurance:** Gale separately assures permission; this is not a second grant.
  Review fields: `{"about": ["oak-permission"], "affects": [], "holder": null, "id": "assurance", "kind": "assurance", "origin": "source", "possibleAbout": [], "required": true, "target": null, "window": "w0"}`. Anchors: source:m3 “My separate assurance is that booked visitors are permitted entry for the Oak session. This reassurance is not a second grant.”
- **other-revocation:** The catering permit revocation is scoped to the other event, not the Oak grant.
  Review fields: `{"about": ["oak-permission"], "affects": [], "holder": null, "id": "other-revocation", "kind": "source-qualifier", "origin": "source", "possibleAbout": [], "required": true, "target": null, "window": "w1"}`. Anchors: source:m5 “That revocation concerns the other event, not the Oak session or the grant in m1.”
- **question:** Ira asks whether booked visitors are permitted entry; this creates neither a grant nor an opposing fact.
  Review fields: `{"about": ["oak-permission"], "affects": [], "holder": null, "id": "question", "kind": "question", "origin": "source", "possibleAbout": [], "required": true, "target": null, "window": "w1"}`. Anchors: source:m6 “Are booked visitors permitted entry for the Oak session?”
- **withdrawal:** Gale withdraws only the assurance in m3, not the grant in m1.
  Review fields: `{"about": ["oak-permission"], "affects": [], "holder": null, "id": "withdrawal", "kind": "assurance-withdrawal", "origin": "source", "possibleAbout": [], "required": true, "target": "assurance", "window": "w1"}`. Anchors: source:m7 “I withdraw the assurance in m3. This withdraws only that endorsement; I do not revoke the grant in m1.”
- **current-permission:** The actual Oak grant remains live. The invitation warning restricts what may serve as permission evidence, not the granted permission or physical access.
  Review fields: `{"about": ["oak-permission"], "affects": [], "holder": null, "id": "current-permission", "kind": "derived-state", "origin": "derived", "possibleAbout": [], "required": true, "target": null, "window": "w1"}`. Anchors: source:m1 “I grant booked visitors entry permission”; source:m7 “I do not revoke the grant in m1.”

### Acceptable recovery paths

- **separate-procedure-topic:** Keep the source-linked instruction under permission-evidence-use and provide a discovery/projection path from questions about using the catering invitation for Oak. Keep the actual grant and its scope separate. A permission-only answer can omit the aside when not pertinent; a relevant evidence-use answer cannot lose it. Retains: grant, venue, warning, assurance, other-revocation, question, withdrawal, current-permission.
- **about-topic-or-projection:** Use an explicitly about-topic link to Oak permission, or a reproducible source-linked procedural projection that exposes the same invitation object and condition. No mandatory directive-node count or layout. Merely archiving the warning without a pertinent recovery path is insufficient; an empty per-message atom array alone does not prove loss if another inspectable path preserves it. Retains: grant, venue, warning, assurance, other-revocation, question, withdrawal, current-permission.

### Forbidden inferences

- “Booked visitors are forbidden entry, or the Oak grant is revoked.” A warning against evidence reuse and withdrawal of an assurance do not revoke the separate grant.
- “The warning is meaningless because it appears in a catering aside.” Apparently unrelated context can contain a pertinent procedural instruction; assess the consumer and recovery path.
- “Every permission answer must repeat every aside, or a directive creates a newly assigned task.” Pertinent answer projection differs from history retention and preserving a source act differs from dispatching work.
- “A present or absent directive atom automatically decides which archived model was correct.” Node layout is not meaning preservation; inspect action arguments and relevant recovery. No retrospective score or approval follows from this review.

**Pertinent current projection:** Booked visitors retain the Oak-session permission under m1 and Oak hall remains the venue. For readers asking what the catering invitation establishes, expose the warning against cross-event reuse and point to the actual Oak grant. Do not manufacture a prohibition, physical-door claim, or task.

**History/recovery:** Recover the original instruction, invitation referent, grant, separate assurance and its targeted withdrawal; keep the unrelated revocation scoped. Preserve the declared digest lineage without treating its repetitions as independent grants or witnesses.
