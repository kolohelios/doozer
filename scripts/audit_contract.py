"""Prospective audit-report ABI: offline validation, never acceptance or repair."""

import argparse
import copy
import json
import subprocess

from scripts import interpretation_review as review, jev_multipass as multi
from scripts.evaluation_client import validate_contract

ROLES = ("interpreter", "verifier")
FILE = review.DIRECTORY / "audit-report.cue"


def load():
    return json.loads(subprocess.run(["cue", "export", str(FILE)], check=True, capture_output=True, text=True).stdout)["auditReportV2"]


def specialize(contract, bindings, sources):
    if not bindings or not sources or len(set(bindings)) != len(bindings) or len(set(sources)) != len(sources) or any(not isinstance(v, str) or not v.strip() for v in [*bindings, *sources]):
        raise ValueError("context identities must be nonempty and unique")
    schema = copy.deepcopy(contract["schema"])
    fields = schema["properties"]["checks"]["items"]["properties"]
    fields["binding"]["enum"] = list(bindings)
    fields["issues"]["items"]["properties"]["evidence"]["items"]["enum"] = list(sources)
    return {"json": schema, "cue": multi.compile_schema(json.dumps(schema, sort_keys=True)), "bindings": list(bindings), "sources": list(sources)}


def validate(value, schema, availability):
    if set(availability) != set(ROLES) or any(type(v) is not bool for v in availability.values()):
        raise ValueError("explicit proposal availability required for both roles")
    validate_contract(schema["cue"], "#Report", json.dumps(value, sort_keys=True, allow_nan=False))
    checks = value["checks"]
    if len(checks) != len(schema["bindings"]) or {c["binding"] for c in checks} != set(schema["bindings"]):
        raise ValueError("missing or duplicate binding assessment")
    for check in checks:
        if not check["rationale"].strip():
            raise ValueError("empty rationale")
        for issue in check["issues"]:
            if not issue["detail"].strip() or len(issue["evidence"]) != len(set(issue["evidence"])):
                raise ValueError("empty finding or duplicate evidence identity")
        for role in ROLES:
            issues = [i for i in check["issues"] if i["affects"] in {role, "both"}]
            material = any(i["severity"] == "material" for i in issues)
            if not availability[role] and (check[role] != "unavailable" or issues):
                raise ValueError("cannot assess or attach findings to an absent proposal")
            if (check[role] == "material-error") != material:
                raise ValueError("material verdict and role-specific material findings disagree")
    return value


def project(value, schema, availability):
    """Only the audit component: never clear mechanical/verifier holds or replace facts."""
    if value is not None:
        validate(value, schema, availability)
    else:
        if set(availability) != set(ROLES) or any(type(v) is not bool for v in availability.values()):
            raise ValueError("explicit proposal availability required")
    checks = {c["binding"]: c for c in value["checks"]} if value is not None else {}
    return {binding: {"audit_blocks": {role: not availability[role] or check.get(role, "unavailable") != "faithful" for role in ROLES},
                      "verdicts": {role: check.get(role, "unavailable") for role in ROLES},
                      "findings": copy.deepcopy(check.get("issues", [])),
                      "limitations": copy.deepcopy(value["limitations"]) if value is not None else [],
                      "canonical_acceptance": False,
                      "boundary": "Untrusted audit signal only. Does not clear other checks, replace a primary, or establish source entailment."}
            for binding in schema["bindings"] for check in [checks.get(binding, {})]}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="compile prospective schema offline; no model or approval capability")
    parser.parse_args(argv)
    contract = load()
    schema = specialize(contract, ["binding"], ["source"])
    validate({"checks": [{"binding": "binding", "interpreter": "faithful", "verifier": "faithful", "issues": [{"severity": "non-material", "affects": "both", "evidence": ["source"], "detail": "Synthetic non-material formatting observation."}], "rationale": "Offline interface smoke check, not a source interpretation."}], "limitations": []}, schema, {role: True for role in ROLES})
    print(json.dumps({"version": contract["version"], "status": contract["status"], "sha256": review.digest(contract), "paid_calls": 0, "canonical_acceptance": False, "archived_results_rescored": False}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
