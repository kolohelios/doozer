package understanding

observations: {
	dateUTC:                 "2026-11-22"
	generationProtocol:      "65e8d424898dbaed33b70297fb17bffccad739dc0ead0e7643688cdc4e494820"
	generationCommit:        "f798741fec99"
	judgeAuditProtocol:      "ef4ba09c746af4bd0b58561fc8a675caa9abf88491485dd858a6242f55891d44"
	judgeAuditCommit:        "13dad1a8b64a"
	questionCount:           3
	understandingsGenerated: 9
	documentsIndexed:        1078
	embedding: {calls: 34, inputTokens: 126004, reportedCostUSD: 0.00252008}
	linkConstruction: {calls: 7, proposedLinks: 33, reportedCostUSD: 0.0102108}
	generation: {calls: 9, reportedCostUSD: 0.00486264}
	originalJudging: {
		recordedCalls:                    3
		structurallyInvalid:              3
		reportedCostUSD:                  0.00579
		interruptedByHarnessTimeout:      true
		additionalInFlightChargePossible: true
	}
	diagnostic: {calls: 1, reportedCostUSD: 0.002028, unchangedOriginalJudgeFormatInvalid: true}
	judgeAudit: {
		calls:                       9
		reportedCostUSD:             0.022708
		accepted:                    6
		rejected:                    3
		completeThreeConditionPairs: 1
		generationWasRepeated:       false
		rubricWasChanged:            false
		verdict:                     "Not calibrated; do not interpret accepted pass fractions as semantic accuracy."
	}
	coverage: {
		"payout-recovery": {full: 1, vector: 0.5714285714285714, rawLinksDiagnostic: 0.7142857142857143, learnedLinks: 1}
		"archive-access": {full: 1, vector: 0.7142857142857143, rawLinksDiagnostic: 0.7142857142857143, learnedLinks: 0.8571428571428571}
		"telemetry-compatibility": {full: 1, vector: 0.7142857142857143, rawLinksDiagnostic: 0.42857142857142855, learnedLinks: 0.5714285714285714}
	}
	inspection: [
		"Archive: link expansion recovered the staff-only correction and removed the vector-only answer's expressed ambiguity about applying staff drill behavior to visitors.",
		"Telemetry: expansion displaced the desktop-only test-suite evidence; the resulting understanding omitted that material test-coverage boundary.",
		"Payout: the vector-only answer retained the core ledger/email/manual-versus-scheduler distinction despite omitting three enumerated sources; source-count coverage is not minimal information sufficiency.",
		"Archive: even full case evidence did not cause the reasoner to preserve the detached Stop as an unresolved intervention.",
		"Judge audit: a validated judgment falsely passed that missing Stop requirement based on unrelated uncertainty sentences. Valid quotes do not establish entailment.",
		"Judge audit: some unsupported findings explicitly described the candidate's uncertainty as appropriate. The automated judge cannot yet be trusted as a primary outcome measure.",
	]
	conclusion: "Mixed qualitative evidence, not confirmation of the hypothesis. Retrieval can help or hurt; full evidence is not sufficient, and the judge requires calibration."
}

// Captured false-positive excerpt, not a desired answer or world evidence.
calibration: {
	"detached-stop-false-pass": {
		candidateExcerpt: "It is uncertain whether 'normal reading room visitor rules' referenced from June 19 are fully defined by the June 1 document, or if other unstated rules apply.\nIt is uncertain if the 'annex' mentioned for June 18 is the only available access point for external visitors that day, or if other arrangements exist."
		source: {id: "heldout/d-6a", text: "Stop."}
		judgment: #Judgment & {
			checks: "unknown-referent": {
				result:    "pass"
				rationale: "The candidate preserves the 'Stop.' utterance as an unresolved context without inventing its target or cancelling access or creating a task queue, correctly marking it as uncertain."
				answerQuotes: [
					"It is uncertain whether 'normal reading room visitor rules' referenced from June 19 are fully defined by the June 1 document, or if other unstated rules apply.",
					"It is uncertain if the 'annex' mentioned for June 18 is the only available access point for external visitors that day, or if other arrangements exist.",
				]
				citations: [{source: "heldout/d-6a", quote: "Stop."}]
			}
			unsupported: []
		}
		inspectionFinding: "False pass: neither candidate span addresses the detached Stop. This passes traceability validation, not semantic review."
	}
}
