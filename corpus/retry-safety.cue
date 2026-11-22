package corpus

version: 1
scenarios: "retry-safety": {
	title:     "Retry safety depends on execution path and side effects"
	design:    "EDD §3, §6.3, §7.4, §12–14"
	synthetic: true
	tags: ["scope", "counterexample", "replay", "one-word-reversal", "ambiguity", "freshness", "projection-feedback", "echo"]
	sources: {
		guide: {kind: "document", text: "Event processing is idempotent.", anchor: "fixture://retry/guide#processing", saidAt: "2026-01-01T09:00:00Z", scope: "unspecified"}
		retry: {kind: "conversation", text: "Yes, failed events can be retried safely.", anchor: "fixture://retry/thread/1", saidAt: "2026-01-02T09:00:00Z", scope: "unspecified"}
		code: {kind: "code", text: "We deduplicate database writes by event ID.", anchor: "fixture://retry/review/42", saidAt: "2026-01-03T09:00:00Z", scope: "database-writes"}
		incident: {kind: "observation", text: "Retrying a failed production event caused two customer notifications.", anchor: "fixture://retry/incident/7", saidAt: "2026-01-04T09:00:00Z", scope: "production-notifications"}
		clarification: {kind: "conversation", text: "Database writes are deduplicated; notification side effects are not.", anchor: "fixture://retry/thread/2", saidAt: "2026-01-05T09:00:00Z", scope: "writes-versus-notifications"}
		manual: {kind: "document", text: "Manual replay suppresses outbound notifications.", anchor: "fixture://retry/ops#manual-replay", saidAt: "2026-01-06T09:00:00Z", scope: "manual-replay"}
		proposal: {kind: "conversation", text: "Then the manual workaround applies to automatic retries too?", anchor: "fixture://retry/thread/3", saidAt: "2026-01-07T09:00:00Z", scope: "automatic-retries"}
		no: {kind: "conversation", text: "No.", replyTo: "proposal", anchor: "fixture://retry/thread/4", saidAt: "2026-01-07T09:01:00Z", scope: "automatic-retries"}
		ambiguous: {kind: "conversation", text: "Stop.", anchor: "fixture://retry/detached/1", saidAt: "2026-01-07T10:00:00Z", scope: "unknown-referent"}
		echo: {kind: "conversation", text: "The incident report says a retry sent two notifications.", replyTo: "incident", anchor: "fixture://retry/thread/5", saidAt: "2026-01-08T09:00:00Z", scope: "reported-incident-not-independent-observation"}
		handbook: {kind: "projection", text: "Database writes are deduplicated. Notifications may duplicate; manual replay suppresses them.", derivedFrom: ["code", "incident", "clarification", "manual"], anchor: "fixture://retry/generated/handbook", saidAt: "2026-01-09T09:00:00Z", scope: "derived-retry-guidance"}
	}
	steps: [
		{
			id: "expressed-guidance"
			receive: ["guide", "retry"]
			reconcile: ["guide", "retry"]
			expect: {
				must: [{id: "expressed-not-proven", meaning: "Sources express broad retry guidance, but do not verify all side effects.", scope: "unspecified", evidence: ["guide", "retry"]}]
				mustNot: [{id: "blanket-guarantee", meaning: "All retries are verified safe.", reason: "Expressed guidance is not implementation evidence."}]
				pending: []
			}
		},
		{
			id: "narrow-code-evidence"
			receive: ["code"]
			reconcile: ["code"]
			expect: {
				must: [{id: "writes-only", meaning: "Implementation evidence supports deduplication of database writes by event ID only.", scope: "database-writes", evidence: ["code", "guide"]}]
				mustNot: [{id: "all-effects", meaning: "Code proves notification idempotence.", reason: "The evidence covers database writes only."}]
				pending: []
			}
		},
		{
			id: "received-not-processed"
			receive: ["incident"]
			reconcile: []
			expect: {
				must: [{id: "snapshot-with-lag", meaning: "The processed view supports database-write deduplication and discloses newer unreconciled evidence.", scope: "processed-snapshot", evidence: ["code"]}]
				mustNot: [{id: "false-freshness", meaning: "The reconciled answer includes all received evidence.", reason: "The incident is still pending; a source-only preview must be labeled."}]
				pending: ["incident"]
				queries: [{question: "Are notifications safe to retry?", state: "pending", meaning: "No reconciled guarantee; newer incident evidence awaits processing.", evidence: ["incident"]}]
			}
		},
		{
			id: "incident-reconciled"
			receive: []
			reconcile: ["incident"]
			expect: {
				must: [{id: "material-counterexample", meaning: "A production retry duplicated notifications; database-write deduplication remains supported.", scope: "production-notifications-versus-writes", evidence: ["incident", "code"]}]
				mustNot: [{id: "blanket-unsafe", meaning: "All retry paths and all database writes are unsafe.", reason: "The counterexample has a bounded scope."}]
				pending: []
			}
		},
		{
			id: "scoped-mitigation"
			receive: ["clarification", "manual"]
			reconcile: ["clarification", "manual"]
			expect: {
				must: [{id: "three-way-distinction", meaning: "Writes deduplicate; retries may duplicate notifications; the documented manual-replay path suppresses notifications. Preserve the original broad guidance as history, not a live guarantee.", scope: "execution-path-specific", evidence: ["guide", "code", "incident", "clarification", "manual"]}]
				mustNot: [{id: "automatic-mitigation", meaning: "The manual-replay workaround protects automatic retries.", reason: "Manual mitigation does not establish automatic behavior."}]
				pending: []
				queries: [
					{question: "Can I replay a failed event?", state: "supported", meaning: "Explain writes versus notifications and limit the suppression mitigation to documented manual replay; cite sources in handbook and directive projections.", evidence: ["code", "incident", "manual"]},
					{question: "Are payment side effects idempotent?", state: "absent", meaning: "No supported answer was found in this fixture; do not claim global absence of knowledge.", evidence: []},
				]
			}
		},
		{
			id: "duplicate-delivery"
			receive: ["incident", "manual"]
			reconcile: ["incident", "manual"]
			expect: {
				must: [{id: "stable-replay", meaning: "No duplicated semantic effects, additional corroboration, or gratuitous rewrite; source and historical discovery links remain usable.", scope: "repeated-source-identities", evidence: ["incident", "manual"]}]
				mustNot: [{id: "double-counting", meaning: "Redelivery is a second independent incident.", reason: "Delivery identity is not new evidence."}]
				pending: []
				equivalentTo: "scoped-mitigation"
			}
		},
		{
			id: "contextual-no"
			receive: ["proposal", "no", "ambiguous"]
			reconcile: ["proposal", "no", "ambiguous"]
			expect: {
				must: [
					{id: "reply-target", meaning: "No rejects extending the manual mitigation to automatic retries, not database deduplication.", scope: "automatic-retries", evidence: ["proposal", "no", "manual"]},
					{id: "unknown-target", meaning: "Retain the detached Stop as ambiguous without inventing a referent or a human task queue.", scope: "unknown-referent", evidence: ["ambiguous"]},
				]
				mustNot: [{id: "global-stop", meaning: "Stop revokes all retry guidance.", reason: "The detached intervention has no known target."}]
				pending: []
			}
		},
		{
			id: "echo-and-projection"
			receive: ["echo", "handbook"]
			reconcile: ["echo", "handbook"]
			expect: {
				must: [{id: "no-self-support", meaning: "Keep the incident's single evidentiary origin; neither its retelling nor the generated handbook independently corroborates it. Handbook and bounded directives preserve the same scope and counterexample.", scope: "evidence-lineage", evidence: ["incident", "echo", "handbook", "manual"]}]
				mustNot: [{id: "evidence-inflation", meaning: "Three independent sources prove notification unsafety.", reason: "Echo and projection depend on the same incident."}]
				pending: []
				equivalentTo: "contextual-no"
			}
		},
	]
}
