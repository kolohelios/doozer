package retrieval

// Supplied knowledge relations from the EDD, not inferred by the retriever.
// Run both with and without these; their availability is an explicit assumption.
#Link: {from: string, to: string, relation: "qualifies" | "counterexample" | "mitigates" | "scope", basis: string & !=""}
knowledgeLinks: [
	#Link & {from: "retry-safety/guide", to: "retry-safety/code", relation: "qualifies", basis: "EDD §3: implementation supports database writes only."},
	#Link & {from: "retry-safety/code", to: "retry-safety/incident", relation: "counterexample", basis: "EDD §3: notification duplication does not negate write deduplication."},
	#Link & {from: "retry-safety/incident", to: "retry-safety/clarification", relation: "qualifies", basis: "EDD §3: clarification separates effects."},
	#Link & {from: "retry-safety/incident", to: "retry-safety/manual", relation: "mitigates", basis: "EDD §3: mitigation is limited to manual replay."},
	#Link & {from: "retry-safety/manual", to: "retry-safety/proposal", relation: "scope", basis: "EDD §3.4: proposed automatic extension is the target of No."},
	#Link & {from: "cnpg-rds/capability", to: "cnpg-rds/node", relation: "scope", basis: "EDD §5.1: capability differs from demonstrated operation."},
	#Link & {from: "cnpg-rds/node", to: "cnpg-rds/cluster", relation: "qualifies", basis: "EDD §5.1: node and cluster loss are different failure modes."},
	#Link & {from: "cnpg-rds/cluster", to: "cnpg-rds/boundary", relation: "scope", basis: "EDD §5.1: recovery suitability is workload-specific."},
	#Link & {from: "breaking-changes/guide", to: "breaking-changes/client", relation: "counterexample", basis: "EDD §5.2: strict client is an exception to additive safety."},
	#Link & {from: "breaking-changes/client", to: "breaking-changes/tests", relation: "scope", basis: "EDD §5.2: suite does not cover every consumer."},
	#Link & {from: "breaking-changes/client", to: "breaking-changes/rollout", relation: "mitigates", basis: "EDD §5.2: migration ordering preserves consumer compatibility."},
	#Link & {from: "code-review/policy", to: "code-review/tool", relation: "scope", basis: "EDD §5.3: model assistance does not establish approval authority."},
	#Link & {from: "code-review/policy", to: "code-review/proposal", relation: "qualifies", basis: "EDD §5.3: proposal does not replace existing policy."},
	#Link & {from: "code-review/policy", to: "code-review/agreement", relation: "qualifies", basis: "EDD §5.3: actual agreement has repository/risk/time limits."},
	#Link & {from: "visitor-access/guide", to: "visitor-access/closure", relation: "qualifies", basis: "Nonengineering fixture: closure changes location for one day only."},
]
