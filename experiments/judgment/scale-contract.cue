package judgment

// Prospective composition only. Do not change the archived contracts or scores.
scaleContract: {
	version: "reviewed-scale-composition-v2"
	status:  "offline-prospective-not-a-live-protocol-or-policy-approval"
	basis:   "Ten individually reviewed development examples. This composition and the reused development corpus are not independently reviewed gold or blanket policy approval. The new framed wire replaces the two legacy source-uncertainty rules and the old wire; the other three base semantic rules are retained verbatim."
	legacyRuleMapping: ["replaced-with-explicit-person-versus-note-frame", "replaced-with-projection-wire-and-recovery", "retained-verbatim", "retained-verbatim", "retained-verbatim"]
	rules: [
		{supports: reviewedContract.rules[0].supports, text: "Separate source-stated conditions, bounded source-window coverage, and extractor limits. Preserve the actual epistemic verb. A source-note no-finding or not-established statement has the source actor as reporter, frame=source-note, and holder=null: it is not personal ignorance. Personal does-not-know has frame=person and holder=source actor. Neither assigns or opposes a world value. Missing reply context is an extractor/context gap, not personal ignorance or world opposition; retain the unavailable-reference marker without guessing scope. Earlier honest conditions remain source-framed history when later evidence establishes a value."},
		{supports: reviewedContract.rules[1].supports, text: "Meaning and inspectable recovery paths matter, not fixed node counts. Qualifiers may appear in atoms or conditions; equivalent duplicates add no evidence. Source-note coverage nodes are optional under the bounded derived coverage view when source qualifications remain recoverable; personal ignorance is not optional coverage. Do not invent a source statement merely because a message lacks a value. Preserve the original source catalogue and history. Declared-origin world repeats and same-actor/same-origin directive repeats may share a material profile without pretending they are independent corroboration or deleting original messages."},
		reviewedContract.rules[2],
		reviewedContract.rules[3],
		reviewedContract.rules[4],
	]
	projection: {
		version:      meaningContract.version
		instructions: meaningContract.instructions
		boundary:     "Use the prospective framed annotation wire described here and in the identical interpretation_schema supplied to every role. Legacy unframed source-uncertainty atoms are unavailable. Do not infer constructor operands from old wire prose. All source identities, scalar bindings, authority, lineage, frames, and topic links are manually supplied conditional premises."
	}
	constructors: {
		assertion:              "eq/neq, exact nonblank source literal, declared scalar binding. Creates a conditional world constraint; dates use canonical ISO dates. This does not prove entailment or truth."
		assurance:              "Same scalar operands as assertion, plus endorsement meaning; not a new grant. Withdrawing the assurance removes only that endorsement's constraint, not an independent authorization."
		question:               "eq/neq with exact asked-about scalar literal. Retains question content but creates no supporting/opposing world constraint."
		directive:              "operator=none, value=null, holder=null. binding is ABOUT the topic, not a scalar assignment. Complete verb/object/condition are contiguous source phrases, case-insensitive; original paragraph resolves referents. No new task or permission effect. A procedure annotation lowers through declared topic links to this constructor."
		grant:                  "Permission-only; operator=none, value=null, holder=null, no prior-target operands. Under declared binding authority, kind=grant itself lowers to a permitted constraint. A null value is REQUIRED, not missing permission status. It is not a physical-door observation or a global permission grant."
		revocation:             "Permission-only; operator=none, value=null, holder=null. targetSource + targetKind=grant + binding identify a prior actual grant under matching declared authority. Retire only that grant; kind=revocation lowers to forbidden for the scoped grant binding, not every permission or physical door."
		"assurance-withdrawal": "operator=none, value=null, holder=null. Targets the specific assurance by targetSource, targetKind=assurance, and binding under matching authority and original actor ownership. Retires that assurance without adding forbidden or revoking a grant."
		supersession:           "operator=none, value=null, holder=null. Targets assertion or qualifier by targetSource, targetKind, and binding under matching declared authority. Never retires every property in a document. Missing/ambiguous prior interpretations and partial multi-topic qualifier targets are rejected, not repaired. No world constraint of its own."
		qualifier:              "operator=one-provisional, binding=null, value=null, holder=null; alternatives name at least two distinct declared bindings. Exactly one unidentified date is provisional, not both unknown. Preserve reported dates and unaffected location. Equivalent atoms/conditions placement and duplicates do not change its meaning."
		other:                  "No material operands, no world effect. Unrelated messages and declared derived digests may use empty entries or other, not new primary facts or annotations. Original digest text and links remain recoverable."
	}
	operands:                 "Every visible source has exactly one ledger entry with nonblank rationale. Non-revision constructors have null targetSource/targetKind; revisions must explicitly name the target in source text or replyTo. Non-directives have action=null. Non-qualifiers have empty alternatives. All core holders are null; personal holders live only in framed annotations. The per-window interpretation_schema is the exact same schema for both extractors and is also supplied to the auditor."
	extractionLimits:         "Your own limitations are not source facts. Every limit cites at least one visible original-source ID in evidence and a nonblank reason; cite the visible reply to explain a missing parent, not the unavailable parent itself. A bounded absence claim must cite the inspected original source window, not an empty evidence array. Empty limits list is allowed."
	auditRationaleProjection: "For both real and control proposals, the audit presentation replaces every ledger rationale with the same placeholder. Original proposal prose must remain separately retained without rewriting. This prevents explicit authored markers and rationale-style differences from identifying controls; it is not proof of complete origin blinding. Typed fields, extractionLimits, original sources, and mechanical diagnostics remain available unchanged. The auditor cannot assess rationale-only qualifications; material meaning must survive in the typed representation and source recovery, not only omitted rationale prose. This is a prospective presentation rule, not a repair of previous results."
	audit:                    "Audit source correspondence under this complete common contract and interpretation_schema, not an imagined wire. Required null grant operands are not missing scalar status. Non-material findings remain visible/nonblocking. Material/unclear/unavailable concerns cannot clear mechanical checks or accept knowledge. Finding evidence IDs must be nonempty and unique; absent proposals cannot receive findings. Structure/literal checks do not establish entailment, completeness, authority authenticity, or independent evidence."
}

scaleContractChecks: {
	version:             "offline-scale-boundary-checks-v1"
	priorProtocolSHA256: scaleObservations.artifact.protocolSHA256
	auditRationale:      "Rationale withheld by the common audit projection; original prose is retained separately."
	fixtureUse:          "Reused development corpus for offline regression only, not fresh held-out evaluation."
	liveExecution:       false
	canonicalAcceptance: false
}
