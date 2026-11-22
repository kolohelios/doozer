package judgment

// Review notation only: not a production IR or approval of previous labels.
interpretationReview: {
	version:  "interpretation-contract-review-v1"
	status:   "pending-user-review"
	approval: "No example or policy is approved by preparing, validating, or merging this packet. Approval must identify the reviewed content or its hashes."
	boundary: "Synthetic development references, not held-out or independently human-authored gold. Each example is a separate scenario with local source/window IDs, not part of one combined evidence pool or a real workplace. No model calls, canonical effects, or retroactive changes to frozen results."
	policies: [
		{id: "meaning-not-layout", proposal: "Evaluate recoverable material meaning, provenance, and projection behavior, not exact atom sets, field names, or node counts. Equivalent encodings need not force a hold. A claim of equivalence still needs an inspectable preservation witness; agreement alone is not that witness."},
		{id: "uncertainty-owner", proposal: "Distinguish what a source says it has not established, what a bounded processed window does not cover, and what an extractor cannot interpret. Record the holder or basis window and the relevant time. Preserve the actual stance: 'not established in these notes' does not itself say the author personally does not know. None is an opposite world fact or a universal claim that nobody knows."},
		{id: "preservation-path", proposal: "Explicit source qualifications must remain source-linked and recoverable to consumers that need them. A typed condition, linked source act, or reproducible coverage derivation can satisfy this; pertinent projections must expose the material qualification rather than merely archive it. An opaque mixed limitations string that the consumer ignores is not a machine-preservation witness. Mere placement in a limitations field is not itself a semantic error."},
		{id: "act-arguments", proposal: "Distinguish an act's action object, its about-topic, the prior assertion or act it targets, and any world or normative binding it changes. A single physical binding field is acceptable only if its kind-specific meaning is explicit. A question retains its proposition without asserting it; a stored directive is not a newly assigned task."},
		{id: "local-revision", proposal: "Withdrawal targets the specified assurance, not permission or all facts in its source. Revocation of an actual grant is a different normative act under the declared authority. Preserve independent support and unaffected facts; a separate live grant cannot be cancelled merely by withdrawing an assurance."},
		{id: "frame-and-history", proposal: "Bind uncertainty and source coverage to their stated frame. Later evidence may establish a fact without falsifying an earlier source's honest uncertainty. History remains inspectable but need not crowd every answer. Leave only the affected binding unresolved, not all otherwise supported knowledge."},
		{id: "shared-contract", proposal: "Give every role the same definitions, preservation obligations, and permitted equivalences. Blind extractors to peer outputs and evaluation answers, not to the semantic contract. Reference disagreements and critic reports are proposals, not votes or new world evidence."},
	]
}

#ContractText: string & !=""
#ContractAnchor: {channel: "source" | "extractor", id: #ContractText, quote: #ContractText}
#ContractSource: {id: #ContractText, actor: #ContractText, saidAt: #ContractText, text: #ContractText}
#ContractMeaning: {
	id:     #ContractText
	kind:   "assertion" | "source-uncertainty" | "coverage-limit" | "source-qualifier" | "extractor-limit" | "question" | "directive" | "assurance" | "assurance-withdrawal" | "grant" | "revocation" | "derived-state" | "contested"
	origin: "source" | "extractor" | "derived"
	window: #ContractText
	holder: *null | #ContractText
	about: [...#ContractText]
	possibleAbout: *[] | [...#ContractText]
	affects: *[] | [...#ContractText]
	target: *null | #ContractText
	action?: {verb: #ContractText, object: #ContractText, condition: #ContractText}
	content:  #ContractText
	required: *true | bool
	anchors: [#ContractAnchor, ...#ContractAnchor]
}
contractExamples: [string]: {
	title:    #ContractText
	decision: #ContractText
	context:  #ContractText
	bindings: [#ContractText, ...#ContractText]
	sources: [#ContractSource, ...#ContractSource]
	extractorReports: *[] | [...{id: #ContractText, actor: #ContractText, window: #ContractText, text: #ContractText}]
	windows: [string]: [#ContractText, ...#ContractText]
	currentWindow: #ContractText
	meanings: [#ContractMeaning, ...#ContractMeaning]
	representations: [{id: #ContractText, description: #ContractText, retains: [#ContractText, ...#ContractText]}, ...{id: #ContractText, description: #ContractText, retains: [#ContractText, ...#ContractText]}]
	forbidden: [{interpretation: #ContractText, why: #ContractText}, ...{interpretation: #ContractText, why: #ContractText}]
	projection: {current: #ContractText, history: #ContractText}
}
