package calibration

// Development examples drawn from the nine saved answers. Labels are drafts.
// They are not held-out tests and must not silently become judge gold data.
samples: [
	{
		id:        "scoped-manual-mitigation", case: "payout-recovery", arm: "vector", target: "excerpt"
		criterion: "Does the passage faithfully state the documented manual mitigation without extending it to every retry path?"
		expected:  "pass"
		reason:    "The directive names manual recovery and the email-bypass switch. This is a supported bounded instruction."
		spans: [{pointer: "/directives/0/instruction", quote: "For a manual rerun where duplicate notifications must be avoided, use the `--ledger-only` recovery command to bypass email sending."}]
		evidence: [{source: "heldout/d-c8", quote: "The Orchid recovery command --ledger-only bypasses email sending."}]
	},
	{
		id:        "automatic-delivery-overclaim", case: "payout-recovery", arm: "full", target: "claim"
		criterion: "Does the evidence justify certainty that automatic retries will deliver email, rather than only lack of this bypass and risk of duplicate effects?"
		expected:  "fail"
		reason:    "Not reading one switch does not exclude other gates or earlier failure paths. The claim goes beyond the supplied evidence; this is not a claim that automatic email never happens."
		spans: [{pointer: "/claims/2/text", quote: "The background retry scheduler does not read the '--ledger-only' switch, so automatic retries will send email."}]
		evidence: [{source: "heldout/d-c8", quote: "This switch is not read by the background retry scheduler."}, {source: "heldout/d-13", quote: "In Orchid's production batch, repeating one failed payout sent two remittance emails; the ledger contained one posting."}]
	},
	{
		id:        "bounded-automatic-risk", case: "payout-recovery", arm: "vector", target: "excerpt"
		criterion: "Is possible duplicate email represented with the proper automatic-path caveat rather than a guaranteed outcome?"
		expected:  "pass"
		reason:    "The passage states a risk grounded in the incident and the documented bypass boundary."
		spans: [{pointer: "/directives/1/instruction", quote: "duplicate remittance emails may be sent"}]
		evidence: [{source: "heldout/d-13", quote: "repeating one failed payout sent two remittance emails"}, {source: "heldout/d-c8", quote: "This switch is not read by the background retry scheduler."}]
	},
	{
		id:        "legitimate-unanswered-uncertainty", case: "payout-recovery", arm: "full", target: "excerpt"
		criterion: "Is this an honest statement of an unanswered question, rather than an unsupported asserted fact or a new directive?"
		expected:  "pass"
		reason:    "The documentation states current behavior but says nothing about permanence. Acknowledged uncertainty is not hallucinated permanence or a task assignment."
		spans: [{pointer: "/uncertainties/2", quote: "It is uncertain if the scheduler's inability to use '--ledger-only' is a permanent design or a temporary limitation."}]
		evidence: [{source: "heldout/d-c8", quote: "This switch is not read by the background retry scheduler."}]
	},
	{
		id:        "manufactured-visitor-ambiguity", case: "archive-access", arm: "vector", target: "excerpt"
		criterion: "Does this uncertainty respect the explicit staff-only scope and external-visitor escort requirement?"
		expected:  "fail"
		reason:    "Both boundaries were supplied to this answer. Missing the later No does not make the visitor rule genuinely ambiguous. This differs from an unanswered uncertainty."
		spans: [{pointer: "/uncertainties/0", quote: "Whether the 'staff-only exception' observed on June 18 implies any unescorted access for external visitors on that day is ambiguous"}]
		evidence: [{source: "heldout/d-51", quote: "Two staff researchers entered the annex unescorted during the June 18 equipment drill under a staff-only exception."}, {source: "heldout/d-8e", quote: "Booked visitors check in at the annex and remain with an archivist."}]
	},
	{
		id:        "dated-complete-visitor-procedure", case: "archive-access", arm: "vector-links", target: "excerpt"
		criterion: "Does the directive retain the date, annex check-in, and escort requirement for the temporary procedure?"
		expected:  "pass"
		reason:    "It includes the material procedure and date boundary without converting it into a permanent rule."
		spans: [{pointer: "/directives/0/instruction", quote: "on June 18, they must check in at the annex and remain with an archivist; unescorted access is not permitted."}]
		evidence: [{source: "heldout/d-8e", quote: "On June 18 only, mold remediation closes Cedar's main reading room. Booked visitors check in at the annex and remain with an archivist. The normal room reopens June 19."}]
	},
	{
		id:        "unrelated-span-false-pass", case: "archive-access", arm: "vector-links", target: "excerpt"
		cohort:    "robustness"
		criterion: "Do these particular passages establish that the answer addressed the detached Stop and its unknown referent? This checks criterion attribution, not whether every question answer must mention Stop."
		expected:  "fail"
		reason:    "The quoted passages concern unspecified visitor arrangements, not the detached intervention. Real quotation spans can support the wrong criterion."
		spans: [
			{pointer: "/uncertainties/0", quote: "It is uncertain whether 'normal reading room visitor rules' referenced from June 19 are fully defined by the June 1 document, or if other unstated rules apply."},
			{pointer: "/uncertainties/1", quote: "It is uncertain if the 'annex' mentioned for June 18 is the only available access point for external visitors that day, or if other arrangements exist."},
		]
		evidence: [{source: "heldout/d-6a", quote: "Stop."}]
	},
	{
		id:        "bounded-test-coverage", case: "telemetry-compatibility", arm: "vector", target: "claim"
		criterion: "Does the passage preserve what the green suite actually covers and does not cover?"
		expected:  "pass"
		reason:    "The actual desktop-only coverage is stated explicitly; a later objection need not be retrieved to convey it."
		spans: [{pointer: "/claims/4/text", quote: "The green Quill contract suite exercises desktop dashboard clients only. It does not execute field monitor firmware."}]
		evidence: [{source: "heldout/d-aa", quote: "The green Quill contract suite exercises desktop dashboard clients only. It does not execute field monitor firmware."}]
	},
	{
		id:        "missing-test-scope", case: "telemetry-compatibility", arm: "vector-links", target: "whole-answer"
		criterion: "Does the whole answer preserve the desktop-only suite coverage boundary?"
		expected:  "fail"
		reason:    "No answer field describes that boundary. The source was missing from generation context, so this is an end-to-end omission, not proof that reasoning ignored a supplied fact."
		spans: []
		evidence: [{source: "heldout/d-aa", quote: "The green Quill contract suite exercises desktop dashboard clients only. It does not execute field monitor firmware."}]
	},
	{
		id:        "desktop-safety-shorthand", case: "telemetry-compatibility", arm: "full", target: "excerpt"
		criterion: "Is conditionally safe for desktop clients a justified bounded inference here, or an overstatement of limited test coverage?"
		expected:  "uncertain"
		reason:    "The conditions are not spelled out in this shorthand. The label needs adjudication of the inference/safety contract, rather than forced confidence."
		spans: [{pointer: "/summary", quote: "it is conditionally safe for desktop dashboard clients"}]
		evidence: [{source: "heldout/d-aa", quote: "The green Quill contract suite exercises desktop dashboard clients only. It does not execute field monitor firmware."}]
	},
	{
		id:        "standalone-directive-contract", case: "archive-access", arm: "full", target: "excerpt"
		criterion: "Should an answer-level judge reject this directive for omitting annex check-in when the whole answer contains that step?"
		expected:  "uncertain"
		reason:    "A standalone procedure directive would need the step; a reminder embedded in the full answer might not. The intended consumer contract must be agreed first."
		spans: [{pointer: "/directives/0/instruction", quote: "Tell the external visitor that on June 18, they must remain with an archivist and cannot access the archive unescorted."}, {pointer: "/claims/1/text", quote: "On June 18, booked visitors check in at the annex and must remain with an archivist."}]
		evidence: [{source: "heldout/d-8e", quote: "Booked visitors check in at the annex and remain with an archivist."}]
	},
	{
		id:        "echo-lineage-contract", case: "payout-recovery", arm: "vector-links", target: "claim"
		criterion: "Does citing the incident and its retelling establish correct source dependence or independent corroboration in the resulting knowledge representation?"
		expected:  "uncertain"
		reason:    "The claim has two citations but no explicit independence count. A text answer alone does not establish the future representation's lineage semantics."
		spans: [{pointer: "/claims/0/text", quote: "Rerunning a failed Orchid payout job can produce duplicate remittance emails."}]
		evidence: [{source: "heldout/d-13", quote: "In Orchid's production batch, repeating one failed payout sent two remittance emails; the ledger contained one posting."}, {source: "heldout/d-26", quote: "The remittance incident says a repeat produced two emails."}]
	},
]
