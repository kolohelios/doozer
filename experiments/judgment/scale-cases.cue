package judgment

scaleCases: {
	"01-hunch-and-observation": {
		subject: "Alder export", room: "Cobalt vault", property: "quiet-mail", scope: "production-north", time: "2032-02-20", values: ["enabled", "disabled"]
		secondarySubject: "Alder export", secondaryProperty: "quiet-mail", secondaryScope: "staging-north", secondaryTime: "2032-02-20", secondaryValues: ["enabled", "disabled"]
		target: "enabled", secondaryTarget: "enabled", states: {w0: "unestablished", w1: "opposed"}, missingParent: true
		messages: {
			m1:  "The Alder export backup is at Cobalt vault. My production-north checklist for 2032-02-20 has no quiet-mail finding yet. The backup location came from the storage register, which is separate from the scheduler deployment record."
			m3:  "My guess is that quiet-mail is enabled in production-north for 2032-02-20. I am extrapolating from how last month's test felt, rather than reading a current deployment export. I would keep the guess apart from a measured result."
			m4:  "The east-region export uses a different schedule and recipient list. Its team has already finished its own checks. Their checklist was attached to the shared meeting invitation, which explains why it appeared in this conversation."
			m5:  "The staging-north Alder scheduler has quiet-mail enabled for 2032-02-20. This comes from the staging deployment export I opened this morning. That row belongs to staging rather than the production checklist mentioned in m1."
			m6:  "For the Alder production setting, please check the deployment register before making notification promises. The spreadsheet preview in the invitation is merely a convenience copy. Its short heading leaves out the environment column."
			m7:  "That setting was enabled in the version I meant. My reply is attached to an earlier note that is not included here, and this sentence does not identify an environment or validity date. The missing parent is needed to bind the reference."
			m10: "The Alder backup is still at Cobalt vault. The storage register has not been replaced during the scheduler discussion. The location record does not tell us which notification setting was deployed."
			m11: "Is production-north quiet-mail enabled for 2032-02-20? I am asking about the deployment, not endorsing the earlier guess. The answer will determine which checklist column I read during the rehearsal."
			m13: "I opened the production-north deployment export for the Alder scheduler on 2032-02-20: quiet-mail is disabled. This is the production observation that was missing from m1. It does not alter the staging record or the backup location."
			m14: "The east attachment was never a production-north deployment result. Its recipients and schedule are different even though the option names look alike. It remains in the thread so the attachment's context can be recovered."
			m15: "I am repeating my earlier request: for the production setting, check the deployment register before making notification promises. The new export can now supply the relevant row. This request is not a change to the setting."
		}
		reference: {
			m1: {atoms: [#TransferAssertion & {binding: "b1", value: "Cobalt vault"}]}
			m3: {annotations: [{kind: "speculation", binding: "b0", operator: "eq", value: "enabled", quote: "My guess is that quiet-mail is enabled in production-north for 2032-02-20."}]}
			m5: {atoms: [#TransferAssertion & {binding: "b2", value: "enabled"}]}
			m6: {atoms: [#TransferAtom & {kind: "directive", binding: "b0", action: {verb: "check", object: "the deployment register", condition: "before making notification promises"}}]}
			m10: {atoms: [#TransferAssertion & {binding: "b1", value: "Cobalt vault"}]}
			m11: {atoms: [#TransferAtom & {kind: "question", binding: "b0", operator: "eq", value: "enabled"}]}
			m13: {atoms: [#TransferAssertion & {binding: "b0", value: "disabled"}]}
			m15: {atoms: [#TransferAtom & {kind: "directive", binding: "b0", action: {verb: "check", object: "the deployment register", condition: "before making notification promises"}}]}
		}
		control: {kind: "fault", mode: "hunch-world", span: "m3", binding: "b0"}
	}
	"02-environment-coverage": {
		subject: "Beacon export", room: "Silver vault", property: "quiet-mail", scope: "production-west", time: "2032-03-20", values: ["enabled", "disabled"]
		secondarySubject: "Beacon export", secondaryProperty: "quiet-mail", secondaryScope: "staging-west", secondaryTime: "2032-03-20", secondaryValues: ["enabled", "disabled"]
		target: "enabled", secondaryTarget: "enabled", states: {w0: "unestablished", w1: "opposed"}
		messages: {
			m1:  "The Beacon export backup is at Silver vault. These notes do not contain a production-west quiet-mail finding for 2032-03-20. The location register and scheduler deployment results are separate records, despite appearing in the same folder."
			m3:  "I have a report index for Beacon, but its production-west row is still absent from these notes. The index lists several environments. An empty entry in this copy is not a claim about what every operator knows."
			m4:  "Quiet-mail is disabled for Beacon production-east on 2032-03-20. My export came from the east deployment account and covers that region only. It should not be relabelled as a west observation when the reports are collated."
			m5:  "The Beacon staging-west scheduler has quiet-mail enabled for 2032-03-20. That is the staging deployment row, with its own environment identifier. The corresponding production-west export is not part of this message."
			m6:  "For production-west notification planning, check the deployment register before making notification promises. The earlier meeting attachment combines region names in its heading. The underlying records keep those names separate."
			m7:  "Is quiet-mail enabled for production-west on 2032-03-20? I am trying to complete the west checklist. This question should not be read as another observation of that deployment."
			m10: "Silver vault remains the Beacon backup location. There is no move associated with the notification review. The backup record can stay usable while the scheduler field is being checked."
			m11: "Is the production-west setting enabled for the named export date? I have seen the staging result and the east attachment. Neither label answers the west question by itself."
			m13: "The Beacon production-west deployment record for 2032-03-20 says quiet-mail is disabled. I retrieved the west export rather than copying the east row. This supplies the missing production-west finding without changing staging."
			m14: "The production-east observation in m4 keeps its east scope. The west record now has its own source in m13. Similar values do not make the two records the same observation."
			m15: "For anyone using the west checklist, check the deployment register before making notification promises. That remains the same evidence-use request as before. The backup-location entry is unrelated to that check."
		}
		reference: {
			m1: {atoms: [#TransferAssertion & {binding: "b1", value: "Silver vault"}]}
			m4: {}
			m5: {atoms: [#TransferAssertion & {binding: "b2", value: "enabled"}]}
			m6: {atoms: [#TransferAtom & {kind: "directive", binding: "b0", action: {verb: "check", object: "the deployment register", condition: "before making notification promises"}}]}
			m7: {atoms: [#TransferAtom & {kind: "question", binding: "b0", operator: "eq", value: "enabled"}]}
			m10: {atoms: [#TransferAssertion & {binding: "b1", value: "Silver vault"}]}
			m11: {atoms: [#TransferAtom & {kind: "question", binding: "b0", operator: "eq", value: "enabled"}]}
			m13: {atoms: [#TransferAssertion & {binding: "b0", value: "disabled"}]}
			m15: {atoms: [#TransferAtom & {kind: "directive", binding: "b0", action: {verb: "check", object: "the deployment register", condition: "before making notification promises"}}]}
		}
		control: {kind: "fault", mode: "add-world", span: "m4", binding: "b0", atom: #TransferAssertion & {binding: "b0", value: "disabled"}}
	}
	"03-personal-unknown": {
		subject:          "Cedar workshop", room:              "Birch hall", property:           "effective-date", scope: "one-day workshop"
		secondarySubject: "Cedar briefing", secondaryProperty: "effective-date", secondaryScope: "separate one-day briefing"
		target:           "2032-04-14", secondaryTarget:       "2032-04-18", states: {w0: "unestablished", w1: "supported"}
		messages: {
			m1:  "The Cedar workshop venue is Birch hall. Its effective date has not been entered in these notes. The workshop date is not 2032-01-01, the date of this message."
			m3:  "I personally do not know whether the Cedar workshop is on 2032-04-14. I have not looked at the newly signed calendar entry. That is a statement about my knowledge at this point, rather than an exclusion of that date."
			m4:  "The facilities tour mentioned in yesterday's chat is a different event. Its booking was handled by another office. That tour should not be substituted for the workshop simply because some attendees overlap."
			m5:  "The separate Cedar briefing is on 2032-04-18. It has its own one-day booking and attendance list. The briefing entry is not an alternative date for the workshop."
			m6:  "For the workshop date, check the calendar before making travel plans. The note pinned to the invitation is not the signed booking entry. This request is about finding the date, not assigning one."
			m7:  "Is the Cedar workshop on 2032-04-14? I saw that date in a proposed itinerary. I am asking which booking supports it rather than confirming the proposal."
			m10: "The venue remains Birch hall. That was not the uncertain part of the workshop record. We can keep the location visible while the date entry is being recovered."
			m11: "Is 2032-04-14 the Cedar workshop date? I would like to know what the calendar actually records. The earlier personal uncertainty should not be converted into a claim that the date is impossible."
			m13: "I have now read the signed entry: the Cedar workshop is on 2032-04-14. This establishes the date that I did not know when writing m3. It does not mean the workshop moved from the date of that message."
			m14: "The facilities tour still belongs to its own booking. Recovering the workshop entry did not combine the events. The separate briefing record in m5 is also unchanged."
			m15: "Please check the calendar before making travel plans for the workshop. The signed entry now provides a source for that check. I am repeating the evidence-use request, not creating a new booking."
		}
		reference: {
			m1: {atoms: [#TransferAssertion & {binding: "b1", value: "Birch hall"}, #TransferAssertion & {binding: "b0", operator: "neq", value: "2032-01-01"}]}
			m3: {annotations: [{kind: "condition", binding: "b0", frame: "person", stance: "does-not-know", holder: "Leah", quote: "I personally do not know whether the Cedar workshop is on 2032-04-14."}]}
			m5: {atoms: [#TransferAssertion & {binding: "b2", value: "2032-04-18"}]}
			m6: {atoms: [#TransferAtom & {kind: "directive", binding: "b0", action: {verb: "check", object: "the calendar", condition: "before making travel plans"}}]}
			m7: {atoms: [#TransferAtom & {kind: "question", binding: "b0", operator: "eq", value: "2032-04-14"}]}
			m10: {atoms: [#TransferAssertion & {binding: "b1", value: "Birch hall"}]}
			m11: {atoms: [#TransferAtom & {kind: "question", binding: "b0", operator: "eq", value: "2032-04-14"}]}
			m13: {atoms: [#TransferAssertion & {binding: "b0", value: "2032-04-14"}]}
			m15: {atoms: [#TransferAtom & {kind: "directive", binding: "b0", action: {verb: "check", object: "the calendar", condition: "before making travel plans"}}]}
		}
		control: {kind: "fault", mode: "add-world", span: "m3", binding: "b0", atom: #TransferAssertion & {binding: "b0", operator: "neq", value: "2032-04-14"}}
	}
	"04-note-date-gap": {
		subject:          "Dune drill", room:                 "Quartz room", property:          "effective-date", scope: "one-day drill"
		secondarySubject: "Dune briefing", secondaryProperty: "effective-date", secondaryScope: "separate briefing"
		target:           "2032-05-14", secondaryTarget:      "2032-05-18", states: {w0: "unestablished", w1: "supported"}, missingParent: true
		messages: {
			m1:  "The Dune drill is at Quartz room. Its effective date is not established in these notes, and it is not 2032-01-01, the date of this message. The missing date and the known location are separate parts of the record."
			m3:  "The notes still have no established Dune drill date. That is a limit of this packet, not a survey of what every organizer knows. The location entry has already been copied from the venue register."
			m4:  "The spring facilities inspection is not the Dune drill. Its paperwork was in the same tray when the invitations were assembled. The shared tray is a filing accident, not a shared schedule."
			m5:  "The Dune briefing is on 2032-05-18. It is a separate one-day event. Its date should stay distinct from the drill date that this conversation is trying to recover."
			m6:  "For the drill date, check the calendar before making travel plans. A draft itinerary is not the signed schedule. The check itself does not put a date into the drill record."
			m7:  "That was the date I was referring to in the earlier note. The parent is not included in this packet, and I did not repeat which event I meant. This reply alone cannot identify the missing booking."
			m10: "The Dune drill venue remains Quartz room. Nothing in the date search has moved it. This location can remain usable without pretending the earlier notes already supplied a date."
			m11: "Is the Dune drill on 2032-05-14? I have found that date on a draft route plan. I am asking whether a source establishes it, not treating the draft as confirmation."
			m13: "The signed calendar establishes the Dune drill date as 2032-05-14. This fills the gap in m1; it is not a rescheduling from the message timestamp. The earlier note accurately described its limited coverage."
			m14: "The facilities inspection remains a separate event. Its paperwork does not revise the drill or briefing. I have kept the original folder references available so the distinction can be checked."
			m15: "For travel planning, check the calendar before making travel plans. The newly recovered signed entry is the relevant source. Repeating this request does not create another schedule observation."
		}
		reference: {
			m1: {atoms: [#TransferAssertion & {binding: "b1", value: "Quartz room"}, #TransferAssertion & {binding: "b0", operator: "neq", value: "2032-01-01"}], annotations: [{kind: "condition", binding: "b0", frame: "source-note", stance: "not-established-in-notes", holder: null, quote: "Its effective date is not established in these notes"}]}
			m5: {atoms: [#TransferAssertion & {binding: "b2", value: "2032-05-18"}]}
			m6: {atoms: [#TransferAtom & {kind: "directive", binding: "b0", action: {verb: "check", object: "the calendar", condition: "before making travel plans"}}]}
			m10: {atoms: [#TransferAssertion & {binding: "b1", value: "Quartz room"}]}
			m11: {atoms: [#TransferAtom & {kind: "question", binding: "b0", operator: "eq", value: "2032-05-14"}]}
			m13: {atoms: [#TransferAssertion & {binding: "b0", value: "2032-05-14"}]}
			m15: {atoms: [#TransferAtom & {kind: "directive", binding: "b0", action: {verb: "check", object: "the calendar", condition: "before making travel plans"}}]}
		}
		control: {kind: "equivalent", mode: "drop-note", span: "m1", binding: "b0"}
	}
	"05-assurance-withdrawal": {
		subject: "Elm exhibition visitors", room: "Copper hall", property: "permission", scope: "booked visitors at Elm exhibition", time: "2032-06-20", values: ["permitted", "forbidden"]
		secondarySubject: "Elm exhibition staff", secondaryProperty: "permission", secondaryScope: "staff under grant m5", secondaryTime: "2032-06-20", secondaryValues: ["permitted", "forbidden"]
		target: "permitted", secondaryTarget: "permitted", states: {w0: "supported", w1: "unestablished"}, reply13: "m3", topic: "permission-evidence-use"
		messages: {
			m1:  "The Elm exhibition venue is Copper hall for 2032-06-20. The booked-visitor arrangement has not been entered in this location note. A room booking is not itself a visitor permission grant."
			m3:  "My assurance is that booked visitors are permitted entry to the Elm exhibition on 2032-06-20. I am reporting an arrangement rather than issuing a grant. The underlying authorization is not included in this note."
			m4:  "The storage annex has its own visitor restrictions during stocktaking. It is not the Elm exhibition space. That separate arrangement should not replace the exhibition's permission record."
			m5:  "I grant staff entry permission for the Elm exhibition on 2032-06-20 under this staff grant. That is a staff-scoped authorization, not a grant to booked visitors. The two groups have different entry records."
			m6:  "The catering meeting has its own invitation. Please do not use its invitation as a visitor permission record for another event. For the exhibition, the relevant evidence is the exhibition's own authorization or assurance, with its stated limits."
			m7:  "Are booked visitors permitted entry to the Elm exhibition? I am asking about the arrangement reported in m3. The staff grant does not by itself settle that separate visitor question."
			m10: "The exhibition venue remains Copper hall. The permission discussion has not changed the room booking. That location should not disappear merely because the entry arrangement needs checking."
			m11: "Are booked visitors permitted entry for the stated exhibition date? I need to distinguish the visitor arrangement from the staff grant. This message does not supply a new authorization."
			m13: "I withdraw the assurance in m3 pending inspection. I now make no finding that booked visitors are permitted or forbidden entry. This is not revocation of a visitor grant, and it does not touch the separate staff grant."
			m14: "The storage annex remains outside this exhibition arrangement. Its stocktaking restrictions have not become a visitor rule for Copper hall. They were mentioned only because the envelopes arrived together."
			m15: "I am repeating the invitation warning: do not use its invitation as a visitor permission record for another event. The invitation I mean is the catering meeting's one from m6. This warning is about evidence reuse, not a new exhibition prohibition."
		}
		reference: {
			m1: {atoms: [#TransferAssertion & {binding: "b1", value: "Copper hall"}]}
			m3: {atoms: [#TransferAssurance & {binding: "b0", value: "permitted"}]}
			m5: {atoms: [#TransferAct & {kind: "grant", binding: "b2"}]}
			m6: {annotations: [{kind: "procedure", topic: "permission-evidence-use", action: {verb: "do not use", object: "its invitation", condition: "as a visitor permission record for another event"}, quote: "Please do not use its invitation as a visitor permission record for another event."}]}
			m7: {atoms: [#TransferAtom & {kind: "question", binding: "b0", operator: "eq", value: "permitted"}]}
			m10: {atoms: [#TransferAssertion & {binding: "b1", value: "Copper hall"}]}
			m11: {atoms: [#TransferAtom & {kind: "question", binding: "b0", operator: "eq", value: "permitted"}]}
			m13: {atoms: [#TransferAtom & {kind: "assurance-withdrawal", binding: "b0", targetSource: "m3", targetKind: "assurance"}]}
			m15: {annotations: [{kind: "procedure", topic: "permission-evidence-use", action: {verb: "do not use", object: "its invitation", condition: "as a visitor permission record for another event"}, quote: "do not use its invitation as a visitor permission record for another event."}]}
		}
		control: {kind: "fault", mode: "add-world", span: "m13", binding: "b0", atom: #TransferAssertion & {binding: "b0", value: "forbidden"}}
	}
	"06-independent-grant": {
		subject: "Fir session visitors", room: "Oak hall", property: "permission", scope: "booked visitors under grant m1", time: "2032-07-20", values: ["permitted", "forbidden"]
		secondarySubject: "Fir session staff", secondaryProperty: "permission", secondaryScope: "staff under grant m5", secondaryTime: "2032-07-20", secondaryValues: ["permitted", "forbidden"]
		target: "permitted", secondaryTarget: "permitted", states: {w0: "supported", w1: "supported"}, reply13: "m3", topic: "permission-evidence-use"
		messages: {
			m1:  "I grant booked visitors entry permission for the Fir session on 2032-07-20. The venue is Oak hall. This message is the actual visitor grant, not merely my recollection of another person's arrangement."
			m3:  "My separate assurance is that booked visitors are permitted entry to the Fir session. That reassurance is not another grant. The authorization in m1 is a distinct record with its own continuing effect."
			m4:  "A permit for the catering meeting belongs to a different attendance list. It does not describe the Fir session. The similar invitation stationery is what brought the other meeting into this conversation."
			m5:  "I grant staff entry permission for the Fir session on 2032-07-20. The staff grant is separate from the booked-visitor grant in m1. Neither is a physical-door observation."
			m6:  "The catering meeting has its own invitation. Please do not use its invitation as a visitor permission record for another event. An about-topic warning like this does not issue or revoke the Fir session grant."
			m7:  "Are booked visitors permitted entry to the Fir session? I am asking which source authorizes them. This question does not replace either grant or the separate assurance."
			m10: "The Fir session venue remains Oak hall. The assurance and grant discussion has not moved it. Its location is a different property from visitor permission."
			m11: "Are booked visitors permitted entry for the Fir session date? I have seen several retellings of the same grant. Repetition should not be counted as several independent authorizations."
			m13: "I withdraw only the assurance in m3. I do not revoke the actual visitor grant in m1 or the staff grant in m5. The inspection question affects my endorsement, not those issued grants."
			m14: "The catering permit is still a different event's record. Its issuer has not changed the Fir session's authorization. Keeping both conversations available does not merge their scopes."
			m15: "The invitation in m6 belongs to catering; do not use its invitation as a visitor permission record for another event. This repeats the earlier evidence-use warning. It adds no new grant or prohibition."
		}
		reference: {
			m1: {atoms: [#TransferAct & {kind: "grant", binding: "b0"}, #TransferAssertion & {binding: "b1", value: "Oak hall"}]}
			m3: {atoms: [#TransferAssurance & {binding: "b0", value: "permitted"}]}
			m5: {atoms: [#TransferAct & {kind: "grant", binding: "b2"}]}
			m6: {annotations: [{kind: "procedure", topic: "permission-evidence-use", action: {verb: "do not use", object: "its invitation", condition: "as a visitor permission record for another event"}, quote: "Please do not use its invitation as a visitor permission record for another event."}]}
			m7: {atoms: [#TransferAtom & {kind: "question", binding: "b0", operator: "eq", value: "permitted"}]}
			m10: {atoms: [#TransferAssertion & {binding: "b1", value: "Oak hall"}]}
			m11: {atoms: [#TransferAtom & {kind: "question", binding: "b0", operator: "eq", value: "permitted"}]}
			m13: {atoms: [#TransferAtom & {kind: "assurance-withdrawal", binding: "b0", targetSource: "m3", targetKind: "assurance"}]}
			m15: {annotations: [{kind: "procedure", topic: "permission-evidence-use", action: {verb: "do not use", object: "its invitation", condition: "as a visitor permission record for another event"}, quote: "do not use its invitation as a visitor permission record for another event."}]}
		}
		control: {kind: "equivalent", mode: "procedure-layout", span: "m6", binding: "b0"}
	}
	"07-grant-revocation": {
		subject: "Grove fair visitors", room: "Bronze hall", property: "permission", scope: "booked visitors under grant m1", time: "2032-08-20", values: ["permitted", "forbidden"]
		secondarySubject: "Grove fair staff", secondaryProperty: "permission", secondaryScope: "staff under grant m5", secondaryTime: "2032-08-20", secondaryValues: ["permitted", "forbidden"]
		target: "permitted", secondaryTarget: "permitted", states: {w0: "supported", w1: "opposed"}, topic: "permission-evidence-use"
		messages: {
			m1:  "I grant booked visitors entry permission for the Grove fair on 2032-08-20. The fair venue is Bronze hall. This grant is limited to those visitors and that event."
			m3:  "Is the Grove visitor grant enough to explain why booked visitors are permitted entry? I am checking the source record for that arrangement. A brochure location is not an authorization by itself."
			m4:  "The storage bay has a separate stocktaking restriction. It is not the Grove fair venue. A restriction for the storage team does not describe the fair's booked visitors."
			m5:  "I grant staff entry permission for the Grove fair on 2032-08-20 under this staff grant. It is distinct from the visitor grant in m1. Both records are scoped authorizations rather than door-sensor reports."
			m6:  "For the visitor arrangement, check the grant register before making entry promises. A room booking and an invitation may describe different aspects of the event. The register identifies the actual issued grant."
			m7:  "Are booked visitors permitted entry under the Grove grant? This is a question about m1. I am not creating another grant by asking it."
			m10: "The Grove fair venue remains Bronze hall. That location has not changed during the entry discussion. The grant and the venue should remain separately inspectable."
			m11: "Are booked visitors permitted entry under the named visitor grant for the fair date? I have kept the staff record in another checklist column. It would be misleading to answer the visitor question with a staff-only authorization."
			m13: "I revoke the booked-visitor entry grant issued in m1 for the Grove fair. This is an actual revocation of that specific grant, not withdrawal of an assurance. It does not revoke the separate staff grant in m5 or change the venue."
			m14: "The storage bay restriction remains outside the fair's visitor record. The fair revocation has its own target in m13. No physical-door condition follows from either authorization statement."
			m15: "For the entry arrangement, check the grant register before making entry promises. That repeats the earlier source-use request. The current visitor revocation and continuing staff grant should not be collapsed."
		}
		reference: {
			m1: {atoms: [#TransferAct & {kind: "grant", binding: "b0"}, #TransferAssertion & {binding: "b1", value: "Bronze hall"}]}
			m3: {atoms: [#TransferAtom & {kind: "question", binding: "b0", operator: "eq", value: "permitted"}]}
			m5: {atoms: [#TransferAct & {kind: "grant", binding: "b2"}]}
			m6: {atoms: [#TransferAtom & {kind: "directive", binding: "b0", action: {verb: "check", object: "the grant register", condition: "before making entry promises"}}]}
			m7: {atoms: [#TransferAtom & {kind: "question", binding: "b0", operator: "eq", value: "permitted"}]}
			m10: {atoms: [#TransferAssertion & {binding: "b1", value: "Bronze hall"}]}
			m11: {atoms: [#TransferAtom & {kind: "question", binding: "b0", operator: "eq", value: "permitted"}]}
			m13: {atoms: [#TransferAtom & {kind: "revocation", binding: "b0", targetSource: "m1", targetKind: "grant"}]}
			m15: {atoms: [#TransferAtom & {kind: "directive", binding: "b0", action: {verb: "check", object: "the grant register", condition: "before making entry promises"}}]}
		}
		control: {kind: "fault", mode: "omit-kind", span: "m13", binding: "b0", targetKind: "revocation"}
	}
	"08-date-conflict": {
		subject:          "Hazel symposium", room:             "Maple hall", property:           "effective-date", scope: "same one-day symposium"
		secondarySubject: "Hazel briefing", secondaryProperty: "effective-date", secondaryScope: "separate briefing"
		target:           "2032-09-14", secondaryTarget:       "2032-09-18", states: {w0: "contested", w1: "contested"}
		messages: {
			m1:  "The one-day Hazel symposium is on 2032-09-14 at Maple hall. This is my current scheduling notice. It describes a single event, not a two-day programme."
			m3:  "Is the Hazel symposium on 2032-09-14? I am checking which notice the travel worksheet used. This question should not be treated as a third scheduling notice."
			m4:  "My current notice gives the same one-day Hazel symposium date as 2032-09-15, at the same Maple hall venue. My scheduling authority is the same as Leah's. No supersession or rescheduling between the notices has been established here."
			m5:  "The separate Hazel briefing is on 2032-09-18. It has its own booking and is not the symposium described by the two notices. Its date can remain usable while the symposium notices disagree."
			m6:  "For the symposium date, check the calendar before making travel plans. A newer timestamp on a copied notice does not itself resolve the difference. The original notices need to remain visible."
			m7:  "Is the symposium on 2032-09-14? I am asking about the conflicting record, not choosing a winner. The venue agreement does not settle the date disagreement."
			m10: "The Hazel symposium venue remains Maple hall. Both scheduling notices name that venue. There is no reason to hide this unaffected location merely because their dates conflict."
			m11: "My hunch is that 2032-09-15 is the Hazel symposium date because that notice reached me later. I have not found a supersession or rescheduling record. The hunch is not an additional calendar observation."
			m13: "My current Hazel symposium notice still gives 2032-09-14. I have not established that it supersedes Owen's notice. This is a repeat of the original scheduling position, not a new resolution."
			m14: "My notice still gives 2032-09-15 for the Hazel symposium. It does not cancel Leah's notice or create a second event. The equal-authority disagreement remains unresolved."
			m15: "For the symposium date, check the calendar before making travel plans. The current source record still contains both notices. Repetition and later arrival do not establish which date is right."
		}
		reference: {
			m1: {atoms: [#TransferAssertion & {binding: "b0", value: "2032-09-14"}, #TransferAssertion & {binding: "b1", value: "Maple hall"}]}
			m3: {atoms: [#TransferAtom & {kind: "question", binding: "b0", operator: "eq", value: "2032-09-14"}]}
			m4: {atoms: [#TransferAssertion & {binding: "b0", value: "2032-09-15"}, #TransferAssertion & {binding: "b1", value: "Maple hall"}]}
			m5: {atoms: [#TransferAssertion & {binding: "b2", value: "2032-09-18"}]}
			m6: {atoms: [#TransferAtom & {kind: "directive", binding: "b0", action: {verb: "check", object: "the calendar", condition: "before making travel plans"}}]}
			m7: {atoms: [#TransferAtom & {kind: "question", binding: "b0", operator: "eq", value: "2032-09-14"}]}
			m10: {atoms: [#TransferAssertion & {binding: "b1", value: "Maple hall"}]}
			m11: {annotations: [{kind: "speculation", binding: "b0", operator: "eq", value: "2032-09-15", quote: "My hunch is that 2032-09-15 is the Hazel symposium date because that notice reached me later."}]}
			m13: {atoms: [#TransferAssertion & {binding: "b0", value: "2032-09-14"}]}
			m14: {atoms: [#TransferAssertion & {binding: "b0", value: "2032-09-15"}]}
			m15: {atoms: [#TransferAtom & {kind: "directive", binding: "b0", action: {verb: "check", object: "the calendar", condition: "before making travel plans"}}]}
		}
		control: {kind: "fault", mode: "omit-origin-world", span: "m1", binding: "b0"}
	}
	"09-local-date-revision": {
		subject:          "Iris workshop", room:              "Willow studio", property:        "effective-date", scope: "one-day workshop"
		secondarySubject: "Iris briefing", secondaryProperty: "effective-date", secondaryScope: "separate briefing"
		target:           "2032-10-14", secondaryTarget:      "2032-10-18", states: {w0: "supported", w1: "opposed"}
		messages: {
			m1:  "The Iris workshop is on 2032-10-14 at Willow studio. This paragraph carries both the date and the venue. A later correction should identify which part it changes rather than silently retiring the whole paragraph."
			m3:  "Is the Iris workshop on 2032-10-14? I am checking the itinerary against the source note. The question is not a separate scheduling decision."
			m4:  "A room inventory for another building was attached to the meeting invitation. It concerns equipment storage rather than the Iris workshop. The attachment is not a venue correction."
			m5:  "The separate Iris briefing is on 2032-10-18. That date belongs to the briefing booking. It is not another proposed date for the workshop."
			m6:  "For the workshop date, check the calendar before making travel plans. A paragraph can carry several independently useful properties. The check is about the date rather than a request to discard the venue."
			m7:  "Is 2032-10-14 the date currently recorded for the Iris workshop? I am looking at m1. I am not claiming that the attached inventory answers the date question."
			m10: "The Iris workshop venue remains Willow studio. There is no venue move in this correspondence. The date and room fields should stay distinguishable."
			m11: "Is the workshop still on 2032-10-14? I heard a calendar correction was being prepared. That question alone does not establish a replacement date."
			m13: "The Iris workshop date is now 2032-10-16, replacing only the date assertion in m1. This is an explicit date correction under the same scheduling authority. The venue clause in m1 and the separate briefing booking are not superseded."
			m14: "The inventory attachment still concerns another building's equipment. It has no role in the date correction. The correction's target is the date assertion identified in m13."
			m15: "For the workshop date, check the calendar before making travel plans. The correction can now be followed from the earlier note. This repeats the source-use request, not a second rescheduling."
		}
		reference: {
			m1: {atoms: [#TransferAssertion & {binding: "b0", value: "2032-10-14"}, #TransferAssertion & {binding: "b1", value: "Willow studio"}]}
			m3: {atoms: [#TransferAtom & {kind: "question", binding: "b0", operator: "eq", value: "2032-10-14"}]}
			m5: {atoms: [#TransferAssertion & {binding: "b2", value: "2032-10-18"}]}
			m6: {atoms: [#TransferAtom & {kind: "directive", binding: "b0", action: {verb: "check", object: "the calendar", condition: "before making travel plans"}}]}
			m7: {atoms: [#TransferAtom & {kind: "question", binding: "b0", operator: "eq", value: "2032-10-14"}]}
			m10: {atoms: [#TransferAssertion & {binding: "b1", value: "Willow studio"}]}
			m11: {atoms: [#TransferAtom & {kind: "question", binding: "b0", operator: "eq", value: "2032-10-14"}]}
			m13: {atoms: [#TransferAtom & {kind: "supersession", binding: "b0", targetSource: "m1", targetKind: "assertion"}, #TransferAssertion & {binding: "b0", value: "2032-10-16"}]}
			m15: {atoms: [#TransferAtom & {kind: "directive", binding: "b0", action: {verb: "check", object: "the calendar", condition: "before making travel plans"}}]}
		}
		control: {kind: "equivalent", mode: "duplicate", span: "m1", binding: "b0"}
	}
	"10-question-not-confirmation": {
		subject:          "Juniper seminar", room:               "Aspen room", property:           "effective-date", scope: "one-day seminar"
		secondarySubject: "Juniper briefing", secondaryProperty: "effective-date", secondaryScope: "separate briefing"
		target:           "2032-11-14", secondaryTarget:         "2032-11-18", states: {w0: "unestablished", w1: "unestablished"}, missingParent: true
		messages: {
			m1:  "The Juniper seminar venue is Aspen room. Its date is not established in this packet. The room reservation and the date search should not be mistaken for one indivisible fact."
			m3:  "Is the Juniper seminar on 2032-11-14? I am asking because that value appears in a draft travel worksheet. I have not confirmed it against a calendar entry."
			m4:  "A different seminar used a similar invitation design. Its printing records are not a schedule for the Juniper seminar. The similar headings explain why the paperwork was filed together."
			m5:  "The separate Juniper briefing is on 2032-11-18. Its booking is established independently of the seminar-date question in this conversation. It should not be borrowed as the seminar date."
			m6:  "For the Juniper seminar date, check the calendar before making travel plans. This is a source-use request about the date. It does not assign a value or create a new booking."
			m7:  "That was provisional in the earlier note I replied to. The parent is absent from this packet, and I did not name the event or value again. The statement cannot identify which booking was provisional by itself."
			m10: "Aspen room remains the Juniper seminar venue. That location was already established separately. It can stay visible while the date is unestablished in this supplied packet."
			m11: "Is 2032-11-14 the Juniper seminar date? I still want the calendar source rather than another copy of the question. This is not an affirmation that the date is correct."
			m13: "The Juniper seminar date is still not established in these notes. We have not supplied the calendar finding in this thread. This describes the packet's coverage rather than anyone's complete personal knowledge."
			m14: "The similar invitation belonged to a different seminar. Its printing history has not turned into a Juniper booking. The missing parent reference also remains unavailable rather than guessed into this event."
			m15: "For the seminar date, check the calendar before making travel plans. That repeats the earlier request while the source finding remains absent here. The request itself does not settle the date."
		}
		reference: {
			m1: {atoms: [#TransferAssertion & {binding: "b1", value: "Aspen room"}]}
			m3: {atoms: [#TransferAtom & {kind: "question", binding: "b0", operator: "eq", value: "2032-11-14"}]}
			m5: {atoms: [#TransferAssertion & {binding: "b2", value: "2032-11-18"}]}
			m6: {atoms: [#TransferAtom & {kind: "directive", binding: "b0", action: {verb: "check", object: "the calendar", condition: "before making travel plans"}}]}
			m10: {atoms: [#TransferAssertion & {binding: "b1", value: "Aspen room"}]}
			m11: {atoms: [#TransferAtom & {kind: "question", binding: "b0", operator: "eq", value: "2032-11-14"}]}
			m15: {atoms: [#TransferAtom & {kind: "directive", binding: "b0", action: {verb: "check", object: "the calendar", condition: "before making travel plans"}}]}
		}
		control: {kind: "fault", mode: "add-world", span: "m3", binding: "b0", atom: #TransferAssertion & {binding: "b0", value: "2032-11-14"}}
	}
	"11-unresolved-provisional": {
		subject:          "Laurel workshop", room:              "Juniper studio", property:       "effective-date", scope: "one-day workshop"
		secondarySubject: "Laurel briefing", secondaryProperty: "effective-date", secondaryScope: "separate briefing"
		target:           "2032-12-14", secondaryTarget:        "2032-12-18", states: {w0: "supported", w1: "supported"}
		messages: {
			m1:  "The Laurel workshop date is 2032-12-14 and the Laurel briefing date is 2032-12-18. Exactly one of these dates is provisional, but this note does not identify which one. The shared venue is Juniper studio."
			m3:  "Is the Laurel workshop on 2032-12-14? I am checking the reported value, not claiming that its provisional status has been resolved. The exactly-one qualification belongs with the pair of dates."
			m4:  "The fundraiser paperwork has its own date and location. It is not the Laurel workshop or briefing. Similar calendar colours do not make those events the same booking."
			m5:  "The Laurel briefing is recorded as 2032-12-18. This repeats the value in m1 and does not say which of the two dates is provisional. It is not another independent calendar confirmation."
			m6:  "For the workshop date, check the calendar before making travel plans. The request is about finding a reliable calendar source. It should not turn both reported dates into personally unknown values."
			m7:  "Is the workshop on 2032-12-14? I am asking about its reported date, with the unresolved qualifier still in place. This question is not a statement that either date is final."
			m10: "The shared Laurel venue remains Juniper studio. The unknown identity of the provisional date does not make the venue uncertain. The location record has not changed during the discussion."
			m11: "Is 2032-12-14 still the reported Laurel workshop date? I am not asking the system to guess which event has the provisional booking. The missing identity is a separate qualification on the two known reported values."
			m13: "The Laurel workshop still has reported date 2032-12-14 and the briefing 2032-12-18. Exactly one of these dates remains provisional, and its identity is still unmarked here. This is not a resolution or a rescheduling."
			m14: "The fundraiser calendar remains a different event's record. It cannot identify the provisional Laurel booking. Its separate paperwork stays available without being treated as another workshop notice."
			m15: "For the workshop date, check the calendar before making travel plans. The two reported values and exactly-one qualifier remain together. Repeating the request does not create another confirmation."
		}
		reference: {
			m1: {atoms: [#TransferAssertion & {binding: "b0", value: "2032-12-14"}, #TransferAssertion & {binding: "b2", value: "2032-12-18"}, #TransferAssertion & {binding: "b1", value: "Juniper studio"}, #TransferAtom & {kind: "qualifier", operator: "one-provisional", alternatives: ["b0", "b2"]}]}
			m3: {atoms: [#TransferAtom & {kind: "question", binding: "b0", operator: "eq", value: "2032-12-14"}]}
			m5: {atoms: [#TransferAssertion & {binding: "b2", value: "2032-12-18"}]}
			m6: {atoms: [#TransferAtom & {kind: "directive", binding: "b0", action: {verb: "check", object: "the calendar", condition: "before making travel plans"}}]}
			m7: {atoms: [#TransferAtom & {kind: "question", binding: "b0", operator: "eq", value: "2032-12-14"}]}
			m10: {atoms: [#TransferAssertion & {binding: "b1", value: "Juniper studio"}]}
			m11: {atoms: [#TransferAtom & {kind: "question", binding: "b0", operator: "eq", value: "2032-12-14"}]}
			m13: {atoms: [#TransferAssertion & {binding: "b0", value: "2032-12-14"}, #TransferAssertion & {binding: "b2", value: "2032-12-18"}, #TransferAtom & {kind: "qualifier", operator: "one-provisional", alternatives: ["b0", "b2"]}]}
			m15: {atoms: [#TransferAtom & {kind: "directive", binding: "b0", action: {verb: "check", object: "the calendar", condition: "before making travel plans"}}]}
		}
		control: {kind: "equivalent", mode: "qualifier-layout", span: "m1", binding: "b0"}
	}
	"12-door-is-not-permission": {
		subject: "Moss session visitors", room: "Hazel hall", property: "permission", scope: "booked visitors under grant m1", time: "2032-11-20", values: ["permitted", "forbidden"]
		secondarySubject: "Moss session staff", secondaryProperty: "permission", secondaryScope: "staff under grant m5", secondaryTime: "2032-11-20", secondaryValues: ["permitted", "forbidden"]
		target: "permitted", secondaryTarget: "permitted", states: {w0: "supported", w1: "supported"}, topic: "permission-evidence-use", missingParent: true
		messages: {
			m1:  "I grant booked visitors entry permission for the Moss session on 2032-11-20. The venue is Hazel hall. This is a session-scoped normative grant, separate from observations about physical entrances."
			m3:  "Are booked visitors permitted entry under the Moss grant? I want to know what the authorization says. I am not reporting a door test in this question."
			m4:  "The service door used by delivery workers was locked during cleaning. It is a physical observation about another entrance. It is not a revocation of the booked-visitor grant for the Moss session."
			m5:  "I grant staff entry permission for the Moss session on 2032-11-20 under this staff grant. That authorization is separate from the visitor grant. It does not tell us which entrance a delivery worker used."
			m6:  "For visitor authorization, check the grant register before making entry promises. A door report and a permission grant are different kinds of information. The register is the source for the scoped authorization."
			m7:  "That access was stopped in the earlier note I replied to. The parent is missing, and this reply does not identify a group, event, or whether access meant a door or a permission rule. It cannot target a particular Moss grant on its own."
			m10: "The Moss session venue remains Hazel hall. The service-door cleaning did not move the event. The location record remains separately useful."
			m11: "Are booked visitors forbidden entry to the Moss session? I wondered because I heard about the service door. This is a question about permission, not a rule or an observation establishing a prohibition."
			m13: "There is no revocation of the visitor grant in m1 in this update. The cleaning report has not been turned into an authorization change. The staff grant is also untouched."
			m14: "The locked service door was still a delivery entrance under the cleaning arrangement. It was not a test of the visitor permission record. The original door report remains available in m4 with that scope."
			m15: "For visitor authorization, check the grant register before making entry promises. This repeats the earlier source-use request. It does not infer a permission rule from the physical door condition."
		}
		reference: {
			m1: {atoms: [#TransferAct & {kind: "grant", binding: "b0"}, #TransferAssertion & {binding: "b1", value: "Hazel hall"}]}
			m3: {atoms: [#TransferAtom & {kind: "question", binding: "b0", operator: "eq", value: "permitted"}]}
			m5: {atoms: [#TransferAct & {kind: "grant", binding: "b2"}]}
			m6: {atoms: [#TransferAtom & {kind: "directive", binding: "b0", action: {verb: "check", object: "the grant register", condition: "before making entry promises"}}]}
			m10: {atoms: [#TransferAssertion & {binding: "b1", value: "Hazel hall"}]}
			m11: {atoms: [#TransferAtom & {kind: "question", binding: "b0", operator: "eq", value: "forbidden"}]}
			m15: {atoms: [#TransferAtom & {kind: "directive", binding: "b0", action: {verb: "check", object: "the grant register", condition: "before making entry promises"}}]}
		}
		control: {kind: "fault", mode: "add-world", span: "m11", binding: "b0", atom: #TransferAssertion & {binding: "b0", value: "forbidden"}}
	}
}
