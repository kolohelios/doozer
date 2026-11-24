package workbench

revisionUpdate: {
	oldText:  "Lantern Dispatch Guide, revision 1. Dispatchers may put a blue marker on the board to request an optional second inventory count. Markers do not change the dispatch deadline."
	newText:  "Lantern Dispatch Guide, revision 2. This edition supersedes revision 1. Dispatchers record completed inventory counts in the shared ledger. Markers do not change the dispatch deadline."
	baseline: "Revision 1 describes an optional blue marker to request a second inventory count; markers do not change the dispatch deadline."
	// Model-facing wire rules, independent of the evaluator's desired meanings.
	wireRules: """
		Patch rules (in addition to the schema):
		- Set baseRevision to current_revision. The keys of accounting must equal the source IDs in incoming, not claim IDs. The other shown sources have already been processed.
		- For add, assertion.id must be one of new_claim_slots. Use each slot at most once. Existing claims already have existing references in current_claims; never use those for add. Use shown existing references or slots declared by your add operations in accounting.claims and retire.replacement. For retire.id use only a shown existing reference. The workbench assigns persistent IDs; do not invent IDs.
		- Every accounting entry names at least one claim that survives the patch. In represented mode, at least one of those claims must cite the incoming source named by that entry. Include any new claim as an add operation; describing it only in rationale does not add it.
		- Use dependent-no-op only for material already accounted for by existing evidence. Its basis must quote already-processed sources (not the incoming source) that the named surviving claims cite. A retirement is not a source accounting disposition.
		- A retire operation needs a nonempty ID of a different surviving claim, either existing or added in this patch. That replacement must retain a citation to every source cited by the retiring claim. If no justified replacement is available, do not retire that claim. An add-only patch is allowed.
		"""
	readerQuestions: [
		"What does revision 2 say about recording completed counts and the deadline?",
		"Where can I recover the revision 1 marker procedure?",
		"Does revision 2 still specify the blue-marker procedure, or does it prohibit markers?",
	]
	boundary: "Synthetic development example. Preserve the revision 1 procedure as history, recognize that revision 2 does not specify it, and do not infer a ban. No prescribed graph layout; no automatic semantic score."
}
