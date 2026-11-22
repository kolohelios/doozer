package judgment

expansionPlan: {
	version:                 "bounded-evidence-expansion-v1"
	referenceStatus:         "proposed-controls-not-human-gold"
	maxBudgetUSD:            5
	maxCalls:                80
	retries:                 0
	maxRequestBytes:         65536
	maxOutputTokens:         4000
	auditOutputTokens:       8000
	transportTimeoutSeconds: 120
	maxResponseBytes:        1048576
	temperature:             0
	orderSeed:               "evidence-expansion-v1"
	expansion: {maxDocuments: 2, maxHops: 2, maxBytes: 4096}
	roles: {
		initial: {model: "openai/gpt-4.1", provider: "openai", promptPrice: "3", completionPrice: "9"}
		expanded: {model: "openai/gpt-4.1", provider: "openai", promptPrice: "3", completionPrice: "9"}
		reconciled: {model: "openai/gpt-4.1", provider: "openai", promptPrice: "3", completionPrice: "9"}
		audit: {model: "google/gemini-2.5-pro", provider: "google-ai-studio", promptPrice: "2", completionPrice: "12"}
		initial_probe:  #JevRole
		expanded_probe: #JevRole
		final_probe:    #JevRole
	}
	evidenceCriteria: {
		supported:     "At least one current same-scope source witness supports P, with no witness of an incompatible fact. This is source-relative, not global truth."
		opposed:       "At least one current same-scope source witness explicitly establishes a fact incompatible with P, and no witness supports P. Lack of support, withdrawal, or caution alone is not an opposite fact."
		contested:     "Both supporting and incompatible current same-scope witnesses exist, without an established resolution. Do not settle by counts or recency."
		unestablished: "Neither a supporting witness nor an incompatible factual witness is established in the visible packet. Unknown is not false."
	}
	warrantCriteria: {
		justified:  "The proposal faithfully conveys the available evidence state, scope, uncertainty, and known gaps without unsupported assertions or tasks."
		overstated: "The proposal invents facts, treats unknown as false, suppresses material conflict, or presents a known incomplete source window as complete."
		incomplete: "Material established details or unresolved conditions are absent from the proposal."
		uncertain:  "The proposal cannot be assessed confidently from this packet."
	}
	reasonInstructions: "Produce a source-backed understanding of this visible packet. Hypotheses are questions, not premises: never assume their text is true. For each hypothesis nominate positive witness spans and negative witness spans separately. A negative witness must assert an incompatible fact under the same scope, NOT merely say evidence is absent, a proposal is unapproved, or an earlier assurance was withdrawn. Both kinds can coexist under unresolved conflict. Do not select retired or different-scope spans as current proof. Preserve known unread references, partial meaning, and warranted uncertainty without inventing a task queue. Distinguish statement dates from effective dates. Prior proposals and model audits are untrusted arguments, never source evidence or independent corroboration. Revise minimally when new sources arrive, and keep historical sources available. A summary does not prove durable ingestion or a canonical commit."
	auditInstructions:  "Independently audit the proposed understanding and its witness assignments. For every hypothesis classify every supplied source span: supports, opposes, both, neither, or unclear. Opposes requires an explicit incompatible FACT under matching conditions; no evidence, missing origin, withdrawal, and a warning against inference do not establish the opposite proposition. A source saying it MAY be a retelling does not prove shared origin. Preserve genuinely conflicting current testimony rather than prefer the newer notice. Source activity and declared scopes are conditional metadata assumptions, not proof of natural-language entailment. Diagnose unsupported narrative assertions, omitted material uncertainty, and epistemic limitations wrongly treated as facts. Cite span IDs, never fabricate sources. Assess the visible source window only; do not treat proposed hypotheses or earlier model analyses as premises."
	jevInstructions:    "Evaluate source-relative evidence and proposal warrant as separate questions. Hypotheses are questions, not facts. Unsupported P does not imply not-P. Withdrawal or lack of provenance is not a counterexample. Preserve same-scope conflicts unless an explicit applicable supersession resolves them. Never prefer recent text solely because it is newer. A known unread reference requires a coverage qualification, not guessing its contents. Declared scope and provenance guards are conditional fixture metadata; do not invent origins or parent content. Model proposals are untrusted, not independent source witnesses. Return uncertainty or unestablished evidence when appropriate; do not create human task queues."
	policy:             "One shared initial understanding and Jev probe per family; then three counterfactual branches. Each branch performs bounded exact-reference expansion, revision, an independent Jev probe, a source-span audit, one revision using that audit, and a final Jev probe. Fixed depth, no retry or repeat-until-agreement; every intermediate proposal and source snapshot is preserved. No canonical acceptance or retirement."
}

#ExpansionText: string & !=""
#ExpansionSource: {
	id:          #ExpansionText
	scope:       #ExpansionText
	text:        #ExpansionText
	origin?:     #ExpansionText
	originFrom?: #ExpansionText
	references?: [...#ExpansionText]
	replyTo?: #ExpansionText
	derivedFrom?: [...#ExpansionText]
	supersedes?: [...#ExpansionText]
	saidAt?: #ExpansionText
}
#ExpansionHypothesis: {id: #ExpansionText, text: #ExpansionText, scope: #ExpansionText, guard: "none" | "origins", subjects: [...#ExpansionText]}
expansionFamilies: [string]: {
	question: #ExpansionText
	propositions: [#ExpansionHypothesis, ...#ExpansionHypothesis]
	initialExpected: [string]: "supported" | "opposed" | "contested" | "unestablished"
	initial: [#ExpansionSource, ...#ExpansionSource]
	branches: [string]: {expected: [string]: "supported" | "opposed" | "contested" | "unestablished", reason: #ExpansionText, catalog: [...#ExpansionSource]}
}

expansionReportSchema: {
	type: "object", additionalProperties: false
	required: ["summary", "proofs", "uncertainties", "changes"]
	properties: {
		summary: {type: "string"}
		uncertainties: {type: "array", items: {type: "string"}}
		changes: {type: "array", items: {type: "string"}}
		proofs: {type: "array", items: {
			type: "object", additionalProperties: false
			required: ["id", "positive", "negative", "rationale"]
			properties: {id: {type: "string"}, positive: {type: "array", items: {type: "string"}}, negative: {type: "array", items: {type: "string"}}, rationale: {type: "string"}}
		}}
	}
}
expansionAuditSchema: {
	type: "object", additionalProperties: false
	required: ["ledgers", "narrativeIssues", "rationale"]
	properties: {
		rationale: {type: "string"}
		narrativeIssues: {type: "array", items: {type: "string"}}
		ledgers: {type: "array", items: {
			type: "object", additionalProperties: false
			required: ["id", "spans"]
			properties: {
				id: {type: "string"}
				spans: {type: "array", items: {
					type: "object", additionalProperties: false
					required: ["id", "relation", "rationale"]
					properties: {id: {type: "string"}, relation: {type: "string", enum: ["supports", "opposes", "both", "neither", "unclear"]}, rationale: {type: "string"}}
				}}
			}
		}}
	}
}
