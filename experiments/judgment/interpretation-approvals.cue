package judgment

// Explicit conversational decisions; separate from the immutable review content.
// Approval is of development interpretations, not independent gold or live runs.
interpretationApprovals: {
	status:               "partial-user-review"
	contextPacketSHA256:  "710a4ddce7cc5f4c07a3f009cec0130c347867550a0f0f8cea68aae7525aaaf2"
	contextPolicySHA256:  "ca46c836288278c62308d5cb5cd481f6da738a6d87b1ae2e4b5f3f1fa1929000"
	sharedPolicyApproval: "not-separately-approved"
	examples: {
		"01-source-uncertainty": {
			status:        "user-approved-development-reference"
			exampleSHA256: "6c65ce342a0ef60b0c09f88dfaebda125066be62d82f9e129dc355648c58d3bc"
			basis:         "User confirmed the source/interpretation walkthrough: 'that seems right, yeah'."
			scope:         "Example 01's scoped uncertainty, exact date exclusion, known venue, and representation flexibility only. No approval of examples 02–08, blanket policies, canonical effects, or paid execution."
		}
	}
}
