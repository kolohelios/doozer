package understanding

#ID:   string & =~"^[a-z][a-z0-9-]*$"
#Ref:  string & =~"^[a-z][a-z0-9-]*/[a-z][a-z0-9-]*$"
#Text: string & !=""
#Citation: {source: #Ref, quote: #Text}
#Source: {
	text:     #Text
	kind:     "document" | "conversation" | "code" | "observation"
	anchor:   #Text
	saidAt:   #Text
	replyTo?: #ID
}
#Case: {
	synthetic: true
	question:  #Text
	sources: [#ID]: #Source
	let refs = or([for key, _ in sources {key}])
	for key, _ in sources {sources: (key): {replyTo?: refs}}
	checks: [{id: #ID, requirement: #Text, evidence: [refs, ...refs]}, ...{
		id: #ID, requirement: #Text, evidence: [refs, ...refs]
	}]
}
#Links: {
	links!: [...{
		from:      #Ref
		to:        #Ref
		kind:      "related" | "qualifies" | "contradicts" | "depends-on"
		fromQuote: #Text
		toQuote:   #Text
		reason:    #Text
	}]
}
#Understanding: {
	summary: #Text
	claims!: [...{
		text:        #Text
		scope:       #Text
		attribution: "expressed" | "observed" | "inferred" | "ambiguous"
		evidence: [#Citation, ...#Citation]
	}]
	directives!: [...{instruction: #Text, scope: #Text, evidence: [#Citation, ...#Citation]}]
	uncertainties!: [...#Text]
}
#Judgment: {
	checks!: [#ID]: {
		result:    "pass" | "fail" | "uncertain"
		rationale: #Text
		// Empty only for an omission or an uncertain assessment.
		answerQuote!: string
		evidence: [#Citation, ...#Citation]
	}
	unsupported!: [...{answerQuote: #Text, reason: #Text}]
}
