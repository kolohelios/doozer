package judgment

expansionObservations: {
	status:                           "completed frozen development investigation; proposed references, not human gold"
	artifact:                         "experiments/judgment/results/first-evidence-expansion.json.gz"
	archiveSHA256:                    "fa58ee44dc9fed46585d08a8718d381bf8806528dddc83e98c37422175998440"
	uncompressedSHA256:               "d49ee4930722e2304c96d1cd0e547fd6c16ed734bdeea70d22a4ccdb3e46460a"
	protocolSHA256:                   "dafafe13c0516201fff4cb6543e0086e78132b99d2a5fc945ab8299bd0b87557"
	sourceCommit:                     "eaa466a8f86371c0db59e7eb5a31d7a79e32206a"
	calls:                            68
	reportedCostUSD:                  0.520824384
	structurallyCompleteTrajectories: 12
	proposedHypothesisStateCells:     15
	matchingProposed: {
		expandedCompiler:   8
		expandedJev:        15
		auditCompiler:      14
		reconciledCompiler: 9
		finalJev:           15
	}
	findings: [
		"Correct prose and a matching Jev verdict can coexist with wrong machine-facing proof polarity.",
		"In conflict-and-withdrawal/v1, the reasoner correctly says access is unavailable but puts the current closed-room witness in positive and the old open-room witness in negative. Historical filtering leaves an inverted supported state.",
		"In parent-recovery/v2, the reasoner correctly preserves location and unknown date, yet puts warnings against inventing the date in negative. Unestablished May 16 is not an incompatible date fact.",
		"The withdrawal branch still defeats the Gemini span audit: it assigns opposition to withdrawal without an opposite factual assertion.",
		"One audit-informed revision improves only one of the fifteen guarded state cells. A correct audit does not ensure correct serialization by the next model.",
		"The declared-origin guard preserves unresolved lineage as unestablished; this does not verify the metadata or solve other natural-language polarity errors.",
		"Schemas, source membership, scope, and history checks remain necessary but do not establish semantic direction or witness sufficiency.",
	]
}
