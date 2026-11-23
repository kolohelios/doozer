package judgment

// Fresh prose after the contract walkthrough. New references are provisional.
reviewedThreads: {
	"drill-date-resolution": {
		authority: "drill"
		bindings: [
			{id: "b0", subject: "Linden staff drill", property: "effective-date", scope: "one-day drill", validTime: null, values: []},
			{id: "b1", subject: "Linden staff drill", property: "location", scope: "drill venue", validTime: null, values: []},
		]
		sources: [
			{id: "m1", actor: "Rin", authority: "drill", origin: "drill-calendar", sentAt: "2031-06-10T09:00:00Z", text: "The Linden staff drill venue is Linden lab. I have not established its effective date in these notes. Its date is not 2031-06-10, the date of this message; please keep that exclusion separate from the date that remains unstated."},
			{id: "m2", actor: "Kai", authority: "participant", origin: "participant-question", sentAt: "2031-06-10T09:10:00Z", replyTo: "m1", text: "Is the Linden staff drill on 2031-06-12? Please check the calendar before making travel plans. I am asking about that date, not confirming it, and the calendar check does not itself change the drill schedule."},
			{id: "m3", actor: "Sam", authority: "facilities", origin: "library-job", sentAt: "2031-06-10T09:20:00Z", text: "The library shelf cleanup is on 2031-06-13 in Cedar room. That is a separate facilities job, not the Linden staff drill. I mention it because both groups asked about borrowing the same trolley."},
			{id: "m4", actor: "Draft", authority: "projection", origin: "drill-calendar", sentAt: "2031-06-10T09:30:00Z", derivedFrom: ["m1"], text: "This draft digest repeats m1: Linden lab is the drill venue and its date is not established here. It is a generated projection, not another observation or a new scheduling notice. It contains no additional calendar evidence."},
			{id: "m5", actor: "Kai", authority: "participant", origin: "coffee", sentAt: "2031-06-11T09:00:00Z", text: "The coffee dispenser near reception is working again. The mugs are on a different shelf this week. This housekeeping message is not a drill-date update."},
			{id: "m6", actor: "Sam", authority: "facilities", origin: "keys", sentAt: "2031-06-11T09:10:00Z", text: "I finished the spare-key inventory for building maintenance. Nothing in that inventory supplies a date for the drill. The trolley has been returned, and the library cleanup still has its own separate booking."},
			{id: "m7", actor: "Rin", authority: "drill", origin: "drill-calendar", sentAt: "2031-06-11T09:20:00Z", replyTo: "m1", text: "I can now establish the Linden staff drill date as 2031-06-12. This supplies the date missing from m1; it is not a statement that the drill was rescheduled from the timestamp of that note. The venue remains Linden lab."},
			{id: "m8", actor: "Draft", authority: "projection", origin: "drill-calendar", sentAt: "2031-06-11T09:30:00Z", derivedFrom: ["m7"], text: "The updated digest repeats the date and venue from m7. It should be read as a projection of that source, not as independent calendar confirmation. The earlier unknown date belongs to the earlier information frame."},
		]
		reference: {
			m1: [#TransferAssertion & {binding: "b1", value: "Linden lab"}, #TransferUncertainty & {binding: "b0", holder: "Rin"}, #TransferAssertion & {binding: "b0", operator: "neq", value: "2031-06-10"}]
			m2: [#TransferAtom & {kind: "question", binding: "b0", operator: "eq", value: "2031-06-12"}, #TransferAtom & {kind: "directive", binding: "b0", action: {verb: "check", object: "calendar", condition: "before making travel plans"}}]
			m3: [], m4: [], m5: [], m6: []
			m7: [#TransferAssertion & {binding: "b0", value: "2031-06-12"}, #TransferAssertion & {binding: "b1", value: "Linden lab"}]
			m8: []
		}
		queries: [{id: "q0", binding: "b0", value: "2031-06-12", expected: {w0: "unestablished", w1: "supported"}}, {id: "q1", binding: "b1", value: "Linden lab", expected: {w0: "supported", w1: "supported"}}]
		control: {kind: "equivalent", span: "m1", binding: "b0", mode: "layout"}
	}
	"regional-coverage": {
		authority: "operations"
		unavailableParents: ["m0"]
		bindings: [
			{id: "b0", subject: "export scheduler", property: "quiet-mail", scope: "production-west", validTime: "2031-07-20", values: ["enabled", "disabled"]},
			{id: "b1", subject: "export scheduler", property: "quiet-mail", scope: "staging-west", validTime: "2031-07-20", values: ["enabled", "disabled"]},
			{id: "b2", subject: "export backup", property: "location", scope: "production-west", validTime: "2031-07-20", values: []},
		]
		sources: [
			{id: "m1", actor: "Tess", authority: "operations", origin: "staging-run", sentAt: "2031-07-18T09:00:00Z", text: "For the staging-west export scheduler on 2031-07-20, quiet-mail is enabled. This observation covers staging-west only and supplies no production-west finding in these notes. A similar option name is not a reason to transfer the result between environments."},
			{id: "m2", actor: "Tess", authority: "operations", origin: "backup-record", sentAt: "2031-07-18T09:10:00Z", text: "The production-west export backup is stored at Sable vault. That is a location record, separate from the scheduler's quiet-mail setting. The backup record is not a test of notification behavior."},
			{id: "m3", actor: "Lee", authority: "other-region", origin: "east-run", sentAt: "2031-07-18T09:20:00Z", text: "In production-east, quiet-mail is disabled for the export scheduler. That report concerns the east region, not production-west or staging-west. I copied the subject line into this conversation because the option names look alike."},
			{id: "m4", actor: "Draft", authority: "projection", origin: "staging-run", sentAt: "2031-07-18T09:30:00Z", derivedFrom: ["m1"], text: "This digest repeats the staging observation from m1. It is not a production deployment record and does not create another independent test. Its shortened heading should not override the source's environment scope."},
			{id: "m5", actor: "Mo", authority: "participant", origin: "unresolved-reply", sentAt: "2031-07-19T09:00:00Z", replyTo: "m0", text: "That quiet-mail setting was enabled. I am replying to deployment note m0, which is not included in this packet, and I have not named the environment or validity date in this reply. The reply alone does not identify which deployment I mean."},
			{id: "m6", actor: "Lee", authority: "other-region", origin: "banner", sentAt: "2031-07-19T09:10:00Z", text: "The word enabled also appears in the status-page banner for our meeting-room display. That banner setting is unrelated to any export scheduler. We fixed the display font this morning."},
			{id: "m7", actor: "Tess", authority: "operations", origin: "production-run", sentAt: "2031-07-19T09:20:00Z", text: "The production-west export scheduler's quiet-mail setting is disabled for 2031-07-20. This is the production-west deployment record that was missing from the earlier notes. It does not supersede the separate backup-location record in m2 or change what was observed in staging-west."},
			{id: "m8", actor: "Draft", authority: "projection", origin: "production-run", sentAt: "2031-07-19T09:30:00Z", derivedFrom: ["m7"], text: "The updated digest repeats the production setting from m7. Repeating that record is not another deployment observation. Please follow its source link rather than treat this summary as corroboration."},
		]
		reference: {m1: [#TransferAssertion & {binding: "b1", value: "enabled"}], m2: [#TransferAssertion & {binding: "b2", value: "Sable vault"}], m3: [], m4: [], m5: [], m6: [], m7: [#TransferAssertion & {binding: "b0", value: "disabled"}], m8: []}
		queries: [{id: "q0", binding: "b0", value: "enabled", expected: {w0: "unestablished", w1: "opposed"}}, {id: "q1", binding: "b1", value: "enabled", expected: {w0: "supported", w1: "supported"}}, {id: "q2", binding: "b2", value: "Sable vault", expected: {w0: "supported", w1: "supported"}}]
		control: {kind: "fault", span: "m7", binding: "b0", mode: "omit"}
	}
	"unresolved-qualifier": {
		authority: "events"
		bindings: [
			{id: "b0", subject: "workshop", property: "effective-date", scope: "one-day workshop", validTime: null, values: []},
			{id: "b1", subject: "briefing", property: "effective-date", scope: "one-day briefing", validTime: null, values: []},
			{id: "b2", subject: "both events", property: "location", scope: "shared venue", validTime: null, values: []},
		]
		sources: [
			{id: "m1", actor: "Ari", authority: "events", origin: "events-calendar", sentAt: "2031-08-10T09:00:00Z", text: "The workshop date is 2031-08-14 and the briefing date is 2031-08-15. Exactly one of these dates remains provisional; I have not marked which one in this note. The venue for both is Juniper studio."},
			{id: "m2", actor: "Bo", authority: "participant", origin: "workshop-question", sentAt: "2031-08-10T09:10:00Z", replyTo: "m1", text: "Is the workshop on 2031-08-14? I am checking which date the workshop line refers to, not adding another confirmation. The note about one provisional date still needs to be read with the two reported values."},
			{id: "m3", actor: "Cal", authority: "other-event", origin: "fundraiser", sentAt: "2031-08-10T09:20:00Z", text: "The fundraiser has a separate room booking at Elm lounge. It is not the workshop or briefing in Ari's note. The similar invitation colors confused the printing team, so I am making that distinction explicit."},
			{id: "m4", actor: "Draft", authority: "projection", origin: "events-calendar", sentAt: "2031-08-10T09:30:00Z", derivedFrom: ["m1"], text: "A shortened draft says both dates are confirmed. This draft is a derived projection of m1, not a new observation or an authoritative correction. Its wording must not erase the original exactly-one provisional qualifier."},
			{id: "m5", actor: "Bo", authority: "participant", origin: "calendar-request", sentAt: "2031-08-11T09:00:00Z", text: "For the workshop date, please check the calendar before making travel plans. That request is about the date and does not assign a new value to it. I have not supplied a resolution of the provisional qualifier."},
			{id: "m6", actor: "Cal", authority: "other-event", origin: "icons", sentAt: "2031-08-11T09:10:00Z", text: "The calendar icon on the fundraiser poster was the wrong size. This is a graphics correction, not a scheduling change. The posters are now ready to print."},
			{id: "m7", actor: "Ari", authority: "events", origin: "events-calendar", sentAt: "2031-08-11T09:20:00Z", replyTo: "m1", text: "The workshop still has reported date 2031-08-14 and the briefing 2031-08-15. Exactly one of those dates is provisional, and its identity is still unmarked here. The shared venue remains Juniper studio."},
			{id: "m8", actor: "Draft", authority: "projection", origin: "events-calendar", sentAt: "2031-08-11T09:30:00Z", derivedFrom: ["m7"], text: "The corrected digest now retains the unresolved qualifier from m7. It is still a projection, not a new source of date evidence. The original values and their context remain the basis for the summary."},
		]
		reference: {
			m1: [#TransferAssertion & {binding: "b0", value: "2031-08-14"}, #TransferAssertion & {binding: "b1", value: "2031-08-15"}, #TransferAssertion & {binding: "b2", value: "Juniper studio"}, #TransferAtom & {kind: "qualifier", operator: "one-provisional", alternatives: ["b0", "b1"]}]
			m2: [#TransferAtom & {kind: "question", binding: "b0", operator: "eq", value: "2031-08-14"}], m3: [], m4: []
			m5: [#TransferAtom & {kind: "directive", binding: "b0", action: {verb: "check", object: "calendar", condition: "before making travel plans"}}], m6: []
			m7: [#TransferAssertion & {binding: "b0", value: "2031-08-14"}, #TransferAssertion & {binding: "b1", value: "2031-08-15"}, #TransferAssertion & {binding: "b2", value: "Juniper studio"}, #TransferAtom & {kind: "qualifier", operator: "one-provisional", alternatives: ["b0", "b1"]}]
			m8: []
		}
		queries: [{id: "q0", binding: "b0", value: "2031-08-14", expected: {w0: "supported", w1: "supported"}}, {id: "q1", binding: "b1", value: "2031-08-15", expected: {w0: "supported", w1: "supported"}}, {id: "q2", binding: "b2", value: "Juniper studio", expected: {w0: "supported", w1: "supported"}}]
		control: {kind: "equivalent", span: "m1", binding: "b0", mode: "layout"}
	}
	"withdraw-only-assurance": {
		authority: "exhibit"
		bindings: [{id: "b0", subject: "booked visitors", property: "permission", scope: "Copper exhibit on 2031-09-20", validTime: "2031-09-20", values: ["permitted", "forbidden"]}, {id: "b1", subject: "Copper exhibit", property: "location", scope: "exhibit venue", validTime: "2031-09-20", values: []}]
		sources: [
			{id: "m1", actor: "Dana", authority: "exhibit", origin: "exhibit-record", sentAt: "2031-09-18T09:00:00Z", text: "My assurance is that booked visitors are permitted entry at the Copper exhibit on 2031-09-20. The venue is Copper hall. I am reporting an arrangement, not issuing a new permission grant."},
			{id: "m2", actor: "Em", authority: "participant", origin: "entry-question", sentAt: "2031-09-18T09:10:00Z", text: "Are booked visitors permitted entry at the Copper exhibit? This is a question about the arrangement Dana reported, not a new authorization. I have not checked the underlying permission record."},
			{id: "m3", actor: "Fin", authority: "storage", origin: "storage-rule", sentAt: "2031-09-18T09:20:00Z", text: "Visitor entry is forbidden at the separate storage bay during the inventory. The storage bay is not Copper hall and this rule does not cover the Copper exhibit. The inventory team has its own access arrangements."},
			{id: "m4", actor: "Draft", authority: "projection", origin: "exhibit-record", sentAt: "2031-09-18T09:30:00Z", derivedFrom: ["m1"], text: "This draft digest repeats the assurance in m1. It is neither a grant nor independent verification of visitor permission. Its source link is necessary to recover the assurance's limited basis."},
			{id: "m5", actor: "Dana", authority: "exhibit", origin: "exhibit-record", sentAt: "2031-09-19T09:00:00Z", text: "The exhibit venue remains Copper hall. That location detail is separate from the permission question. We are not moving the exhibit as part of this correspondence."},
			{id: "m6", actor: "Em", authority: "participant", origin: "brochures", sentAt: "2031-09-19T09:10:00Z", text: "The brochures will be printed after lunch. The printer location is a separate logistics issue, not evidence about visitor permission. I have replaced the empty paper tray."},
			{id: "m7", actor: "Dana", authority: "exhibit", origin: "exhibit-record", sentAt: "2031-09-19T09:20:00Z", replyTo: "m1", text: "I withdraw the assurance in m1 pending inspection. I am not revoking a grant, and I now make no finding that booked-visitor entry is permitted or forbidden. The venue remains Copper hall; this message does not supply a new permission rule."},
			{id: "m8", actor: "Draft", authority: "projection", origin: "exhibit-record", sentAt: "2031-09-19T09:30:00Z", derivedFrom: ["m7"], text: "The revised digest records the assurance withdrawal and the resulting lack of a current finding. It is still a projection of m7. Repeating it must not manufacture a prohibition or an independent witness."},
		]
		reference: {m1: [#TransferAssurance & {binding: "b0", value: "permitted"}, #TransferAssertion & {binding: "b1", value: "Copper hall"}], m2: [#TransferAtom & {kind: "question", binding: "b0", operator: "eq", value: "permitted"}], m3: [], m4: [], m5: [#TransferAssertion & {binding: "b1", value: "Copper hall"}], m6: [], m7: [#TransferAtom & {kind: "assurance-withdrawal", binding: "b0", targetSource: "m1", targetKind: "assurance"}, #TransferUncertainty & {binding: "b0", holder: "Dana"}, #TransferAssertion & {binding: "b1", value: "Copper hall"}], m8: []}
		queries: [{id: "q0", binding: "b0", value: "permitted", expected: {w0: "supported", w1: "unestablished"}}, {id: "q1", binding: "b1", value: "Copper hall", expected: {w0: "supported", w1: "supported"}}]
		control: {kind: "fault", span: "m7", binding: "b0", mode: "add", atom: #TransferAssertion & {binding: "b0", value: "forbidden"}}
	}
	"independent-grant-survives": {
		authority: "session"
		bindings: [{id: "b0", subject: "booked visitors", property: "permission", scope: "Oak session on 2031-09-21", validTime: "2031-09-21", values: ["permitted", "forbidden"]}, {id: "b1", subject: "Oak session", property: "location", scope: "session venue", validTime: "2031-09-21", values: []}]
		sources: [
			{id: "m1", actor: "Gale", authority: "session", origin: "grant-register", sentAt: "2031-09-18T09:00:00Z", text: "I grant booked visitors entry permission for the Oak session on 2031-09-21. The venue is Oak hall. This is an actual session-scoped grant, not merely an assurance about some other authorization."},
			{id: "m2", actor: "Hal", authority: "participant", origin: "other-meeting", sentAt: "2031-09-18T09:10:00Z", text: "The catering meeting has a different attendance list. It is not the Oak session. Please do not use its invitation as a visitor permission record for another event."},
			{id: "m3", actor: "Gale", authority: "session", origin: "inspection-assurance", sentAt: "2031-09-18T09:20:00Z", text: "My separate assurance is that booked visitors are permitted entry for the Oak session. This reassurance is not a second grant. The grant already issued in m1 remains a distinct record."},
			{id: "m4", actor: "Draft", authority: "projection", origin: "grant-register", sentAt: "2031-09-18T09:30:00Z", derivedFrom: ["m1"], text: "This is a projection of the grant in m1. Repeating the permission does not issue it again or provide independent corroboration. The venue information is inherited from that same source."},
			{id: "m5", actor: "Hal", authority: "participant", origin: "other-revocation", sentAt: "2031-09-19T09:00:00Z", text: "A different coordinator revoked a permit for the catering meeting. That revocation concerns the other event, not the Oak session or the grant in m1. I am separating the two conversations because their subject lines were similar."},
			{id: "m6", actor: "Ira", authority: "participant", origin: "permission-question", sentAt: "2031-09-19T09:10:00Z", text: "Are booked visitors permitted entry for the Oak session? I am asking about that session, not granting permission myself. My question does not replace the existing source records."},
			{id: "m7", actor: "Gale", authority: "session", origin: "grant-register", sentAt: "2031-09-19T09:20:00Z", replyTo: "m3", text: "I withdraw the assurance in m3. This withdraws only that endorsement; I do not revoke the grant in m1. The venue remains Oak hall."},
			{id: "m8", actor: "Draft", authority: "projection", origin: "grant-register", sentAt: "2031-09-19T09:30:00Z", derivedFrom: ["m1", "m7"], text: "This digest derives the session view from the grant and the assurance withdrawal. It is not a new grant or a revocation. Its existence does not change which original acts remain current."},
		]
		reference: {m1: [#TransferAct & {kind: "grant", binding: "b0"}, #TransferAssertion & {binding: "b1", value: "Oak hall"}], m2: [], m3: [#TransferAssurance & {binding: "b0", value: "permitted"}], m4: [], m5: [], m6: [#TransferAtom & {kind: "question", binding: "b0", operator: "eq", value: "permitted"}], m7: [#TransferAtom & {kind: "assurance-withdrawal", binding: "b0", targetSource: "m3", targetKind: "assurance"}, #TransferAssertion & {binding: "b1", value: "Oak hall"}], m8: []}
		queries: [{id: "q0", binding: "b0", value: "permitted", expected: {w0: "supported", w1: "supported"}}, {id: "q1", binding: "b1", value: "Oak hall", expected: {w0: "supported", w1: "supported"}}]
		control: {kind: "equivalent", span: "m1", binding: "b0", mode: "layout"}
	}
	"actual-grant-revoked": {
		authority: "fair"
		bindings: [{id: "b0", subject: "booked visitors under grant m1", property: "permission", scope: "Bronze fair on 2031-09-22", validTime: "2031-09-22", values: ["permitted", "forbidden"]}, {id: "b1", subject: "Bronze fair", property: "location", scope: "fair venue", validTime: "2031-09-22", values: []}]
		sources: [
			{id: "m1", actor: "Jae", authority: "fair", origin: "fair-grant", sentAt: "2031-09-18T09:00:00Z", text: "I grant booked visitors entry permission for the Bronze fair on 2031-09-22. The venue is Bronze hall. The grant applies only to this fair and does not describe whether any physical door is open."},
			{id: "m2", actor: "Jae", authority: "fair", origin: "fair-grant", sentAt: "2031-09-18T09:10:00Z", text: "The venue record still names Bronze hall. It is not a second permission grant. This note is only a reminder of where the fair is being held."},
			{id: "m3", actor: "Kim", authority: "participant", origin: "grant-question", sentAt: "2031-09-18T09:20:00Z", text: "Are booked visitors permitted entry under the grant for the Bronze fair? This is a question about m1, not my own grant. The venue reminder does not answer the authority question by itself."},
			{id: "m4", actor: "Draft", authority: "projection", origin: "fair-grant", sentAt: "2031-09-18T09:30:00Z", derivedFrom: ["m1"], text: "The draft visitor summary repeats the grant from m1. It has no independent authority to grant or revoke permission. Its link to the source is part of its meaning."},
			{id: "m5", actor: "Kim", authority: "participant", origin: "service-door", sentAt: "2031-09-19T09:00:00Z", text: "The service door used by delivery workers was locked during cleaning. That is a physical observation about a different entrance, not the booked-visitor permission for the Bronze fair. Do not use a door report as a permission rule."},
			{id: "m6", actor: "Kim", authority: "participant", origin: "staff-entry", sentAt: "2031-09-19T09:10:00Z", text: "Staff use a separate entrance arrangement. I am not reporting any change to the visitor grant in this message. The two groups should not be conflated merely because both attend the fair."},
			{id: "m7", actor: "Jae", authority: "fair", origin: "fair-grant", sentAt: "2031-09-19T09:20:00Z", replyTo: "m1", text: "I revoke the visitor entry permission granted in m1 for the Bronze fair. This is an actual revocation of that grant, not withdrawal of an assurance. The venue remains Bronze hall."},
			{id: "m8", actor: "Draft", authority: "projection", origin: "fair-grant", sentAt: "2031-09-19T09:30:00Z", derivedFrom: ["m7"], text: "The corrected summary repeats the revocation and the unchanged venue from m7. It does not claim a physical door is locked. This summary is not a new source of permission evidence."},
		]
		reference: {m1: [#TransferAct & {kind: "grant", binding: "b0"}, #TransferAssertion & {binding: "b1", value: "Bronze hall"}], m2: [#TransferAssertion & {binding: "b1", value: "Bronze hall"}], m3: [#TransferAtom & {kind: "question", binding: "b0", operator: "eq", value: "permitted"}], m4: [], m5: [], m6: [], m7: [#TransferAtom & {kind: "revocation", binding: "b0", targetSource: "m1", targetKind: "grant"}, #TransferAssertion & {binding: "b1", value: "Bronze hall"}], m8: []}
		queries: [{id: "q0", binding: "b0", value: "permitted", expected: {w0: "supported", w1: "opposed"}}, {id: "q1", binding: "b1", value: "Bronze hall", expected: {w0: "supported", w1: "supported"}}]
		control: {kind: "fault", span: "m7", binding: "b0", mode: "omit"}
	}
	"equal-authority-date-conflict": {
		authority: "scheduling"
		bindings: [{id: "b0", subject: "one-day symposium", property: "effective-date", scope: "same symposium", validTime: null, values: []}, {id: "b1", subject: "one-day symposium", property: "location", scope: "symposium venue", validTime: null, values: []}]
		sources: [
			{id: "m1", actor: "Lou", authority: "scheduling", origin: "notice-a", sentAt: "2031-10-01T09:00:00Z", text: "The one-day symposium is scheduled for 2031-10-11. Its venue is Maple hall. This is a current scheduling notice, not a record of two separate events."},
			{id: "m2", actor: "Nia", authority: "participant", origin: "chairs", sentAt: "2031-10-01T09:10:00Z", text: "The spare chairs are for another event in Cedar room. They are not a change to the symposium venue. We have finished counting them and returned the list to facilities."},
			{id: "m3", actor: "Max", authority: "scheduling", origin: "notice-b", sentAt: "2031-10-01T09:20:00Z", text: "The same one-day symposium is scheduled for 2031-10-12. Its venue is Maple hall. My notice has the same authority as m1, and no supersession or rescheduling between them is established here."},
			{id: "m4", actor: "Draft", authority: "projection", origin: "notice-b", sentAt: "2031-10-01T09:30:00Z", derivedFrom: ["m3"], text: "This draft summary repeats the later date from m3. It is a projection of that notice, not another independently sourced date or a supersession act. Its shortened wording must not hide the unresolved earlier notice."},
			{id: "m5", actor: "Nia", authority: "participant", origin: "date-question", sentAt: "2031-10-02T09:00:00Z", text: "Is the symposium on 2031-10-12? I am asking because the source notices conflict, not declaring the later notice correct. The calendar entry I saw was copied from the draft summary."},
			{id: "m6", actor: "Nia", authority: "participant", origin: "lunch", sentAt: "2031-10-02T09:10:00Z", text: "The lunch menu has been finalized for the catering team. That does not establish which symposium date is correct. The menu discussion concerns food choices, not scheduling authority."},
			{id: "m7", actor: "Lou", authority: "scheduling", origin: "notice-a", sentAt: "2031-10-02T09:20:00Z", text: "My current notice still gives the symposium date as 2031-10-11. Maple hall remains the venue. I have not established that either notice supersedes the other, so this repetition should not be mistaken for a resolution."},
			{id: "m8", actor: "Draft", authority: "projection", origin: "notice-b", sentAt: "2031-10-02T09:30:00Z", derivedFrom: ["m3"], text: "Another digest repeats m3's date again. It introduces no independent observation and does not outrank m1 or m7 by being repeated. The original disagreement remains part of the record."},
		]
		reference: {m1: [#TransferAssertion & {binding: "b0", value: "2031-10-11"}, #TransferAssertion & {binding: "b1", value: "Maple hall"}], m2: [], m3: [#TransferAssertion & {binding: "b0", value: "2031-10-12"}, #TransferAssertion & {binding: "b1", value: "Maple hall"}], m4: [], m5: [#TransferAtom & {kind: "question", binding: "b0", operator: "eq", value: "2031-10-12"}], m6: [], m7: [#TransferAssertion & {binding: "b0", value: "2031-10-11"}, #TransferAssertion & {binding: "b1", value: "Maple hall"}], m8: []}
		queries: [{id: "q0", binding: "b0", value: "2031-10-11", expected: {w0: "contested", w1: "contested"}}, {id: "q1", binding: "b1", value: "Maple hall", expected: {w0: "supported", w1: "supported"}}]
		control: {kind: "fault", span: "m1", binding: "b0", mode: "omit"}
	}
}
