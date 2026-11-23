import copy
from contextlib import redirect_stderr, redirect_stdout
import io
import unittest
from unittest.mock import patch

from scripts import audit_contract as audit


class AuditContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.contract = audit.load()
        cls.schema = audit.specialize(cls.contract, ["date", "venue"], ["m1", "m2"])

    def report(self):
        return {"checks": [{"binding": b, "interpreter": "faithful", "verifier": "faithful", "issues": [], "rationale": "Source-linked test assessment."} for b in ("date", "venue")], "limitations": []}

    def issue(self, severity="non-material", affects="interpreter"):
        return {"severity": severity, "affects": affects, "evidence": ["m1"], "detail": "An explicitly classified test observation, not established truth."}

    def project(self, report, **availability):
        return audit.project(report, self.schema, availability or {"interpreter": True, "verifier": True})

    def test_faithful_can_have_nonmaterial_notes_that_remain_visible(self):
        report = self.report()
        report["checks"][0]["issues"] = [self.issue()]
        view = self.project(report)
        self.assertFalse(any(view[b]["audit_blocks"][r] for b in view for r in audit.ROLES))
        self.assertEqual(view["date"]["findings"], report["checks"][0]["issues"])
        self.assertFalse(view["date"]["canonical_acceptance"])
        view["date"]["findings"][0]["detail"] = "changed projection"
        self.assertNotEqual(view["date"]["findings"], report["checks"][0]["issues"])

    def test_material_finding_blocks_only_the_declared_role_and_binding(self):
        report = self.report()
        report["checks"][0].update(interpreter="material-error", issues=[self.issue("material")])
        view = self.project(report)
        self.assertEqual(view["date"]["audit_blocks"], {"interpreter": True, "verifier": False})
        self.assertEqual(view["venue"]["audit_blocks"], {"interpreter": False, "verifier": False})

    def test_shared_material_finding_needs_both_material_verdicts(self):
        report = self.report()
        report["checks"][0].update(interpreter="material-error", verifier="material-error", issues=[self.issue("material", "both")])
        self.assertTrue(all(self.project(report)["date"]["audit_blocks"].values()))
        report["checks"][0]["verifier"] = "faithful"
        with self.assertRaises(ValueError):
            self.project(report)

    def test_material_error_cannot_be_supported_only_by_a_note_or_other_role(self):
        for issue in (self.issue(), self.issue("material", "verifier")):
            with self.subTest(issue=issue):
                report = self.report()
                report["checks"][0].update(interpreter="material-error", issues=[issue])
                with self.assertRaises(ValueError):
                    self.project(report)

    def test_faithful_cannot_coexist_with_a_material_finding(self):
        report = self.report()
        report["checks"][0]["issues"] = [self.issue("material")]
        with self.assertRaises(ValueError):
            self.project(report)

    def test_legacy_issues_are_not_silently_assigned_a_severity(self):
        report = self.report()
        issue = self.issue()
        del issue["severity"]
        report["checks"][0]["issues"] = [issue]
        with self.assertRaises(ValueError):
            self.project(report)
        self.assertNotIn("severity", report["checks"][0]["issues"][0])

    def test_unclear_and_unavailable_still_block_despite_only_nonmaterial_notes(self):
        for verdict in ("unclear", "unavailable"):
            report = self.report()
            report["checks"][0].update(verifier=verdict, issues=[self.issue(affects="verifier")])
            view = self.project(report)
            self.assertTrue(view["date"]["audit_blocks"]["verifier"])
            self.assertFalse(view["venue"]["audit_blocks"]["verifier"])

    def test_absent_proposal_cannot_be_assessed_or_given_notes(self):
        report = self.report()
        for check in report["checks"]:
            check["interpreter"] = "unavailable"
        view = self.project(report, interpreter=False, verifier=True)
        self.assertTrue(all(view[b]["audit_blocks"]["interpreter"] for b in view))
        self.assertFalse(any(view[b]["audit_blocks"]["verifier"] for b in view))
        report["checks"][0]["issues"] = [self.issue()]
        with self.assertRaises(ValueError):
            self.project(report, interpreter=False, verifier=True)

    def test_missing_report_is_not_faithful_or_a_verifier_fallback(self):
        view = self.project(None)
        self.assertTrue(all(view[b]["audit_blocks"][r] for b in view for r in audit.ROLES))
        self.assertTrue(all(not view[b]["canonical_acceptance"] for b in view))
        self.assertNotIn("replacement", view["date"])

    def test_every_binding_must_be_present_exactly_once(self):
        for entries in (["date"], ["date", "date"], ["date", "venue", "venue"]):
            report = self.report()
            template = report["checks"][0]
            report["checks"] = [{**copy.deepcopy(template), "binding": b} for b in entries]
            with self.assertRaises(ValueError):
                self.project(report)

    def test_context_and_finding_identities_are_checked(self):
        for sources in (["m1", "m1"], [""]):
            with self.assertRaises(ValueError):
                audit.specialize(self.contract, ["date"], sources)
        for evidence in ([], ["m99"], ["m1", "m1"]):
            report = self.report()
            report["checks"][0]["issues"] = [{**self.issue(), "evidence": evidence}]
            with self.assertRaises(ValueError):
                self.project(report)
        with self.assertRaises(ValueError):
            self.project(self.report(), interpreter=1, verifier=True)

    def test_unsupported_free_text_and_wrong_severity_are_not_semantically_proved(self):
        report = self.report()
        report["checks"][0]["issues"] = [{**self.issue(), "detail": "This source proves an invented fact; I call that harmless."}]
        report["limitations"] = ["A free-text caveat may itself be mistaken or conceal a material concern."]
        view = self.project(report)
        self.assertFalse(view["date"]["audit_blocks"]["interpreter"])
        self.assertFalse(view["date"]["canonical_acceptance"])
        self.assertEqual(view["date"]["limitations"], report["limitations"])

    def test_empty_reason_and_unrequested_fields_are_rejected(self):
        for key, value in (("rationale", "   "), ("replacement_ledger", [])):
            report = self.report()
            report["checks"][0][key] = value
            with self.assertRaises(ValueError):
                self.project(report)

    def test_offline_cli_has_no_network_or_live_mode(self):
        with patch("urllib.request.OpenerDirector.open", side_effect=AssertionError("network called")), redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            self.assertEqual(audit.main(["--check"]), 0)
            with self.assertRaises(SystemExit):
                audit.main(["--live"])


if __name__ == "__main__":
    unittest.main()
