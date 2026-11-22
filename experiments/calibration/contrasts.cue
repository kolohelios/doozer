package calibration

// Deliberately authored contrasts, not observed model outputs or human gold.
// Each group shares one criterion and the same unmodified source thread.
threadContrasts: [
	{
		thread:    "recovery-path-correction"
		criterion: "Does the whole answer distinguish ledger-write protection from email risk, preserve the manual-command-only bypass, and interpret the correction without retracting ledger deduplication?"
		candidates: [
			{
				id:        "harbor-bounded-answer"
				candidate: "Qualify the broad safe-to-retry guidance by effect and execution path. The reported retry left one ledger posting but produced two emails. The operator recovery command's --ledger-only option bypasses email; the background scheduler does not read that option, so do not extend that mitigation to automatic retries. The correction rejects that extension, not ledger-write deduplication."
				expected:  "pass"
				reason:    "The answer preserves both distinctions and the target of the correction without claiming every automatic retry delivers email."
				spans: ["The correction rejects that extension, not ledger-write deduplication."]
				evidence: [{message: "m-b7", quote: "repeating the failed payout produced two customer emails while the ledger still had one posting."}, {message: "m-c4", quote: "That option belongs to this command; the background retry scheduler does not read it."}, {message: "m-f2", quote: "Keep the ledger-write assurance"}]
			},
			{
				id:        "harbor-global-retraction"
				candidate: "The latest correction retracts the ledger-write assurance as well as email safety. The guide should now say repeated payouts can duplicate ledger postings, regardless of the payout-id constraint. The manual recovery command can bypass email, but the scheduler does not read its switch."
				expected:  "fail"
				reason:    "It retains the command boundary but reverses the correction's explicit preservation of the ledger assurance. This is a scope error, not merely an omitted citation."
				spans: ["The latest correction retracts the ledger-write assurance as well as email safety."]
				evidence: [{message: "m-d9", quote: "could we say automatic retries are protected by it as well?"}, {message: "m-f2", quote: "Keep the ledger-write assurance"}]
			},
			{
				id:        "harbor-bypass-extension"
				candidate: "Ledger writes are deduplicated and email previously duplicated. The recovery command's --ledger-only option is the mitigation for both operator recovery and the background scheduler, so automatic retries using that option are protected from duplicate email. The correction preserves the ledger assurance."
				expected:  "fail"
				reason:    "Most of the answer is faithful, but it extends the manual mitigation to the path that explicitly does not read it."
				spans: ["the mitigation for both operator recovery and the background scheduler"]
				evidence: [{message: "m-c4", quote: "That option belongs to this command; the background retry scheduler does not read it."}]
			},
		]
	},
	{
		thread:    "staff-exception-correction"
		criterion: "Does the whole answer preserve September 12 annex check-in and escort, reject extending the staff drill exception to visitors, restore normal catalog-box access from September 13, and retain the manuscript escort restriction?"
		candidates: [
			{
				id:        "maple-bounded-answer"
				candidate: "On September 12, booked external visitors must check in at the annex and stay with an archivist. Unescorted staff drill access does not grant visitors the same permission. From September 13 the normal room procedure resumes: catalog boxes may be examined without an escort after check-in, but original manuscripts still require an archivist. The correction answers the visitor proposal, not the intervening note about signs."
				expected:  "pass"
				reason:    "All material procedure, date, activity, and staff-versus-visitor boundaries are explicit in this whole answer. It makes no claim about retained system history."
				spans: ["Unescorted staff drill access does not grant visitors the same permission.", "but original manuscripts still require an archivist."]
				evidence: [{message: "m-l4", quote: "The normal room and its usual visitor procedure resume on September 13"}, {message: "m-k2", quote: "allows visitors to examine catalog boxes without an escort after check-in."}, {message: "m-r8", quote: "External visitors still need annex check-in and an archivist with them today."}, {message: "m-r8", quote: "keeping the original-manuscript escort requirement in place."}]
			},
			{
				id:        "maple-permanent-exception"
				candidate: "The staff-only drill exception does not apply to external visitors. From September 12 onward, booked visitors must always check in at the annex and remain with an archivist, even after the normal room reopens. Original manuscripts also require an archivist."
				expected:  "fail"
				reason:    "Correct staff scope and manuscript handling do not rescue converting a one-day procedure into a permanent visitor rule."
				spans: ["even after the normal room reopens"]
				evidence: [{message: "m-l4", quote: "The normal room and its usual visitor procedure resume on September 13; this notice is not a permanent move to the annex."}]
			},
			{
				id:        "maple-staff-transfer"
				candidate: "On September 12 booked external visitors check in at the annex, but may then enter unescorted under the same exception used by staff in the drill. From September 13 normal catalog-box access after check-in resumes. Original manuscripts still require an archivist."
				expected:  "fail"
				reason:    "The answer preserves the date and manuscript boundaries but grants exactly the visitor permission the correction rejects."
				spans: ["may then enter unescorted under the same exception used by staff in the drill"]
				evidence: [{message: "m-r8", quote: "No, that unescorted exception was limited to staff taking part in the equipment drill. External visitors still need annex check-in and an archivist with them today."}]
			},
			{
				id:        "maple-manuscript-omission"
				candidate: "On September 12, booked external visitors must check in at the annex and stay with an archivist. The staff drill exception does not apply to them. From September 13 normal room access resumes, with catalog boxes available without an escort after check-in."
				expected:  "fail"
				reason:    "The whole answer omits the material manuscript restriction required by this criterion. There is no fabricated quotation for the absent meaning."
				spans: []
				evidence: [{message: "m-k2", quote: "Original manuscript handling is different and still requires an archivist"}]
			},
		]
	},
	{
		thread:    "missing-reply-context"
		criterion: "Does the whole answer retain the explicit staff-only limitation and rejection of a visitor-procedure change while acknowledging the unavailable parent, unknown precise exception, location, applicable date, and complete visitor procedure, without inventing them?"
		candidates: [
			{
				id:        "partial-context-bounded-answer"
				candidate: "The available message limits an exception to staff participating in a drill and says it did not change the visitor procedure. Preserve that message and its reply reference, but the parent body is unavailable: the precise exception, location, applicable date, and full visitor procedure are not established here. The statement timestamp alone does not establish the exception's effective date. Do not revise unrelated visitor guidance on this evidence alone. This answer does not verify that a storage system retained the message."
				expected:  "pass"
				reason:    "It keeps supported partial meaning and marks the missing context without guessing it or treating an answer as proof of durable retention."
				spans: ["the precise exception, location, applicable date, and full visitor procedure are not established here"]
				evidence: [{message: "m-v6", quote: "that exception was limited to staff taking part in the drill. It was not a change to the visitor procedure."}]
			},
			{
				id:        "partial-context-invented-target"
				candidate: "This replies to Maple's September 12 annex visitor proposal. The exception was staff-only, so Maple's booked visitors must use annex check-in and stay with an archivist on that date. The message timestamp establishes when that visitor procedure applies."
				expected:  "fail"
				reason:    "It borrows plausible specifics from another fixture even though this local message supplies no location, parent body, or complete procedure. Statement time does not fill that gap."
				spans: ["This replies to Maple's September 12 annex visitor proposal."]
				evidence: [{message: "m-v6", quote: "Please keep the restriction attached to the situation we were discussing rather than carrying it over to unrelated visits."}]
			},
			{
				id:        "partial-context-total-abstention"
				candidate: "The parent is missing, so nothing can be concluded from this message, including whether the exception was staff-only. No meaning should be retained until someone supplies the full thread."
				expected:  "fail"
				reason:    "Uncertainty about the referent does not erase the explicit partial meaning. The criterion requires bounded interpretation, not indiscriminate abstention."
				spans: ["nothing can be concluded from this message, including whether the exception was staff-only"]
				evidence: [{message: "m-v6", quote: "that exception was limited to staff taking part in the drill."}]
			},
		]
	},
]
