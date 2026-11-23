package judgment

scaleObservations: {
	status: "completed-frozen-protocol-with-contract-composition-and-control-cue-limitations"
	artifact: {
		path:           "experiments/judgment/results/first-larger-transfer.json.gz"
		sha256:         "9e29a682a37956595b1b08c67377fdf53f1c37ea59c7259d90c703b416518575"
		bytes:          1341955
		rawSHA256:      "a8b114e8a086a6f107d36b41c02f71121a300e5c806a16228c86f09e025f5929"
		rawBytes:       10871970
		protocolSHA256: "4fc33b638aa8c104124c4f9f90fdd23b9ef26c1c929c07025099f6aece688ff7"
		sourceCommit:   "f5220378a22fde838ef1aa32b4af77aa72027139"
	}
	calls: {planned: 84, submitted: 84, accounted: 84, retries: 0, unattempted: 0, unknownBilling: 0}
	budgetUSD:    5
	knownCostUSD: 2.527731
	stages: {interpreter: {valid: 22, invalid: 2, planned: 24}, verifier: {valid: 23, invalid: 1, planned: 24}, auditor: {valid: 23, invalid: 1, planned: 24}, control: {valid: 12, invalid: 0, planned: 12}}
	snapshots: {planned: 24, realComplete: 20, evaluationsComplete: 20}
	roles: {
		interpreter: {plannedBindings: 72, available: 66, profileMatches: 38, queryMatches: 62, unavailable: 6, missingMemberships: 11, extraMemberships: 48, mechanicalRejections: 36, noteDifferenceSnapshots: 19}
		verifier: {plannedBindings: 72, available: 69, profileMatches: 54, queryMatches: 69, unavailable: 3, missingMemberships: 0, extraMemberships: 25, mechanicalRejections: 6, noteDifferenceSnapshots: 16}
	}
	arms: {
		single: {planned: 72, unavailable: 6, discrepantFlagged: 19, discrepantUnflagged: 9, matchingFlagged: 0, matchingEligible: 38}
		blindCheck: {planned: 72, unavailable: 6, discrepantFlagged: 28, discrepantUnflagged: 0, matchingFlagged: 7, matchingEligible: 31}
		panel: {planned: 72, unavailable: 6, discrepantFlagged: 28, discrepantUnflagged: 0, matchingFlagged: 11, matchingEligible: 27}
	}
	controls: {planned: 12, valid: 12, plantedFaultBindings: 8, bothRolesChallenged: 8, faithfulRoleBindingsAssessed: 56, proposedFalseChallenges: 4}
	costsUSD: {interpreter: 0.52179, verifier: 1.143845, auditor: 0.639966, controls: 0.22213, realPanel: 2.305601}
	transitions: {pairedBindings: 36, unchangedProfiles: 24, changedQueries: 7, changedQueryPairsMatched: 7, unchangedMatching: 19, singleEligible: 19, blindEligible: 18, panelEligible: 14}
	caveats: [
		"Actual common_contract contains meaningContract v2 only, not reviewedContract rules/wire. All roles share that wire, but it is not the intended complete base-plus-extension contract. In particular the auditor lacks the extractor constructor schema and explicit grant-none/null lowering semantics. Do not attribute all resulting errors solely to model reasoning.",
		"Control proposals retain the reference builder's Authored development interpretation rationale, revealing authored origin even though fault labels and expected verdicts are absent. This is not a clean control-blinding result. Original prompts remain unchanged.",
		"Profiles and references are provisional. Some extra memberships may preserve valid source exclusions or reflect layout/wire disputes, not wrong meanings. The Grove storage-bay/venue exclusion is an unreviewed reference omission candidate. No labels, original scores, or invalid reports are repaired or rescored.",
		"Two interpreter outputs have empty evidence arrays in extraction limits; the JSON schema allows them but the conditional validator rejects them. One verifier output ends with finish_reason length. One auditor repeats an evidence ID and is invalid. Complete raw outputs and failures remain in the archive.",
		"All four panel-only added holds affect profile-matching final-window bindings: two dispute omission of an original location atom despite a declared-origin repeat; two follow the invalid audit. No incremental detection over blind verification is demonstrated by this metric.",
		"All eight planted faults receive both-role material challenges, but two unaffected staff grants also receive both-role material challenges for null value operands that the frozen compiler requires. Control cues and incomplete shared semantics prevent treating these numbers as calibrated diagnostic rates.",
	]
	canonicalAcceptance: false
	publication:         false
	retirement:          false
}
