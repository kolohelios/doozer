package calibration

// Derived experimental data; never independent corroborating world evidence.
pilotObservations: {
	artifact:        "experiments/calibration/results/first-judge-pilot.json"
	artifactSHA256:  "59b4fba2b7ef17b3019fd24c0cc210a4cfde50c3d00cb97e3929c3a1086b1ccc"
	protocolSHA256:  "3d95739904f93da270db4f854fb848b05772deb62a1442cc11d87637ef90b40d"
	sourceCommit:    "9612ffc585b070e758923a1c8a8bd660ed7f7ef0"
	calls:           10
	retries:         0
	reportedCostUSD: 0.010438
	cohorts: {
		primary: {planned: 7, validAgreement: 3, validFalsePass: 1, invalidAnswerQuotes: 3}
		robustness: {planned: 3, validAgreement: 1, validFalsePass: 2, invalidAnswerQuotes: 0}
	}
	invalidAnswerQuotes: ["maple-permanent-exception", "harbor-global-retraction", "maple-staff-transfer"]
	falsePasses: {
		"maple-manuscript-omission": {
			failure:             "Fills an answer omission from the authoritative context instead of checking whether the answer conveys the required manuscript restriction. This is incompleteness under the approved criterion, not an asserted false visitor rule."
			judgeRationaleQuote: "Although the candidate does not explicitly mention the manuscript escort restriction, it is implied by the absence of any change to that rule"
		}
		"partial-context-total-abstention": {
			failure:             "Attributes acknowledgement of the explicit staff-only limitation to an answer that expressly denies that it can be concluded. Exact quotations did not ensure correct interpretation of negation."
			candidateQuote:      "nothing can be concluded from this message, including whether the exception was staff-only"
			judgeRationaleQuote: "It acknowledges the explicit limitation that the exception was staff-only and not a change to visitor procedures"
		}
		"partial-context-invented-target": {
			failure:             "Accepts an invented location, parent, procedure, and effective date although its only supplied source is the missing-parent message. These were stateless calls; no Maple thread was included in this call."
			candidateQuote:      "This replies to Maple's September 12 annex visitor proposal."
			judgeRationaleQuote: "without inventing any additional details about the exception, location, or procedure"
		}
	}
	conclusion:     "Do not use this judge for unattended semantic acceptance or retirement. Seven mechanically accepted judgments contain three false passes; three additional attempts fail candidate-quote integrity. Four fully valid agreements out of ten attempts are a development observation, not general accuracy."
	nextHypothesis: "Evaluate candidate meaning separately from source truth so missing or contradicted candidate meaning cannot be supplied by a correct source quotation. Any new prompt, model, or contract requires a new frozen protocol; do not repair this run or spend the remaining budget automatically."
}
