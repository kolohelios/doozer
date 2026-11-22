package retrieval

#Metric: {recall: number & >=0 & <=1, complete: int & >=0 & <=6}
observations: {
	dateUTC:              "2026-11-22"
	benchmark:            "budget-matched-v2"
	embeddingModel:       "openai/text-embedding-3-small"
	dimensions:           512
	documents:            1057
	noiseDocuments:       1024
	corpusBytes:          838151
	contextBytes:         2560
	positiveQueries:      6
	negativeQueries:      1
	embeddingCalls:       34
	embeddingInputTokens: 125661
	reportedCostUSD:      0.00251322
	networkWallSeconds:   19.845
	inputFingerprint:     "e61f1fef267efbd3c14463eb0c65080fd28fcdf0761714a39cb1ca4ac9960a8a"
	contextFingerprint:   "913343288de0dce21e50e543b276352adb29a17803c6faae007fc46c4018ffa6"
	// Plain baselines greedily fill the byte budget from up to 100 candidates.
	// Expanded arms take four seeds and traverse up to three explicit-link hops.
	results: {
		lexical: #Metric & {recall: 0.27777777777777773, complete: 0}
		"lexical+raw-links": #Metric & {recall: 0.4583333333333333, complete: 2}
		"lexical+knowledge-links": #Metric & {recall: 0.6666666666666666, complete: 4}
		vector: #Metric & {recall: 0.6527777777777778, complete: 1}
		"vector+raw-links": #Metric & {recall: 0.7916666666666666, complete: 3}
		"vector+knowledge-links": #Metric & {recall: 1, complete: 6}
		hybrid: #Metric & {recall: 0.3611111111111111, complete: 0}
		"hybrid+raw-links": #Metric & {recall: 0.4583333333333333, complete: 2}
		"hybrid+knowledge-links": #Metric & {recall: 0.6666666666666666, complete: 4}
	}
	budgetSweep: {
		"512": {vectorRecall: 0.5277777777777778, vectorKnowledgeRecall: 0.611111111111111, vectorKnowledgeComplete: 1}
		"1024": {vectorRecall: 0.611111111111111, vectorKnowledgeRecall: 0.9583333333333334, vectorKnowledgeComplete: 5}
		"2560": {vectorRecall: 0.6527777777777778, vectorKnowledgeRecall: 1, vectorKnowledgeComplete: 6}
		"4096": {vectorRecall: 0.6527777777777778, vectorKnowledgeRecall: 1, vectorKnowledgeComplete: 6}
	}
	failures: {
		"automatic-workaround": {vectorMissing: ["retry-safety/no"], vectorKnowledgeMissing: []}
		"human-approval": {
			vectorMissing: ["code-review/no"]
			hybridKnowledgeMissing: ["code-review/agreement", "code-review/no", "code-review/policy", "code-review/tool"]
			hybridKnowledgeBoundaryEmpty: true
		}
	}
	limitations: [
		"Six familiar positive queries and heavily templated synthetic distractors, not a general retrieval benchmark.",
		"Knowledge links are supplied from the EDD, not discovered by this retriever; raw-links ablation uses only source reply and derivation metadata.",
		"Required-source recall is an evaluator-side oracle. Empty known-link boundaries do not prove global completeness.",
		"No downstream answers or semantic transformations were generated or evaluated.",
		"All budget sweeps reused one paid embedding cache; no additional network calls.",
	]
}
