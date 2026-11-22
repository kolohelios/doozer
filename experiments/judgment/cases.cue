package judgment

// Fresh, controlled synthetic packets. References are proposed fixture expectations,
// not independently adjudicated human gold. Variant identifiers never enter requests.
families: {
	"automatic-recovery": {
		candidate: "Aster's production scheduler reads --quiet-mail on automatic recovery. Ledger postings remain deduplicated by bill ID."
		base: [
			{id: "d1", kind: "document", saidAt: "2027-01-05T09:00:00Z", text: "The Aster recovery guide distinguishes bill postings from outbound mail. A bill-id uniqueness constraint protects ledger writes on repeated execution. Mail is outside that transaction, so the guide must describe recovery paths separately rather than call every side effect idempotent."},
			{id: "d2", kind: "conversation", saidAt: "2027-01-06T09:00:00Z", replyTo: "d1", text: "The operator command has a --quiet-mail option for suppressing outbound mail during recovery. I am checking whether the production scheduler reads that option too. The manual command and automatic scheduler are separate execution paths, even though both can process the same bill."},
		]
		variants: {
			v1: {reference: "pass", reason: "The implementation reply explicitly confirms the scheduler behavior while preserving ledger protection.", extra: [{id: "d3", kind: "conversation", saidAt: "2027-01-07T09:00:00Z", replyTo: "d2", text: "I checked the deployed production scheduler: it does read --quiet-mail and suppresses outbound mail when that option is set on automatic recovery. The ledger uniqueness constraint is unchanged. This confirmation concerns the scheduler, not just the operator command."}]}
			v2: {reference: "fail", reason: "The same candidate extends an operator-only option to a scheduler that explicitly ignores it.", extra: [{id: "d3", kind: "conversation", saidAt: "2027-01-07T09:00:00Z", replyTo: "d2", text: "I checked the deployed production scheduler: it does not read --quiet-mail. The option suppresses mail only in the operator command, not on automatic recovery. The ledger uniqueness constraint is unchanged, so this correction must not retract the narrower ledger assurance."}]}
			v3: {reference: "fail", reason: "A staging experiment does not establish the asserted production behavior.", extra: [{id: "d3", kind: "conversation", saidAt: "2027-01-07T09:00:00Z", replyTo: "d2", text: "The staging scheduler experiment reads --quiet-mail, but that experiment has not been deployed to production. I have no verified result for production scheduler behavior in this packet. The operator command and ledger uniqueness constraint are unchanged."}]}
		}
	}
	"visitor-exception": {
		candidate: "Booked external visitors at Birch may examine catalog boxes without an escort during the October 4 drill after check-in."
		base: [
			{id: "d1", kind: "document", saidAt: "2027-10-01T09:00:00Z", text: "Birch is recording access arrangements for the October 4 equipment drill separately from its ordinary reading-room procedures. Catalog-box work and original-manuscript handling are different activities. Original manuscripts require an archivist throughout the drill regardless of any catalog-box exception."},
			{id: "d2", kind: "conversation", saidAt: "2027-10-02T09:00:00Z", replyTo: "d1", text: "Two staff researchers practiced entering the catalog area without an escort after check-in. Their drill report does not itself settle what booked external visitors may do. We need to read the actual visitor arrangement rather than infer permission from staff behavior."},
		]
		variants: {
			v1: {reference: "pass", reason: "The explicit drill arrangement includes booked external visitors for catalog-box work.", extra: [{id: "d3", kind: "document", saidAt: "2027-10-03T09:00:00Z", replyTo: "d2", text: "For the October 4 drill, booked external visitors may examine catalog boxes without an escort after check-in. This temporary catalog-box permission includes visitors, not just staff. Original-manuscript handling still requires an archivist."}]}
			v2: {reference: "fail", reason: "The explicit arrangement reserves unescorted access to staff.", extra: [{id: "d3", kind: "document", saidAt: "2027-10-03T09:00:00Z", replyTo: "d2", text: "For the October 4 drill, unescorted catalog-box access after check-in is a staff-only exception. Booked external visitors must remain with an archivist. Original-manuscript handling still requires an archivist for everyone."}]}
			v3: {reference: "fail", reason: "A proposed visitor extension was not an established permission.", extra: [{id: "d3", kind: "conversation", saidAt: "2027-10-03T09:00:00Z", replyTo: "d2", text: "Someone proposed extending the staff drill exception to booked visitors, but no visitor authorization is recorded in this packet. The staff practice report is not approval of that proposal. Please distinguish the suggested arrangement from an established visitor permission."}]}
		}
	}
	"firmware-coverage": {
		candidate: "The green Juniper contract suite executes battery-sensor firmware, not just desktop viewer clients."
		base: [
			{id: "d1", kind: "document", saidAt: "2027-02-01T09:00:00Z", text: "Juniper's zone-label rollout has desktop viewers and battery sensors as separate consumers. A green suite name alone does not identify which consumers were exercised. This thread records test coverage, not blanket deployment safety for every client."},
			{id: "d2", kind: "conversation", saidAt: "2027-02-02T09:00:00Z", replyTo: "d1", text: "The contract job is green for this revision. Before citing it for sensors, distinguish an actual firmware execution from a viewer test or a simulated sensor payload. The job title has been reused while its contents changed."},
		]
		variants: {
			v1: {reference: "pass", reason: "The suite description explicitly reports actual firmware execution in addition to viewers.", extra: [{id: "d3", kind: "document", saidAt: "2027-02-03T09:00:00Z", replyTo: "d2", text: "This green Juniper contract run executes battery-sensor firmware on the bench as well as desktop viewer clients. The sensor checks run the actual firmware binary, not a viewer's simulated payload. That is the coverage of this run, not proof of every deployment condition."}]}
			v2: {reference: "fail", reason: "The suite is explicitly desktop-only and does not execute firmware.", extra: [{id: "d3", kind: "document", saidAt: "2027-02-03T09:00:00Z", replyTo: "d2", text: "This green Juniper contract run executes desktop viewer clients only. It does not execute battery-sensor firmware. Sensor-shaped example payloads in a viewer test must not be described as firmware execution."}]}
			v3: {reference: "fail", reason: "Simulated sensor payloads do not establish actual firmware execution.", extra: [{id: "d3", kind: "document", saidAt: "2027-02-03T09:00:00Z", replyTo: "d2", text: "This green Juniper contract run exercises simulated battery-sensor payloads through desktop viewers. The packet does not establish whether the actual sensor firmware binary was executed. Describe the simulation without upgrading it to a firmware test."}]}
		}
	}
	"effective-time": {
		candidate: "On April 10 the Meadow catalog room uses its normal unescorted-after-check-in procedure. Original manuscripts still require an archivist."
		base: [
			{id: "d1", kind: "document", saidAt: "2027-03-01T09:00:00Z", text: "Meadow's normal catalog-room procedure permits unescorted catalog-box examination after check-in. Original manuscripts always require an archivist. Temporary closures can replace the normal catalog-room procedure for their stated validity window without changing the manuscript restriction."},
			{id: "d2", kind: "conversation", saidAt: "2027-04-10T08:00:00Z", text: "I received the closure notice on April 10, but receipt time is not its effective period. Use the dates in the notice rather than assume a message timestamp establishes reopening. The ordinary manuscript restriction is unchanged."},
		]
		variants: {
			v1: {reference: "pass", reason: "The notice ends the closure before the candidate's date.", extra: [{id: "d3", kind: "document", saidAt: "2027-04-08T09:00:00Z", replyTo: "d1", text: "The temporary catalog-room closure applies on April 8 and April 9 only. The normal room and its ordinary catalog-box procedure resume on April 10. Original manuscripts continue to require an archivist."}]}
			v2: {reference: "fail", reason: "The candidate's date remains within the explicit closure window.", extra: [{id: "d3", kind: "document", saidAt: "2027-04-08T09:00:00Z", replyTo: "d1", text: "The temporary catalog-room closure applies from April 8 through April 11 inclusive. Normal catalog-room access resumes on April 12, not April 10. Original manuscripts continue to require an archivist."}]}
			v3: {reference: "fail", reason: "Receipt time and an unconfirmed reopening do not justify the candidate's date-specific normal-access assertion.", extra: [{id: "d3", kind: "document", saidAt: "2027-04-08T09:00:00Z", replyTo: "d1", text: "A temporary catalog-room closure is in effect, but the effective end date is absent from this copy of the notice. The reopening date cannot be recovered from this packet. Original manuscripts continue to require an archivist."}]}
		}
	}
	"independent-evidence": {
		candidate: "The two recovery notes describe independent successful drills, not two retellings of one drill."
		base: [
			{id: "d1", kind: "observation", saidAt: "2027-06-01T09:00:00Z", origin: "run-a", text: "I executed recovery drill A against the isolated test database and verified its restored row counts. This is my first-hand record of that successful run. The drill says nothing about unrelated failure modes or a second operator's test."},
		]
		variants: {
			v1: {reference: "pass", reason: "Separate first-hand runs with distinct origins establish the controlled independence claim.", extra: [{id: "d2", kind: "observation", saidAt: "2027-06-02T09:00:00Z", origin: "run-b", text: "I executed a separate recovery drill B against a separately initialized isolated test database and verified its restored row counts. This successful run is not a repetition of the report of drill A. It is a second first-hand observation with its own run log."}]}
			v2: {reference: "fail", reason: "The second document explicitly derives from the first run.", extra: [{id: "d2", kind: "document", saidAt: "2027-06-02T09:00:00Z", origin: "run-a", derivedFrom: ["d1"], text: "This handbook note retells the successful recovery drill A from the earlier report. I did not execute another drill or collect a second first-hand result. A second document must not be counted as a second successful run."}]}
			v3: {reference: "fail", reason: "A distinct document identity without a recoverable origin is not proof of independent observation.", extra: [{id: "d2", kind: "conversation", saidAt: "2027-06-02T09:00:00Z", text: "I saw another note saying recovery was successful, but this copy does not record which run it describes or whether its author performed a drill. It may be a retelling. Do not infer a second independent result merely from this note's separate identity."}]}
		}
	}
	"epistemic-scope": {
		candidate: "The available evidence limits the exception to staff. Its location and effective date are not established here. This answer does not verify that a storage system retained the message."
		base: []
		variants: {
			v1: {reference: "pass", reason: "The parent is unavailable, the restriction is explicit, and the answer correctly limits its own verification claim.", extra: [{id: "d2", kind: "conversation", saidAt: "2027-05-15T09:00:00Z", replyTo: "d0", text: "No, that exception was limited to staff participating in the maintenance drill. It was not an extension of visitor permissions. Keep the restriction attached to the situation under discussion rather than carry it over to unrelated visits."}]}
			v2: {reference: "fail", reason: "The recovered parent supplies the location and date that the answer wrongly says are unestablished.", extra: [{id: "d0", kind: "conversation", saidAt: "2027-05-14T09:00:00Z", text: "The exception under discussion is the Oriel annex maintenance drill on May 16 only. The location and date are fixed; I am asking whether its staff access also authorizes unescorted external visitors there. This is not a question about other buildings or dates."}, {id: "d2", kind: "conversation", saidAt: "2027-05-15T09:00:00Z", replyTo: "d0", text: "No, that exception was limited to staff participating in the maintenance drill. It was not an extension of visitor permissions. Keep the restriction attached to the situation under discussion rather than carry it over to unrelated visits."}]}
			v3: {reference: "fail", reason: "The source contradicts staff-only scope; the self-limitation sentence remains legitimate.", extra: [{id: "d2", kind: "conversation", saidAt: "2027-05-15T09:00:00Z", replyTo: "d0", text: "The exception includes booked external visitors as well as staff participating in the drill. It is not a staff-only restriction. The location and effective date are in the unavailable parent, so do not infer those details from this message's timestamp."}]}
		}
	}
}
