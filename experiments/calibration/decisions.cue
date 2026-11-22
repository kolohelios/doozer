package calibration

// Accepted interpretation policy only; this does not approve draft labels.
interpretationPolicy: {
	status:                "accepted"
	scope:                 "Contextual correspondence and separation of answer behavior from evidence/history retention."
	primaryPath:           "Interpret corrections using reply links and surrounding thread context; terse isolated messages are robustness probes, not the assumed normal workload."
	missingContext:        "Retain the source and supported partial meaning, expose the missing referent, and do not invent a target or change unrelated guidance."
	answerHistoryBoundary: "An unrelated unscoped intervention need not appear in every question answer; preserving it must be assessed in evidence/history, not inferred from answer omission."
	labelApproval:         "pending-user-review"
	otherDecisions:        "Standalone directive completeness, safety shorthand, source-independence rendering, and evidence-bundle labels remain unresolved."
}
