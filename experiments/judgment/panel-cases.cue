package judgment

// Fresh prose, adapted to known failure categories. References are provisional.
panelCases: {
	"assurance-withdrawn": {
		controlFault: {span: "d2-p0", mode: "add-world", binding: "b0", atom: #PanelWorld & {binding: "b0", value: "forbidden"}}
		bindings: [
			{id: "b0", subject: "booked visitors", property: "permission", scope: "Lumen evening event", validTime: "2028-06-11", values: ["permitted", "forbidden"]},
			{id: "b1", subject: "Lumen evening event", property: "location", scope: "event venue", validTime: "2028-06-11", values: []},
		]
		sources: [
			{id: "d1", authority: "event-coordinator", bindings: ["b0", "b1"], sentAt: "2028-06-08", paragraphs: ["My current assurance is that entry for booked visitors at the Lumen evening event is permitted. The venue is Juniper room. This is an assurance about the arrangement, not a new grant of permission."]},
			{id: "d2", authority: "event-coordinator", bindings: ["b0"], sentAt: "2028-06-09", paragraphs: ["I withdraw d1's assurance about visitor entry for the Lumen evening event pending inspection. I am withdrawing an assurance, not revoking the actual entry permission. I now make no finding that entry is permitted or forbidden."]},
		]
		reference: {
			"d1-p0": [#PanelWorld & {binding: "b0", value: "permitted"}, #PanelWorld & {binding: "b1", value: "Juniper room"}]
			"d2-p0": [#PanelAct & {kind: "withdraw-assurance", binding: "b0", target: "d1"}, #PanelUnknown & {binding: "b0"}]
		}
		queries: [{id: "q0", binding: "b0", value: "permitted", expected: "unestablished"}, {id: "q1", binding: "b1", value: "Juniper room", expected: "supported"}]
	}
	"permission-revoked": {
		controlFault: {span: "d2-p0", mode: "omit-binding", binding: "b0"}
		bindings: [
			{id: "b0", subject: "booked visitors", property: "permission", scope: "Marlow evening event", validTime: "2028-06-12", values: ["permitted", "forbidden"]},
			{id: "b1", subject: "Marlow evening event", property: "location", scope: "event venue", validTime: "2028-06-12", values: []},
		]
		sources: [
			{id: "d1", authority: "event-coordinator", bindings: ["b0", "b1"], sentAt: "2028-06-08", paragraphs: ["As event coordinator, I grant booked visitors entry permission for the Marlow evening event. The venue is Alder room. This grant applies only to this event."]},
			{id: "d2", authority: "event-coordinator", bindings: ["b0"], sentAt: "2028-06-09", paragraphs: ["I revoke the booked-visitor entry permission granted in d1 for the Marlow evening event. This changes the actual permission, not merely my confidence in an earlier assurance. It does not change the venue recorded in d1."]},
		]
		reference: {
			"d1-p0": [#PanelAct & {kind: "grant-permission", binding: "b0"}, #PanelWorld & {binding: "b1", value: "Alder room"}]
			"d2-p0": [#PanelAct & {kind: "revoke-permission", binding: "b0", target: "d1"}]
		}
		queries: [{id: "q0", binding: "b0", value: "permitted", expected: "opposed"}, {id: "q1", binding: "b1", value: "Alder room", expected: "supported"}]
	}
	"date-not-established": {
		controlFault: {span: "d1-p0", mode: "invert-exclusion", binding: "b0"}
		bindings: [
			{id: "b0", subject: "staff drill", property: "effective-date", scope: "one-day exception", validTime: null, values: []},
			{id: "b1", subject: "staff drill", property: "location", scope: "one-day exception", validTime: null, values: []},
		]
		sources: [
			{id: "d1", authority: "drill-coordinator", bindings: ["b0", "b1"], sentAt: "2028-10-03", paragraphs: ["The staff drill is located at Cobalt annex. Its single effective date is not established in this packet. The effective date is explicitly not 2028-10-03, the date of this message; no other date is supplied."]},
		]
		reference: {"d1-p0": [#PanelWorld & {binding: "b1", value: "Cobalt annex"}, #PanelUnknown & {binding: "b0"}, #PanelWorld & {binding: "b0", operator: "neq", value: "2028-10-03"}]}
		queries: [{id: "q0", binding: "b0", value: "2028-10-05", expected: "unestablished"}, {id: "q1", binding: "b0", value: "2028-10-03", expected: "opposed"}, {id: "q2", binding: "b1", value: "Cobalt annex", expected: "supported"}]
	}
	"date-established": {
		controlFault: {span: "d1-p0", mode: "omit-binding", binding: "b0"}
		bindings: [
			{id: "b0", subject: "staff drill", property: "effective-date", scope: "single-day arrangement", validTime: null, values: []},
			{id: "b1", subject: "staff drill", property: "location", scope: "single-day arrangement", validTime: null, values: []},
		]
		sources: [
			{id: "d1", authority: "drill-coordinator", bindings: ["b0", "b1"], sentAt: "2028-10-03", paragraphs: ["The staff drill is located at Birch annex. Its single effective date is 2028-10-06. That date is the arrangement's validity, not the timestamp of this message."]},
		]
		reference: {"d1-p0": [#PanelWorld & {binding: "b1", value: "Birch annex"}, #PanelWorld & {binding: "b0", value: "2028-10-06"}]}
		queries: [{id: "q0", binding: "b0", value: "2028-10-05", expected: "opposed"}, {id: "q1", binding: "b0", value: "2028-10-06", expected: "supported"}, {id: "q2", binding: "b1", value: "Birch annex", expected: "supported"}]
	}
	"unresolved-conflict": {
		controlFault: {span: "d1-p0", mode: "omit-binding", binding: "b0"}
		bindings: [{id: "b0", subject: "nightly export", property: "quiet-mail", scope: "production-north", validTime: "2028-09-09", values: ["enabled", "disabled"]}]
		sources: [
			{id: "d1", authority: "operations", bindings: ["b0"], sentAt: "2028-09-08", paragraphs: ["For the nightly export in production-north on 2028-09-09, quiet-mail is enabled. This is a report of that environment's setting. It is not a statement about notification delivery guarantees."]},
			{id: "d2", authority: "operations", bindings: ["b0"], sentAt: "2028-09-09", paragraphs: ["For that same nightly export in production-north on 2028-09-09, quiet-mail is disabled. This report has the same authority as d1. Neither report is established here as superseding the other."]},
		]
		reference: {"d1-p0": [#PanelWorld & {binding: "b0", value: "enabled"}], "d2-p0": [#PanelWorld & {binding: "b0", value: "disabled"}]}
		queries: [{id: "q0", binding: "b0", value: "enabled", expected: "contested"}]
	}
	"property-scoped-replacement": {
		controlFault: {span: "d1-p0", mode: "omit-binding", binding: "b1"}
		bindings: [
			{id: "b0", subject: "nightly export", property: "quiet-mail", scope: "production-south", validTime: "2028-09-10", values: ["enabled", "disabled"]},
			{id: "b1", subject: "export backup", property: "location", scope: "production-south", validTime: "2028-09-10", values: []},
		]
		sources: [
			{id: "d1", authority: "operations", bindings: ["b0", "b1"], sentAt: "2028-09-08", paragraphs: ["For the production-south nightly export on 2028-09-10, quiet-mail is enabled. The export backup is stored at Ridge vault. These are separate properties in the same note."]},
			{id: "d2", authority: "operations", bindings: ["b0"], sentAt: "2028-09-09", paragraphs: ["This notice supersedes d1 only for the quiet-mail setting of that production-south nightly export. Quiet-mail is now disabled for 2028-09-10. It does not supersede d1's separate backup-location information."]},
		]
		reference: {"d1-p0": [#PanelWorld & {binding: "b0", value: "enabled"}, #PanelWorld & {binding: "b1", value: "Ridge vault"}], "d2-p0": [#PanelAct & {kind: "supersedes", binding: "b0", target: "d1"}, #PanelWorld & {binding: "b0", value: "disabled"}]}
		queries: [{id: "q0", binding: "b0", value: "enabled", expected: "opposed"}, {id: "q1", binding: "b1", value: "Ridge vault", expected: "supported"}]
	}
	"different-environment": {
		controlFault: {span: "d1-p0", mode: "omit-binding", binding: "b1"}
		bindings: [
			{id: "b0", subject: "export scheduler", property: "quiet-mail", scope: "production-west", validTime: "2028-09-11", values: ["enabled", "disabled"]},
			{id: "b1", subject: "export scheduler", property: "quiet-mail", scope: "staging-west", validTime: "2028-09-11", values: ["enabled", "disabled"]},
		]
		sources: [
			{id: "d1", authority: "operations", bindings: ["b0", "b1"], worldBindings: ["b1"], sentAt: "2028-09-10", paragraphs: ["For the staging-west export scheduler on 2028-09-11, quiet-mail is enabled. This observation covers staging-west only. It supplies no finding about production-west."]},
		]
		reference: {"d1-p0": [#PanelWorld & {binding: "b1", value: "enabled"}, #PanelUnknown & {binding: "b0"}]}
		queries: [{id: "q0", binding: "b0", value: "enabled", expected: "unestablished"}, {id: "q1", binding: "b1", value: "enabled", expected: "supported"}]
	}
	"question-and-directive": {
		controlFault: {span: "d1-p0", mode: "add-world", binding: "b0", atom: #PanelWorld & {binding: "b0", value: "2028-10-05"}}
		bindings: [
			{id: "b0", subject: "volunteer briefing", property: "effective-date", scope: "single-day briefing", validTime: null, values: []},
			{id: "b1", subject: "volunteer briefing", property: "location", scope: "single-day briefing", validTime: null, values: []},
		]
		sources: [
			{id: "d1", authority: "briefing-coordinator", bindings: ["b0", "b1"], sentAt: "2028-10-04", paragraphs: ["The volunteer briefing venue is Ash room. Is its single effective date 2028-10-05? Please check the calendar before making plans; that question is not a confirmed schedule."]},
		]
		reference: {"d1-p0": [#PanelWorld & {binding: "b1", value: "Ash room"}, #PanelAct & {kind: "question", binding: "b0"}, #PanelAct & {kind: "directive", binding: "b0"}]}
		optionalReference: {"d1-p0": [#PanelUnknown & {binding: "b0"}]}
		queries: [{id: "q0", binding: "b0", value: "2028-10-05", expected: "unestablished"}, {id: "q1", binding: "b1", value: "Ash room", expected: "supported"}]
	}
}
