package judgment

scalePlan: {
	version:                 "larger-reviewed-contract-pair-v1"
	referenceStatus:         "fresh-template-derived-synthetic-development-probes-provisional-authored-references-not-independent-gold"
	maxBudgetUSD:            5
	maxCalls:                84
	retries:                 0
	maxRequestBytes:         131072
	maxResponseBytes:        1048576
	transportTimeoutSeconds: 300
	maxOutputTokens:         8000
	orderSeed:               "larger-reviewed-contract-pair-v1"
	roles:                   reviewedPanelPlan.roles
	extract:                 "Interpret the correspondence using the complete common contract and declared binding/topic vocabulary. You are not answering evaluation hypotheses. Every visible source gets exactly one entry; unrelated conversation may have empty arrays. Preserve original statements, stance, qualifications, action objects, and scope without inventing facts or tasks. Source statement time is not an event's effective date. Speculation is not world support/opposition. Questions are not assertions; their value slots hold canonical scalar literals, not full sentences. The checker, not your report, produces rejections. Use other or empty entries for derived digests, not new primary assertions. Do not introduce personal ignorance from source/window coverage. Limits on your interpretation belong in extractionLimits, not source assertions. You receive neither references nor peer outputs."
	audit:                   auditReportV2.instructions
	policy:                  "Twelve new sixteen-message threads, extracted independently at eight and sixteen messages. Three fixed real calls per snapshot plus one separate authored final-window control per thread: 84 calls. Exact same primary output and checks serve all paired policies. Four clean equivalence controls and eight mechanically admissible identical shared faults are separate from real outputs. No retries, repair, fallback, consensus round, canonical acceptance, deletion, or retirement. Stop the whole run on unknown accounting, transport/credit failure, or inability to reserve the next request; a top-up does not restart it."
	scoring: [
		"Compare single plus deterministic checks, add blind verification, then add the real auditor. Agreement is not truth. No policy substitutes verifier facts. Candidate flags do not delete source-qualified views.",
		"Keep all 24 snapshots, 72 scalar query cells per extractor, 72 binding assessments per policy, 12 paired threads, and 12 controls in denominators. Availability is distinct from fidelity. Separate known reported cost, unknown billing, and reservations; the $5 bound is local, not provider/global enforcement.",
		"Provisional binding-local material profiles retain scalar assertions/provenance, history, targeted acts, questions, qualifiers, personal-ignorance holder/frame, and speculative proposition/attribution. Known-origin same-speaker directive repeats normalize; a declared procedure-topic link lowers to the same about-binding act. Literal casing/spacing and binary complements use the existing finite normal form, not general language equivalence.",
		"Source-note condition nodes are optional under reviewed explicit/derived coverage recovery: bound the window and retain the exact source catalogue. Do not penalize node presence alone. Preserve and report their raw differences separately for inspection; this metric does not prove every source-note annotation's entailment. Personal ignorance is not optional coverage.",
		"Grade raw typed profiles including mechanically rejected proposals separately from filtered four-state query results, missing/extra profile memberships, unsupported/missing polarities, diagnostic flags, unaffected knowledge, and prefix/final transitions. Memberships overlap and are not independent semantic units or population samples.",
		"A binding-coincident auditor challenge is not proof its reason identifies the actual defect. Proposed false challenges/holds remain relative to provisional profiles. Read issue text and control anchors. Unavailable or unattempted controls are not semantic detection misses.",
		"New prose uses twelve authored semantic cores and a shared sixteen-message correspondence envelope. It is larger and fresh relative to prior model requests, not independently sampled real correspondence. Fixtures/labels and shared contracts are frozen before any paid role call.",
	]
}

#ScaleBinding: {id: string, subject: string, property: "effective-date" | "permission" | "quiet-mail" | "location", scope: string, validTime: *null | string, values: *[] | [...string], authority: *"coord" | string}
#ScaleInterpretation: {atoms: *[] | [...#TransferAtom], annotations: *[] | [...]}
#ScaleCase: {
	subject:  string
	room:     string
	property: "effective-date" | "permission" | "quiet-mail"
	scope:    string
	time:     *null | string
	values: *[] | [...string]
	secondarySubject:  string
	secondaryProperty: "effective-date" | "permission" | "quiet-mail"
	secondaryScope:    string
	secondaryTime:     *null | string
	secondaryValues: *[] | [...string]
	target:          string
	secondaryTarget: string
	states: {w0: string, w1: string}
	reply13:       *"m1" | string
	missingParent: *false | bool
	topic:         *"calendar-use" | string
	messages: [string]:  string
	reference: [string]: #ScaleInterpretation
	control: {kind: "fault" | "equivalent", mode: "hunch-world" | "add-world" | "omit-kind" | "omit-origin-world" | "drop-note" | "procedure-layout" | "duplicate" | "qualifier-layout", span: string, binding: string, atom?: #TransferAtom, targetKind?: string}
}
scaleCases: [string]: #ScaleCase

// A fixed envelope makes the expanded source size explicit; it is not claimed
// to be independently authored natural correspondence or a new truth oracle.
scaleCorpus: {for id, c in scaleCases {
	"\(id)": {
		bindings: [
			#ScaleBinding & {id: "b0", subject: c.subject, property: c.property, scope: c.scope, validTime: c.time, values: c.values},
			#ScaleBinding & {id: "b1", subject: c.subject + " location record", property: "location", scope: "stable location associated with this thread"},
			#ScaleBinding & {id: "b2", subject: c.secondarySubject, property: c.secondaryProperty, scope: c.secondaryScope, validTime: c.secondaryTime, values: c.secondaryValues},
		]
		topics: {"\(c.topic)": ["b0"]}
		queries: [{id: "q0", binding: "b0", value: c.target, expected: c.states}, {id: "q1", binding: "b1", value: c.room, expected: {w0: "supported", w1: "supported"}}, {id: "q2", binding: "b2", value: c.secondaryTarget, expected: {w0: "supported", w1: "supported"}}]
		reference: c.reference
		control:   c.control
		sources: [for i, label in ["m1", "m2", "m3", "m4", "m5", "m6", "m7", "m8", "m9", "m10", "m11", "m12", "m13", "m14", "m15", "m16"] {
			id:        label
			actor:     string
			authority: string
			origin:    string
			frame:     string
			sentAt:    string
			replyTo:   *null | string
			derivedFrom: *[] | [...string]
			text: string
			if i < 8 {frame: "w0", sentAt: "2032-01-01T09:\(10+i):00Z"}
			if i >= 8 {frame: "w1", sentAt: "2032-01-02T09:\(10+i):00Z"}
			if label == "m1" || label == "m3" || label == "m5" || label == "m10" || label == "m13" {actor: "Leah", authority: "coord"}
			if label == "m4" || label == "m14" {actor: "Owen", authority: "coord"}
			if label == "m6" || label == "m7" || label == "m11" || label == "m15" {actor: "Mira", authority: "participant"}
			if label == "m2" || label == "m9" || label == "m12" {actor: "Noah", authority: "logistics"}
			if label == "m8" || label == "m16" {actor: "Digest", authority: "projection"}
			if label == "m1" || label == "m8" || label == "m10" || label == "m13" || label == "m16" {origin: "planning-record"}
			if label == "m3" {origin: "source-stance"}
			if label == "m4" || label == "m14" {origin: "other-notice"}
			if label == "m5" {origin: "secondary-record"}
			if label == "m6" || label == "m15" {origin: "procedure"}
			if label == "m7" || label == "m11" {origin: "participant-question"}
			if label == "m2" || label == "m9" || label == "m12" {origin: "housekeeping-\(label)"}
			if label == "m2" {text: "The supply boxes for \(c.subject) have reached the reception desk. The labels describe contents and delivery contacts, not the setting or authorization being discussed here. I have put the packing list beside the empty cartons."}
			if label == "m9" {text: "The projector cable is back in the equipment cupboard after yesterday's check. We also found the missing trolley handle. This equipment note is separate from the open question in the \(c.subject) conversation."}
			if label == "m12" {text: "The catering team has finished counting mugs for a separate lunch. Its attendance sheet belongs to that lunch rather than to \(c.subject). I am keeping the lunch paperwork in its own folder so the two records do not get mixed."}
			if label == "m8" {text: "I made an index digest that links back to m1 for the \(c.subject) record. It is a derived aid to finding that original paragraph. There is no additional observation, confirmation, grant, or correction behind this copy.", derivedFrom: ["m1"]}
			if label == "m16" {text: "The index digest now links to m13 as well as the earlier correspondence about \(c.subject). This is still a projection of the cited record, not a fresh witness. The original messages remain the place to recover scope and qualifications.", derivedFrom: ["m13"]}
			if label != "m2" && label != "m9" && label != "m12" && label != "m8" && label != "m16" {text: c.messages[label]}
			if label == "m13" {replyTo: c.reply13}
			if label == "m7" && c.missingParent {replyTo: "absent-parent"}
		}]
	}
}}
