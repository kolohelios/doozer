package understanding

// New source texts and rubrics, authored before this experiment's live calls.
// Opaque source IDs avoid teaching the linker the fixture partition or roles.
cases: {
	"payout-recovery": #Case & {
		synthetic: true
		question:  "Can Orchid's on-call engineer rerun a failed payout job, and what precautions depend on the execution path?"
		sources: {
			"d-f4": {kind: "document", anchor: "fixture://holdout/d-f4", saidAt: "2026-07-01T09:00:00Z", text: "Orchid payout recovery is safe to rerun."}
			"d-a9": {kind: "code", anchor: "fixture://holdout/d-a9", saidAt: "2026-07-02T09:00:00Z", text: "Orchid ledger postings use a payout-id uniqueness constraint. The email delivery step is outside that transaction."}
			"d-13": {kind: "observation", anchor: "fixture://holdout/d-13", saidAt: "2026-07-03T09:00:00Z", text: "In Orchid's production batch, repeating one failed payout sent two remittance emails; the ledger contained one posting."}
			"d-c8": {kind: "document", anchor: "fixture://holdout/d-c8", saidAt: "2026-07-04T09:00:00Z", text: "The Orchid recovery command --ledger-only bypasses email sending. This switch is not read by the background retry scheduler."}
			"d-77": {kind: "conversation", anchor: "fixture://holdout/d-77", saidAt: "2026-07-05T09:00:00Z", text: "Can the scheduler use that ledger-only switch so all automatic retries avoid email?"}
			"d-b2": {kind: "conversation", anchor: "fixture://holdout/d-b2", saidAt: "2026-07-05T09:01:00Z", text: "No.", replyTo: "d-77"}
			"d-26": {kind: "conversation", anchor: "fixture://holdout/d-26", saidAt: "2026-07-06T09:00:00Z", text: "The remittance incident says a repeat produced two emails.", replyTo: "d-13"}
		}
		checks: [
			{id: "effects-separated", requirement: "Distinguish payout-id ledger uniqueness from nontransactional email delivery; the production repeat sent duplicate emails but one ledger posting.", evidence: ["d-a9", "d-13"]},
			{id: "path-boundary", requirement: "Limit the email suppression switch to the recovery command; it does not protect the background scheduler. Interpret No against that proposed extension, not as a global ban on payout recovery.", evidence: ["d-c8", "d-77", "d-b2"]},
			{id: "qualified-guidance", requirement: "Replace blanket rerun safety with execution-path-specific guidance and retain the incident as a material caveat; do not simply declare all recovery unsafe.", evidence: ["d-f4", "d-13", "d-c8"]},
			{id: "dependent-retelling", requirement: "Do not count the retelling as an additional independent production incident or stronger corroboration. It may be omitted from the compact answer if it adds no new meaning.", evidence: ["d-13", "d-26"]},
		]
	}
	"archive-access": #Case & {
		synthetic: true
		question:  "What should a curator tell an external visitor about unescorted Cedar archive access on June 18 and in normal weeks after June 19?"
		sources: {
			"d-02": {kind: "document", anchor: "fixture://holdout/d-02", saidAt: "2026-06-01T09:00:00Z", text: "Cedar reading room visitors may examine catalog boxes without an escort after check-in."}
			"d-8e": {kind: "document", anchor: "fixture://holdout/d-8e", saidAt: "2026-06-15T09:00:00Z", text: "On June 18 only, mold remediation closes Cedar's main reading room. Booked visitors check in at the annex and remain with an archivist. The normal room reopens June 19."}
			"d-51": {kind: "observation", anchor: "fixture://holdout/d-51", saidAt: "2026-06-18T09:00:00Z", text: "Two staff researchers entered the annex unescorted during the June 18 equipment drill under a staff-only exception."}
			"d-e3": {kind: "conversation", anchor: "fixture://holdout/d-e3", saidAt: "2026-06-18T09:01:00Z", text: "So booked external visitors can also use the annex unescorted on June 18?"}
			"d-9b": {kind: "conversation", anchor: "fixture://holdout/d-9b", saidAt: "2026-06-18T09:02:00Z", text: "No. The drill exception applies only to staff researchers.", replyTo: "d-e3"}
			"d-34": {kind: "document", anchor: "fixture://holdout/d-34", saidAt: "2026-06-18T10:00:00Z", text: "From June 19 the normal reading room visitor rules resume; original manuscript handling still requires an archivist even in normal weeks."}
			"d-6a": {kind: "conversation", anchor: "fixture://holdout/d-6a", saidAt: "2026-06-18T10:01:00Z", text: "Stop."}
		}
		checks: [
			{id: "temporary-exception", requirement: "On June 18 booked external visitors use annex check-in and remain with an archivist; this is a date-bounded rule, not a permanent annex move.", evidence: ["d-8e"]},
			{id: "normal-access", requirement: "From June 19 normal room access resumes: catalog-box examination can be unescorted after check-in. Preserve check-in rather than saying all access is unrestricted.", evidence: ["d-02", "d-34"]},
			{id: "manuscript-exception", requirement: "Retain the separate original-manuscript handling requirement for an archivist even in normal weeks; do not merge it into the catalog-box permission.", evidence: ["d-34", "d-02"]},
			{id: "practice-not-permission", requirement: "Staff-only drill behavior does not authorize unescorted external visitor access; the explicit reply rejects extending the exception.", evidence: ["d-51", "d-e3", "d-9b"]},
			{id: "unknown-referent", requirement: "Preserve the detached Stop as unresolved context without inventing its target, cancelling all access, or manufacturing a task queue.", evidence: ["d-6a"]},
		]
	}
	"telemetry-compatibility": #Case & {
		synthetic: true
		question:  "Is it safe to add an optional zone label to the Quill telemetry payload, and which consumers and rollout conditions matter?"
		sources: {
			"d-45": {kind: "document", anchor: "fixture://holdout/d-45", saidAt: "2026-08-01T09:00:00Z", text: "Adding optional labels to Quill telemetry does not break consumers."}
			"d-0c": {kind: "code", anchor: "fixture://holdout/d-0c", saidAt: "2026-08-02T09:00:00Z", text: "The field monitor firmware rejects any telemetry object with an unrecognized label key."}
			"d-aa": {kind: "observation", anchor: "fixture://holdout/d-aa", saidAt: "2026-08-03T09:00:00Z", text: "The green Quill contract suite exercises desktop dashboard clients only. It does not execute field monitor firmware."}
			"d-69": {kind: "document", anchor: "fixture://holdout/d-69", saidAt: "2026-08-04T09:00:00Z", text: "Gate the zone label by consumer revision. Upgrade field monitor firmware before enabling zone for those devices; retain the old payload format until their upgrade is verified."}
			"d-ce": {kind: "observation", anchor: "fixture://holdout/d-ce", saidAt: "2026-08-05T09:00:00Z", text: "A format-preserving sampling-cadence change caused gaps in a Quill alert stream despite passing its JSON schema checks."}
			"d-12": {kind: "conversation", anchor: "fixture://holdout/d-12", saidAt: "2026-08-06T09:00:00Z", text: "The green contract suite proves backward compatibility."}
			"d-88": {kind: "conversation", anchor: "fixture://holdout/d-88", saidAt: "2026-08-06T09:01:00Z", text: "No. Not for the field monitors.", replyTo: "d-12"}
		}
		checks: [
			{id: "consumer-boundary", requirement: "Optional labels are not universally compatible: strict field-monitor firmware rejects unknown keys. Qualify the broad guide by the actual consumer contract.", evidence: ["d-45", "d-0c"]},
			{id: "test-coverage", requirement: "Passing desktop dashboard checks does not establish field monitor compatibility; retain the contextual objection to the broad claim.", evidence: ["d-aa", "d-12", "d-88"]},
			{id: "rollout-order", requirement: "Gate by consumer revision, upgrade and verify field monitor firmware before enabling zone there, and retain the old format until that prerequisite is met.", evidence: ["d-69"]},
			{id: "behavioral-contract", requirement: "Schema preservation does not prove behavioral compatibility; preserve the sampling-cadence counterexample without conflating it with unknown-field rejection.", evidence: ["d-ce", "d-0c"]},
			{id: "no-inferred-completion", requirement: "Do not invent completed firmware upgrades, passing monitor tests, or rollout approval. State the documented conditions without claiming they have been met.", evidence: ["d-69", "d-aa"]},
		]
	}
}
