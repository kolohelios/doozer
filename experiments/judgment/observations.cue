package judgment

// Derived experimental observations, not independent fixture-world evidence.
observations: {
	artifact:           "experiments/judgment/results/first-multipass.json.gz"
	archiveSHA256:      "a0eed60fca2d0c6c9671edb3e5530172cd2efa0ab83cd51f38791012b2569706"
	uncompressedSHA256: "d929d04c04615f03fd53f2a760623f5376bd4a844cb02ca193604b50758948bb"
	protocolSHA256:     "644bc9fa3c01d519f496028129188030f9be2b08d921c666a6d132a57ec76421"
	sourceCommit:       "cfbc5a1277b607eea5fbe8f52133813a86913828"
	referenceStatus:    "proposed-controlled-fixture-not-human-gold"
	packets:            18
	families:           6
	calls:              126
	retries:            0
	reportedCostUSD:    0.2850785
	componentCostsUSD: {direct: 0.001014594, atoms: 0.001524894, analyst: 0.081914, skeptic: 0.195909, recheck: 0.002686824, order: 0.001014594, repeat: 0.001014594}
	matchesProposedWholeReferences: {direct: 18, atomsProxy: 17, analyst: 18, skeptic: 12, recheck: 18, order: 18, repeat: 18}
	wholeVerdictChangesAfterAudit: 0
	completeValidTrajectories:     12
	controls: {sourceOrderStable: 16, sourceOrderNoOp: 2, identicalInputVerdictStable: 18}
	skepticRefusals: {
		count:              6
		provider:           "Anthropic"
		finishReason:       "content_filter"
		nativeFinishReason: "refusal"
		outputTokensEach:   0
		reportedCostUSD:    0.042681
		packets: ["firmware-coverage/v3", "visitor-exception/v3", "firmware-coverage/v1", "epistemic-scope/v2", "visitor-exception/v1", "firmware-coverage/v2"]
		note: "No semantic audit was returned for these benign packets. Cause is not established. No fallback or replacement was attempted; all charged input costs remain included."
	}
	claimTyping: {
		packet:              "epistemic-scope/v1"
		claim:               "c1"
		text:                "Its location and effective date are not established here."
		initialRelation:     "not-established"
		initialConfidence:   0.42
		recheckedRelation:   "meta"
		recheckedConfidence: 0.4
		note:                "The blind analyst and valid skeptic treated this as a legitimate epistemic limitation. Re-adjudication changed the type after those arguments, while the whole verdict was already pass. One trajectory does not prove causal improvement or eliminate ambiguity."
	}
	unknownVersusContradictedAudit: {
		packet:                       "independent-evidence/v3"
		claim:                        "c0"
		sourceSpan:                   "d2-s1"
		sourceQuote:                  "It may be a retelling."
		analystRelation:              "contradicted"
		skepticRelation:              "contradicted"
		recheckedRelation:            "contradicted"
		analystRationaleQuote:        "There is no evidence that d2 describes a separate, independent drill."
		declaredOriginGroups:         1
		sourcesWithoutDeclaredOrigin: 1
		echoEdges:                    0
		finding:                      "Rejecting the unsupported independence assertion is justified, but absent provenance is not proof that both notes share an origin. The packet establishes one first-hand run and an unknown second origin, not that no second run happened. Relation taxonomy must distinguish an epistemically unjustified assertion from a world-level contradiction. This qualitative concern is not separately adjudicated unit gold."
	}
	probabilityDiagnostics: {
		artifact:                     "experiments/judgment/results/probability-diagnostics.json"
		artifactSHA256:               "de4fbe44a5655122d0b7861376c1cc49c9a4efa72162f07f03df6689e4d26268"
		implementationSHA256:         "1d7b7a67a99203eea216564edf805f4e50e16d4f8fff312be4e8c52e772467cd"
		status:                       "post-hoc-exploratory-not-an-acceptance-policy"
		maximumIdenticalRepeatJSBits: 0.006299170656442216
		maximumSourceOrderJSBits:     0.015215133032178772
		positiveVsContradictorySourceJSBits: {"automatic-recovery": 0.9021547608988222, "effective-time": 0.8336791289905015, "epistemic-scope": 0.5721573867464173, "firmware-coverage": 0.7090555628019524, "independent-evidence": 0.959531296097706, "visitor-exception": 0.959531296097706}
		epistemicClaimEntropyBits: {before: 1.2920717416914025, after: 1.4637068202000796}
		note: "Whole verdicts stayed stable under order/repeat controls, but distributions were not identical. Entropy increased on the retyped epistemic claim. These are output-distribution diagnostics, not calibrated truth probabilities, independent evidence, or fitted routing thresholds."
	}
	comparisonClarification: "The raw summary's analyst_skeptic_disagreements list includes invalid-status differences. Among valid reports there were 12 agreements and zero differing whole verdicts; six skeptic reports were unavailable. Unavailability is not a semantic disagreement."
	preparationNote:         "The first offline preview encoded the default budget as integer 5, while the explicit live CLI encoded 5.0; scientific inputs and effective limits were identical but digests differed. The published live protocol was frozen before calls. Future preparation normalizes budget numbers; the archived run was not rewritten."
	interpretation:          "Jev responds to source changes rather than candidate wording alone on these controlled packets. Deeper auditing exposed a claim-type error and provider unavailability, but improved no whole verdict because the direct baseline already matched all provisional references. Repeated conditions are not independent samples and no population accuracy claim follows."
	next:                    "Exercise genuine unresolved source conflicts, warranted uncertain answers, longer distracting threads, and bounded source expansion. Make claim kinds and epistemic relations explicit before compiling knowledge updates. Treat model reports as proposals, not witnesses; never loop until consensus or allow a final verdict to hide missing audits."
}
