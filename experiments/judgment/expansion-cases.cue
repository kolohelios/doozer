package judgment

// All sources are synthetic. Expectations are proposed controls, not human gold.
expansionFamilies: {
	"origin-recovery": {
		question: "What does this packet establish about whether the two notes have distinct first-hand origins? Preserve uncertainty when lineage is missing; rejection of an assertion is not proof of its opposite."
		propositions: [{id: "p0", text: "The two notes have distinct first-hand observation origins.", scope: "recovery-notes", guard: "origins", subjects: ["d1", "d2"]}]
		initialExpected: {p0: "unestablished"}
		initial: [
			{id: "d1", scope: "recovery-notes", origin: "run-a", text: "I executed recovery drill A and verified the restored row counts in its isolated database. This note is my first-hand record of that run. It is not a report about any other operator's test."},
			{id: "d2", scope: "recovery-notes", originFrom: "d3", text: "This second recovery note refers to the run log attached as d3, but the log is not included in the current packet. A separate note identity alone does not establish whether this was another first-hand run or a retelling. Keep that origin unresolved until the log is available."},
		]
		branches: {
			v1: {expected: {p0: "supported"}, reason: "The retrieved log declares a distinct first-hand origin for d2.", catalog: [
				{id: "d3", scope: "recovery-notes", origin: "run-b", text: "The run behind note d2 is recovery drill B, independently executed against a separately initialized isolated database. Its restored row counts were verified in this log. It is a distinct first-hand run, not a retelling of drill A."},
			]}
			v2: {expected: {p0: "opposed"}, reason: "The retrieved lineage identifies both notes as reports of the same run.", catalog: [
				{id: "d3", scope: "recovery-notes", origin: "run-a", derivedFrom: ["d1"], text: "The run behind note d2 is recovery drill A from d1. This log is a copy of that earlier run record, not a second execution. These two notes therefore share one first-hand observation origin."},
			]}
			v3: {expected: {p0: "unestablished"}, reason: "The referenced log is unavailable. Missing lineage proves neither distinct nor shared origins.", catalog: []}
		}
	}
	"environment-scope": {
		question: "What does this evidence establish about the production-west scheduler reading --quiet-mail? Do not transfer staging or another region's behavior into production-west."
		propositions: [{id: "p0", text: "The production-west scheduler reads --quiet-mail.", scope: "production-west", guard: "none", subjects: []}]
		initialExpected: {p0: "unestablished"}
		initial: [
			{id: "d1", scope: "staging", text: "The staging scheduler reads --quiet-mail during automatic recovery. This test concerns staging only and is not evidence of the deployed production-west scheduler's behavior. Ledger write protection and email behavior are separate properties."},
			{id: "d2", scope: "production-west", references: ["d3"], text: "The deployment result relevant to production-west is linked as d3. Its contents are not reproduced in this packet. Do not use the staging test as a substitute for reading the deployment result."},
		]
		branches: {
			v1: {expected: {p0: "supported"}, reason: "The retrieved record explicitly confirms the target environment.", catalog: [
				{id: "d3", scope: "production-west", text: "The deployed production-west scheduler reads --quiet-mail on automatic recovery. I verified that behavior in the production-west deployment record. This confirmation concerns that region, not every scheduler deployment."},
			]}
			v2: {expected: {p0: "opposed"}, reason: "The retrieved record explicitly states the incompatible target-environment behavior.", catalog: [
				{id: "d3", scope: "production-west", text: "The deployed production-west scheduler does not read --quiet-mail on automatic recovery. The option remains confined to the operator command there. This is a production-west result, not a statement that staging failed."},
			]}
			v3: {expected: {p0: "unestablished"}, reason: "The linked result covers production-east; production-west remains unestablished.", catalog: [
				{id: "d3", scope: "production-east", text: "The production-east scheduler reads --quiet-mail on automatic recovery. This record covers production-east only and does not establish production-west behavior. Region identity must survive any consolidation of these notes."},
			]}
		}
	}
	"conflict-and-withdrawal": {
		question: "What does the current packet establish about normal Meadow catalog-room access on April 10? Do not resolve equally current conflicting notices by recency alone. Withdrawal of an assurance does not assert its opposite."
		propositions: [{id: "p0", text: "Normal Meadow catalog-room access is available on April 10.", scope: "meadow-april-10", guard: "none", subjects: []}]
		initialExpected: {p0: "supported"}
		initial: [
			{id: "d1", scope: "meadow-april-10", text: "This notice confirms that normal Meadow catalog-room access is available on April 10. Catalog boxes may be examined after the ordinary check-in procedure. Original manuscripts continue to require an archivist."},
			{id: "d2", scope: "meadow-april-10", references: ["d3"], text: "A further availability notice is linked as d3, but I have not copied its contents into this packet. The visible notice is not a guarantee that the linked material agrees with it. Keep this known coverage gap explicit until the further notice is read."},
		]
		branches: {
			v1: {expected: {p0: "opposed"}, reason: "The new same-scope notice explicitly supersedes the old assurance and says access is unavailable.", catalog: [
				{id: "d3", scope: "meadow-april-10", supersedes: ["d1"], text: "This notice replaces d1 for April 10. Normal Meadow catalog-room access is not available on April 10 because the room is closed for remediation. The earlier availability assurance is historical, not a current instruction."},
			]}
			v2: {expected: {p0: "contested"}, reason: "Two same-scope notices conflict without a declared supersession or authority resolution.", catalog: [
				{id: "d3", scope: "meadow-april-10", text: "This notice states that normal Meadow catalog-room access is not available on April 10. It is issued at the same authority level as d1, and this packet does not establish that either notice supersedes the other. Preserve the conflict rather than invent a settled visitor rule."},
			]}
			v3: {expected: {p0: "unestablished"}, reason: "The assurance is withdrawn without a positive or negative availability finding.", catalog: [
				{id: "d3", scope: "meadow-april-10", supersedes: ["d1"], text: "This notice withdraws d1's assurance of normal April 10 access pending inspection. It does not establish that the room is open or that it is closed on that date. The older assurance is no longer current, but uncertainty must not be converted into an opposite factual instruction."},
			]}
		}
	}
	"parent-recovery": {
		question: "What location and effective date does this staff-only exception apply to? Distinguish a source's statement time from the exception's validity and preserve any detail that remains unknown. This answer is not evidence of durable storage."
		propositions: [
			{id: "p0", text: "The staff-only exception applies at Oriel annex.", scope: "exception-context", guard: "none", subjects: []},
			{id: "p1", text: "The staff-only exception applies on May 16.", scope: "exception-context", guard: "none", subjects: []},
		]
		initialExpected: {p0: "unestablished", p1: "unestablished"}
		initial: [
			{id: "d1", scope: "exception-context", replyTo: "d3", saidAt: "2027-05-15T09:00:00Z", text: "No, that exception is limited to staff participating in the maintenance drill. It does not extend visitor permissions. The location and effective period were in the parent message, which is not included here; do not infer them from when I sent this reply."},
		]
		branches: {
			v1: {expected: {p0: "supported", p1: "supported"}, reason: "The recovered parent supplies both details, making a previously qualified answer stale if left unchanged.", catalog: [
				{id: "d3", scope: "exception-context", saidAt: "2027-05-14T09:00:00Z", text: "The staff maintenance-drill exception applies at Oriel annex on May 16 only. These are its location and effective date, not the timestamp of a later reply. I am asking whether that staff arrangement also gives booked external visitors unescorted access."},
			]}
			v2: {expected: {p0: "supported", p1: "unestablished"}, reason: "The parent establishes location but deliberately leaves the effective date unknown.", catalog: [
				{id: "d3", scope: "exception-context", saidAt: "2027-05-14T09:00:00Z", text: "The staff maintenance-drill exception applies at Oriel annex. Its effective date has not been established in this packet and is not the date of this message. Keep the known location without inventing a date or discarding that partial meaning."},
			]}
			v3: {expected: {p0: "unestablished", p1: "unestablished"}, reason: "No parent can be retrieved; the source still supplies staff-only scope but neither requested detail.", catalog: []}
		}
	}
}
