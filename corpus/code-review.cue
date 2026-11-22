package corpus

scenarios: "code-review": {
	title:     "Observed practice does not silently rewrite review policy"
	design:    "EDD §5.3, §6.4, §14"
	synthetic: true
	tags: ["authority", "policy-versus-practice", "one-word-reversal", "conflict", "temporal-scope"]
	sources: {
		policy: {kind: "document", text: "Two human approvals are required before merge.", anchor: "fixture://review/policy", saidAt: "2026-04-01T09:00:00Z", scope: "all-repositories-stated-policy"}
		tool: {kind: "conversation", text: "We use automated model review to catch mechanical issues before humans look.", anchor: "fixture://review/thread/1", saidAt: "2026-04-02T09:00:00Z", scope: "mechanical-assistance"}
		practice: {kind: "observation", text: "Several low-risk changes merged with one human approval under documented exceptions.", anchor: "fixture://review/records/low-risk", saidAt: "2026-04-03T09:00:00Z", scope: "documented-low-risk-exceptions"}
		proposal: {kind: "conversation", text: "Could we use one human reviewer everywhere?", anchor: "fixture://review/thread/2", saidAt: "2026-04-04T09:00:00Z", scope: "proposed-universal-rule"}
		no: {kind: "conversation", text: "No. Not for authentication or permission changes.", replyTo: "proposal", anchor: "fixture://review/thread/3", saidAt: "2026-04-04T09:01:00Z", scope: "authentication-and-permissions"}
		agreement: {kind: "document", text: "Effective April 10, the docs repository requires one human approval for ordinary prose changes. Security policy and all other repositories retain existing requirements.", anchor: "fixture://review/agreement", saidAt: "2026-04-10T09:00:00Z", scope: "docs-repository-ordinary-prose-from-april-10"}
	}
	steps: [
		{
			id: "policy-and-exceptions", receive: ["policy", "tool", "practice"], reconcile: ["policy", "tool", "practice"]
			expect: {
				must: [{id: "distinct-authority", meaning: "Distinguish the two-human stated policy, model assistance, and observed one-human documented exceptions without inferring a policy change.", scope: "review-expectations", evidence: ["policy", "tool", "practice"]}]
				mustNot: [{id: "tool-as-approval", meaning: "Automated review replaces a required human approval.", reason: "Tool usage does not authorize changing the human-review requirement."}]
				pending: []
			}
		},
		{
			id: "contested-proposal", receive: ["proposal", "no"], reconcile: ["proposal", "no"]
			expect: {
				must: [{id: "bounded-objection", meaning: "The objection targets universal one-reviewer adoption and preserves high-risk exceptions; the proposal is not settled policy. Show unresolved disagreement without generating an approval task queue.", scope: "authentication-and-permissions", evidence: ["proposal", "no", "policy"]}]
				mustNot: [{id: "invented-consensus", meaning: "The team agreed to one human reviewer everywhere.", reason: "A proposal and explicit objection do not establish agreement."}]
				pending: []
				queries: [{question: "Did everyone agree to one reviewer?", state: "conflicted", meaning: "No settlement of the universal proposal is supported; preserve the objection and existing policy.", evidence: ["proposal", "no", "policy"]}]
			}
		},
		{
			id: "scoped-effective-change", receive: ["agreement"], reconcile: ["agreement"]
			expect: {
				must: [{id: "temporal-repo-boundary", meaning: "One human approval applies to ordinary docs-repository prose from April 10 only; retain historical two-reviewer policy and exclusions for security policy and other repositories. A directive must carry the same applicability as the handbook.", scope: "repository-risk-and-effective-time", evidence: ["agreement", "policy", "no"]}]
				mustNot: [{id: "retroactive-global-rule", meaning: "One reviewer was always enough for authentication in every repository.", reason: "The new agreement is neither retroactive nor universal."}]
				pending: []
			}
		},
	]
}
