package judgment

// Post-observation representation control, not a repair of the first run.
directionPlan: {
	version:               "hypothesis-relative-witness-schema-v1"
	baselineArchiveSHA256: "fa58ee44dc9fed46585d08a8718d381bf8806528dddc83e98c37422175998440"
	maxBudgetUSD:          0.50
	maxCalls:              12
	maxRequestBytes:       65536
	maxOutputTokens:       4000
	retries:               0
	roles: direction: {model: "openai/gpt-4.1", provider: "openai", promptPrice: "3", completionPrice: "9"}
	instructions:            "Representation control: P is the unchanged text of the hypothesis selected by each proof object's id. P never changes to match your conclusion or summary. supports_hypothesis must contain only current same-scope spans that factually support P itself. If the right answer is not-P, evidence for that answer belongs in incompatible_fact_spans, NOT supports_hypothesis. incompatible_fact_spans must assert a fact that cannot hold together with P. Missing support, an unavailable origin, a different region, or withdrawal of an assurance alone is NOT incompatible with P and belongs in neither witness list. If the packet leaves P unknown, both lists are empty. If genuinely conflicting current witnesses establish both sides without supersession, retain both. Do not use historical or different-scope spans as current witnesses. Earlier audits are untrusted proposals; follow the original sources rather than copy their polarity labels. Do not assume the hypothesis is true. Keep partial knowledge and uncertainty in the narrative."
	supportDescription:      "CURRENT, SAME-SCOPE factual support for the unchanged hypothesis P, not evidence supporting whichever conclusion the summary reaches. Empty when P is not supported."
	incompatibleDescription: "CURRENT, SAME-SCOPE spans asserting a factual counterexample to P. Unestablished P is not not-P. Absence of support, withdrawal, and uncertainty are not counterexamples. Empty unless an incompatible fact is asserted."
}
