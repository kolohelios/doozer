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
		"04-question-and-directive": {
			status:        "user-approved-development-reference"
			exampleSHA256: "b212dfdf06b6ec79a95940e4cb6ca59afcc7037c68c9c8a296f1cf4292fc2297"
			basis:         "User confirmed the source/interpretation walkthrough: 'yes'."
			scope:         "Example 04's known venue, non-asserted question content, calendar-check action and condition, legitimate about-date topic link without date assignment, and optional derived-unknown annotation only. A stored request does not create a newly assigned task. No approval of examples 05–08, blanket policies, canonical effects, or paid execution."
		}
		"05-assurance-withdrawal": {
			status:        "user-approved-development-reference"
			exampleSHA256: "3942bfa88bb77be18301779ec886d33278830c802bb4043c7de0f934c1728492"
			basis:         "User confirmed the source/interpretation walkthrough: 'yes'."
			scope:         "Example 05's assurance-targeted withdrawal, loss of current permission support without an inferred prohibition, preservation of the unaffected venue and original history, and survival of any separate valid grant only. No approval of examples 06–08, blanket policies, canonical effects, or paid execution."
		}
		"06-permission-revocation": {
			status:        "user-approved-development-reference"
			exampleSHA256: "f601726416009adf342301b465a72cfde9df0797e164ab241518c100219fbb47"
			basis:         "User confirmed the source/interpretation walkthrough: 'yes'."
			scope:         "Example 06's authorized, session-scoped revocation of the specified grant, distinct from assurance withdrawal or physical access observations; preservation of the unaffected venue and recoverable grant history only. No approval of examples 07–08, blanket policies, canonical effects, or paid execution."
		}
		"07-resolved-uncertainty": {
			status:        "user-approved-development-reference"
			exampleSHA256: "11ee890a3b0f31a94280416d7cb97ee0afdab82cd953a72f330ad0748a2736b5"
			basis:         "User confirmed the source/interpretation walkthrough: 'yes'."
			scope:         "Example 07's later establishment of the current date, distinction from statement time, preservation of earlier honestly scoped uncertainty as history rather than permanent fog or a false statement, and unaffected venue only. History need not crowd every current answer. No approval of example 08, blanket policies, canonical effects, or paid execution."
		}
	}
}
