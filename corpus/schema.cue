package corpus

#ID:   string & =~"^[a-z][a-z0-9-]*$"
#Text: string & !=""

#Source: {
	kind:   "document" | "conversation" | "code" | "observation" | "projection"
	text:   #Text
	anchor: #Text
	// Synthetic event time, not ingestion time or an inferred validity date.
	saidAt:   string & =~"^2026-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$"
	scope:    #Text
	replyTo?: #ID
	derivedFrom?: [#ID, ...#ID]
	// Declared source attribution, separate from assertion stance or authority.
	attributedTo?: {id: #Text, label: #Text, basis: #Text}
	if kind == "projection" {
		derivedFrom: [#ID, ...#ID]
	}
}

#Outcome: {
	id:      #ID
	meaning: #Text
	scope:   #Text
	evidence: [#ID, ...#ID]
}

#Forbidden: {
	id:      #ID
	meaning: #Text
	reason:  #Text
}

#Scenario: {
	title:     #Text
	design:    #Text
	synthetic: true
	tags: [#ID, ...#ID]
	sources: [#ID]: #Source
	let sourceIDs = [for id, _ in sources {id}]
	let sourceRef = or(sourceIDs)
	for id, _ in sources {
		sources: (id): {
			replyTo?: sourceRef
			derivedFrom?: [...sourceRef]
		}
	}
	#Step: {
		id: #ID
		receive: [...sourceRef]
		reconcile: [...sourceRef]
		expect: {
			// Meaning-level requirements, not exact generated prose or graph shape.
			must: [#Outcome & {evidence: [...sourceRef]}, ...#Outcome & {evidence: [...sourceRef]}]
			mustNot: [#Forbidden, ...#Forbidden]
			pending: [...sourceRef]
			// Semantic equivalence to an earlier checkpoint, not byte identity.
			equivalentTo?: #ID
			queries?: [...{
				question: #Text
				state:    "supported" | "insufficient" | "conflicted" | "pending" | "absent"
				meaning:  #Text
				evidence: [...sourceRef]
			}]
		}
	}
	steps: [#Step, ...#Step]
}

#Corpus: {
	version: 1
	scenarios: [#ID]: #Scenario
}

#Corpus
