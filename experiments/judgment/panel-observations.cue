package judgment

panelObservations: {
	status:                                     "completed development trial; references remain provisional, not human-reviewed gold"
	artifact:                                   "experiments/judgment/results/first-source-panel.json.gz"
	archiveSHA256:                              "4dda53f831cacd6ae1a8addb51412f3b04cb9b4a947b929c7375bd68142f9c75"
	uncompressedSHA256:                         "d28813c23bf746ff8a3b2bdd917f5c10ed13ba180872c328f81ab7ef47ee1256"
	protocolSHA256:                             "b7e21948a83dc1bcbb8015221c9fa9a705128e512b99822b3af08463ade0a80f"
	sourceCommit:                               "8acde59775f2f242fc2f24491863c70f7a4ddcb6"
	calls:                                      40
	reportedCostUSD:                            0.372893466
	structurallyCompletePanelTrajectories:      8
	structurallyCompleteEvaluationTrajectories: 8
	roleCostsUSD: {interpreter: 0.025552, verifier: 0.15838, auditor: 0.103708, audit_control: 0.08478, baseline: 0.000473466}
	filteredStateMatchesProposed: {interpreter: 17, verifier: 17, baseline: 17, denominatorPerRole: 17}
	paragraphReferenceMatches: {interpreter: 10, verifier: 11, denominatorPerExtractor: 12}
	mechanicallyRejectedAtoms: {interpreter: 1, verifier: 1}
	actualAudit: {
		roleSpanComparisons:                         24
		provisionalReferenceDiscrepancies:           3
		challenged:                                  2
		unchallenged:                                1
		falseChallengesRelativeToProposedReferences: 2
		unassessed:                                  0
		sharedReferenceDiscrepancySpans:             0
	}
	sharedErrorControls: {
		planned:                         8
		validAudits:                     8
		bothCandidatesChallenged:        8
		falseChallengesOnUnchangedSpans: 0
		qualitativeCheck:                "Saved rationales explicitly identify the planted fault in all eight controls, not merely another concern in the same paragraph. Controls are authored inputs, not real model mistakes."
	}
	panelStatuses: {uncheckedAgreementNotAcceptance: 4, unresolvedInterpretationDisagreement: 2, unresolvedMechanicalCheck: 2}
	findings: [
		"Filtered query-state agreement hides source-level problems. Interpreter invents a targetless withdrawal in an assurance paragraph; verifier adds venue-unknown to a no-change statement. Code rejects both atoms without changing the source or raw proposal.",
		"The two real reference discrepancies challenged by the auditor were already flagged by mechanical checks. No incremental real-run state accuracy gain from the auditor was demonstrated.",
		"The remaining reference discrepancy is a scope limitation stated in prose limitations/rationale but omitted as a typed epistemic atom. The auditor calls this stylistic; the frozen reference requires the atom. This is a preservation-contract disagreement, not adjudicated model error.",
		"Both raw ledgers satisfy the optional reference variant for the question/directive packet, but differ in whether they also emit explicit unknown. Exact ledger comparison therefore creates a conservative hold.",
		"The auditor challenges both directive atoms because binding a calendar-check action to an effective-date scalar is disputed. The frozen reference uses the binding as a topic link, not a value assignment. The shared binding field needs a clearer semantic contract; the two proxy false challenges are not human-adjudicated mistakes.",
		"Blindness must hide peer answers and evaluation labels, not the shared semantic contract. The auditor did not receive the extractor's full instructions; contract visibility is not label leakage.",
		"Use specialist panels to expose and stress-test failures, not to turn consensus into canonical truth. Source metadata and canonical scalar premises remain manually supplied; no held-out population accuracy or autonomous compaction result follows.",
	]
}
