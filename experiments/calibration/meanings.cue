package calibration

// Prospective answer contract, NOT a replacement for the frozen v1 rubric.
// Availability of a bundle is only a draft support proxy, not entailment proof.
meanings: {
	"payout-recovery": [
		{
			id:        "ledger-email-boundary", surface: "answer", applicability: "required"
			statement: "Separate payout-id ledger uniqueness from the email step outside that transaction."
			references: [{source: "heldout/d-a9", quote: "Orchid ledger postings use a payout-id uniqueness constraint. The email delivery step is outside that transaction."}]
			sufficient: [{id: "design-statement", allOf: [{source: "heldout/d-a9", quote: "Orchid ledger postings use a payout-id uniqueness constraint. The email delivery step is outside that transaction."}], note: "The design statement supports this boundary; one observed ledger posting alone would not establish the invariant."}]
		},
		{
			id:        "duplicate-email-risk", surface: "answer", applicability: "required"
			statement: "A production rerun demonstrated duplicate remittance email risk; do not present blanket rerun safety."
			references: [{source: "heldout/d-13", quote: "In Orchid's production batch, repeating one failed payout sent two remittance emails; the ledger contained one posting."}]
			sufficient: [{id: "production-incident", allOf: [{source: "heldout/d-13", quote: "In Orchid's production batch, repeating one failed payout sent two remittance emails; the ledger contained one posting."}], note: "The original incident suffices. Its retelling is not an additional required source or independent corroboration."}]
		},
		{
			id:        "manual-bypass", surface: "answer", applicability: "required"
			statement: "The documented recovery command's --ledger-only switch bypasses email sending."
			references: [{source: "heldout/d-c8", quote: "The Orchid recovery command --ledger-only bypasses email sending."}]
			sufficient: [{id: "command-documentation", allOf: [{source: "heldout/d-c8", quote: "The Orchid recovery command --ledger-only bypasses email sending."}], note: "Bound the mitigation to the named command, not all forms of recovery."}]
		},
		{
			id:        "scheduler-boundary", surface: "answer", applicability: "required"
			statement: "Do not extend the manual-switch mitigation to the background scheduler."
			references: [{source: "heldout/d-c8", quote: "This switch is not read by the background retry scheduler."}]
			sufficient: [
				{id: "explicit-implementation-boundary", allOf: [{source: "heldout/d-c8", quote: "The Orchid recovery command --ledger-only bypasses email sending. This switch is not read by the background retry scheduler."}], note: "This directly states the boundary; retrieving the later question and No is not necessary to convey it."},
				{id: "contextual-rejection", allOf: [{source: "heldout/d-77", quote: "Can the scheduler use that ledger-only switch so all automatic retries avoid email?"}, {source: "heldout/d-b2", quote: "No."}], note: "Alternative support for the stated rejection, using replyTo context. It is not a proof of every runtime side effect."},
			]
		},
		{
			id:        "delivery-certainty", surface: "answer", applicability: "if-mentioned"
			statement: "No protection from this switch does not establish that every automatic retry will deliver email. Use risk rather than unproven certainty."
			references: [{source: "heldout/d-c8", quote: "This switch is not read by the background retry scheduler."}, {source: "heldout/d-13", quote: "repeating one failed payout sent two remittance emails"}]
		},
		{
			id:        "echo-independence", surface: "answer", applicability: "if-mentioned"
			statement: "A retelling is not another independent incident. Two citations alone do not tell us whether independence was inflated."
			references: [{source: "heldout/d-26", quote: "The remittance incident says a repeat produced two emails."}, {source: "heldout/d-13", quote: "In Orchid's production batch, repeating one failed payout sent two remittance emails; the ledger contained one posting."}]
		},
	]
	"archive-access": [
		{
			id:        "temporary-procedure", surface: "answer", applicability: "required"
			statement: "On June 18 only, booked visitors use annex check-in and remain with an archivist."
			references: [{source: "heldout/d-8e", quote: "On June 18 only, mold remediation closes Cedar's main reading room. Booked visitors check in at the annex and remain with an archivist. The normal room reopens June 19."}]
			sufficient: [{id: "dated-notice", allOf: [{source: "heldout/d-8e", quote: "On June 18 only, mold remediation closes Cedar's main reading room. Booked visitors check in at the annex and remain with an archivist. The normal room reopens June 19."}], note: "The direct notice already establishes visitor escort requirements without needing the staff correction."}]
		},
		{
			id:        "normal-catalog-access", surface: "answer", applicability: "required"
			statement: "After the one-day closure, normal catalog-box access permits unescorted examination after check-in."
			references: [{source: "heldout/d-02", quote: "Cedar reading room visitors may examine catalog boxes without an escort after check-in."}, {source: "heldout/d-34", quote: "From June 19 the normal reading room visitor rules resume"}]
			sufficient: [
				{id: "explicit-resumption", allOf: [{source: "heldout/d-02", quote: "Cedar reading room visitors may examine catalog boxes without an escort after check-in."}, {source: "heldout/d-34", quote: "From June 19 the normal reading room visitor rules resume"}], note: "Normal policy plus explicit resumption; neither source alone describes the complete date-bound permission."},
				{id: "one-day-exception", allOf: [{source: "heldout/d-02", quote: "Cedar reading room visitors may examine catalog boxes without an escort after check-in."}, {source: "heldout/d-8e", quote: "On June 18 only, mold remediation closes Cedar's main reading room. Booked visitors check in at the annex and remain with an archivist. The normal room reopens June 19."}], note: "Draft inference from the one-day exception plus standing policy. Review whether this is sufficient; it does not establish the manuscript exception."},
			]
		},
		{
			id:        "manuscript-escort", surface: "answer", applicability: "required"
			statement: "Original manuscript handling still requires an archivist in normal weeks; do not merge it with catalog-box permission."
			references: [{source: "heldout/d-34", quote: "original manuscript handling still requires an archivist even in normal weeks."}]
			sufficient: [{id: "manuscript-restriction", allOf: [{source: "heldout/d-34", quote: "original manuscript handling still requires an archivist even in normal weeks."}], note: "The restriction is stated directly; the standing catalog policy supports a separate meaning."}]
		},
		{
			id:        "staff-scope", surface: "answer", applicability: "if-mentioned"
			statement: "If staff drill behavior is discussed, keep its staff-only scope; do not manufacture visitor permission or ambiguity from it."
			references: [{source: "heldout/d-51", quote: "Two staff researchers entered the annex unescorted during the June 18 equipment drill under a staff-only exception."}, {source: "heldout/d-8e", quote: "Booked visitors check in at the annex and remain with an archivist."}]
		},
		{
			id:        "unresolved-intervention", surface: "history", applicability: "retention-only"
			statement: "Retain the detached Stop without inventing a referent. An answer-only artifact cannot establish whether the knowledge/history layer retained it."
			references: [{source: "heldout/d-6a", quote: "Stop."}]
		},
	]
	"telemetry-compatibility": [
		{
			id:        "strict-consumer", surface: "answer", applicability: "required"
			statement: "The field monitor firmware rejects unrecognized label keys; additive does not imply universal compatibility."
			references: [{source: "heldout/d-0c", quote: "The field monitor firmware rejects any telemetry object with an unrecognized label key."}]
			sufficient: [{id: "firmware-contract", allOf: [{source: "heldout/d-0c", quote: "The field monitor firmware rejects any telemetry object with an unrecognized label key."}], note: "The actual consumer contract suffices to establish the exception; the broad guide is not required context."}]
		},
		{
			id:        "suite-scope", surface: "answer", applicability: "required"
			statement: "The green suite covers desktop dashboards only, not field monitor firmware."
			references: [{source: "heldout/d-aa", quote: "The green Quill contract suite exercises desktop dashboard clients only. It does not execute field monitor firmware."}]
			sufficient: [{id: "suite-description", allOf: [{source: "heldout/d-aa", quote: "The green Quill contract suite exercises desktop dashboard clients only. It does not execute field monitor firmware."}], note: "No merely rejects universal monitor proof; it does not by itself identify the suite's actual desktop-only coverage."}]
		},
		{
			id:        "rollout-order", surface: "answer", applicability: "required"
			statement: "Gate by consumer revision; upgrade and verify field monitors before enabling zone there, retaining the old format until then."
			references: [{source: "heldout/d-69", quote: "Gate the zone label by consumer revision. Upgrade field monitor firmware before enabling zone for those devices; retain the old payload format until their upgrade is verified."}]
			sufficient: [{id: "rollout-procedure", allOf: [{source: "heldout/d-69", quote: "Gate the zone label by consumer revision. Upgrade field monitor firmware before enabling zone for those devices; retain the old payload format until their upgrade is verified."}], note: "Preserve ordering and prerequisites, not just the existence of an upgrade."}]
		},
		{
			id:        "behavior-not-schema", surface: "answer", applicability: "required"
			statement: "A format-preserving cadence change still caused alert gaps; schema compatibility is not behavioral safety."
			references: [{source: "heldout/d-ce", quote: "A format-preserving sampling-cadence change caused gaps in a Quill alert stream despite passing its JSON schema checks."}]
			sufficient: [{id: "behavioral-counterexample", allOf: [{source: "heldout/d-ce", quote: "A format-preserving sampling-cadence change caused gaps in a Quill alert stream despite passing its JSON schema checks."}], note: "This counterexample is distinct from strict decoding; another source is not required to state it."}]
		},
		{
			id:        "no-inferred-completion", surface: "answer", applicability: "if-mentioned"
			statement: "Do not turn rollout prerequisites into invented completed upgrades, passing field tests, or approval."
			references: [{source: "heldout/d-69", quote: "Upgrade field monitor firmware before enabling zone for those devices; retain the old payload format until their upgrade is verified."}]
		},
		{
			id:        "desktop-safety-scope", surface: "answer", applicability: "if-mentioned"
			statement: "Desktop-only test coverage does not by itself prove broad desktop safety. Review ambiguous shorthand such as conditionally safe rather than force a binary label."
			references: [{source: "heldout/d-aa", quote: "The green Quill contract suite exercises desktop dashboard clients only. It does not execute field monitor firmware."}]
		},
	]
}
