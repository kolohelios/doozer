package judgment

reviewedTransferObservations: {
	status:              "stopped-no-retry; partial transfer trial; new references remain provisional"
	artifact:            "experiments/judgment/results/first-reviewed-transfer.json.gz"
	archiveSHA256:       "3b95db71031ef55fc10772a6644376e5435f90ea85785d210e4d46ecd5beace4"
	uncompressedSHA256:  "ce59bc137fd3c34a63054f4bfc35e250f73be5c5ee8178fc175f771b1662b9aa"
	archiveBytes:        230921
	uncompressedBytes:   1701283
	protocolSHA256:      "56f768f9e809385184e377484d010a8a13d09ff05f1d1d56bd2e5ced4d7909f5"
	sourceCommit:        "3bc99cc8d9c1f8931858e3b6fbc87ff1cf149203"
	plannedCalls:        49
	submittedCalls:      21
	accountedResponses:  20
	unknownBillingCalls: 1
	billingLookup: {artifact: "experiments/judgment/results/first-reviewed-transfer-billing.json", sha256: "93b053de1bea534b08b866d16ed69c43813f8cf4a74b24a02f3356b170318f1d", requests: 1, method: "GET", httpStatus: 404, generationCalls: 0, result: "Generation not found; billing remains unknown. Separate post-hoc record, no retries or change to frozen run."}
	unattemptedCalls:           28
	knownReportedCostUSD:       0.458809
	unaccountedCallReservedUSD: 0.160557
	accountedOrReservedUSD:     0.619366
	warning:                    "Reservation is not a bill; actual total cost is unknown. Unused budget authorizes no retries or continuation. No canonical publication or retirement occurred."
	stages: {
		interpreter: {planned: 14, valid: 6, invalid: 0, failed: 0, unattempted: 8}
		verifier: {planned: 14, valid: 6, invalid: 0, failed: 0, unattempted: 8}
		auditor: {planned: 14, valid: 4, invalid: 2, failed: 0, unattempted: 8}
		control: {planned: 7, valid: 2, invalid: 0, failed: 1, unattempted: 4}
	}
	completeRealPanelSnapshots:  4
	completeEvaluationSnapshots: 3
	snapshotDenominator:         14
	filteredQueryStates: {matchesPerExtractor: 16, availablePerExtractor: 16, unavailablePerExtractor: 16, plannedPerExtractor: 32}
	rawBindingReferences: {interpreterMatches: 8, verifierMatches: 9, availablePerExtractor: 16, plannedPerExtractor: 32}
	mechanicallyRejectedAtoms: {interpreter: 4, verifier: 2}
	roleKnownCostsUSD: {interpreter: 0.084854, verifier: 0.178845, auditor: 0.158474, control: 0.036636}
	arms: {
		single: {referenceDiscrepanciesFlagged: 7, referenceDiscrepanciesUnflagged: 1, referenceFaithfulFlagged: 0, referenceFaithfulEligible: 8, unavailablePrimary: 16}
		blindCheck: {referenceDiscrepanciesFlagged: 7, referenceDiscrepanciesUnflagged: 1, referenceFaithfulFlagged: 2, referenceFaithfulEligible: 6, unavailablePrimary: 16}
		panel: {referenceDiscrepanciesFlagged: 8, referenceDiscrepanciesUnflagged: 0, referenceFaithfulFlagged: 4, referenceFaithfulEligible: 4, unavailablePrimary: 16}
		denominatorEach: 32
		interpretation:  "The one extra panel flag is caused by invalid audit availability, not identification of a missed semantic error. Reference discrepancies are binding-local proxy memberships, not independent errors. No final scalar accuracy benefit was demonstrated."
	}
	unaffectedFinalBindings: {planned: 9, primaryAvailableAndReferenceFaithful: 5, primaryUnavailable: 4, singleEligible: 5, blindCheckEligible: 5, panelEligible: 3, panelFlaggedDueToInvalidAudit: 2}
	actualAudit: {plannedRoleBindingAssessments: 64, referenceDiscrepancies: 15, coincidentChallenges: 3, proposedFalseChallenges: 1, unclearOrUnavailableAssessments: 44}
	controls: {planned: 7, valid: 2, failed: 1, unattempted: 4, plantedFaultsPlanned: 4, plantedFaultsAssessed: 1, plantedFaultsIdentifiedForBothRoles: 1, faithfulRoleBindingsAssessed: 10, proposedFalseChallenges: 0}
	findings: [
		"Only regional-coverage, unresolved-qualifier, and independent-grant-survives were attempted. Four other families were not reached; they are unavailable, not successes or semantic misses.",
		"The last request, the independent-grant-survives layout control, has an API-reported 504 timeout response but no usage or reported cost. The ledger halted at this unknown-accounting result; the original request and its reservation remain. No retry, replacement, provider fallback, repair, or resume was performed.",
		"Both extractors match all sixteen available filtered query states, while raw binding-reference agreement is eight and nine of sixteen. Code rejects four primary and two verifier atoms. Good scalar states do not prove faithful intermediate interpretations.",
		"The three valid binding-coincident auditor challenges concern two noncanonical verifier question values and one primary fabricated negative permission literal. All three were already mechanically rejected.",
		"Both regional audit responses label proposals faithful but place explicitly harmless observations in issues. The frozen validator treats any role issue beside faithful as invalid. This is a reporting-ABI mismatch, not malformed JSON or established factual error; no post-hoc salvage was used for scoring.",
		"The regional final snapshot is the only primary discrepancy missed by single plus code. It concerns optional explicit coverage versus source-uncertainty representation. The panel flags it because the audit is invalid, not because a valid audit identifies that proposed discrepancy. Stage unavailability also flags the unaffected staging setting and backup location.",
		"The verifier preserves an anti-transfer invitation directive that the fresh reference treats as out-of-vocabulary. The final auditor calls the primary omission a material error. This about-topic/materiality disagreement remains unadjudicated; the proposed false-challenge count is not human gold.",
		"The assessed qualifier-layout control is accepted, including duplicate conditions. The assessed shared missing-production-finding fault is explicitly identified for both candidates. Other controls are unavailable, not negative detections.",
		"The configured urllib timeout is a socket-operation timeout, not a hard request wall-clock deadline. A local poll saw the last submitted checkpoint older than 249 seconds. The trace has no per-call timing or provider completion; its API error reports timeout, without identifying the underlying provider/network phase. The frozen implementation is preserved, not repaired in this run.",
		"This partial run does not justify an always-on panel. It exposes costs, report availability, finite-wire equivalence limits, and still-disputed interpretation coverage. New labels and wire grammar are provisional; eight earlier example approvals remain narrow and unchanged.",
	]
}
