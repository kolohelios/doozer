package corpus

scenarios: "cnpg-rds": {
	title:     "Database safety is conditional, not a vendor ranking"
	design:    "EDD §5.1, §6.4, §14"
	synthetic: true
	tags: ["scope", "capability-versus-evidence", "unanswered", "out-of-order"]
	sources: {
		managed: {kind: "conversation", text: "RDS is safer because failover is managed.", anchor: "fixture://database/thread/1", saidAt: "2026-02-01T09:00:00Z", scope: "unspecified-workload"}
		capability: {kind: "document", text: "CloudNativePG supports automated failover and point-in-time recovery.", anchor: "fixture://database/capabilities", saidAt: "2026-02-02T09:00:00Z", scope: "product-capabilities-not-local-tests"}
		gap: {kind: "conversation", text: "We have not tested a full restore or cross-cluster recovery against our objectives.", anchor: "fixture://database/thread/2", saidAt: "2026-02-03T09:00:00Z", scope: "local-restore-readiness"}
		node: {kind: "observation", text: "The internal-service configuration passed a single-node failover drill.", anchor: "fixture://database/drill/node", saidAt: "2026-02-04T09:00:00Z", scope: "internal-service-single-node-loss"}
		cluster: {kind: "observation", text: "The same configuration missed the recovery objective after total Kubernetes cluster loss.", anchor: "fixture://database/drill/cluster", saidAt: "2026-02-05T09:00:00Z", scope: "internal-service-cluster-loss"}
		boundary: {kind: "conversation", text: "CNPG could fit the internal service; the customer-critical database needs different recovery evidence. This is not a deployment decision.", anchor: "fixture://database/thread/3", saidAt: "2026-02-06T09:00:00Z", scope: "workload-specific-proposal"}
	}
	steps: [
		{
			id: "capability-not-readiness", receive: ["managed", "capability", "gap"], reconcile: ["managed", "capability", "gap"]
			expect: {
				must: [{id: "unproven-recovery", meaning: "Separate managed-service claims and CNPG features from demonstrated local recovery readiness; restore evidence is missing.", scope: "local-recovery", evidence: ["managed", "capability", "gap"]}]
				mustNot: [{id: "vendor-winner", meaning: "RDS wins or CNPG is demonstrated safe for every workload.", reason: "No scoped comparative operating evidence supports a universal winner."}]
				pending: []
				queries: [{question: "Have we demonstrated full recovery within our objectives?", state: "insufficient", meaning: "Capabilities are documented, but the required local drill has not been demonstrated.", evidence: ["capability", "gap"]}]
			}
		},
		{
			id: "newer-negative-first", receive: ["cluster"], reconcile: ["cluster"]
			expect: {
				must: [{id: "bounded-failure", meaning: "The tested configuration missed its cluster-loss recovery objective; retain the failure model and workload scope.", scope: "internal-service-cluster-loss", evidence: ["cluster"]}]
				mustNot: [{id: "universal-failure", meaning: "CNPG cannot recover from any node failure.", reason: "Cluster-loss failure does not establish every other failure mode."}]
				pending: []
			}
		},
		{
			id: "older-positive-arrives-late", receive: ["node", "boundary"], reconcile: ["node", "boundary"]
			expect: {
				must: [{id: "coexisting-results", meaning: "Single-node failover passed while cluster-loss recovery failed. Late arrival of the older positive drill must not erase the newer gap. The proposed internal-service fit is conditional, not a decision.", scope: "workload-and-failure-model", evidence: ["node", "cluster", "boundary"]}]
				mustNot: [{id: "inferred-approval", meaning: "The team approved CNPG for the customer-critical database.", reason: "A conditional proposal is neither a settlement nor evidence for a different workload."}]
				pending: []
				queries: [{question: "What should our agent deploy?", state: "insufficient", meaning: "Explain the evidence and gaps; do not compile a deployment mandate from a conditional proposal.", evidence: ["node", "cluster", "boundary"]}]
			}
		},
	]
}
