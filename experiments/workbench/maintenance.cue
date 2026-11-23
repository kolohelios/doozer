package workbench

#Consolidated: #Assertion & {
	id:          "retry-safety-current"
	text:        #Scoped.text + " " + #Correction.text
	scope:       "database-writes-notifications-manual-and-automatic-retries"
	attribution: "inferred"
	evidence: [for citation in #Scoped.evidence {citation}, for citation in #Correction.evidence if citation.source != "manual" {citation}]
}

maintenance: {
	version:  "retry-maintenance-offline-v1"
	scenario: "retry-safety"
	status:   "hand-authored-patch-playback-not-model-quality-or-approved-semantic-gold"
	baseline: "Same recorded additions and accounting, but omit retire operations. This is an append-only patch ablation, not an independently generated summarization baseline."
	queries: ["notifications", "database writes", "manual replay", "automatic retries", "implementation", "payments"]
	references: ["retry-guidance", "database-writes", "notification-exception", "retry-safety-scoped"]
	rollbackPosition: 3
	consolidation: {
		analysis: #Analysis & {assertions: [#Consolidated]}
		route: #Route & {action: "analyze"}
		patch: #Patch & {
			baseRevision: 5
			accounting: {}
			operations: [
				{op: "add", assertion: #Consolidated},
				{op: "retire", id: "retry-safety-scoped", replacement: "retry-safety-current", reason: "Unify the execution-path explanation with its contextual automatic-retry restriction."},
				{op: "retire", id: "automatic-retry-boundary", replacement: "retry-safety-current", reason: "Preserve the correction in the same current explanation, keeping its original reply context."},
			]
			rationale: "Source-free consolidation of existing understanding, not new evidence or a new source receipt."
		}
		repeatPatch: #Patch & {baseRevision: 6, accounting: {}, operations: [], rationale: "The consolidated view is unchanged; no further maintenance effect."}
	}
	expected: {
		"scoped-mitigation": {maintained: 1, appendOnly: 4}
		"echo-and-projection": {maintained: 3, appendOnly: 6}
		"maintenance-consolidation": {maintained: 2, appendOnly: 7}
	}
	limitations: [
		"Authored patches demonstrate executable maintenance and recovery, not an autonomous model choosing semantically correct transformations.",
		"Reader probes return lexical candidates, original-source anchors, and historical matches, not generated answers or general fuzzy understanding.",
		"Counts and word totals are structural compactness diagnostics. Meaning preservation remains evaluator-side, not a compression score or release guarantee.",
		"Local recovery is not durable ingestion, crash-safe persistence, concurrency isolation, or a source deletion mechanism.",
	]
}
