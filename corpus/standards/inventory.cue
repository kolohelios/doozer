package standards

#ExternalStandardArtifact: {
	id:         string
	kind:       "published-rfc" | "internet-draft"
	url:        string & =~"^https://"
	headerDate: string
	bytes:      int & >0
	sha256:     string & =~"^[a-f0-9]{64}$"
}

// Public metadata only. No third-party document text, authors, or discussion bodies.
publicStandardsPilot: {
	id:          "http-problem-details-development-v1"
	status:      "external-inventory-with-one-curated-development-arc"
	inspectedOn: "2026-11-24"
	documents: [...#ExternalStandardArtifact] & [
		{id: "rfc7807", kind: "published-rfc", url: "https://www.rfc-editor.org/rfc/rfc7807.txt", headerDate: "March 2016", bytes: 31210, sha256: "c6ee12b7109d42ed3e68659da5f67397bd573226d86492fecf7d954f5f6ca03e"},
		{id: "draft-00", kind: "internet-draft", url: "https://www.ietf.org/archive/id/draft-ietf-httpapi-rfc7807bis-00.txt", headerDate: "14 April 2021", bytes: 31553, sha256: "36ab5bc8b9ef60abf853785da8a90cb35e1fe6d1ae194ecdabafecba3ee6728f"},
		{id: "draft-01", kind: "internet-draft", url: "https://www.ietf.org/archive/id/draft-ietf-httpapi-rfc7807bis-01.txt", headerDate: "13 October 2021", bytes: 37254, sha256: "60c0c1d48d4efaba0ecae339e06912dc03d0cbee1de55c447263714ee31764bf"},
		{id: "draft-02", kind: "internet-draft", url: "https://www.ietf.org/archive/id/draft-ietf-httpapi-rfc7807bis-02.txt", headerDate: "16 April 2022", bytes: 37233, sha256: "f1ee6cd562536dda6d40ce44a2ff4930ce8f712abb3a14e1a38fa91dc3372629"},
		{id: "draft-03", kind: "internet-draft", url: "https://www.ietf.org/archive/id/draft-ietf-httpapi-rfc7807bis-03.txt", headerDate: "25 May 2022", bytes: 40459, sha256: "c85bd6175e082674647d17d5fda81bef4e6b24c20641e204e9f5410fdc212480"},
		{id: "draft-04", kind: "internet-draft", url: "https://www.ietf.org/archive/id/draft-ietf-httpapi-rfc7807bis-04.txt", headerDate: "5 September 2022", bytes: 41103, sha256: "4492821a5573cb78104e761a2cdf8ad66a49389bc0a7a4b9cad83e734b1d08cc"},
		{id: "draft-05", kind: "internet-draft", url: "https://www.ietf.org/archive/id/draft-ietf-httpapi-rfc7807bis-05.txt", headerDate: "26 January 2023", bytes: 38933, sha256: "d577b93663c95aa1031d4d82a9e04906cf40927d6ab03ddb342850ad34e10d3d"},
		{id: "draft-06", kind: "internet-draft", url: "https://www.ietf.org/archive/id/draft-ietf-httpapi-rfc7807bis-06.txt", headerDate: "1 March 2023", bytes: 38658, sha256: "57fee171f84723ae67144711f3e80242299065a33490468b994e27b197945800"},
		{id: "draft-07", kind: "internet-draft", url: "https://www.ietf.org/archive/id/draft-ietf-httpapi-rfc7807bis-07.txt", headerDate: "23 April 2023", bytes: 38334, sha256: "d9a0d0951b083657bd9ea127a4e59fb35e33f782593e6dc35dc9a3cdfd5f84c7"},
		{id: "rfc9457", kind: "published-rfc", url: "https://www.rfc-editor.org/rfc/rfc9457.txt", headerDate: "July 2023", bytes: 34106, sha256: "f2b3db92fb0bf3489cb3841a0da0c0d88dff40797b64d40b6123085183886c7b"},
	]
	discussionDiscovery: {
		status:      "http-field-excerpts-captured-other-arcs-locators-only"
		repository:  "https://github.com/ietf-wg-httpapi/rfc7807bis"
		nextArc:     "proposed-http-field"
		mailingList: "https://mailarchive.ietf.org/arch/browse/httpapi/"
		arcs: [
			{id: "relative-type-uris", issues: [14, 64], pulls: [20]},
			{id: "invalid-object-processing", issues: [19], pulls: [23]},
			{id: "proposed-http-field", issues: [35, 67], pulls: [39]},
		]
		cautions: [
			"Issue/PR closure is not adoption, consensus, or proof of causal influence on a draft.",
			"Current issue/comment bodies can include later edits. Creation time alone does not establish historical visibility; preserve edit/capture times and mark unavailable historical bodies.",
			"The HTTP-field arc has frozen technical excerpts and conditional cutoff previews in http-field.cue. Other arcs remain locators only; no model result or blanket meaning/rights approval follows.",
		]
	}
	licensing: {
		status:           "http-field-scoped-excerpt-review-other-reuse-pending"
		repositoryNotice: "https://github.com/ietf-wg-httpapi/rfc7807bis/blob/main/CONTRIBUTING.md"
		noticeSHA256:     "34eacc032d37437ca918d97ce1afafc620108c4659ed9903fcfe261dfef2f83c"
		trustTerms:       "https://trustee.ietf.org/license-info"
		boundary:         "The HTTP-field capture has a scoped unmodified-excerpt reuse review under TLP 5.0 section 3.c.iii, with original notices/public attribution in http-field/NOTICE.md. Other artifact reuse and any model transmission need separate review. These materials do not inherit Doozer's MIT OR Apache-2.0 license."
	}
	evaluation: {
		status:            "not-run-no-approved-rubric"
		plannedModelCalls: 0
		budgetUSD:         0
		boundary:          "Development selection, not held-out evidence. Publication is later evidence with release-specific normative scope, not a truth oracle. Document obsolescence does not make every earlier assertion false; absence of a proposal from a release is not a universal prohibition. Preserve effective scope, uncertainty, unresolved feedback, and history."
	}
}
