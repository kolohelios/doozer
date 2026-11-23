package judgment

reviewedContract: {
	version: "reviewed-meaning-transfer-v1"
	basis:   "Operationalization of the eight individually reviewed development examples, not blanket approval of the previous policy prose or any new fixture labels."
	rules: [
		{supports: ["01-source-uncertainty", "02-window-coverage", "03-extractor-limitation", "07-resolved-uncertainty"], text: "Separate source-stated uncertainty, bounded source-window coverage, and extractor interpretation limits. Source uncertainty has the source speaker as holder and the source's supplied frame; it is not an opposite world fact. Preserve the actual epistemic verb: not established in these notes does not prove personal ignorance. Extractor limitations go in extractionLimits, never source atoms. A missing reply parent is a context gap, not the speaker's professed ignorance or world opposition: retain the unavailable-reference marker and do not guess an environment or validity binding. Earlier honest uncertainty can be historical while a later date is established."},
		{supports: ["01-source-uncertainty", "02-window-coverage", "04-question-and-directive"], text: "Meaning and an inspectable recovery/projection path matter, not exact node counts or field placement. source-uncertainty and qualifier atoms may appear in atoms or conditions; duplicate equivalent annotations do not add evidence. Coverage and unestablished scalar views are DERIVED by code from the bounded supplied source window and scoped constraints: do not invent an extra source-unknown atom just because a source does not discuss a binding. Source limitations must not be hidden only in extractor prose."},
		{supports: ["03-extractor-limitation", "04-question-and-directive"], text: "A question retains its exact proposition value without asserting it. A directive's binding means ABOUT that topic, not a scalar assignment. Retain its action verb, object, and condition; storing the source's request creates no new task. A qualifier with operator one-provisional and alternative bindings means exactly one unidentified date is provisional, not that both are. Preserve the reported dates and unaffected venue."},
		{supports: ["05-assurance-withdrawal", "06-permission-revocation"], text: "An assurance asserts a proposition with an endorsement, not a new permission grant. Withdrawal targets the specified assurance, never the underlying permission or a separate current grant. Revocation targets an actual grant under declared authority. targetSource plus targetKind plus binding identifies the affected prior interpretation; never retire every property in a source. Grants/revocations concern normative permission, not a physical door."},
		{supports: ["07-resolved-uncertainty", "08-local-conflict"], text: "Keep source frame/statement time distinct from validity. New evidence can establish a previously unknown date without rescheduling the event or falsifying the earlier source limit. Preserve incompatible equally current values unless explicit applicable supersession resolves them; recency and counts are not resolution. Leave only the affected binding unresolved, keeping other supported facts available. Repetitions and projections are not independent corroboration."},
	]
	wire: "All bindings are manually declared scoped scalar variables with canonical literals and authority groups, not automatic entity linking. Every visible message gets a ledger entry. assertion and assurance use eq/neq with an exact literal in that message. source-uncertainty uses unknown, no value, and holder=source actor; its as-of frame is inherited from the source, not the latest window. question uses eq/neq and an exact asked-about value but makes no world constraint. directive uses none, no value, and a complete action tuple whose verb, object, and condition are contiguous source phrases (case-insensitive); its binding is an about-topic. grant/revocation are permission-only none/null acts. assurance-withdrawal targets an assurance; revocation targets a grant; supersession targets an assertion or qualifier. Grant and revision acts must match binding.authority; prior and current authority groups must match, and withdrawing an assurance also requires the original actor. Ambiguous prior interpretations or a partial target on a multi-topic qualifier are held, not repaired. Target pointers must be explicit in source text or replyTo. qualifier uses one-provisional, null binding/value, and two or more alternative binding IDs. Other atoms have no world effect. All other holder/target/action operands are null and alternatives empty. conditions is an equivalent placement only for source-uncertainty or qualifier. Source frames, actors, provenance origins, and authority identifiers are declared fixture premises, not verified truth. In this bounded wire, derived projection messages have only empty entries or other atoms: their originals carry the material interpretations and their complete projection text remains recoverable. This convention is not a universal prohibition on typed derived data."
}

reviewedPanelPlan: {
	version:                 "paired-reviewed-contract-transfer-v1"
	referenceStatus:         "fresh-transfer-probes-with-provisional-authored-labels-not-human-reviewed-held-out-gold"
	maxBudgetUSD:            5
	maxCalls:                49
	retries:                 0
	maxRequestBytes:         131072
	maxResponseBytes:        1048576
	transportTimeoutSeconds: 120
	maxOutputTokens:         8000
	orderSeed:               "reviewed-panel-transfer-v1"
	roles: {
		interpreter: {model: "openai/gpt-4.1", provider: "openai", promptPrice: "3", completionPrice: "9"}
		verifier: {model: "google/gemini-2.5-pro", provider: "google-ai-studio", promptPrice: "2", completionPrice: "12"}
		auditor: {model: "openai/o3", provider: "openai", promptPrice: "3", completionPrice: "9"}
		control: {model: "openai/o3", provider: "openai", promptPrice: "3", completionPrice: "9"}
	}
	extract: "Interpret the original correspondence using the complete shared semantic contract. You are not answering an evaluation hypothesis. Extract material assertions and acts in the declared binding vocabulary; unrelated conversation may have empty entries. Read reply targets and event/environment scope, not just matching values. Preserve explicit source uncertainty as typed source conditions; your own uncertainty belongs in extractionLimits. All model proposals remain untrusted. Do not invent tasks, dates, grants, or source statements. No reference labels, peer outputs, or future messages are supplied."
	audit:   "Audit both proposed ledgers against original messages under the SAME shared contract given to the extractors. Do not vote, repair, or choose a winning model. Assess each declared binding separately: faithful, material-error, unclear, or unavailable for each role. Inspect omitted qualifiers and unsupported extra facts even when scalar outcomes match. Topic links on directives are valid; atoms versus conditions placement and equivalent duplicates are not errors. Earlier source uncertainty must remain as-of its source frame, not current global fog. Derived coverage requires no duplicate unknown atom. A material-error label needs a role-specific issue citing original message IDs; faithful cannot coexist with a material issue for that role. Put general caveats in limitations. Agreeing proposals may share errors; original sources, not model opinions, are evidence. Missing proposals must be unavailable."
	scoring: [
		"Primary paired arms: single + deterministic checks versus the same primary + independent verifier + auditor. A verifier-only ablation separates disagreement checks from audit concerns. No arm substitutes verifier facts or hides a flagged source-qualified view.",
		"Compare binding-local normalized material signatures, separately from four-state query outcomes. Normalize conditions/atoms placement, identical duplicate atoms, canonical binary complements, source-assertion repeats in declared origin groups, qualifier alternative ordering, and action case/spacing/leading object article. Epistemic holder/frame and act targets remain distinct. This finite operational equivalence is not a general semantic oracle.",
		"Raw material signatures include rejected proposals; filtered scalar outcomes do not. Schema-invalid or uncompiled primary stages remain unavailable, not wrong answers or successes. Role, binding, query, snapshot, and cost denominators are retained.",
		"Flagged reference-faithful means disagreement against provisional signatures, not adjudicated unnecessary withholding. Count omitted/extra material memberships, unsupported or missing polarities, and eligibility separately. A binding-coincident auditor challenge is not proof that its stated reason identifies the actual fault; inspect issue text.",
		"Report prefix-to-final changes and stable supported query views, including eligibility of unaffected bindings. Shared controls test four authored semantic faults and three faithful layout pairs, not the distribution of naturally occurring errors.",
		"Limits prose and original source history remain inspectable; a free-text caveat neither becomes a source fact nor automatically suppresses an entire packet. Candidate eligibility is never acceptance. All roles receive the shared contract, not scoring rules, controls, references, or query hypotheses.",
	]
	policy: "Seven eight-message threads, prefixes of four and eight messages, three fixed calls per snapshot: interpreter, independent blind verifier, auditor. The same interpreter response and deterministic checks serve both arms; the panel only adds diagnostics, never replacement facts. One predeclared final-snapshot control per thread: three faithful layout-equivalence pairs and four identical shared semantic faults. Controls are authored, not real model outputs. No retries, repair, fallback, canonical acceptance, or retirement. No reference data in role inputs. Full availability denominators and all costs persist."
}

#TransferAtom: {
	kind:         "assertion" | "assurance" | "source-uncertainty" | "question" | "directive" | "grant" | "revocation" | "assurance-withdrawal" | "supersession" | "qualifier" | "other"
	binding:      *null | string
	operator:     *"none" | "eq" | "neq" | "unknown" | "one-provisional"
	value:        *null | string
	holder:       *null | string
	targetSource: *null | string
	targetKind:   *null | "assertion" | "assurance" | "grant" | "qualifier"
	action: *null | {verb: string, object: string, condition: string}
	alternatives: *[] | [...string]
}
#TransferAssertion: #TransferAtom & {kind: "assertion", binding: string, operator: *"eq" | "neq", value: string}
#TransferAssurance: #TransferAtom & {kind: "assurance", binding: string, operator: *"eq" | "neq", value: string}
#TransferUncertainty: #TransferAtom & {kind: "source-uncertainty", binding: string, operator: "unknown", holder: string}
#TransferAct: #TransferAtom & {binding: string}
#TransferSource: {id: string, actor: string, authority: string, origin: string, sentAt: string, replyTo: *null | string, derivedFrom: *[] | [...string], text: string}
reviewedThreads: [string]: {
	authority: string
	unavailableParents: *[] | [...string]
	bindings: [...{id: string, subject: string, property: "effective-date" | "location" | "permission" | "quiet-mail", scope: string, validTime: string | null, values: [...string]}]
	sources: [#TransferSource, ...#TransferSource]
	reference: [string]: [...#TransferAtom]
	queries: [...{id: string, binding: string, value: string, expected: {w0: string, w1: string}}]
	control: {kind: "equivalent" | "fault", span: string, binding: string, mode: "layout" | "omit" | "add", atom?: #TransferAtom}
}

transferLedgerSchema: {
	type: "object", additionalProperties: false, required: ["ledger", "extractionLimits"]
	properties: {
		extractionLimits: {type: "array", items: {type: "object", additionalProperties: false, required: ["about", "evidence", "reason"], properties: {about: {type: "array", items: {type: "string"}}, evidence: {type: "array", items: {type: "string"}}, reason: {type: "string"}}}}
		ledger: {type: "array", items: {
			type: "object", additionalProperties: false, required: ["span", "atoms", "conditions", "rationale"]
			properties: {
				span: {type: "string"}
				rationale: {type: "string"}
				atoms: {type: "array", items: #TransferAtomSchema}
				conditions: {type: "array", items: #TransferAtomSchema}
			}
		}}
	}
}
#TransferAtomSchema: {
	type: "object", additionalProperties: false
	required: ["kind", "binding", "operator", "value", "holder", "targetSource", "targetKind", "action", "alternatives"]
	properties: {
		kind: {type: "string", enum: ["assertion", "assurance", "source-uncertainty", "question", "directive", "grant", "revocation", "assurance-withdrawal", "supersession", "qualifier", "other"]}
		binding: {type: ["string", "null"], description: "Scoped proposition or ABOUT-topic, not automatically a changed value. Null only for qualifier or other."}
		operator: {type: "string", enum: ["none", "eq", "neq", "unknown", "one-provisional"]}
		value: {type: ["string", "null"], description: "Exact source literal for assertion, assurance, or question only. Questions retain content without asserting it."}
		holder: {type: ["string", "null"], description: "Source actor ONLY for source-uncertainty. The statement frame is inherited from its source."}
		targetSource: {type: ["string", "null"]}
		targetKind: {type: ["string", "null"], enum: [null, "assertion", "assurance", "grant", "qualifier"]}
		action: {anyOf: [{type: "null"}, {type: "object", additionalProperties: false, required: ["verb", "object", "condition"], properties: {verb: {type: "string"}, object: {type: "string"}, condition: {type: "string"}}}]}
		alternatives: {type: "array", items: {type: "string"}}
	}
}
transferAuditSchema: {
	type: "object", additionalProperties: false, required: ["checks", "limitations"]
	properties: {
		limitations: {type: "array", items: {type: "string"}}
		checks: {type: "array", items: {
			type: "object", additionalProperties: false, required: ["binding", "interpreter", "verifier", "issues", "rationale"]
			properties: {
				binding: {type: "string"}
				interpreter: {type: "string", enum: ["faithful", "material-error", "unclear", "unavailable"]}
				verifier: {type: "string", enum: ["faithful", "material-error", "unclear", "unavailable"]}
				rationale: {type: "string"}
				issues: {type: "array", items: {type: "object", additionalProperties: false, required: ["affects", "evidence", "detail"], properties: {affects: {type: "string", enum: ["interpreter", "verifier", "both"]}, evidence: {type: "array", items: {type: "string"}}, detail: {type: "string"}}}}
			}
		}}
	}
}
