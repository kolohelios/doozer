package calibration

// Derived experiment observations, not independent evidence for fixture-world facts.
splitObservations: {
	artifact:       "experiments/calibration/results/first-split-judgment.json"
	artifactSHA256: "58136632d81cc8afa636a325a88b8ddff1846c2b67cacd60c96527df0150b2b1"
	protocolSHA256: "62b32af99ff0b3c5114d942b06d3759e7ac8d1341c127014cea01429ce196b89"
	sourceCommit:   "bd3e93568c617625aad2206e36e433dd0bbc1531"
	calls: {coverage: 10, grounding: 10, jev: 10, embedding: 1, total: 31, retries: 0}
	reportedCostUSD: 0.017979816
	componentCostsUSD: {coverage: 0.0067216, grounding: 0.0107148, jev: 0.000504336, embedding: 0.00003908}
	embeddingInputs: 65
	wholeAnswerObservations: {
		jev: {matchedReferences: 10, falsePasses: 0, falseFailures: 0, abstentions: 0}
		generative: {matchedFailures: 7, matchedPasses: 0, falseFailures: 1, abstentions: 2, falsePasses: 0}
		combined: {matchedFailures: 7, matchedPasses: 0, falseFailures: 0, abstentions: 3, falsePasses: 0}
	}
	coverageOnlyProxy: "All ten coverage stages were mechanically valid and their completeness-only aggregates matched whole-answer references. This does not test source truth or establish correctness of every card-level rationale."
	failures: {
		"harbor-bounded-answer":          "Grounding returned an object keyed by sentence IDs instead of the required array. Retained as invalid; no normalization or replacement."
		"maple-bounded-answer":           "Grounding quotations changed punctuation/capitalization from the source. Retained as invalid, not silently repaired."
		"partial-context-bounded-answer": "Grounding labeled a valid self-limitation unsupported because world sources did not discuss storage verification. The narrow nonfactual category may contribute; future contracts should distinguish meta-epistemic statements from world claims."
	}
	audit: {
		inventedContextStillAcceptedLocally: {
			sample:         "partial-context-invented-target"
			sentence:       "s0"
			result:         "supported"
			rationaleQuote: "The authoritative source is a reply dated September 12 discussing visitor procedures related to an annex proposal"
			finding:        "The sole source contains no Maple or annex proposal. The grounding stage still rationalizes invented context, even though a different unsupported timestamp sentence makes its aggregate fail."
		}
		coverageRationaleScope: "The Harbor bypass-extension effects card was called contradicted despite the opening sentence preserving ledger/email distinction. Aggregate agreement must not be mistaken for perfect unit-level interpretation."
	}
	math: {
		mapleCorrectVsWrongStaffTransferDenseCosine: 0.9372344591293329
		mapleCorrectVsManuscriptOmissionDenseCosine: 0.9258466240924901
		manuscriptRequirementMaxSentenceCosine: {
			dense: {correct: 0.6511516340892832, omission: 0.46251054734809544}
			tfidf: {correct: 0.26612054939516944, omission: 0.07482125918901152}
		}
		interpretation: "Local meaning-gap features are promising diagnostics, but high overall similarity also joins materially different answers. No thresholds were chosen and vectors did not influence decisions."
	}
	limitations: "Ten known authored development controls, no held-out evidence, no calibrated Jev confidence or independence claim, and zero accepted positives from the combined policy. Do not promote to unattended semantic acceptance."
	next:        "Test Jev on fresh positive and negative held-out correspondence, including unchanged candidates with swapped source policies and neutral criteria to check evidence sensitivity. Refine grounding statement types and structural output constraints in a new frozen variant; do not repair this run or weaken quote checks after seeing outputs."
}
