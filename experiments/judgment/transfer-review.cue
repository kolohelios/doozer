package judgment

transferReview: {
	version:  "transfer-meaning-review-v1"
	status:   "pending-user-review"
	approval: "Review these examples one at a time. Neither preparation, validation, merging, nor earlier example approvals approves these proposals. Decisions must identify the exact example content; there is no approval-writing or model capability here."
	boundary: "Post-hoc development review of two disputes exposed by the partial transfer run. Not held-out gold, a rescore, a new paid protocol, blanket policy approval, or permission for canonical effects. The audit-report ABI is separate from semantic reference approval."
	policies: [{id: "meaning-before-wire", proposal: "Decide source meaning, relevant consumer recovery, and forbidden inferences before selecting field names. Equivalent encodings need inspectable recovery paths. A model verdict or an atom count cannot establish either fidelity or loss."}]
}
transferReviewArchive: {
	path:   "experiments/judgment/results/first-reviewed-transfer.json.gz"
	sha256: "3b95db71031ef55fc10772a6644376e5435f90ea85785d210e4d46ecd5beace4"
}
transferReviewOrigins: {
	"01-coverage-frame":       "regional-coverage/w0"
	"02-invitation-directive": "independent-grant-survives/w1"
}
transferExamples: [string]: #ContractExample
transferExamples: {
	"01-coverage-frame": {
		title:    "A report's coverage is not its author's personal ignorance"
		decision: "Pending: preserve the bounded no-finding qualification without inventing a person's knowledge state; allow explicit or derived coverage with the same consumer meaning."
		context:  "Exact four-message prefix from the archived regional thread, before the later production record. The east observation is a separate scope; the digest is a declared derivative of m1. Speaker attribution is not automatically an epistemic knowledge holder."
		bindings: ["staging-west-quiet-mail", "production-west-quiet-mail", "production-west-backup", "production-east-quiet-mail"]
		sources: [for s in reviewedThreads["regional-coverage"].sources[:4] {id: s.id, actor: s.actor, saidAt: s.sentAt, text: s.text, authority: s.authority, origin: s.origin, replyTo: s.replyTo, derivedFrom: s.derivedFrom}]
		windows: {w0: ["m1", "m2", "m3", "m4"]}
		currentWindow: "w0"
		meanings: [
			{id: "staging", kind: "assertion", origin: "source", window: "w0", about: ["staging-west-quiet-mail"], content: "Tess reports quiet-mail enabled for staging-west on 2031-07-20, not for every environment.", anchors: [{channel: "source", id: "m1", quote: "For the staging-west export scheduler on 2031-07-20, quiet-mail is enabled."}]},
			{id: "report-limit", kind: "coverage-limit", origin: "source", window: "w0", about: ["staging-west-quiet-mail", "production-west-quiet-mail"], content: "Tess explicitly limits this observation to staging-west and reports no production-west finding in these notes. Keep the speaker attribution and source-note frame; do not turn it into Tess personally not knowing the production value.", anchors: [{channel: "source", id: "m1", quote: "This observation covers staging-west only and supplies no production-west finding in these notes."}]},
			{id: "backup", kind: "assertion", origin: "source", window: "w0", about: ["production-west-backup"], content: "The production-west backup is at Sable vault; this independent property remains usable.", anchors: [{channel: "source", id: "m2", quote: "The production-west export backup is stored at Sable vault."}]},
			{id: "east", kind: "assertion", origin: "source", window: "w0", about: ["production-east-quiet-mail"], content: "Lee reports quiet-mail disabled in production-east. This is not a finding for production-west or staging-west, and no validity date is borrowed from the other region's observation.", anchors: [{channel: "source", id: "m3", quote: "In production-east, quiet-mail is disabled for the export scheduler."}, {channel: "source", id: "m3", quote: "That report concerns the east region, not production-west or staging-west."}]},
			{id: "west-view", kind: "derived-state", origin: "derived", window: "w0", about: ["production-west-quiet-mail"], content: "The production-west setting is unestablished within this supplied prefix, neither enabled nor disabled on its evidence. This is bounded coverage, not global absence or anyone's personal ignorance.", anchors: [{channel: "source", id: "m1", quote: "supplies no production-west finding in these notes"}, {channel: "source", id: "m2", quote: "The backup record is not a test of notification behavior."}, {channel: "source", id: "m3", quote: "not production-west or staging-west"}, {channel: "source", id: "m4", quote: "It is not a production deployment record and does not create another independent test."}]},
		]
		representations: [
			{id: "explicit-coverage", description: "A source-linked coverage condition records no-finding-in-this-note, attributed to Tess as speaker, with the relevant environment and basis window. The current consumer receives that condition; no personal-ignorance claim is added. Source attribution is retained without making Tess the holder of a broader unknown world proposition.", retains: ["staging", "report-limit", "backup", "east", "west-view"]},
			{id: "derived-coverage", description: "The original explicit scope clause remains anchored and the consumer derives no production-west finding from the identified four-message window and its scoped assertions. No extra unknown atom is required. A legacy holder/unknown encoding is equivalent only if its inspectable contract and projection retain this note/report frame, not a person's ignorance; the field name alone proves neither correctness nor error.", retains: ["staging", "report-limit", "backup", "east", "west-view"]},
		]
		forbidden: [
			{interpretation: "Tess or Lee personally does not know production-west's setting.", why: "A report's scope and lack of a finding do not establish its author's overall knowledge."},
			{interpretation: "Production-west is disabled because east is disabled, or enabled because staging is enabled.", why: "Different scoped variables do not transfer support or opposition."},
			{interpretation: "No production-west finding exists anywhere, or the repeated digest independently confirms staging.", why: "Coverage is bounded; a declared derivative supplies no new independent observation."},
			{interpretation: "A source-uncertainty label alone settles whether a ledger is wrong.", why: "Inspect its actual stance, source-note frame, attribution, and consumer projection. Approval of this meaning does not rescore old fields."},
		]
		projection: {current: "Staging-west enabled for the stated date; production-west not established in this four-message prefix; backup at Sable vault. Mention the coverage bound where the production setting is requested. East remains a separate report, not a west finding.", history: "Recover all four messages, the exact scope clause and author attribution, and the digest's derivation from m1. A later finding may change the current west view without falsifying this earlier coverage bound. This example approves no later-window interpretation."}
	}
	"02-invitation-directive": {
		title:    "A warning about using evidence is not a permission assignment"
		decision: "Pending: preserve the invitation-use warning as a source directive about evidence reuse, with a relevant recovery path; do not require it in every unrelated answer or convert it into prohibition."
		context:  "Exact eight-message Oak-session thread. The catering invitation belongs to another meeting. The warning's action object is that invitation, its condition is use as permission evidence for another event, and its topic may be an evidence-use procedure linked to the Oak permission question."
		bindings: ["oak-permission", "oak-venue", "permission-evidence-use"]
		sources: [for s in reviewedThreads["independent-grant-survives"].sources {id: s.id, actor: s.actor, saidAt: s.sentAt, text: s.text, authority: s.authority, origin: s.origin, replyTo: s.replyTo, derivedFrom: s.derivedFrom}]
		windows: {w0: ["m1", "m2", "m3", "m4"], w1: ["m1", "m2", "m3", "m4", "m5", "m6", "m7", "m8"]}
		currentWindow: "w1"
		meanings: [
			{id: "grant", kind: "grant", origin: "source", window: "w0", about: ["oak-permission"], affects: ["oak-permission"], content: "Gale issues the actual booked-visitor entry grant for the Oak session on 2031-09-21 under the supplied fixture authority.", anchors: [{channel: "source", id: "m1", quote: "I grant booked visitors entry permission for the Oak session on 2031-09-21."}]},
			{id: "venue", kind: "assertion", origin: "source", window: "w0", about: ["oak-venue"], content: "The session venue is Oak hall and remains unaffected by the permission correspondence.", anchors: [{channel: "source", id: "m1", quote: "The venue is Oak hall."}]},
			{id: "warning", kind: "directive", origin: "source", window: "w0", about: ["permission-evidence-use"], action: {verb: "do not use", object: "catering meeting invitation", condition: "as a visitor permission record for another event"}, content: "Hal instructs readers not to reuse the catering meeting's invitation as permission evidence for another event. Preserve the source request; it neither assigns permission nor creates a new task. A link to the Oak permission topic is legitimate if it is explicitly about-topic, not a scalar effect.", anchors: [{channel: "source", id: "m2", quote: "The catering meeting has a different attendance list. It is not the Oak session. Please do not use its invitation as a visitor permission record for another event."}]},
			{id: "assurance", kind: "assurance", origin: "source", window: "w0", about: ["oak-permission"], content: "Gale separately assures permission; this is not a second grant.", anchors: [{channel: "source", id: "m3", quote: "My separate assurance is that booked visitors are permitted entry for the Oak session. This reassurance is not a second grant."}]},
			{id: "other-revocation", kind: "source-qualifier", origin: "source", window: "w1", about: ["oak-permission"], content: "The catering permit revocation is scoped to the other event, not the Oak grant.", anchors: [{channel: "source", id: "m5", quote: "That revocation concerns the other event, not the Oak session or the grant in m1."}]},
			{id: "question", kind: "question", origin: "source", window: "w1", about: ["oak-permission"], content: "Ira asks whether booked visitors are permitted entry; this creates neither a grant nor an opposing fact.", anchors: [{channel: "source", id: "m6", quote: "Are booked visitors permitted entry for the Oak session?"}]},
			{id: "withdrawal", kind: "assurance-withdrawal", origin: "source", window: "w1", about: ["oak-permission"], target: "assurance", content: "Gale withdraws only the assurance in m3, not the grant in m1.", anchors: [{channel: "source", id: "m7", quote: "I withdraw the assurance in m3. This withdraws only that endorsement; I do not revoke the grant in m1."}]},
			{id: "current-permission", kind: "derived-state", origin: "derived", window: "w1", about: ["oak-permission"], content: "The actual Oak grant remains live. The invitation warning restricts what may serve as permission evidence, not the granted permission or physical access.", anchors: [{channel: "source", id: "m1", quote: "I grant booked visitors entry permission"}, {channel: "source", id: "m7", quote: "I do not revoke the grant in m1."}]},
		]
		representations: [
			{id: "separate-procedure-topic", description: "Keep the source-linked instruction under permission-evidence-use and provide a discovery/projection path from questions about using the catering invitation for Oak. Keep the actual grant and its scope separate. A permission-only answer can omit the aside when not pertinent; a relevant evidence-use answer cannot lose it.", retains: ["grant", "venue", "warning", "assurance", "other-revocation", "question", "withdrawal", "current-permission"]},
			{id: "about-topic-or-projection", description: "Use an explicitly about-topic link to Oak permission, or a reproducible source-linked procedural projection that exposes the same invitation object and condition. No mandatory directive-node count or layout. Merely archiving the warning without a pertinent recovery path is insufficient; an empty per-message atom array alone does not prove loss if another inspectable path preserves it.", retains: ["grant", "venue", "warning", "assurance", "other-revocation", "question", "withdrawal", "current-permission"]},
		]
		forbidden: [
			{interpretation: "Booked visitors are forbidden entry, or the Oak grant is revoked.", why: "A warning against evidence reuse and withdrawal of an assurance do not revoke the separate grant."},
			{interpretation: "The warning is meaningless because it appears in a catering aside.", why: "Apparently unrelated context can contain a pertinent procedural instruction; assess the consumer and recovery path."},
			{interpretation: "Every permission answer must repeat every aside, or a directive creates a newly assigned task.", why: "Pertinent answer projection differs from history retention and preserving a source act differs from dispatching work."},
			{interpretation: "A present or absent directive atom automatically decides which archived model was correct.", why: "Node layout is not meaning preservation; inspect action arguments and relevant recovery. No retrospective score or approval follows from this review."},
		]
		projection: {current: "Booked visitors retain the Oak-session permission under m1 and Oak hall remains the venue. For readers asking what the catering invitation establishes, expose the warning against cross-event reuse and point to the actual Oak grant. Do not manufacture a prohibition, physical-door claim, or task.", history: "Recover the original instruction, invitation referent, grant, separate assurance and its targeted withdrawal; keep the unrelated revocation scoped. Preserve the declared digest lineage without treating its repetitions as independent grants or witnesses."}
	}
}
