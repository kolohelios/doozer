package judgment

panelPlan: {
	version:                 "source-centric-specialists-v1"
	referenceStatus:         "provisional-authored-development-controls-not-human-reviewed-gold"
	maxBudgetUSD:            5
	maxCalls:                40
	retries:                 0
	maxRequestBytes:         65536
	maxResponseBytes:        1048576
	transportTimeoutSeconds: 120
	orderSeed:               "source-panel-v1"
	roles: {
		interpreter: {model: "openai/gpt-4.1", provider: "openai", promptPrice: "3", completionPrice: "9"}
		verifier: {model: "google/gemini-2.5-pro", provider: "google-ai-studio", promptPrice: "2", completionPrice: "12"}
		auditor: {model: "openai/o3", provider: "openai", promptPrice: "3", completionPrice: "9"}
		audit_control: {model: "openai/o3", provider: "openai", promptPrice: "3", completionPrice: "9"}
		baseline: #JevRole
	}
	extractionInstructions: "Extract source-centric typed assertions and acts, NOT an answer or hypothesis verdict. Only the original paragraphs are evidence. The binding vocabulary, scalar domains, allowed bindings, and source authority identifiers are declared controlled metadata, not semantic truth. Produce one ledger entry for EVERY paragraph span, with zero or more atoms. Preserve multiple facts/acts in a paragraph separately. world eq/neq means an asserted value or explicit exclusion of that exact value, not whether a statement is warranted. epistemic unknown has no world value: lack of local knowledge is not a denied world fact. A question is not an assertion. Distinguish withdrawal of an ASSURANCE about permission from revocation of PERMISSION itself; grant/revoke are normative acts, not observations of physical access. withdraw-assurance, revoke-permission, and supersedes name the prior source in target; bind only the affected property, not every fact in that source. grant-permission has no prior target. Directive, question, and other atoms have no world value. Unknown effective dates must not borrow a statement timestamp. For concrete world values use the exact canonical literal appearing in the cited paragraph, including ISO dates. All fields are required; use null where inapplicable. Unrelated context can have an empty atom list. Your output is an untrusted interpretation, not new evidence or an authorization to update knowledge."
	auditInstructions:      "Adversarially audit two proposed source interpretations. Their origins and independence are not evidence; identical wording may be correlated. Agreement is NOT proof: actively look for shared errors, omitted material atoms, wrong modal level, polarity/value binding errors, questions or directives turned into facts, and assurance withdrawal confused with permission revocation. Inspect original sources rather than vote or select the more confident model. Classify each role's fidelity for EVERY paragraph span as faithful, material-error, unclear, or unavailable. A material-error label requires an issue affecting that role and citing that same paragraph; an absent proposal must be unavailable. A faithful label cannot have a material issue affecting that role; put general caveats in limitations. Cite original span IDs for every issue; preserve uncertainty about fidelity. Mechanical checks only validate necessary constraints, not entailment. Do not propose replacement facts or repair the ledgers. There are no evaluation questions or reference labels in this task."
	baselineInstructions:   "Evaluate each neutral scalar hypothesis using only original sources and declared scope/authority metadata. Distinguish world facts, local lack of knowledge, questions, directives, withdrawal of assurance, revocation of actual permission, and explicit property-scoped supersession. Do not transfer another environment's behavior. Explicit date exclusion contradicts only the excluded date, not every possible date. Preserve genuinely incompatible current assertions; do not settle by recency or number of sources. A different known scalar value is incompatible under the declared single-value domain. Unknown is not false. No model interpretation is source evidence."
	criteria: {
		supported:     "Current source assertions or applicable normative acts support this exact binding/value without incompatible current evidence. Source-relative, not universal truth."
		opposed:       "Current same-binding source evidence establishes an incompatible fact or revokes this actual permission, without current support. Missing support or assurance withdrawal alone is not incompatible."
		contested:     "Both supporting and incompatible current source evidence exist without an applicable resolution."
		unestablished: "Neither exact support nor an incompatible current fact is established for this binding/value."
	}
	policy: "Eight fresh synthetic packets, five fixed paid stages each: independent interpreter, blind verifier, adversarial auditor, a separate shared-error audit control, and source-only Jev evaluation baseline. Each control uses two identical authored ledgers with one predeclared mechanically admissible semantic mutation, not actual model outputs. Controls are constructed before calls and never repair or replace the real trajectory. No reconciliation or repair round. Code evaluates each ledger independently and renders attributed unverified constraints; panel flags are diagnostic holds, never acceptance or source corroboration. Record role-specific failures, disagreements, false holds, and shared misses with full denominators. No canonical effects."
}

panelLedgerSchema: {
	type: "object", additionalProperties: false, required: ["ledger", "limitations"]
	properties: {
		limitations: {type: "array", items: {type: "string"}}
		ledger: {type: "array", items: {
			type: "object", additionalProperties: false, required: ["span", "atoms", "rationale"]
			properties: {
				span: {type: "string"}
				rationale: {type: "string"}
				atoms: {type: "array", items: {
					type: "object", additionalProperties: false, required: ["kind", "binding", "operator", "value", "target"]
					properties: {
						kind: {type: "string", enum: ["world", "epistemic", "withdraw-assurance", "grant-permission", "revoke-permission", "supersedes", "directive", "question", "other"]}
						binding: {type: "string"}
						operator: {type: "string", enum: ["eq", "neq", "unknown", "none"]}
						value: {type: ["string", "null"], description: "Exact source literal ONLY for world eq/neq. Local unknown, question, directive, or source act uses null, never a borrowed hypothesis value."}
						target: {type: ["string", "null"], description: "Prior source ID ONLY for withdraw-assurance, revoke-permission, or supersedes; null otherwise."}
					}
				}}
			}
		}}
	}
}
panelAuditSchema: {
	type: "object", additionalProperties: false, required: ["checks", "limitations"]
	properties: {
		limitations: {type: "array", items: {type: "string"}}
		checks: {type: "array", items: {
			type: "object", additionalProperties: false, required: ["span", "interpreter", "verifier", "issues", "rationale"]
			properties: {
				span: {type: "string"}
				interpreter: {type: "string", enum: ["faithful", "material-error", "unclear", "unavailable"]}
				verifier: {type: "string", enum: ["faithful", "material-error", "unclear", "unavailable"]}
				rationale: {type: "string"}
				issues: {type: "array", items: {
					type: "object", additionalProperties: false, required: ["affects", "kind", "evidence", "detail"]
					properties: {
						affects: {type: "string", enum: ["interpreter", "verifier", "both"]}
						kind: {type: "string", enum: ["modality", "binding", "value", "omission", "history", "other"]}
						evidence: {type: "array", items: {type: "string"}}
						detail: {type: "string"}
					}
				}}
			}
		}}
	}
}

#PanelSignature: {
	kind:     "world" | "epistemic" | "withdraw-assurance" | "grant-permission" | "revoke-permission" | "supersedes" | "directive" | "question" | "other"
	binding:  string
	operator: "eq" | "neq" | "unknown" | "none"
	value:    string | null
	target:   string | null
}
#PanelWorld: #PanelSignature & {kind: "world", operator: *"eq" | "neq", target: null}
#PanelUnknown: #PanelSignature & {kind: "epistemic", operator: "unknown", value: null, target: null}
#PanelAct: #PanelSignature & {operator: "none", value: null, target: *null | string}
#PanelBinding: {id: string, subject: string, property: "permission" | "location" | "effective-date" | "quiet-mail", scope: string, validTime: string | null, values: [...string]}
#PanelSource: {id: string, authority: string, bindings: [...string], worldBindings?: [...string], sentAt: string, paragraphs: [string, ...string]}
panelCases: [string]: {
	bindings: [#PanelBinding, ...#PanelBinding]
	sources: [#PanelSource, ...#PanelSource]
	reference: [string]: [...#PanelSignature]
	optionalReference?: [string]: [...#PanelSignature]
	controlFault: {span: string, mode: "add-world" | "omit-binding" | "invert-exclusion", binding: string, atom?: #PanelSignature}
	queries: [...{id: string, binding: string, value: string, expected: "supported" | "opposed" | "contested" | "unestablished"}]
}
