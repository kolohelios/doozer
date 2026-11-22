package calibration

// Unblinded draft inspection, not human-adjudicated gold or original scores.
reviews: {
	"payout-recovery": {
		full: {
			"ledger-email-boundary": {label: "pass", reason: "Ledger uniqueness and the separate email transaction boundary are both stated.", spans: [{pointer: "/claims/4/text", quote: "The ledger posting step uses a uniqueness constraint on payout-id"}, {pointer: "/claims/5/text", quote: "The email delivery step is outside the ledger posting transaction."}]}
			"duplicate-email-risk": {label: "pass", reason: "The answer retains the observed duplicate-remittance risk rather than declaring every rerun safe.", spans: [{pointer: "/claims/3/text", quote: "can result in duplicate remittance emails."}]}
			"manual-bypass": {label: "pass", reason: "The mitigation is explicitly a manual recovery command switch.", spans: [{pointer: "/claims/1/text", quote: "A manual rerun of a failed payout job using the '--ledger-only' command switch bypasses email sending."}]}
			"scheduler-boundary": {label: "pass", reason: "The scheduler does not read the switch. The stronger tail of this statement is reviewed separately as delivery certainty.", spans: [{pointer: "/claims/2/text", quote: "The background retry scheduler does not read the '--ledger-only' switch"}]}
			"delivery-certainty": {label: "fail", reason: "Lack of this bypass and one observed duplicate do not establish that every automatic retry will deliver email; the directive repeats the unsupported certainty.", spans: [{pointer: "/claims/2/text", quote: "so automatic retries will send email."}, {pointer: "/directives/1/instruction", quote: "automatic retries by the scheduler will send email notifications."}]}
			"echo-independence": {label: "uncertain", reason: "The claim cites the incident and its retelling without explicitly claiming two independent incidents. Whether citation rendering preserves dependency needs an agreed provenance contract, not a source-count heuristic.", spans: [{pointer: "/claims/3/text", quote: "Repeating a failed payout without the '--ledger-only' switch can result in duplicate remittance emails."}]}
		}
		vector: {
			"ledger-email-boundary": {label: "pass", reason: "The same design boundary is preserved using the direct source.", spans: [{pointer: "/claims/2/text", quote: "The ledger postings use a payout-id uniqueness constraint, but the email delivery step is outside that transaction."}]}
			"duplicate-email-risk": {label: "pass", reason: "The production duplicate and single ledger posting are explicitly retained.", spans: [{pointer: "/claims/1/text", quote: "Repeating one failed payout sent two remittance emails, while the ledger contained only one posting."}]}
			"manual-bypass": {label: "pass", reason: "The answer gives a scoped manual bypass, not universal suppression.", spans: [{pointer: "/claims/3/text", quote: "A manual recovery command (`--ledger-only`) can bypass email sending."}]}
			"scheduler-boundary": {label: "pass", reason: "The command documentation suffices despite the missing question/No pair.", spans: [{pointer: "/claims/4/text", quote: "The `--ledger-only` switch is not read by the background retry scheduler."}]}
			"delivery-certainty": {label: "pass", reason: "The scheduler warning is appropriately expressed as risk rather than guaranteed delivery.", spans: [{pointer: "/directives/1/instruction", quote: "duplicate remittance emails may be sent"}]}
			"echo-independence": {label: "not-applicable", reason: "The answer does not use the retelling; omitting a redundant echo is allowed, not a meaning loss.", spans: []}
		}
		"vector-links": {
			"ledger-email-boundary": {label: "pass", reason: "The architecture boundary remains explicit.", spans: [{pointer: "/claims/1/text", quote: "The ledger posting uses a payout-id uniqueness constraint, but the email delivery step is outside that transaction."}]}
			"duplicate-email-risk": {label: "pass", reason: "The answer states that a rerun can duplicate remittance emails.", spans: [{pointer: "/claims/0/text", quote: "Rerunning a failed Orchid payout job can produce duplicate remittance emails."}]}
			"manual-bypass": {label: "pass", reason: "The named recovery-command mitigation is retained.", spans: [{pointer: "/claims/2/text", quote: "A manual recovery command with a --ledger-only switch can bypass email sending."}]}
			"scheduler-boundary": {label: "pass", reason: "The direct boundary is conveyed; extra source identities do not add another required meaning here.", spans: [{pointer: "/claims/3/text", quote: "The --ledger-only switch is not read by the background retry scheduler."}]}
			"delivery-certainty": {label: "pass", reason: "The directive warns of possible duplicate effects, not certain delivery on every retry.", spans: [{pointer: "/directives/1/instruction", quote: "may cause duplicate emails."}]}
			"echo-independence": {label: "uncertain", reason: "Two citations to an incident and dependent retelling do not alone prove either independence inflation or correct lineage handling. Review the rendering/history contract.", spans: [{pointer: "/claims/0/text", quote: "Rerunning a failed Orchid payout job can produce duplicate remittance emails."}]}
		}
	}
	"archive-access": {
		full: {
			"temporary-procedure": {label: "pass", reason: "The whole answer includes annex check-in, escort, and the June 18 boundary. Standalone directive completeness is a separate contract question.", spans: [{pointer: "/claims/1/text", quote: "On June 18, booked visitors check in at the annex and must remain with an archivist."}]}
			"normal-catalog-access": {label: "pass", reason: "Normal access resumes June 19 with catalog-box permission still conditional on check-in.", spans: [{pointer: "/claims/4/text", quote: "From June 19, the normal reading room visitor rules resume."}, {pointer: "/claims/5/text", quote: "visitors may examine catalog boxes without an escort after check-in."}]}
			"manuscript-escort": {label: "pass", reason: "The manuscript exception remains distinct from catalog-box access.", spans: [{pointer: "/claims/6/text", quote: "In normal weeks, handling original manuscripts still requires an archivist."}]}
			"staff-scope": {label: "pass", reason: "The staff drill exception is not extended to external visitors.", spans: [{pointer: "/claims/3/text", quote: "The drill exception for unescorted access on June 18 does not apply to external visitors."}]}
			"unresolved-intervention": {label: "not-assessed", reason: "The answer does not mention Stop, but this artifact does not test knowledge/history retention. The original frozen answer-rubric omission remains recorded separately.", spans: []}
		}
		vector: {
			"temporary-procedure": {label: "pass", reason: "The required dated visitor procedure is present despite the missing later correction.", spans: [{pointer: "/claims/1/text", quote: "On June 18, booked visitors check in at the annex and remain with an archivist."}]}
			"normal-catalog-access": {label: "pass", reason: "The answer includes policy resumption and after-check-in catalog access.", spans: [{pointer: "/claims/3/text", quote: "From June 19, the normal reading room visitor rules resume."}, {pointer: "/claims/4/text", quote: "Cedar reading room visitors may examine catalog boxes without an escort after check-in."}]}
			"manuscript-escort": {label: "pass", reason: "The continuing manuscript restriction is explicit.", spans: [{pointer: "/claims/5/text", quote: "In normal weeks, original manuscript handling still requires an archivist."}]}
			"staff-scope": {label: "fail", reason: "The answer manufactures ambiguity despite receiving both the staff-only observation and the visitor escort notice. Its main directive is correct, but this uncertainty conflicts with the available scope.", spans: [{pointer: "/uncertainties/0", quote: "Whether the 'staff-only exception' observed on June 18 implies any unescorted access for external visitors on that day is ambiguous"}]}
			"unresolved-intervention": {label: "not-assessed", reason: "Missing the detached source from an answer neighborhood is not a measured history deletion; no history mutation occurred.", spans: []}
		}
		"vector-links": {
			"temporary-procedure": {label: "pass", reason: "The answer and directive state the date-bounded annex check-in and escort requirements.", spans: [{pointer: "/directives/0/instruction", quote: "on June 18, they must check in at the annex and remain with an archivist; unescorted access is not permitted."}]}
			"normal-catalog-access": {label: "pass", reason: "The normal catalog rule is kept distinct from the temporary closure.", spans: [{pointer: "/claims/4/text", quote: "From June 19, the normal reading room visitor rules resume."}, {pointer: "/claims/5/text", quote: "visitors may examine catalog boxes without an escort after check-in."}]}
			"manuscript-escort": {label: "pass", reason: "The original-manuscript exception is retained.", spans: [{pointer: "/claims/6/text", quote: "Under normal rules, original manuscript handling still requires an archivist."}]}
			"staff-scope": {label: "pass", reason: "The added correction makes the boundary explicit and the earlier unnecessary ambiguity disappears. The vector context already had sufficient evidence, so retrieval is not the sole explanation.", spans: [{pointer: "/claims/3/text", quote: "The drill exception for unescorted access on June 18 does not apply to external visitors."}]}
			"unresolved-intervention": {label: "not-assessed", reason: "Unrelated uncertainty sentences do not demonstrate Stop handling, but the answer contract here does not claim to test history retention.", spans: []}
		}
	}
	"telemetry-compatibility": {
		full: {
			"strict-consumer": {label: "pass", reason: "Actual field-monitor behavior qualifies the broad additive-safety statement.", spans: [{pointer: "/claims/3/text", quote: "The field monitor firmware rejects any telemetry object with an unrecognized label key."}]}
			"suite-scope": {label: "pass", reason: "Desktop-only coverage and missing monitor coverage are both stated.", spans: [{pointer: "/claims/2/text", quote: "The green Quill contract suite exercises desktop dashboard clients only. It does not execute field monitor firmware."}]}
			"rollout-order": {label: "pass", reason: "The directive preserves gating, upgrade/verification ordering, and retention of the old format.", spans: [{pointer: "/directives/0/instruction", quote: "Gate the zone label by consumer revision. Upgrade field monitor firmware before enabling zone for those devices; retain the old payload format until their upgrade is verified."}]}
			"behavior-not-schema": {label: "pass", reason: "The cadence counterexample remains separate from strict decoding.", spans: [{pointer: "/claims/5/text", quote: "A format-preserving sampling-cadence change caused gaps in a Quill alert stream despite passing its JSON schema checks."}]}
			"no-inferred-completion": {label: "pass", reason: "The rollout is a prerequisite-bearing directive, not a claimed completed migration.", spans: [{pointer: "/directives/0/instruction", quote: "before enabling zone for those devices; retain the old payload format until their upgrade is verified."}]}
			"desktop-safety-scope": {label: "uncertain", reason: "Conditionally safe might be shorthand for covered tests, or it might overstate what test coverage proves. Review the intended threshold rather than invent an automatic pass/fail.", spans: [{pointer: "/summary", quote: "it is conditionally safe for desktop dashboard clients"}]}
		}
		vector: {
			"strict-consumer": {label: "pass", reason: "The field-monitor exception is retained even without the later No reply.", spans: [{pointer: "/claims/2/text", quote: "The field monitor firmware rejects any telemetry object with an unrecognized label key."}]}
			"suite-scope": {label: "pass", reason: "The direct suite description supplies the required meaning without needing the broad assertion and rejection pair.", spans: [{pointer: "/claims/4/text", quote: "The green Quill contract suite exercises desktop dashboard clients only. It does not execute field monitor firmware."}]}
			"rollout-order": {label: "pass", reason: "All material migration prerequisites remain in the directive.", spans: [{pointer: "/directives/0/instruction", quote: "Gate the zone label by consumer revision. Upgrade field monitor firmware before enabling zone for those devices; retain the old payload format until their upgrade is verified."}]}
			"behavior-not-schema": {label: "pass", reason: "The behavioral counterexample is present, not reduced to schema shape.", spans: [{pointer: "/claims/5/text", quote: "A format-preserving sampling-cadence change caused gaps in a Quill alert stream despite passing its JSON schema checks."}]}
			"no-inferred-completion": {label: "pass", reason: "Nothing asserts that the firmware migration has already happened.", spans: [{pointer: "/directives/0/instruction", quote: "until their upgrade is verified."}]}
			"desktop-safety-scope": {label: "not-applicable", reason: "The answer does not positively declare desktop safety; it describes limited test coverage.", spans: []}
		}
		"vector-links": {
			"strict-consumer": {label: "pass", reason: "The strict monitor contract remains explicit.", spans: [{pointer: "/claims/0/text", quote: "The field monitor firmware rejects any telemetry object with an unrecognized label key."}]}
			"suite-scope": {label: "fail", reason: "The desktop-only test boundary is absent from the whole answer. Its source was also absent from this neighborhood: an end-to-end omission, not evidence that the reasoner ignored a supplied fact.", spans: []}
			"rollout-order": {label: "pass", reason: "The ordered rollout procedure survives even though the suite-coverage source is missing.", spans: [{pointer: "/directives/0/instruction", quote: "Gate the zone label by consumer revision. Upgrade field monitor firmware before enabling zone for those devices; retain the old payload format until their upgrade is verified."}]}
			"behavior-not-schema": {label: "pass", reason: "The historical cadence failure remains available and stated.", spans: [{pointer: "/claims/2/text", quote: "A format-preserving sampling-cadence change caused gaps in a Quill alert stream despite passing its JSON schema checks."}]}
			"no-inferred-completion": {label: "pass", reason: "The directive still conditions enablement on verified upgrade completion.", spans: [{pointer: "/directives/0/instruction", quote: "until their upgrade is verified."}]}
			"desktop-safety-scope": {label: "not-applicable", reason: "No claim of desktop safety is made.", spans: []}
		}
	}
}
