package standards

#CapturedExcerpt: {
	startByte: int & >=0
	endByte:   int & >0
	text:      string & !=""
	sha256:    string & =~"^[a-f0-9]{64}$"
}
#CapturedSource: {
	id:         string
	kind:       "published-rfc" | "internet-draft" | "github-comment" | "github-issue-body" | "github-review" | "github-inline-comment" | "editor-commit"
	anchor:     string & =~"^https://"
	bodyBytes:  int & >=0
	bodySHA256: string & =~"^[a-f0-9]{64}$"
	excerpts: [...#CapturedExcerpt]
	legalNotice?: string
	timing: {
		statementAt:      null | string
		versionNotBefore: null | string
		basis:            "datatracker-availability-event" | "github-api-last-update-not-edit-history" | "review-body-edit-history-unknown" | "commit-time-is-not-publication-time"
		evidence:         string
	}
	attribution: string & !=""
	actor: null | {id: string, label: string, basis: string}
	thread:   null | string
	omission: null | string
}
#HTTPFieldCapture: {
	version:   "http-field-capture-v1"
	curatedAt: string
	rights:    "IETF-TLP-5.0-3.c.iii"
	inputCaptures: [string]: {bytes: int & >0, sha256: string & =~"^[a-f0-9]{64}$"}
	sources: [#CapturedSource, ...#CapturedSource]
	coverage: string
}

httpFieldArc: {
	version:           "http-field-replay-offline-v1"
	capture:           "corpus/standards/http-field/capture.json"
	captureSHA256:     "3bf70034dc78e227d076ef234062161a5906b184928c9f1882efd87a71b8ff58"
	notice:            "corpus/standards/http-field/NOTICE.md"
	noticeSHA256:      "5fe2d12e09cc3f73e09f5164f11d015379aade9028c2c885e9a35883c8c5e5c2"
	status:            "curated-development-excerpts-not-model-evaluated"
	plannedModelCalls: 0
	budgetUSD:         0
	maxPreviewBytes:   262144
	checkpoints: [
		{id: "checkpoint-01", asOf: "2022-03-24T12:00:00Z"},
		{id: "checkpoint-02", asOf: "2022-09-07T00:00:00Z"},
		{id: "checkpoint-03", asOf: "2023-01-24T12:00:00Z"},
		{id: "checkpoint-04", asOf: "2023-01-25T12:00:00Z"},
		{id: "checkpoint-05", asOf: "2023-01-27T02:03:00Z"},
		{id: "checkpoint-06", asOf: "2023-02-01T00:00:00Z"},
		{id: "checkpoint-07", asOf: "2023-09-01T00:00:00Z"},
	]
	questions: [
		"What guidance is published, what does the available working draft propose, and what remains only a suggestion?",
		"What changes or reasons are actually expressed, what disagreement or qualifications remain, and what cannot be concluded from this evidence?",
		"Can a reader recover the earlier proposal and objections without treating them as current released requirements?",
	]
	// Evaluator-side development references: never included in public contexts.
	reviewStatus: "pending-human-meaning-review-not-an-oracle"
	references: {
		"checkpoint-01": {meaning: "Tentative header discussion and ASCII concerns, not a released requirement or adopted consensus.", sources: ["g35-c-1031313241", "g35-c-1077031008", "rfc7807"]}
		"checkpoint-02": {meaning: "Draft 04 defines a Problem HTTP field; published RFC 7807 remains distinct. Consumer-discovery objections and requested consensus are not erased by draft inclusion.", sources: ["draft-04", "rfc7807", "g39-c-1078741879", "g35-c-1110512331"]}
		"checkpoint-03": {meaning: "Removal is being suggested, with Unicode/SF and compatibility disagreements. The later remove-field statement must not appear yet; claims of consensus remain attributed expressions, not independently established settlement.", sources: ["draft-04", "g67-c-1399542946", "g67-c-1400139421", "g67-c-1401408724"]}
		"checkpoint-04": {meaning: "One participant says to remove the field and perhaps reintroduce it separately; a later participant is reluctant/disappointed and proposes alternatives. Intention is not yet evidence of an updated published draft or unanimous technical agreement.", sources: ["g67-c-1402805495", "g67-c-1403213007", "draft-04"]}
		"checkpoint-05": {meaning: "Draft 05's header date is already in the past, but its availability event is still later than this cutoff. Do not leak its bytes or infer a push time from the later-captured removal commit. Latest available draft remains 04.", sources: ["draft-04", "g67-c-1402805495"]}
		"checkpoint-06": {meaning: "Available draft 05 no longer defines the field; published RFC 7807 remains a distinct release scope. Prior proposal and objections survive as history. No universal prohibition or blanket rejection of SF follows.", sources: ["draft-05", "rfc7807", "g67-c-1402805495", "g67-c-1403213007"]}
		"checkpoint-07": {meaning: "RFC 9457 supplies released guidance without the draft field definition; earlier drafts remain historical. Retain the distinction between textual change, attributed reasons, unresolved technical objections, and any general claim about headers/SF.", sources: ["rfc9457", "draft-04", "draft-05", "g67-c-1402805495", "g67-c-1403213007"]}
	}
}
