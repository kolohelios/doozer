package judgment

meaningContract: {
	version:      "reviewed-source-projection-v2"
	status:       "offline-prospective-wire-and-authored-controls-not-a-live-protocol"
	instructions: "Extract only from original sources, using the declared scoped scalar bindings and procedure topics. Every source has one ledger entry with atoms, conditions, annotations, and rationale. Keep ordinary scalar assertions, questions, grants, withdrawals, and revocations in their existing constructors. Unframed source-uncertainty is not allowed in this version: use a condition annotation with an explicit frame and stance. source-note conditions mean no-finding-in-note or not-established-in-notes, holder=null; the source actor remains the reporting speaker, not a claim about personal ignorance. person conditions mean does-not-know and holder=the source actor. Conditions require exact source quotes and never assign world values. Derived source-window coverage is computed by code; an extra source-note node is optional if its qualification remains recoverable to the pertinent consumer. Speculation retains its quoted eq/neq proposition and speaker but is never a supporting or opposing world witness. Assess any separately supplied observation independently. A directive can use the existing about-binding constructor or a procedure annotation naming a declared topic linked to bindings. Preserve its action verb, object, and condition as source phrases and retain the complete source paragraph for referent recovery. Neither encoding changes permission or dispatches a task. Report your own extraction limits separately. Literal/shape checks do not prove stance classification, entailment, or correct topic linking."
	boundary:     "Two individually reviewed source meanings and the user's hunch clarification guide these controls. New wire grammar and fresh hunch/personal-ignorance probes are provisional, not separately approved or held-out gold. No model calls, old-result rescoring, canonical acceptance, or retirement. Source identity, frames, scalar bindings, authority, lineage, and procedure-topic links remain manually supplied premises."
}

meaningAnnotationSchema: {
	anyOf: [
		{type: "object", additionalProperties: false, required: ["kind", "binding", "frame", "stance", "holder", "quote"], properties: {
			kind: {type: "string", enum: ["condition"]}
			binding: {type: "string"}
			frame: {type: "string", enum: ["source-note", "person"]}
			stance: {type: "string", enum: ["no-finding-in-note", "not-established-in-notes", "does-not-know"]}
			holder: {type: ["string", "null"]}
			quote: {type: "string"}
		}},
		{type: "object", additionalProperties: false, required: ["kind", "binding", "operator", "value", "quote"], properties: {
			kind: {type: "string", enum: ["speculation"]}
			binding: {type: "string"}
			operator: {type: "string", enum: ["eq", "neq"]}
			value: {type: "string"}
			quote: {type: "string"}
		}},
		{type: "object", additionalProperties: false, required: ["kind", "topic", "action", "quote"], properties: {
			kind: {type: "string", enum: ["procedure"]}
			topic: {type: "string"}
			action: {type: "object", additionalProperties: false, required: ["verb", "object", "condition"], properties: {verb: {type: "string"}, object: {type: "string"}, condition: {type: "string"}}}
			quote: {type: "string"}
		}},
	]
}

#ProjectionCase: {
	packet: string
	topics: *{} | {[string]: [string, ...string]}
	annotations: *{} | {[string]: [...]}
	directives: *[] | [...{span: string, binding: string, action: {verb: string, object: string, condition: string}}]
	addedSources: *[] | [...{id: string, actor: string, authority: string, origin: string, sentAt: string, text: string, frame: string, replyTo: *null | string, derivedFrom: *[] | [...string], atoms: *[] | [...#TransferAtom], annotations: *[] | [...]}]
	expected: [...{binding: string, value: string, state: "supported" | "opposed" | "contested" | "unestablished"}]
}
projectionCases: [string]: #ProjectionCase
projectionCases: {
	"unresolved-qualifier": {packet: "unresolved-qualifier/w1", expected: [{binding: "b0", value: "2031-08-14", state: "supported"}, {binding: "b1", value: "2031-08-15", state: "supported"}, {binding: "b2", value: "Juniper studio", state: "supported"}]}
	"coverage-derived": {packet: "regional-coverage/w0", expected: [{binding: "b0", value: "enabled", state: "unestablished"}, {binding: "b1", value: "enabled", state: "supported"}, {binding: "b2", value: "Sable vault", state: "supported"}]}
	"coverage-explicit": {
		packet: "regional-coverage/w0"
		annotations: m1: [{kind: "condition", binding: "b0", frame: "source-note", stance: "no-finding-in-note", holder: null, quote: "This observation covers staging-west only and supplies no production-west finding in these notes."}]
		expected: projectionCases["coverage-derived"].expected
	}
	"coverage-known-later": {
		packet:      "regional-coverage/w1"
		annotations: projectionCases["coverage-explicit"].annotations
		expected: [{binding: "b0", value: "enabled", state: "opposed"}, {binding: "b2", value: "Sable vault", state: "supported"}]
	}
	"invitation-direct": {
		packet: "independent-grant-survives/w1"
		directives: [{span: "m2", binding: "b0", action: {verb: "do not use", object: "its invitation", condition: "as a visitor permission record for another event"}}]
		expected: [{binding: "b0", value: "permitted", state: "supported"}, {binding: "b1", value: "Oak hall", state: "supported"}]
	}
	"invitation-topic": {
		packet: "independent-grant-survives/w1"
		topics: "permission-evidence-use": ["b0"]
		annotations: m2: [{kind: "procedure", topic: "permission-evidence-use", action: {verb: "do not use", object: "its invitation", condition: "as a visitor permission record for another event"}, quote: "Please do not use its invitation as a visitor permission record for another event."}]
		expected: projectionCases["invitation-direct"].expected
	}
	"hunch-only": {
		packet: "regional-coverage/w0"
		addedSources: [{id: "h1", actor: "Mo", authority: "participant", origin: "hunch", sentAt: "2031-07-19T09:00:00Z", frame: "w1", text: "My hunch is that quiet-mail is enabled in production-west for 2031-07-20. This is speculation, not a deployment observation.", annotations: [{kind: "speculation", binding: "b0", operator: "eq", value: "enabled", quote: "My hunch is that quiet-mail is enabled in production-west for 2031-07-20."}]}]
		expected: projectionCases["coverage-derived"].expected
	}
	"hunch-with-observation": {
		packet: "regional-coverage/w0"
		addedSources: [projectionCases["hunch-only"].addedSources[0], {id: "h2", actor: "Tess", authority: "operations", origin: "production-observation", sentAt: "2031-07-19T09:10:00Z", frame: "w1", text: "For production-west on 2031-07-20, the export scheduler's quiet-mail setting is disabled.", atoms: [#TransferAssertion & {binding: "b0", value: "disabled"}]}]
		expected: [{binding: "b0", value: "enabled", state: "opposed"}, {binding: "b1", value: "enabled", state: "supported"}]
	}
	"personal-unknown": {
		packet: "regional-coverage/w0"
		addedSources: [{id: "u1", actor: "Mo", authority: "participant", origin: "personal-unknown", sentAt: "2031-07-19T09:00:00Z", frame: "w1", text: "I do not know the production-west quiet-mail setting for 2031-07-20.", annotations: [{kind: "condition", binding: "b0", frame: "person", stance: "does-not-know", holder: "Mo", quote: "I do not know the production-west quiet-mail setting for 2031-07-20."}]}]
		expected: projectionCases["coverage-derived"].expected
	}
}
