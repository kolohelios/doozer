package workbench

// Compact captured observations from synthetic live runs, not expected outputs.
// The first patch deliberately predates #Patch.accounting and is invalid today.
observations: {
	dateUTC: "2026-11-22"
	roles: {
		router:    "typesafe/jev-1.14-20261014"
		analysis:  "openai/gpt-4.1-mini"
		reasoning: "deepseek/deepseek-v3.2"
	}
	v1: {
		promptRevision:  "retry-slice-v1"
		calls:           12
		reportedCostUSD: 0.00566076
		step:            "scoped-mitigation"
		incoming: ["clarification", "manual"]
		analysisExtracted: ["Database writes are deduplicated; notification side effects are not.", "Manual replay suppresses outbound notifications."]
		lastPatch: {
			baseRevision: 3
			operations: [
				{op: "retire", id: "retry-safe-limited-to-database-writes", replacement: "retry-database-writes-safe", reason: "The existing claim's text and scope are ambiguous and could be misinterpreted. The scope is 'database-writes' but the text's concluding phrase about safety 'due to deduplication' introduces an overgeneralization by implying the single documented mechanism is a complete guarantee. It should be replaced by a narrower assertion that captures the safe prevention of duplicate writes."},
				{op: "add", assertion: {
					id:          "retry-database-writes-safe"
					text:        "Retrying a failed event prevents duplicate database writes due to deduplication by event ID."
					scope:       "database-writes"
					attribution: "inferred"
					evidence: [
						{source: "retry", quote: "Yes, failed events can be retried safely."},
						{source: "code", quote: "We deduplicate database writes by event ID."},
						{source: "incident", quote: "Retrying a failed production event caused two customer notifications."},
					]
				}},
			]
			rationale: "The incoming sources 'clarification' and 'manual' are already processed and do not create new operations. All existing assertions are active and generally correct; however, 'retry-safe-limited-to-database-writes' contains a subtle overgeneralization. Its text frames deduplication as the mechanism for safety, which the incident report shows is incomplete (safety does not extend to notifications). To preserve the material counterexample and avoid a canonical support error, the assertion is retired and replaced with a more precise statement: 'prevents duplicate database writes due to deduplication'. This retains all original citations, preserves the incident as a counterexample to broader idempotence, and corrects the scope to 'database-writes' without implying a universal mitigation. The other claims ('idempotent-event-processing-enforced', 'incident-retry-duplicate-notifications') remain active as they accurately represent expressed guidance and observed facts."
		}
		review: "Material failure: omitted manual mitigation; incorrectly treated incoming sources as already processed. The current accounting contract rejects this historical response."
	}
	v2: {
		promptRevision:   "retry-slice-v2"
		calls:            12
		reportedCostUSD:  0.005672781
		step:             "scoped-mitigation"
		activeClaimCount: 6
		activeSourceIDs: ["clarification", "code", "guide", "incident", "manual", "retry"]
		manualClaim: {
			id:          "manual-replay-suppresses-notifications"
			text:        "Manual replay suppresses outbound notifications."
			scope:       "manual-replay"
			attribution: "expressed"
			evidence: [{source: "manual", quote: "Manual replay suppresses outbound notifications."}]
		}
		broadClaimStillActive: {
			id:          "safe-retry-of-failed-events"
			text:        "Failed events can be retried safely."
			scope:       "unspecified"
			attribution: "expressed"
			evidence: [{source: "retry", quote: "Yes, failed events can be retried safely."}]
		}
		review: "Coverage improved, but a flat attributed-claim list is not yet the desired compact qualified understanding; original broad guidance remains active. Not a semantic pass."
	}
}
