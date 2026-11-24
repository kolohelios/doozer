package workbench

contrastObservations: {
	status: "two-accounted-noops-utility-review-pending"
	artifact: {
		path:           "experiments/workbench/results/first-maintenance-contrast.json.gz"
		sha256:         "783d037053a552bd6f877301af76d3f837aa2c2609f3cb0dd0a288964c9244c7"
		bytes:          76972
		rawSHA256:      "8fbc3f24a931b379c34031bae1aab93740db5a42e62208a9306056dbb1f66886"
		rawBytes:       853975
		protocolSHA256: "a6950b007760bb4971d53afa30323bacfdff036fcfafdaf6794228f0855e2e9e"
		sourceCommit:   "85f9392e27f20ae6e9d2d4dc707723b06d945929"
	}
	authorization: "User explicitly replied yes to the direct request to authorize two frozen GPT-4.1/OpenAI calls within $0.30 total and no retries. PR #28 was still open; merge was not used as spending authorization. This scope is consumed, not transferable."
	order: ["case-b", "case-a"]
	calls: {planned: 2, submitted: 2, accounted: 2, retries: 0, unknownBilling: 0}
	knownCostUSD:          0.011594
	localBudgetUSD:        0.30
	initialReservationUSD: 0.254169
	requestedModel:        "openai/gpt-4.1"
	provider:              "OpenAI"
	cases: {
		"case-a": {
			protocolSHA256:   "011b7f263570f44c48fc8a27df3041f1d25c94e88f4a9e09bbfb9991eb61e532"
			inputClaims:      3
			outputClaims:     3
			knownCostUSD:     0.005450
			promptTokens:     2129
			completionTokens: 149
			proposal: {baseRevision: 5, accounting: {}, operations: [], rationale: "A source-free maintenance patch is appropriate here because the current claims already accurately reflect the distinctions, uncertainties, and evidence present in the supplied sources. The claims preserve the nuanced boundaries between database write deduplication, notification side effects, and the manual replay path, as well as the explicit rejection of extending manual suppression to automatic retries. The ambiguous 'Stop.' remains correctly detached. No new synthesis, clarification, or consolidation is warranted without additional evidence or a change in interpretive context. This no-op serves readers by maintaining a careful, evidence-aligned view without introducing unwarranted changes or erasing important distinctions."}
		}
		"case-b": {
			protocolSHA256:   "4fab89f586bbc5b96758c8de7e99ca955fbd6f596493783d3b99ca85a4bb7257"
			inputClaims:      6
			outputClaims:     6
			knownCostUSD:     0.006144
			promptTokens:     2472
			completionTokens: 150
			proposal: {baseRevision: 5, accounting: {}, operations: [], rationale: "A source-free maintenance patch is appropriate here because the current claims already accurately reflect the distinctions, uncertainties, and evidence boundaries present in the supplied sources. Each claim preserves the material differences between database write deduplication and notification side effects, the scope of manual replay, and the limits of retry safety guidance. No new synthesis, clarification, or consolidation is warranted without additional evidence or a change in interpretive context. Retaining the current structure and content best serves readers by maintaining explicit attributions, scope boundaries, and recoverable evidence paths, while not introducing unwarranted certainty or collapsing distinctions that remain relevant to consumers."}
		}
	}
	outcome: {
		materialUnchanged:                true
		recovery:                         "not-exercised-no-change"
		semanticJudgment:                 "pending-human-review"
		selectiveMaintenanceDemonstrated: false
		canonicalAcceptance:              false
		externalPublication:              false
	}
	interpretation: [
		"Both mechanically valid no-ops retain their own working views, citations, history, aliases, projections, reader probes, and revisions exactly. No nontrivial generated transformation or recovery was demonstrated.",
		"Both rationales condition consolidation on additional evidence or changed interpretive context, despite the common v0.5 instruction that lack of new sources alone does not justify no-op. This raises an objective/representation-maintenance concern, not a calibrated semantic failure label.",
		"Accurate existing claims do not alone establish that their current representation is useful or free of avoidable redundancy. The replies give no detailed comparison of overlap or alternative reader access. Whether either no-op is warranted remains pending review; neither was forced to match an authored layout or node count.",
		"This is one pair of reused authored development views under one prompt/model/provider configuration, not independent held-out evidence of general model capability. Equal action choices do not prove equal utility or inability to distinguish inputs.",
		"No further call, repair, replacement, judge, provider/account check, billing lookup, or use of unused budget occurred. Parent and child receipts remain consumed; the old one-call no-op and its layout clarification are unchanged.",
	]
}
