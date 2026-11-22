package calibration

// New synthetic correspondence, not edits to the saved study or human gold.
threads: [
	{
		id:               "recovery-path-correction"
		cohort:           "primary"
		synthetic:        true
		context:          "complete"
		question:         "How should the Harbor payout retry guidance be qualified after this exchange?"
		correction:       "m-f2"
		expectedReferent: "m-d9"
		messages: [
			{id: "m-a1", speaker: "speaker-a", saidAt: "2026-09-01T09:00:00Z", anchor: "fixture://correspondence/m-a1", text: "The Harbor recovery page currently says failed payouts are safe to retry. I would like to keep the advice short, but we should be clear about which effects are covered rather than make the operator infer that from the implementation."},
			{id: "m-b7", speaker: "speaker-b", saidAt: "2026-09-01T09:10:00Z", anchor: "fixture://correspondence/m-b7", replyTo: "m-a1", text: "In yesterday's Harbor incident, repeating the failed payout produced two customer emails while the ledger still had one posting. The payout-id constraint protected ledger writes; email delivery happens outside that transaction. The incident does not mean ledger deduplication stopped working."},
			{id: "m-c4", speaker: "speaker-c", saidAt: "2026-09-01T09:20:00Z", anchor: "fixture://correspondence/m-c4", replyTo: "m-b7", text: "For an operator recovery we can use the documented --ledger-only option on the recovery command to bypass email sending. That option belongs to this command; the background retry scheduler does not read it. Please keep that path distinction in the recovery page."},
			{id: "m-d9", speaker: "speaker-a", saidAt: "2026-09-01T09:25:00Z", anchor: "fixture://correspondence/m-d9", replyTo: "m-c4", text: "If the recovery option bypasses email, could we say automatic retries are protected by it as well? I was going to put the manual command and scheduler under a single safe-to-retry heading so the guide has only one procedure."},
			{id: "m-e3", speaker: "speaker-b", saidAt: "2026-09-01T09:26:00Z", anchor: "fixture://correspondence/m-e3", replyTo: "m-b7", text: "Separately, the ledger uniqueness constraint is still the right mechanism for repeated writes. We should not remove that narrower assurance just because the email side effect behaved differently in the incident."},
			{id: "m-f2", speaker: "speaker-c", saidAt: "2026-09-01T09:30:00Z", anchor: "fixture://correspondence/m-f2", replyTo: "m-d9", text: "No, that email bypass is only for the operator recovery command. It does not make the scheduler's automatic retries safe from duplicate email. Keep the ledger-write assurance, but qualify notification behavior by execution path instead of replacing the whole guide with either safe or unsafe."},
		]
		expected: {
			known: [
				{meaning: "The reported retry kept one ledger posting but duplicated email; the thread distinguishes those effects.", support: [{message: "m-b7", quote: "In yesterday's Harbor incident, repeating the failed payout produced two customer emails while the ledger still had one posting. The payout-id constraint protected ledger writes; email delivery happens outside that transaction."}]},
				{meaning: "The correction rejects extending the operator-command email bypass to the scheduler, not the ledger assurance.", support: [{message: "m-d9", quote: "could we say automatic retries are protected by it as well?"}, {message: "m-f2", quote: "No, that email bypass is only for the operator recovery command. It does not make the scheduler's automatic retries safe from duplicate email. Keep the ledger-write assurance, but qualify notification behavior by execution path instead of replacing the whole guide with either safe or unsafe."}]},
			]
			unresolved: []
			forbidden: ["Treat the correction as retracting ledger deduplication.", "Present the manual bypass as protection for all automatic retries.", "Treat the immediately preceding ledger side discussion as the correction's reply target."]
		}
	},
	{
		id:               "staff-exception-correction"
		cohort:           "primary"
		synthetic:        true
		context:          "complete"
		question:         "What visitor guidance applies at Maple on September 12 and after the normal reading room reopens?"
		correction:       "m-r8"
		expectedReferent: "m-p5"
		messages: [
			{id: "m-k2", speaker: "speaker-d", saidAt: "2026-09-09T09:00:00Z", anchor: "fixture://correspondence/m-k2", text: "The normal Maple reading room procedure allows visitors to examine catalog boxes without an escort after check-in. Original manuscript handling is different and still requires an archivist; please do not collapse those two activities into one permission."},
			{id: "m-l4", speaker: "speaker-e", saidAt: "2026-09-10T09:00:00Z", anchor: "fixture://correspondence/m-l4", replyTo: "m-k2", text: "The main room will be closed on September 12 only for remediation. Booked visitors must check in at the annex and stay with an archivist that day. The normal room and its usual visitor procedure resume on September 13; this notice is not a permanent move to the annex."},
			{id: "m-n7", speaker: "speaker-f", saidAt: "2026-09-12T08:00:00Z", anchor: "fixture://correspondence/m-n7", replyTo: "m-l4", text: "Two staff researchers entered the annex without an escort during the equipment drill. That was a staff-only exception for the drill, not a new public visitor arrangement. I am recording it here so the sign-in report is not mistaken for the ordinary visitor procedure."},
			{id: "m-p5", speaker: "speaker-d", saidAt: "2026-09-12T08:05:00Z", anchor: "fixture://correspondence/m-p5", replyTo: "m-n7", text: "Does the unescorted drill access mean we can also let booked external visitors use the annex on their own today? I want to tell the afternoon group the correct rule rather than send them through a staff-only arrangement."},
			{id: "m-q1", speaker: "speaker-e", saidAt: "2026-09-12T08:06:00Z", anchor: "fixture://correspondence/m-q1", replyTo: "m-l4", text: "A separate logistics note: the temporary signs will be removed after the closure, when the normal room reopens. The signs are not a change to the manuscript handling requirement or the check-in procedure."},
			{id: "m-r8", speaker: "speaker-f", saidAt: "2026-09-12T08:10:00Z", anchor: "fixture://correspondence/m-r8", replyTo: "m-p5", text: "No, that unescorted exception was limited to staff taking part in the equipment drill. External visitors still need annex check-in and an archivist with them today. After the main room reopens, use the normal catalog-box rule, while keeping the original-manuscript escort requirement in place."},
		]
		expected: {
			known: [
				{meaning: "September 12 visitor access uses annex check-in and an archivist; staff drill behavior does not extend permission to visitors.", support: [{message: "m-p5", quote: "let booked external visitors use the annex on their own today?"}, {message: "m-r8", quote: "No, that unescorted exception was limited to staff taking part in the equipment drill. External visitors still need annex check-in and an archivist with them today."}]},
				{meaning: "Normal catalog-box access resumes after the one-day closure, without erasing the manuscript exception.", support: [{message: "m-k2", quote: "allows visitors to examine catalog boxes without an escort after check-in."}, {message: "m-l4", quote: "The normal room and its usual visitor procedure resume on September 13"}, {message: "m-r8", quote: "keeping the original-manuscript escort requirement in place."}]},
			]
			unresolved: []
			forbidden: ["Infer visitor permission from observed staff-only drill access.", "Turn the one-day annex procedure into a permanent rule.", "Apply the correction to the intervening logistics message instead of its explicit reply target."]
		}
	},
	{
		id:         "missing-reply-context"
		cohort:     "robustness"
		synthetic:  true
		context:    "missing"
		question:   "What can responsibly be retained or concluded from this available message?"
		correction: "m-v6"
		messages: [
			{id: "m-v6", speaker: "speaker-g", saidAt: "2026-09-12T08:10:00Z", anchor: "fixture://correspondence/m-v6", replyTo: "m-unavailable", text: "No, that exception was limited to staff taking part in the drill. It was not a change to the visitor procedure. Please keep the restriction attached to the situation we were discussing rather than carrying it over to unrelated visits."},
		]
		expected: {
			known: [{meaning: "The speaker expresses a staff-only limitation and rejects treating it as a visitor-procedure change.", support: [{message: "m-v6", quote: "that exception was limited to staff taking part in the drill. It was not a change to the visitor procedure."}]}]
			unresolved: ["The actual parent message and precise exception referent are unavailable.", "The location, applicable date, and complete visitor procedure are not established by the message timestamp."]
			forbidden: ["Invent a parent message or attach the correction to another thread by vocabulary similarity alone.", "Discard the known staff-only limitation merely because some context is missing.", "Rewrite unrelated visitor guidance or manufacture a human task queue."]
		}
	},
]
