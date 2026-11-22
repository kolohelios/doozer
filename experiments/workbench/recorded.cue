package workbench

// Hand-authored backend responses, not model observations or hidden rubrics.
// The offline smoke test exercises plumbing; it cannot measure model quality.
#Broad: #Assertion & {
	id:          "retry-guidance"
	text:        "Sources express broad retry safety guidance; no evidence yet verifies every side effect."
	scope:       "unspecified-retry-behavior"
	attribution: "expressed"
	evidence: [
		{source: "guide", quote: "Event processing is idempotent."},
		{source: "retry", quote: "Yes, failed events can be retried safely."},
	]
}
#Writes: #Assertion & {
	id:          "database-writes"
	text:        "Database writes are deduplicated by event ID; this does not establish notification idempotence. The earlier broad guidance remains attributable, not a blanket implementation guarantee."
	scope:       "database-writes-versus-other-effects"
	attribution: "inferred"
	evidence: [
		{source: "guide", quote: "Event processing is idempotent."},
		{source: "retry", quote: "Yes, failed events can be retried safely."},
		{source: "code", quote: "We deduplicate database writes by event ID."},
	]
}
#Split: #Assertion & {
	id:          "notification-exception"
	text:        "Database writes are deduplicated by event ID. A production retry duplicated customer notifications, so the original unqualified retry guidance cannot be a live guarantee; this does not establish that every retry path is unsafe."
	scope:       "production-notifications-versus-database-writes"
	attribution: "inferred"
	evidence: [
		{source: "guide", quote: "Event processing is idempotent."},
		{source: "retry", quote: "Yes, failed events can be retried safely."},
		{source: "code", quote: "We deduplicate database writes by event ID."},
		{source: "incident", quote: "Retrying a failed production event caused two customer notifications."},
	]
}
#Scoped: #Assertion & {
	id:          "retry-safety-scoped"
	text:        "Database writes are deduplicated by event ID; notification side effects can duplicate. The documented manual-replay path suppresses outbound notifications. Retry safety depends on execution path and effects: retain the original broad guidance as history, not a blanket guarantee."
	scope:       "database-writes-notifications-and-manual-replay"
	attribution: "inferred"
	evidence: [
		{source: "guide", quote: "Event processing is idempotent."},
		{source: "retry", quote: "Yes, failed events can be retried safely."},
		{source: "code", quote: "We deduplicate database writes by event ID."},
		{source: "incident", quote: "Retrying a failed production event caused two customer notifications."},
		{source: "clarification", quote: "Database writes are deduplicated; notification side effects are not."},
		{source: "manual", quote: "Manual replay suppresses outbound notifications."},
	]
}
#Correction: #Assertion & {
	id:          "automatic-retry-boundary"
	text:        "The contextual No rejects extending the manual-replay mitigation to automatic retries; it does not revoke database-write deduplication."
	scope:       "automatic-retries"
	attribution: "inferred"
	evidence: [
		{source: "proposal", quote: "Then the manual workaround applies to automatic retries too?"},
		{source: "no", quote: "No."},
		{source: "manual", quote: "Manual replay suppresses outbound notifications."},
	]
}
#Ambiguous: #Assertion & {
	id:          "detached-stop"
	text:        "The detached Stop has no recoverable referent; retain the ambiguity without changing unrelated guidance or creating a human task."
	scope:       "unknown-referent"
	attribution: "ambiguous"
	evidence: [{source: "ambiguous", quote: "Stop."}]
}

recorded: {
	"expressed-guidance": {
		route: #Route & {action: "analyze"}
		analysis: #Analysis & {assertions: [#Broad]}
		patch: #Patch & {accounting: {guide: {mode: "represented", claims: ["retry-guidance"], reason: "Preserve expressed guidance."}, retry: {mode: "represented", claims: ["retry-guidance"], reason: "Preserve the attributable retry claim."}}, baseRevision: 0, operations: [{op: "add", assertion: #Broad}], rationale: "Retain expressed guidance without elevating it to verified implementation behavior."}
	}
	"narrow-code-evidence": {
		route: #Route & {action: "analyze"}
		analysis: #Analysis & {assertions: [#Writes]}
		patch: #Patch & {
			baseRevision: 1
			accounting: code: {mode: "represented", claims: ["database-writes"], reason: "Retain the implementation scope."}
			operations: [{op: "add", assertion: #Writes}, {op: "retire", id: "retry-guidance", replacement: "database-writes", reason: "Qualify the broad claim with implementation-specific evidence."}]
			rationale: "Preserve broad source history while narrowing the live view."
		}
	}
	"incident-reconciled": {
		route: #Route & {action: "analyze"}
		analysis: #Analysis & {assertions: [#Split]}
		patch: #Patch & {
			baseRevision: 2
			accounting: incident: {mode: "represented", claims: ["notification-exception"], reason: "Keep the material counterexample."}
			operations: [{op: "add", assertion: #Split}, {op: "retire", id: "database-writes", replacement: "notification-exception", reason: "Preserve deduplication while surfacing the material notification counterexample."}]
			rationale: "Split side-effect scopes instead of changing safe to universally unsafe."
		}
	}
	"scoped-mitigation": {
		route: #Route & {action: "analyze"}
		analysis: #Analysis & {assertions: [#Scoped]}
		patch: #Patch & {
			baseRevision: 3
			accounting: {
				clarification: {mode: "represented", claims: ["retry-safety-scoped"], reason: "Preserve separate effects."}
				manual: {mode: "represented", claims: ["retry-safety-scoped"], reason: "Preserve the manual-only mitigation."}
			}
			operations: [{op: "add", assertion: #Scoped}, {op: "retire", id: "notification-exception", replacement: "retry-safety-scoped", reason: "Add the manual-only mitigation without losing the notification exception."}]
			rationale: "Retain all evidence while making the execution-path distinction discoverable."
		}
	}
	"contextual-no": {
		route: #Route & {action: "analyze"}
		analysis: #Analysis & {assertions: [#Correction, #Ambiguous]}
		patch: #Patch & {accounting: {
			proposal: {mode: "represented", claims: ["automatic-retry-boundary"], reason: "Keep the correction's target."}
			no: {mode: "represented", claims: ["automatic-retry-boundary"], reason: "Keep the bounded correction."}
			ambiguous: {mode: "represented", claims: ["detached-stop"], reason: "Retain unresolved context."}
		}, baseRevision: 4, operations: [{op: "add", assertion: #Correction}, {op: "add", assertion: #Ambiguous}], rationale: "Resolve the explicit reply target but retain the detached intervention as ambiguous."
		}
	}
	"echo-and-projection": {
		route: #Route & {action: "analyze"}
		analysis: #Analysis & {assertions: [{
			id:          "incident-retelling"
			text:        "The new conversation repeats the existing incident; the generated handbook is derived from earlier sources, not independent corroboration."
			scope:       "dependent-retelling"
			attribution: "inferred"
			evidence: [{source: "echo", quote: "The incident report says a retry sent two notifications."}, {source: "incident", quote: "Retrying a failed production event caused two customer notifications."}]
		}]}
		patch: #Patch & {accounting: {
			echo: {mode: "dependent-no-op", claims: ["retry-safety-scoped"], reason: "Retelling of the existing incident, not a new independent observation.", basis: [{source: "incident", quote: "Retrying a failed production event caused two customer notifications."}]}
			handbook: {mode: "dependent-no-op", claims: ["retry-safety-scoped"], reason: "Derived handbook, not independent corroboration.", basis: [{source: "manual", quote: "Manual replay suppresses outbound notifications."}, {source: "incident", quote: "Retrying a failed production event caused two customer notifications."}]}
		}, baseRevision: 5, operations: [], rationale: "Retelling and derived text add no independent incident or new supported meaning."
		}
	}
}
