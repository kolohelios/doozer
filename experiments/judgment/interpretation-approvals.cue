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
		"02-window-coverage": {
			status:        "user-approved-development-reference"
			exampleSHA256: "281f412b256717fb836f265983e4e51505fc6845c6b7ae2b13eecc63f0e03caa"
			basis:         "User confirmed the source/interpretation and representation-choice walkthrough: 'yes, seems right'."
			scope:         "Example 02's bounded coverage distinction and explicit-or-derived representation with an effective consumer recovery path only. No approval of examples 03–08, blanket policies, canonical effects, or paid execution."
		}
		"03-extractor-limitation": {
			status:        "user-approved-development-reference"
			exampleSHA256: "7f8ee943aab5d176b37fe6f1cd0bb01233da18982b33d9b15b40c58fdf689097"
			basis:         "User confirmed the source/interpretation walkthrough: 'yes'."
			scope:         "Example 03's reported dates, unresolved exactly-one provisional qualifier, extractor-origin limitation, and unaffected venue only. The extractor report is not source testimony or corroboration. No approval of examples 04–08, blanket policies, canonical effects, or paid execution."
		}
	}
}
