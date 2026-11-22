package workbench

#ID:   string & =~"^[a-z][a-z0-9-]*$"
#Text: string & !=""
#Citation: {
	source: #ID
	quote:  #Text
}
#Assertion: {
	id:          #ID
	text:        #Text
	scope:       #Text
	attribution: "expressed" | "observed" | "inferred" | "ambiguous"
	evidence: [#Citation, ...#Citation]
}
#Route: {
	action: "analyze" | "no-op" | "retain-ambiguity"
}
#Analysis: {
	assertions: [#Assertion, ...#Assertion]
}
#Retrieval: {
	method:   "lexical-and-links"
	revision: int & >=0
	candidates: [...#ID]
	// Small-corpus preservation envelope; retrieval cannot hide active claims.
	protected: [...#Assertion]
}
#Operation: {
	op: "add" | "retire"
	if op == "add" {
		assertion: #Assertion
	}
	if op == "retire" {
		id:          #ID
		replacement: #ID
		reason:      #Text
	}
}
#Disposition: {
	mode: "represented" | "dependent-no-op"
	claims: [#ID, ...#ID]
	reason: #Text
	if mode == "dependent-no-op" {
		basis: [#Citation, ...#Citation]
	}
}
#Patch: {
	accounting!: [#ID]: #Disposition
	baseRevision: int & >=0
	operations: [...#Operation]
	rationale: #Text
}
#Projection: {
	revision:     int & >=0
	handbook:     #Text
	agentContext: #Text
	claims: [...#ID]
}
