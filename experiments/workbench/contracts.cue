package workbench

#ID:   string & =~"^[a-z][a-z0-9-]*$"
#Text: string & !=""
#Citation: {
	source: #ID
	quote:  #Text
}
#SourceExcerpts: [{
	startByte: int & >=0
	endByte:   int & >0
	text:      #Text
	sha256:    string & =~"^[a-f0-9]{64}$"
}, ...{
	startByte: int & >=0
	endByte:   int & >0
	text:      #Text
	sha256:    string & =~"^[a-f0-9]{64}$"
}]

// Local inbox source record; source IDs identify immutable versions within one workspace.
#InboxSource: {
	kind:     "document" | "conversation" | "code" | "observation" | "projection"
	text:     #Text
	anchor:   #Text
	scope:    #Text
	saidAt?:  #Text
	replyTo?: #ID
	derivedFrom?: [#ID, ...#ID]
	attributedTo?: {id: #Text, label: #Text, basis: #Text}
	excerpts?: #SourceExcerpts
	origin?:   #SourceOrigin
	if kind == "projection" {
		derivedFrom: [#ID, ...#ID]
	}
}
#SourceOrigin: {
	artifact:          #ID
	kind:              #Text
	bodySHA256:        string & =~"^[a-f0-9]{64}$"
	bodyBytes:         int & >0
	captureSHA256:     string & =~"^[a-f0-9]{64}$"
	versionNotBefore:  #Text
	availabilityBasis: #Text
	attribution:       #Text
	thread:            null | #Text
	rights:            #Text
	legalNotice?:      #Text
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

// Canonical source-free workbench patch; no source dispositions are allowed.
#MaintenancePatch: #Patch & {accounting: close({})}

// Prepared proposal before the workbench supplies empty source accounting.
#MaintenanceProposal: {
	baseRevision: int & >=0
	operations: [...#Operation]
	rationale: #Text
}

// Local operator recovery only; this is not a model-proposed patch operation.
// Offline public-standards evidence context; no execution authority or gold labels.
#StandardsPacket: {
	asOf: #Text
	sources: [#ID]: {
		kind:              #Text
		anchor:            #Text
		statementAt:       null | #Text
		versionNotBefore:  #Text
		availabilityBasis: #Text
		attribution:       #Text
		actor: null | {id: #Text, label: #Text, basis: #Text}
		thread: null | #Text
		excerpts: [{startByte: int & >=0, endByte: int & >0, text: #Text, sha256: #Text}, ...{startByte: int & >=0, endByte: int & >0, text: #Text, sha256: #Text}]
		legalNotice?: #Text
	}
	unavailableContext: [...{id: #ID, anchor: #Text, reason: #Text}]
	questions: [...#Text]
	coverage: #Text
}

#Restore: {
	baseRevision:   int & >=0
	targetPosition: int & >=0
	reason:         #Text
}
#Projection: {
	revision:     int & >=0
	handbook:     #Text
	agentContext: #Text
	claims: [...#ID]
}
