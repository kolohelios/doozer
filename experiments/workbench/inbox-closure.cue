package workbench

inboxClosure: {
	sources: {
		note: #InboxSource & {
			kind:   "conversation"
			anchor: "fixture://greenhouse/closing-note"
			scope:  "east greenhouse evening closure"
			text:   "At evening closure of the east greenhouse, latch the vent and leave the circulation fan running. The west greenhouse has separate instructions."
		}
		west: #InboxSource & {
			kind:   "conversation"
			anchor: "fixture://greenhouse/west-note"
			scope:  "west greenhouse evening closure"
			text:   "For evening closure of the west greenhouse, turn the circulation fan off."
		}
	}
	claimRecords: [
		#Assertion & {id: "east-vent", text: "Latch the vent at evening closure.", scope: "east greenhouse evening closure", attribution: "expressed", evidence: [{source: "note", quote: sources.note.text}]},
		#Assertion & {id: "east-fan", text: "Leave the circulation fan running at evening closure.", scope: "east greenhouse evening closure", attribution: "expressed", evidence: [{source: "note", quote: sources.note.text}]},
		#Assertion & {id: "west-fan", text: "Turn the circulation fan off at evening closure.", scope: "west greenhouse evening closure", attribution: "expressed", evidence: [{source: "west", quote: sources.west.text}]},
	]
	seed: #Patch & {
		baseRevision: 0
		operations: [for claim in claimRecords {{op: "add", assertion: claim}}]
		accounting: {
			note: {mode: "represented", claims: ["east-vent", "east-fan"], reason: "Record the vent and fan instructions separately."}
			west: {mode: "represented", claims: ["west-fan"], reason: "Record the distinct west greenhouse instruction."}
		}
		rationale: "Capture the two scoped closure notes."
	}
}
