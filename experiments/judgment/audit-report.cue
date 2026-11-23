package judgment

// Prospective interface only. No conversion or rescoring of archived responses.
auditReportV2: {
	version:      "source-audit-report-v2"
	status:       "offline-prospective-contract-not-wired-to-live-runner"
	instructions: "Assess each declared binding separately for interpreter and verifier. Every issue must explicitly say severity=material or severity=non-material. Material means an alleged loss, unsupported claim, wrong scope, provenance, or qualification in that role's interpretation. Non-material means an observation that does not allege such a defect, not an unresolved possible defect. A role is material-error iff at least one issue with severity=material affects that role. Faithful may coexist with non-material notes, never material findings. Use unclear for an unresolved assessment; it still blocks that role on that binding. Use unavailable for an absent proposal or unavailable assessment; never assess or attach issues to an absent proposal. All issues cite visible source IDs and a nonempty explanation. Use limitations for general caveats. Notes are preserved but do not block; unclear/unavailable and material-error block only the indicated role/binding. These are untrusted audit signals, not source facts, replacement ledgers, or canonical acceptance. Severity and claimed scope require semantic scrutiny; structural validation does not prove them correct."
	schema: {
		type: "object", additionalProperties: false, required: ["checks", "limitations"]
		properties: {
			limitations: {type: "array", items: {type: "string"}}
			checks: {type: "array", items: {
				type: "object", additionalProperties: false, required: ["binding", "interpreter", "verifier", "issues", "rationale"]
				properties: {
					binding: {type: "string"}
					interpreter: #AuditVerdictV2
					verifier:    #AuditVerdictV2
					// Nonempty/whitespace checks are enforced by the local validator.
					rationale: {type: "string"}
					issues: {type: "array", items: {
						type: "object", additionalProperties: false, required: ["severity", "affects", "evidence", "detail"]
						properties: {
							severity: {type: "string", enum: ["material", "non-material"]}
							affects: {type: "string", enum: ["interpreter", "verifier", "both"]}
							evidence: {type: "array", minItems: 1, items: {type: "string"}}
							detail: {type: "string"}
						}
					}}
				}
			}}
		}
	}
}
#AuditVerdictV2: {type: "string", enum: ["faithful", "material-error", "unclear", "unavailable"]}
