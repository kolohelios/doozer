package calibration

#ID:   string & =~"^[a-z][a-z0-9-]*$"
#Text: string & !=""
#Evidence: {source: string & !="", quote: #Text}
#AnswerSpan: {pointer: string & =~"^/", quote: #Text}
#Bundle: {
	id: #ID
	allOf: [#Evidence, ...#Evidence]
	note: #Text
}
#Meaning: {
	id:            #ID
	statement:     #Text
	surface:       "answer" | "history"
	applicability: "required" | "if-mentioned" | "retention-only"
	references: [#Evidence, ...#Evidence]
	if applicability == "required" {
		surface: "answer"
		sufficient: [#Bundle, ...#Bundle]
	}
	if applicability == "retention-only" {surface: "history"}
}
#Assessment: {
	label:  "pass" | "fail" | "uncertain" | "not-applicable" | "not-assessed"
	reason: #Text
	spans!: [...#AnswerSpan]
}
#Sample: {
	id:        #ID
	case:      #ID
	arm:       "full" | "vector" | "vector-links"
	target:    "excerpt" | "claim" | "whole-answer"
	criterion: #Text
	expected:  "pass" | "fail" | "uncertain"
	reason:    #Text
	spans!: [...#AnswerSpan]
	evidence: [#Evidence, ...#Evidence]
}

meanings: [#ID]: [#Meaning, ...#Meaning]
reviews: [#ID]: [=~"^(full|vector|vector-links)$"]: [#ID]: #Assessment
samples: [#Sample, ...#Sample]

meta: {
	version:                  "answer-meaning-draft-v1"
	status:                   "pending-user-review"
	split:                    "development"
	semanticScoringEnabled:   false
	originalResultsRewritten: false
	artifact:                 "experiments/understanding/results/first-comparison.json"
	artifactSHA256:           "9936ce23eb3d11c8358dbd31b9d985871dcdacd532e8132043460604d665e477"
	// These are unblinded draft annotations, not independent human gold labels.
	annotationScope: "Draft inspection of nine saved answers; requires user adjudication before judge evaluation."
}
