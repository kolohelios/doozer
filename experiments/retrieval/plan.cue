package retrieval

#Query: {
	text: string & !=""
	requiredSources: [...string & =~"^[a-z-]+/[a-z-]+$"]
	negative: *false | bool
}
plan: {
	version:                  1
	noiseDocuments:           1024
	contextBytes:             2560
	seedCount:                4
	candidateCount:           100
	graphHops:                3
	embeddingDimensions:      512
	batchSize:                32
	maxRequestBytes:          65536
	maxPromptPricePerMillion: "0.03"
	queries: {
		"repeat-without-alerts": #Query & {
			text: "Can I run a failed event again without sending the customer a second alert?"
			requiredSources: ["retry-safety/code", "retry-safety/incident", "retry-safety/clarification", "retry-safety/manual"]
		}
		"automatic-workaround": #Query & {
			text: "Does the manual replay workaround also protect automatic retries?"
			requiredSources: ["retry-safety/manual", "retry-safety/proposal", "retry-safety/no"]
		}
		"recovery-readiness": #Query & {
			text: "Is a successful single-server failover drill enough evidence for recovering our critical database?"
			requiredSources: ["cnpg-rds/capability", "cnpg-rds/node", "cnpg-rds/cluster", "cnpg-rds/boundary"]
		}
		"additive-client-risk": #Query & {
			text: "Can an additive API response break clients even after our compatibility suite passed?"
			requiredSources: ["breaking-changes/guide", "breaking-changes/client", "breaking-changes/tests", "breaking-changes/rollout"]
		}
		"human-approval": #Query & {
			text: "Can automated model review count as human approval for permission changes?"
			requiredSources: ["code-review/policy", "code-review/tool", "code-review/no", "code-review/agreement"]
		}
		"after-reception-closure": #Query & {
			text: "What entrance do guests use after the one-day reception closure ends?"
			requiredSources: ["visitor-access/guide", "visitor-access/closure"]
		}
		"unknown-payments": #Query & {
			text: "Are payment side effects idempotent?"
			requiredSources: []
			negative: true
		}
	}
}
