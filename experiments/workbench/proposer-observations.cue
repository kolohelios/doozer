package workbench

proposerObservations: {
	status: "one-accounted-call-noop-only-meaning-review-pending"
	artifact: {
		path:                    "experiments/workbench/results/first-maintenance-proposer.json.gz"
		sha256:                  "b33d871334ce6cadd417cfcd066de2d313c7084e8b8f86b444ac44576524fbb9"
		bytes:                   25459
		rawSHA256:               "6c4ffd7ef055a30dcf3abc2b1e5f60ce4776821f0234029b94f935ad3e306adc"
		rawBytes:                265223
		protocolSHA256:          "42e951b2de3d064265c8518aee521c2896a3a5bd0cd06e90db94dcd6ccd83e03"
		checkpointSHA256:        "cb5b84b4cc1a4953c51361e1238efb3bf192d515d353cc82574051ad7d1c7f00"
		preparationSourceCommit: "5946f6532b31b722ee8c87defc3cd5fdf0c051e1"
		mergedExecutionBase:     "2d427f468c22ac0cd19c197b27250a93e437a61b"
	}
	authorization: "User instructed execution in reply to the direct request to authorize the frozen one-call GPT-4.1/OpenAI request within $0.15. This is not inferred from PR merge alone and does not authorize another call."
	calls: {planned: 1, submitted: 1, accounted: 1, retries: 0, unknownBilling: 0}
	requestedModel:        "openai/gpt-4.1"
	servedModel:           "openai/gpt-4.1"
	provider:              "OpenAI"
	startedAt:             "2026-11-23T06:53:31.134182+00:00"
	knownCostUSD:          0.004806
	localBudgetUSD:        0.15
	initialReservationUSD: 0.123036
	usage: {promptTokens: 2035, completionTokens: 92, totalTokens: 2127}
	proposal: {baseRevision: 5, operations: [], accounting: {}, rationale: "No new sources are being ingested, and the current claims accurately reflect the distinctions, uncertainties, and evidence present in the supplied sources. Each claim is scoped and attributed appropriately, with ambiguity and boundaries preserved where the evidence is inconclusive or contextually limited. No consolidation, amendment, or retirement is warranted at this checkpoint."}
	outcome: {
		application:         "no-op-in-isolated-copy"
		semanticJudgment:    "pending-human-review"
		beforeClaims:        3
		afterClaims:         3
		materialUnchanged:   true
		recovery:            "not-exercised-no-change"
		canonicalAcceptance: false
		externalPublication: false
	}
	// Subsequent user review is separate from the immutable original run outcome.
	layoutReview: {
		date:           "2026-11-24"
		status:         "user-permitted-integrated-layout"
		artifactSHA256: proposerObservations.artifact.sha256
		userText:       "the automatic-retry restriction doesn't need to stay separate."
		scope:          "At this retry checkpoint, the automatic-retry restriction may be folded into the main retry explanation while retaining its specific scope, reply context, original evidence, and useful recovery/discovery paths. A separate node is not required; integration is permitted, not mandated."
		notApproved: ["the model's no-op was warranted", "all current claims are semantically correct", "a specific merger or fixed target claim count", "blanket policy or other reference meanings", "canonical acceptance or further spending"]
	}
	interpretation: [
		"Observed one syntactically/mechanically valid no-op, not model-selected consolidation, amendment, or retirement. No-op was explicitly permitted; failing to match the authored target is not itself a semantic failure.",
		"The rationale asserts current fidelity but supplies no detailed comparison of whether joining the overlapping explanations would improve usefulness. Lack of incoming sources alone cannot establish that source-free maintenance is unnecessary.",
		"All working claims, citations, old aliases, reader views, source history, and revision remain unchanged. This is not evidence of meaning preservation under a nontrivial transformation or proof that the supplied working interpretation is correct.",
		"The fixture was authored development material, not independent held-out gold. Whether no-op is useful/warranted remains a narrow human meaning review, not a calibrated semantic score or a runtime approval queue.",
		"No second proposal, repair, judge, billing lookup, or provider/account check was made. Unused budget is not spent or transferred to another attempt.",
	]
}
