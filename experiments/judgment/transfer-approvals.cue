package judgment

// Explicit user decision, separate from the unchanged proposal snapshot.
transferApprovals: {
	status:               "example-review-complete"
	contextPacketSHA256:  "fcbaebd37bc47fa9789b879b54450344d6c9b8cbf2994d246e4236078ab20468"
	contextPolicySHA256:  "2fab286273e107488cc9d0853431ded53a6b03fba16ab1f74137b297e92995d7"
	sharedPolicyApproval: "not-separately-approved"
	examples: {
		"01-coverage-frame": {
			exampleSHA256: "e2c6dc4386fedeacfbeb500d4724f3f4d02123ff7b8a34557b2848553b8a203c"
			status:        "user-approved-development-reference"
			basis:         "The user explicitly answered the preceding one-at-a-time coverage review: \"yes... folks can speculate, but that isn't evidence, it's a hunch. 18 merged. do the next thing\""
			scope:         "Only example 01's reviewed coverage interpretation and recovery alternatives, plus the explicit hunch clarification below. No approval of example 02, blanket shared policy, a particular wire/classifier, canonical effects, historical rescoring, or new paid execution follows. Merging PR 18 is not the semantic approval basis."
			clarification: {
				quote:          "folks can speculate, but that isn't evidence, it's a hunch."
				interpretation: "Preserve speculation as an attributed hunch if useful, not as a supporting or opposing witness establishing the production setting. Evidence that someone expressed a hunch is distinct from evidence for its guessed world value. Assess any separately supplied observations on their own grounds."
			}
		}
		"02-invitation-directive": {
			exampleSHA256: "b6e5cd86167e44bc7c6b455b6e1d4672d2f0d58ab58122809ceeb8eb57ae2139"
			status:        "user-approved-development-reference"
			basis:         "The user explicitly answered the preceding one-at-a-time invitation-warning review: \"I think that makes sense, yeah\""
			scope:         "Only example 02's reviewed source meaning and recovery alternatives: retain Hal's invitation-use warning without treating it as permission revocation, prohibition, or a new task; preserve the live Oak grant and unaffected venue. No blanket shared policy or wire/classifier approval, canonical effects, historical rescoring, or new paid execution follows."
		}
	}
}
