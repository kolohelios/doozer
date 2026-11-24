package standards

// Direct user decision, not a replacement for the unchanged proposal snapshot.
httpFieldApprovals: {
	status:        "user-approved-development-references"
	userText:      "yes, seems pretty good"
	basis:         "Direct reply to the seven-checkpoint plain-language meaning review, not approval inferred from PR merge."
	captureSHA256: "3bf70034dc78e227d076ef234062161a5906b184928c9f1882efd87a71b8ff58"
	scope:         "Only these seven reviewed development meanings, under the supplied evidence and conservative visibility assumptions. Preserve conditional acceptance, attributed reasons, unresolved disagreement, and the distinction between available working drafts and released guidance."
	notApproved: [
		"A prescribed graph layout or target node count",
		"Blanket policy, a particular schema/classifier, or general semantic correctness",
		"Authenticated source identity, authority, or historically complete visibility",
		"The earlier proposer no-ops were warranted",
		"Canonical acceptance or publication",
		"Additional reuse/model-transmission rights or paid execution",
	]
	bindings: {
		"checkpoint-01": "e5ea7f41b5193b8d55486501d3cca7ffd058352ed6d5e1580783c1a032396daf"
		"checkpoint-02": "971b6373ae28e575d9f0b0d0028e8d5a961e6d8faa169dad5cedc9ebba4eef7a"
		"checkpoint-03": "b5e6931530866319eb1d3b5aee4146d395b9c50aa090c7b5d5b1868afe2ea121"
		"checkpoint-04": "2ce7c52bcc2faa66ed811c2d2861f72bdb4f5b6e3809649ac425e8427971acb0"
		"checkpoint-05": "b0eea352bdd5b97fda5ff6f48b4318a96bc5dac2c7a3ace9c78a5d05f678049c"
		"checkpoint-06": "4d5459d9ad7ba26726778a43a35966c34f629ff27efdff5bce0d01c3661352a9"
		"checkpoint-07": "0acd280a369348003e1c6edfaa9a00a89220f965e976ac2a35ff2c577a12e09c"
	}
	reviewedMeanings: {
		"checkpoint-01": "The header is a tentative proposal, with ASCII concerns and weak support—not a released requirement or established consensus."
		"checkpoint-02": "Draft 04 defines it, but that remains distinct from published RFC 7807. Draft inclusion does not erase consumer-discovery objections."
		"checkpoint-03": "Removing the field is being suggested. The supplied discussion does not establish unanimous agreement or implementation."
		"checkpoint-04": "One participant says to remove it, potentially reintroducing it separately. Another expresses conditional acceptance and disappointment, while continuing to propose alternatives—not simple opposition or enthusiastic consensus."
		"checkpoint-05": "Our conservative replay still withholds draft 05 until its 02:05:42 availability event, despite its January 26 header date."
		"checkpoint-06": "Draft 05 no longer defines the field. Preserve the earlier proposal and objections as history; removal does not imply a universal prohibition."
		"checkpoint-07": "RFC 9457 supplies released guidance without that definition. Preserve the distinction between the textual outcome, participants’ expressed reasons, and unresolved technical disagreement."
	}
}
