package judgment

contractExamples: {
	"01-source-uncertainty": {
		title:    "A source's uncertainty is not an opposite date fact"
		decision: "Preserve the speaker's stated uncertainty, exact date exclusion, and known venue as distinct meanings."
		context:  "All dates and names are synthetic. This is a one-day drill; statement time and effective date are different variables."
		bindings: ["date", "venue"]
		sources: [{id: "s1", actor: "coordinator", saidAt: "2030-02-11", text: "The drill venue is Pine annex. I have not established its effective date in these notes. Its effective date is not 2030-02-11, the date of this message."}]
		windows: w1: ["s1"]
		currentWindow: "w1"
		meanings: [
			{id: "venue", kind: "assertion", origin: "source", window: "w1", about: ["venue"], content: "The source reports Pine annex as the drill venue.", anchors: [{channel: "source", id: "s1", quote: "The drill venue is Pine annex."}]},
			{id: "not-message-date", kind: "assertion", origin: "source", window: "w1", about: ["date"], content: "The source excludes effective date 2030-02-11, not every other date.", anchors: [{channel: "source", id: "s1", quote: "Its effective date is not 2030-02-11, the date of this message."}]},
			{id: "speaker-limit", kind: "source-uncertainty", origin: "source", holder: "coordinator", window: "w1", about: ["date"], content: "The coordinator says they have not established the date in these notes; this is not universal ignorance.", anchors: [{channel: "source", id: "s1", quote: "I have not established its effective date in these notes."}]},
		]
		representations: [
			{id: "separate", description: "Separate date constraint, venue assertion, and source-uncertainty record with holder and window.", retains: ["venue", "not-message-date", "speaker-limit"]},
			{id: "qualified", description: "One qualified date record carries the exclusion and source's scoped epistemic statement, alongside the venue. The consumer can recover both meanings without matching a particular node count.", retains: ["venue", "not-message-date", "speaker-limit"]},
		]
		forbidden: [
			{interpretation: "The drill does not take place on 2030-02-14.", why: "Excluding 2030-02-11 and lacking an established date do not exclude 2030-02-14."},
			{interpretation: "Nobody knows the date, and the venue is unknown.", why: "The source limits its own establishment in these notes and explicitly gives a venue."},
		]
		projection: {current: "Venue: Pine annex. The coordinator has not established the date in w1; 2030-02-11 is explicitly excluded.", history: "Retain the source's statement time separately from any effective date."}
	}
	"02-window-coverage": {
		title:    "A coverage boundary may be represented without a redundant unknown atom"
		decision: "Require recoverable scoped coverage, not a particular epistemic-node layout."
		context:  "w1 is exactly the supplied processed snapshot, not the complete universe of possible evidence. The setting is scalar within each environment."
		bindings: ["staging-setting", "production-setting"]
		sources: [{id: "s1", actor: "operator", saidAt: "2030-02-12", text: "Quiet-mail is enabled in staging-east. These notes cover staging-east only and provide no finding about production-east. Do not transfer this observation to production."}]
		windows: w1: ["s1"]
		currentWindow: "w1"
		meanings: [
			{id: "staging", kind: "assertion", origin: "source", window: "w1", about: ["staging-setting"], content: "The observation reports quiet-mail enabled in staging-east only.", anchors: [{channel: "source", id: "s1", quote: "Quiet-mail is enabled in staging-east."}]},
			{id: "coverage", kind: "coverage-limit", origin: "source", window: "w1", about: ["production-setting"], content: "This note supplies no production-east finding. This is about coverage of w1, not the operator's total knowledge or universal absence of evidence.", anchors: [{channel: "source", id: "s1", quote: "These notes cover staging-east only and provide no finding about production-east."}]},
		]
		representations: [
			{id: "explicit", description: "A source-linked coverage-limit record identifies w1 and production-east separately from the staging assertion.", retains: ["staging", "coverage"]},
			{id: "derived", description: "Typed source scopes and the bounded-window registry retain the explicit coverage anchor; a reproducible projection derives 'no production finding in w1'. No duplicate unknown atom is required. The qualifier must actually reach the relevant consumer.", retains: ["staging", "coverage"]},
		]
		forbidden: [
			{interpretation: "Quiet-mail is disabled in production-east.", why: "Lack of a production finding is not an observation of either state."},
			{interpretation: "No production evidence exists anywhere, or the operator does not know production behavior.", why: "A processed-window coverage statement does not establish either global absence or personal ignorance."},
			{interpretation: "The qualifier appears only in an opaque mixed limitations string ignored by the projection, so the machine-facing representation is complete.", why: "Field placement is not decisive, but an inspectable recovery/projection path for material coverage is required."},
		]
		projection: {current: "Staging-east: enabled. Production-east: not established by w1; do not transfer the staging result.", history: "Keep the coverage statement attached to its source/window, not a permanent global unknown flag."}
	}
	"03-extractor-limitation": {
		title:    "An extractor's unresolved reference is not a source's professed ignorance"
		decision: "Preserve the ambiguous qualifier and reported values; attribute the interpretation limitation to the extractor."
		context:  "The extractor report below is hypothetical review input, not an actual model call or additional world evidence."
		bindings: ["drill-date", "briefing-date", "venue"]
		sources: [{id: "s1", actor: "organizer", saidAt: "2030-02-12", text: "The drill is dated 2030-02-14 and the briefing 2030-02-15. Exactly one of those dates remains provisional; I have not identified which in this note. The venue for both is Aspen room."}]
		extractorReports: [{id: "x1", actor: "extractor", window: "w1", text: "I cannot bind the provisional qualifier to a unique date from this packet."}]
		windows: w1: ["s1"]
		currentWindow: "w1"
		meanings: [
			{id: "reported-dates", kind: "assertion", origin: "source", window: "w1", about: ["drill-date", "briefing-date"], content: "The source reports drill date 2030-02-14 and briefing date 2030-02-15, subject to the unresolved provisional qualifier.", anchors: [{channel: "source", id: "s1", quote: "The drill is dated 2030-02-14 and the briefing 2030-02-15."}]},
			{id: "qualifier", kind: "source-qualifier", origin: "source", window: "w1", about: [], possibleAbout: ["drill-date", "briefing-date"], content: "One of the two date claims is provisional; the note does not identify which. Do not silently attach the qualifier to both or choose one as settled.", anchors: [{channel: "source", id: "s1", quote: "Exactly one of those dates remains provisional; I have not identified which in this note."}]},
			{id: "interpretation-limit", kind: "extractor-limit", origin: "extractor", holder: "extractor", window: "w1", about: [], possibleAbout: ["drill-date", "briefing-date"], content: "The extractor cannot resolve the qualifier target from w1. This does not say the organizer does not know the dates.", anchors: [{channel: "extractor", id: "x1", quote: "I cannot bind the provisional qualifier to a unique date from this packet."}]},
			{id: "venue", kind: "assertion", origin: "source", window: "w1", about: ["venue"], content: "Both events have venue Aspen room; uncertainty over the date qualifier does not erase this.", anchors: [{channel: "source", id: "s1", quote: "The venue for both is Aspen room."}]},
		]
		representations: [
			{id: "alternatives", description: "Keep a source qualifier with alternative date targets and a separate extractor-origin unresolved-reference report.", retains: ["reported-dates", "qualifier", "interpretation-limit", "venue"]},
			{id: "shared-condition", description: "A shared qualified date group retains the exact reported dates and 'one unidentified date is provisional', with an attributed interpretation-limit annotation. It does not assert that both dates are provisional.", retains: ["reported-dates", "qualifier", "interpretation-limit", "venue"]},
		]
		forbidden: [
			{interpretation: "The organizer says they do not know either date, or both dates are definitely provisional.", why: "The source supplies both dates and leaves the qualifier's referent unidentified; the extractor's limitation is not a source statement of ignorance."},
			{interpretation: "Both dates are confirmed, or all information including the venue must be withheld.", why: "The first drops a material unresolved qualifier; the second discards unaffected supported meaning."},
		]
		projection: {current: "Drill: 2030-02-14; briefing: 2030-02-15. One date is provisional, but w1 does not identify which. Venue for both: Aspen room.", history: "The hypothetical extractor report stays derived interpretation metadata, not another corroborating source."}
	}
	"04-question-and-directive": {
		title:    "An action can be about a date without assigning the date"
		decision: "Separate the question's content, the directive's action object/condition, its topic, and any world effect."
		context:  "Storing the organizer's request does not assign a new task to a person or to Doozer."
		bindings: ["date", "venue"]
		sources: [{id: "s1", actor: "organizer", saidAt: "2030-02-12", text: "The briefing venue is Aspen room. Is the briefing on 2030-02-16? Please check the calendar before making travel plans; that question is not a confirmed schedule."}]
		windows: w1: ["s1"]
		currentWindow: "w1"
		meanings: [
			{id: "venue", kind: "assertion", origin: "source", window: "w1", about: ["venue"], content: "The briefing venue is reported as Aspen room.", anchors: [{channel: "source", id: "s1", quote: "The briefing venue is Aspen room."}]},
			{id: "question", kind: "question", origin: "source", window: "w1", about: ["date"], content: "The proposition 'briefing date = 2030-02-16' is asked, not asserted. Retain which date was asked about.", anchors: [{channel: "source", id: "s1", quote: "Is the briefing on 2030-02-16?"}]},
			{id: "request", kind: "directive", origin: "source", window: "w1", about: ["date"], affects: [], action: {verb: "check", object: "calendar", condition: "before making travel plans"}, content: "The requested action is checking the calendar before travel plans; date is its topic, not an assigned scalar value.", anchors: [{channel: "source", id: "s1", quote: "Please check the calendar before making travel plans"}]},
			{id: "derived-unknown", kind: "derived-state", origin: "derived", window: "w1", about: ["date"], required: false, content: "The effective date is unestablished in w1. This can be derived without a separately stored unknown atom; it is not a claim that the organizer is personally ignorant.", anchors: [{channel: "source", id: "s1", quote: "that question is not a confirmed schedule."}]},
		]
		representations: [
			{id: "separate-arguments", description: "Separate question content and directive action, with about(date) and no world-date effect. Derive the unknown date when projecting w1.", retains: ["venue", "question", "request"]},
			{id: "typed-topic-link", description: "A kind-qualified topic binding on the directive is acceptable if every role and consumer knows it means about(date), not date assignment. An extra derived-unknown annotation is also acceptable, not a reason to force disagreement.", retains: ["venue", "question", "request", "derived-unknown"]},
		]
		forbidden: [
			{interpretation: "The briefing takes place on 2030-02-16, or checking the calendar changes its date to that value.", why: "A question and an action about a date are not assertions or changes of the world date."},
			{interpretation: "Any link from the directive to the date binding is intrinsically a material error.", why: "An explicitly typed about-topic link is legitimate. Ambiguous overloading should be diagnosed as a contract ambiguity, not settled by critic votes."},
		]
		projection: {current: "Venue: Aspen room. 2030-02-16 is mentioned in a question, not confirmed; checking the calendar was requested before travel planning. The date is not confirmed in w1.", history: "A venue-only answer need not repeat the request, but its content and conditions remain source-linked and recoverable."}
	}
	"05-assurance-withdrawal": {
		title:    "Withdrawing the only assurance does not revoke permission"
		decision: "Target the assurance; distinguish loss of current support from a negative permission fact."
		context:  "The supplied snapshot contains no separate grant or independent current permission evidence. The coordinator is the declared authority for these fictional notices. A separate live grant, if present, would not be revoked by assurance withdrawal."
		bindings: ["permission", "venue"]
		sources: [
			{id: "s1", actor: "coordinator", saidAt: "2030-04-10", text: "My assurance is that booked visitors are permitted entry at the Lark session on 2030-04-12. The venue is Hazel room. This is a report of the arrangement, not a new permission grant."},
			{id: "s2", actor: "coordinator", saidAt: "2030-04-11", text: "I withdraw the assurance in s1 pending inspection. I am not revoking permission, and I now make no finding that visitor entry is permitted or forbidden. The venue record is unchanged."},
		]
		windows: {w1: ["s1"], w2: ["s1", "s2"]}
		currentWindow: "w2"
		meanings: [
			{id: "assurance", kind: "assurance", origin: "source", holder: "coordinator", window: "w1", about: ["permission"], content: "The coordinator assured permitted visitor entry for this session; this was not a grant and is no longer a current endorsement after s2.", anchors: [{channel: "source", id: "s1", quote: "My assurance is that booked visitors are permitted entry at the Lark session on 2030-04-12."}]},
			{id: "withdrawal", kind: "assurance-withdrawal", origin: "source", window: "w2", about: ["permission"], affects: [], target: "assurance", content: "s2 withdraws the assurance, not the underlying permission or unrelated facts in s1.", anchors: [{channel: "source", id: "s2", quote: "I withdraw the assurance in s1 pending inspection."}]},
			{id: "current-limit", kind: "source-uncertainty", origin: "source", holder: "coordinator", window: "w2", about: ["permission"], content: "The coordinator now supplies no permitted/forbidden finding. With the only assurance withdrawn, current permission is unestablished in w2.", anchors: [{channel: "source", id: "s2", quote: "I am not revoking permission, and I now make no finding that visitor entry is permitted or forbidden."}]},
			{id: "venue", kind: "assertion", origin: "source", window: "w2", about: ["venue"], content: "Hazel room remains the supported venue in w2; the change targets only the assurance.", anchors: [{channel: "source", id: "s1", quote: "The venue is Hazel room."}, {channel: "source", id: "s2", quote: "The venue record is unchanged."}]},
		]
		representations: [
			{id: "act-target", description: "An assurance act carries the permission proposition; withdrawal targets that act. Keep the current support gap and venue independently.", retains: ["assurance", "withdrawal", "current-limit", "venue"]},
			{id: "endorsement-link", description: "A source-linked proposition with an assurance/endorsement relation can instead lose that current endorsement; the original proposition and venue history remain reachable. Do not flip its world polarity.", retains: ["assurance", "withdrawal", "current-limit", "venue"]},
		]
		forbidden: [
			{interpretation: "Visitor entry is forbidden, or all facts in s1 are retired.", why: "The assurance, not permission or venue, was withdrawn."},
			{interpretation: "Assurance withdrawal always makes permission unknown even if another valid grant remains current.", why: "The unestablished result here depends on the stated lack of other current support, not a universal withdrawal rule."},
		]
		projection: {current: "Venue: Hazel room. Visitor permission is not established by current support in w2; the earlier assurance was withdrawn, not replaced by a prohibition.", history: "The original assurance, its withdrawal, and the unaffected venue stay independently traceable."}
	}
	"06-permission-revocation": {
		title:    "Revoking an actual grant changes the normative permission"
		decision: "Distinguish a permission act from an assurance act and from physical access observations."
		context:  "The coordinator is stipulated to be authorized for the fictional session, with no later restoration. The scope is this session only."
		bindings: ["permission", "venue"]
		sources: [
			{id: "s1", actor: "coordinator", saidAt: "2030-04-10", text: "I grant booked visitors entry permission for the Reed session on 2030-04-12. The venue is Willow room. This grant applies only to that session."},
			{id: "s2", actor: "coordinator", saidAt: "2030-04-11", text: "I revoke the entry permission granted in s1 for the Reed session. This is a permission change, not merely withdrawal of an assurance. It does not change the venue."},
		]
		windows: {w1: ["s1"], w2: ["s1", "s2"]}
		currentWindow: "w2"
		meanings: [
			{id: "grant", kind: "grant", origin: "source", window: "w1", about: ["permission"], affects: ["permission"], content: "An authorized session-scoped grant permits booked visitor entry until its revocation.", anchors: [{channel: "source", id: "s1", quote: "I grant booked visitors entry permission for the Reed session on 2030-04-12."}]},
			{id: "revoke", kind: "revocation", origin: "source", window: "w2", about: ["permission"], affects: ["permission"], target: "grant", content: "The grant is revoked for this session; permission under that grant no longer holds in w2. This is not evidence that a physical door is locked.", anchors: [{channel: "source", id: "s2", quote: "I revoke the entry permission granted in s1 for the Reed session."}]},
			{id: "venue", kind: "assertion", origin: "source", window: "w2", about: ["venue"], content: "Willow room remains the venue in w2.", anchors: [{channel: "source", id: "s1", quote: "The venue is Willow room."}, {channel: "source", id: "s2", quote: "It does not change the venue."}]},
		]
		representations: [
			{id: "act-chain", description: "Keep the grant and revocation as an act chain; derive the current session permission from it under the declared authority.", retains: ["grant", "revoke", "venue"]},
			{id: "qualified-permission", description: "A current permission view can state that the grant is revoked if it links back to the grant/revocation and preserves venue and session scope, rather than replacing history with a bare false flag.", retains: ["grant", "revoke", "venue"]},
		]
		forbidden: [
			{interpretation: "The coordinator merely became uncertain, all visitor access everywhere is forbidden, or the room is physically locked.", why: "An explicit scoped normative revocation establishes none of those alternative meanings."},
		]
		projection: {current: "Booked-visitor permission under this grant is revoked for the Reed session. Venue: Willow room. No physical-door observation is supplied.", history: "Keep the earlier grant as history, not a current conflicting permission alongside the explicit revocation."}
	}
	"07-resolved-uncertainty": {
		title:    "Later evidence resolves a window, not the truth of an earlier honest limitation"
		decision: "Update the affected current binding without leaving permanent fog or erasing uncertainty history."
		context:  "The drill has one effective date. s2 explicitly supplies the previously missing date for the same drill."
		bindings: ["date", "venue"]
		sources: [
			{id: "s1", actor: "coordinator", saidAt: "2030-02-11", text: "The drill venue is Pine annex. I have not established its effective date in these notes. This describes my information as of this note."},
			{id: "s2", actor: "coordinator", saidAt: "2030-02-12", text: "I can now establish the drill's single effective date as 2030-02-14. This supplies the date absent from s1. The venue remains Pine annex."},
		]
		windows: {w1: ["s1"], w2: ["s1", "s2"]}
		currentWindow: "w2"
		meanings: [
			{id: "earlier-limit", kind: "source-uncertainty", origin: "source", holder: "coordinator", window: "w1", about: ["date"], content: "The coordinator had not established the date in w1; this remains a historical statement, not current global ignorance.", anchors: [{channel: "source", id: "s1", quote: "I have not established its effective date in these notes."}]},
			{id: "new-date", kind: "assertion", origin: "source", window: "w2", about: ["date"], content: "s2 establishes the reported effective date 2030-02-14 for the same drill in w2, distinct from the 2030-02-12 statement date.", anchors: [{channel: "source", id: "s2", quote: "I can now establish the drill's single effective date as 2030-02-14."}]},
			{id: "venue", kind: "assertion", origin: "source", window: "w2", about: ["venue"], content: "Pine annex remains the known venue, unaffected by the date update.", anchors: [{channel: "source", id: "s1", quote: "The drill venue is Pine annex."}, {channel: "source", id: "s2", quote: "The venue remains Pine annex."}]},
		]
		representations: [
			{id: "framed-condition", description: "Keep the explicit earlier source condition framed to w1 and derive the established date in w2; no contradiction between those different claims.", retains: ["earlier-limit", "new-date", "venue"]},
			{id: "current-plus-history", description: "A compact current view gives the new date and venue with a traversable source/revision path to the prior uncertainty. The earlier limitation need not be repeated in every current answer.", retains: ["earlier-limit", "new-date", "venue"]},
		]
		forbidden: [
			{interpretation: "The date remains unknown forever, s1 is now false, or the effective date is 2030-02-12.", why: "Later establishment changes current support, not what was established in w1; statement and effective times remain distinct."},
		]
		projection: {current: "As of w2, reported effective date: 2030-02-14. Venue: Pine annex.", history: "A deliberate history lookup recovers the coordinator's uncertainty in w1 and the source that resolved it; no need to crowd every answer with it."}
	}
	"08-local-conflict": {
		title:    "A real date conflict does not make an agreed venue unknown"
		decision: "Preserve both current date assertions without choosing by recency or holding unrelated knowledge."
		context:  "Sources have equal declared authority and refer to the same one-day session. No source establishes supersession or rescheduling."
		bindings: ["date", "venue"]
		sources: [
			{id: "s1", actor: "scheduler-a", saidAt: "2030-03-01", text: "The one-day session is scheduled for 2030-03-11. Its venue is Maple room. This is our current notice."},
			{id: "s2", actor: "scheduler-b", saidAt: "2030-03-02", text: "The same one-day session is scheduled for 2030-03-12. Its venue is Maple room. I have not established that either notice supersedes the other."},
		]
		windows: w1: ["s1", "s2"]
		currentWindow: "w1"
		meanings: [
			{id: "first-date", kind: "assertion", origin: "source", window: "w1", about: ["date"], content: "s1 asserts 2030-03-11 for the session.", anchors: [{channel: "source", id: "s1", quote: "The one-day session is scheduled for 2030-03-11."}]},
			{id: "second-date", kind: "assertion", origin: "source", window: "w1", about: ["date"], content: "s2 asserts 2030-03-12 for that same single-day session.", anchors: [{channel: "source", id: "s2", quote: "The same one-day session is scheduled for 2030-03-12."}]},
			{id: "conflict", kind: "contested", origin: "derived", window: "w1", about: ["date"], content: "These date assertions conflict without a supported resolution. Recency is not a supersession proof.", anchors: [{channel: "source", id: "s1", quote: "2030-03-11"}, {channel: "source", id: "s2", quote: "I have not established that either notice supersedes the other."}]},
			{id: "venue", kind: "assertion", origin: "source", window: "w1", about: ["venue"], content: "Both sources report Maple room. The date dispute does not establish venue uncertainty or independent corroboration by itself.", anchors: [{channel: "source", id: "s1", quote: "Its venue is Maple room."}, {channel: "source", id: "s2", quote: "Its venue is Maple room."}]},
		]
		representations: [
			{id: "competing-claims", description: "Separate date claims and a derived conflict condition, with the venue kept available under its own binding.", retains: ["first-date", "second-date", "conflict", "venue"]},
			{id: "qualified-date-group", description: "A date alternative group preserves both source-linked values and their unresolved incompatibility, without a separate independently maintained contested flag. The venue is still answerable.", retains: ["first-date", "second-date", "conflict", "venue"]},
		]
		forbidden: [
			{interpretation: "The session moved to 2030-03-12 because s2 is newer, or all information including venue must be withheld.", why: "There is no established move/supersession, and the venue binding is unaffected."},
			{interpretation: "The two venue statements prove independent corroboration or a duty to create a resolution ticket.", why: "Origin independence is not supplied, and uncertainty is not automatically an assigned task."},
		]
		projection: {current: "Date unresolved: sources give 2030-03-11 and 2030-03-12 without an established supersession. Venue: Maple room.", history: "Retain both date assertions and their context; do not invent a rescheduling event or an intervention queue."}
	}
}
