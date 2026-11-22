package corpus

scenarios: "breaking-changes": {
	title:     "Compatibility depends on consumers and the contract"
	design:    "EDD §5.2, §6.4, §14"
	synthetic: true
	tags: ["scope", "exception-preservation", "contract", "duplicate-with-exception"]
	sources: {
		guide: {kind: "document", text: "Adding optional API fields is nonbreaking.", anchor: "fixture://compat/guide", saidAt: "2026-03-01T09:00:00Z", scope: "unspecified-consumers"}
		paraphrase: {kind: "conversation", text: "Optional response additions are safe, except for consumers with strict unknown-field rejection.", anchor: "fixture://compat/thread/1", saidAt: "2026-03-02T09:00:00Z", scope: "response-additions-with-exception"}
		client: {kind: "code", text: "The legacy importer rejects responses containing unknown fields.", anchor: "fixture://compat/client/decoder", saidAt: "2026-03-03T09:00:00Z", scope: "legacy-importer"}
		tests: {kind: "observation", text: "Compatibility checks pass for generated SDK clients; the legacy importer is not in this suite.", anchor: "fixture://compat/tests/run", saidAt: "2026-03-04T09:00:00Z", scope: "generated-sdk-clients-only"}
		rollout: {kind: "document", text: "Expand the response behind a flag, migrate the importer, then enable for that consumer; remove the old representation only after migration.", anchor: "fixture://compat/rollout", saidAt: "2026-03-05T09:00:00Z", scope: "importer-migration-order"}
		behavior: {kind: "observation", text: "A default sort-order change broke an integration despite unchanged response schema.", anchor: "fixture://compat/incident/sort", saidAt: "2026-03-06T09:00:00Z", scope: "behavioral-contract-sort-order"}
	}
	steps: [
		{
			id: "compact-with-exception", receive: ["guide", "paraphrase", "client"], reconcile: ["guide", "paraphrase", "client"]
			expect: {
				must: [{id: "consumer-specific", meaning: "Compact the overlapping guidance but preserve the strict-decoder exception and the legacy importer's source link.", scope: "response-additions", evidence: ["guide", "paraphrase", "client"]}]
				mustNot: [{id: "additive-always-safe", meaning: "Optional additions are universally compatible.", reason: "The actual consumer rejects unknown fields."}]
				pending: []
			}
		},
		{
			id: "limited-suite-and-migration", receive: ["tests", "rollout"], reconcile: ["tests", "rollout"]
			expect: {
				must: [{id: "preserve-order", meaning: "Passing SDK checks exclude the importer; preserve expand, migrate, enable, and contract ordering in handbook and scoped directives.", scope: "importer-migration", evidence: ["client", "tests", "rollout"]}]
				mustNot: [{id: "green-means-all", meaning: "All consumers passed, so remove the old representation now.", reason: "Coverage is partial and the migration precondition remains."}]
				pending: []
			}
		},
		{
			id: "schema-not-behavior", receive: ["behavior"], reconcile: ["behavior"]
			expect: {
				must: [{id: "contract-dimensions", meaning: "An unchanged wire schema can still break a behavioral contract; keep the sort-order case distinct from unknown-field decoding.", scope: "behavior-versus-schema", evidence: ["behavior", "client"]}]
				mustNot: [{id: "schema-only", meaning: "Unchanged schema proves a nonbreaking change.", reason: "The integration depends on behavior not captured by schema alone."}]
				pending: []
				queries: [{question: "Is this additive API change safe?", state: "supported", meaning: "Explain consumer contracts, strict decoder exception, partial test coverage, and migration order rather than answering universally.", evidence: ["client", "tests", "rollout", "behavior"]}]
			}
		},
	]
}
