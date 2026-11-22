package corpus

scenarios: "visitor-access": {
	title:     "A nonengineering procedure retains temporary exceptions"
	design:    "EDD §5.4 and §14 nonengineering procedure"
	synthetic: true
	tags: ["nonengineering", "temporal-scope", "exception-preservation"]
	sources: {
		guide: {kind: "document", text: "Visitors check in at the front desk before entering.", anchor: "fixture://visitors/guide", saidAt: "2026-05-01T09:00:00Z", scope: "normal-opening-hours"}
		closure: {kind: "document", text: "On May 8 only, the front desk is closed; visitors must check in with the host at the east entrance. The normal procedure resumes May 9.", anchor: "fixture://visitors/notice", saidAt: "2026-05-07T09:00:00Z", scope: "may-8-only"}
		question: {kind: "conversation", text: "So visitors no longer need to check in?", anchor: "fixture://visitors/thread/1", saidAt: "2026-05-07T10:00:00Z", scope: "proposed-interpretation"}
		no: {kind: "conversation", text: "No. Check-in is still required; only the location changes that day.", replyTo: "question", anchor: "fixture://visitors/thread/2", saidAt: "2026-05-07T10:01:00Z", scope: "may-8-check-in"}
	}
	steps: [
		{
			id: "temporary-location", receive: ["guide", "closure"], reconcile: ["guide", "closure"]
			expect: {
				must: [{id: "date-bounded-exception", meaning: "Use host check-in at the east entrance on May 8; retain front-desk check-in otherwise and keep both source anchors.", scope: "visitor-check-in-by-date", evidence: ["guide", "closure"]}]
				mustNot: [{id: "permanent-replacement", meaning: "All future visitors use the east entrance.", reason: "The notice applies on one date only."}]
				pending: []
				queries: [{question: "Where do I check in on May 9?", state: "supported", meaning: "At the front desk under the normal procedure.", evidence: ["guide", "closure"]}]
			}
		},
		{
			id: "correction-not-cancellation", receive: ["question", "no"], reconcile: ["question", "no"]
			expect: {
				must: [{id: "preserve-obligation", meaning: "No rejects dropping check-in, not the temporary east-entrance exception. Any visitor directive must retain both date and host requirements.", scope: "may-8-check-in", evidence: ["question", "no", "closure"]}]
				mustNot: [{id: "no-check-in", meaning: "Visitors may enter without checking in.", reason: "The explicit correction preserves the obligation."}]
				pending: []
			}
		},
	]
}
