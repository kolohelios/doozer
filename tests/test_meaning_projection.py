import copy
from contextlib import redirect_stdout
import io
import json
import unittest
from unittest.mock import patch

from scripts import meaning_projection as meaning
from scripts.cue_contract import compile_schema
from scripts.evaluation_client import validate_contract


class MeaningProjectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = meaning.legacy.multi.export_cue(sorted(meaning.legacy.DIRECTORY.glob("*.cue")))
        cls.cases = meaning.prepare(cls.data)

    def case(self, key):
        return copy.deepcopy(self.cases[key])

    def entry(self, case, source):
        return next(e for e in case["proposal"]["ledger"] if e["span"] == source)

    def compile(self, case):
        return meaning.compile_ledger(case["proposal"], case["context"], case["schema"])

    def view(self, case, binding="b0", value="enabled", **kwargs):
        return meaning.project(case["compiled"], case["context"], binding, value, **kwargs)

    def audit(self, case):
        return {"checks": [{"binding": b, "interpreter": "faithful", "verifier": "faithful", "issues": [], "rationale": "Authored ABI check, not an entailment proof."} for b in case["context"]["binding_index"]], "limitations": []}

    def test_authored_controls_are_offline_and_context_does_not_include_labels(self):
        self.assertEqual(len(self.cases), 9)
        self.assertEqual(sum(len(c["expected"]) for c in self.cases.values()), 23)
        for case in self.cases.values():
            self.assertFalse({"expected", "queries", "reference", "proposal"} & case["context"].keys())
            self.assertTrue(all(not ({"atoms", "annotations"} & s.keys()) for s in case["context"]["sources"]))
            self.assertFalse(case["compiled"]["canonical_acceptance"])

    def test_explicit_and_derived_coverage_preserve_same_bounded_answer(self):
        derived, explicit = self.case("coverage-derived"), self.case("coverage-explicit")
        a, b = self.view(derived), self.view(explicit)
        self.assertEqual(a["understanding"], b["understanding"])
        self.assertEqual(a["coverage"], b["coverage"])
        self.assertEqual(a["understanding"]["state"], "unestablished")
        self.assertEqual(a["coverage"]["frame"], "source-window")
        self.assertIsNone(a["coverage"]["holder"])
        self.assertFalse(a["source_conditions"])
        self.assertEqual(b["source_conditions"][0]["annotation"]["frame"], "source-note")
        self.assertIsNone(b["source_conditions"][0]["annotation"]["holder"])
        for case in (derived, explicit):
            view = self.view(case)
            self.assertIn("m1", view["source_links"])
            self.assertIn("supplies no production-west finding in these notes", meaning.recover(case["compiled"], "m1")["text"])
            text = meaning.render(view)
            self.assertIn("unestablished", text)
            self.assertIn("Bounded interpreted evidence", text)
            self.assertNotIn("Tess does not know", text)
            self.assertEqual(self.view(case, "b2", "Sable vault")["understanding"]["state"], "supported")

    def test_later_finding_does_not_turn_old_coverage_into_current_fog(self):
        case = self.case("coverage-known-later")
        view = self.view(case)
        self.assertEqual(view["understanding"]["state"], "opposed")
        self.assertFalse(view["source_conditions"])
        self.assertEqual(view["historical_conditions"][0]["as_of"], "w0")
        self.assertIn("source-note", json.dumps(view["historical_conditions"]))
        self.assertIn("production-west finding", meaning.recover(case["compiled"], "m1")["text"])

    def test_personal_uncertainty_has_its_actual_holder_and_no_world_effect(self):
        case = self.case("personal-unknown")
        view = self.view(case)
        condition = view["source_conditions"][0]
        self.assertEqual((condition["speaker"], condition["annotation"]["holder"], condition["annotation"]["frame"]), ("Mo", "Mo", "person"))
        self.assertEqual(view["understanding"]["state"], "unestablished")
        self.assertFalse(view["understanding"]["positive"] or view["understanding"]["negative"])

    def test_wrong_owner_or_frame_causes_only_affected_annotation_hold(self):
        case = self.case("coverage-explicit")
        annotation = self.entry(case, "m1")["annotations"][0]
        annotation["holder"] = "Tess"
        case["compiled"] = self.compile(case)
        self.assertIn("annotation-mechanical", self.view(case)["mechanical_flags"])
        self.assertFalse(self.view(case, "b2", "Sable vault")["mechanical_flags"])
        self.assertEqual(self.view(case, "b2", "Sable vault")["understanding"]["state"], "supported")
        case = self.case("personal-unknown")
        self.entry(case, "u1")["annotations"][0]["holder"] = "Tess"
        compiled = self.compile(case)
        self.assertIn("actual holder", compiled["rejected_annotations"][0]["reason"])

    def test_hunch_is_attributed_but_neither_support_nor_opposition(self):
        case = self.case("hunch-only")
        view = self.view(case)
        self.assertEqual(view["understanding"]["state"], "unestablished")
        self.assertEqual(len(view["speculations"]), 1)
        record = view["speculations"][0]
        self.assertEqual((record["speaker"], record["annotation"]["value"]), ("Mo", "enabled"))
        self.assertFalse(view["understanding"]["positive"] or view["understanding"]["negative"])
        self.assertIn("not world evidence", meaning.render(view))
        self.assertIn("My hunch", meaning.recover(case["compiled"], "h1")["text"])

    def test_hunch_does_not_manufacture_contestation_against_real_observation(self):
        case = self.case("hunch-with-observation")
        view = self.view(case)
        self.assertEqual(view["understanding"]["state"], "opposed")
        self.assertFalse(view["understanding"]["positive"])
        self.assertEqual(view["understanding"]["negative"], ["h2-atoms-0"])
        self.assertEqual(len(view["speculations"]), 1)
        self.assertFalse(any(c["witness"].startswith("h1-") for c in case["compiled"]["core"]["constraints"]))

    def test_negated_hunch_does_not_become_a_world_exclusion(self):
        case = self.case("hunch-only")
        text = "My hunch is that quiet-mail is not enabled in production-west."
        case["context"]["source_index"]["h1"]["text"] = text
        annotation = self.entry(case, "h1")["annotations"][0]
        annotation.update(operator="neq", quote=text)
        case["compiled"] = self.compile(case)
        self.assertEqual(self.view(case)["understanding"]["state"], "unestablished")
        self.assertEqual(self.view(case)["speculations"][0]["annotation"]["operator"], "neq")

    def test_direct_and_procedure_topic_layouts_keep_permission_and_recovery(self):
        direct, topic = self.case("invitation-direct"), self.case("invitation-topic")
        a = self.view(direct, value="permitted", consumer="evidence-use")
        b = self.view(topic, value="permitted", consumer="evidence-use")
        self.assertEqual(a["understanding"], b["understanding"])
        self.assertEqual(a["procedures"], b["procedures"])
        self.assertEqual(a["understanding"]["state"], "supported")
        self.assertTrue(topic["compiled"]["lowerings"])
        self.assertEqual(topic["compiled"]["original_proposal"], topic["proposal"])
        self.assertEqual(a["procedures"][0]["action"]["object"], "its invitation")
        text = meaning.render(a)
        self.assertIn("The catering meeting", text)
        self.assertIn("Please do not use its invitation", text)
        self.assertIn("not a newly assigned task", text)
        self.assertEqual(self.view(topic, "b1", "Oak hall")["understanding"]["state"], "supported")
        grant = next(r for r in topic["compiled"]["core"]["records"] if r["atom"]["kind"] == "grant")
        assurance = next(r for r in topic["compiled"]["core"]["records"] if r["atom"]["kind"] == "assurance")
        self.assertTrue(grant["not_explicitly_retired"])
        self.assertFalse(assurance["not_explicitly_retired"])

    def test_fact_answer_can_omit_warning_text_without_losing_procedure_path(self):
        case = self.case("invitation-topic")
        view = self.view(case, value="permitted")
        self.assertFalse(view["procedures"])
        self.assertTrue(view["procedure_links"])
        self.assertNotIn("Please do not use", meaning.render(view))
        pertinent = self.view(case, value="permitted", consumer="evidence-use")
        self.assertIn("Please do not use", meaning.render(pertinent))
        self.assertIn("catering meeting", meaning.recover(case["compiled"], "m2")["text"])

    def test_unknown_procedure_links_cannot_be_guessed(self):
        data = copy.deepcopy(self.data)
        data["projectionCases"]["invitation-topic"]["topics"]["permission-evidence-use"] = ["b99"]
        with self.assertRaises(ValueError):
            meaning.prepare(data)

    def test_fixture_annotations_cannot_be_silently_dropped_for_unknown_sources(self):
        data = copy.deepcopy(self.data)
        case = data["projectionCases"]["coverage-explicit"]
        case["annotations"]["m99"] = case["annotations"].pop("m1")
        with self.assertRaisesRegex(ValueError, "unknown source"):
            meaning.prepare(data)

    def test_kind_specific_schema_rejects_null_world_binding_and_unframed_unknown(self):
        for invalid in (meaning.atom("assertion", None, operator="eq", value="enabled"), meaning.atom("source-uncertainty", "b0", operator="unknown", holder="Tess")):
            case = self.case("coverage-derived")
            self.entry(case, "m1")["atoms"].append(invalid)
            with self.assertRaises(ValueError):
                self.compile(case)

    def test_digest_annotations_and_fabricated_quotes_are_not_primary_evidence(self):
        for source, quote in (("m4", "This digest repeats the staging observation from m1."), ("m1", "invented quote")):
            case = self.case("coverage-derived")
            self.entry(case, source)["annotations"] = [{"kind": "condition", "binding": "b0", "frame": "source-note", "stance": "no-finding-in-note", "holder": None, "quote": quote}]
            self.assertTrue(self.compile(case)["rejected_annotations"])

    def test_severity_aware_audit_is_an_optional_component_not_a_clearance_or_fact(self):
        case = self.case("coverage-explicit")
        self.entry(case, "m1")["annotations"][0]["holder"] = "Tess"
        case["compiled"] = self.compile(case)
        report = self.audit(case)
        report["checks"][0]["issues"] = [{"severity": "non-material", "affects": "both", "evidence": ["m1"], "detail": "Authored harmless formatting observation."}]
        view = self.view(case, audit_report=report, availability={"interpreter": True, "verifier": True})
        self.assertFalse(any(view["audit"]["audit_blocks"].values()))
        self.assertIn("annotation-mechanical", view["mechanical_flags"])
        self.assertFalse(view["canonical_acceptance"])
        report["checks"][0]["interpreter"] = "material-error"
        report["checks"][0]["issues"] = [{"severity": "material", "affects": "interpreter", "evidence": ["m1"], "detail": "Authored material finding."}]
        self.assertTrue(self.view(case, audit_report=report, availability={"interpreter": True, "verifier": True})["audit"]["audit_blocks"]["interpreter"])
        self.assertFalse(self.view(case, "b2", "Sable vault", audit_report=report, availability={"interpreter": True, "verifier": True})["audit"]["audit_blocks"]["interpreter"])

    def test_wrong_natural_language_stance_classification_can_still_pass_mechanics(self):
        case = self.case("hunch-only")
        entry = self.entry(case, "h1")
        entry["annotations"] = []
        entry["atoms"] = [meaning.atom("assertion", "b0", operator="eq", value="enabled")]
        case["compiled"] = self.compile(case)
        self.assertFalse(case["compiled"]["core"]["rejected"])
        self.assertEqual(self.view(case)["understanding"]["state"], "supported")
        self.assertFalse(self.view(case)["canonical_acceptance"])
        # Conditional typing guarantees are not a classifier or proof of source entailment.

    def test_native_cue_schema_import_keeps_standard_library_imports_at_file_scope(self):
        schema = compile_schema(json.dumps({"type": "object", "required": ["s", "a"], "additionalProperties": False, "properties": {"s": {"type": "string", "minLength": 1}, "a": {"type": "array", "items": {"type": "string"}, "maxItems": 0}}}))
        validate_contract(schema, "#Report", json.dumps({"s": "text", "a": []}))
        with self.assertRaises(ValueError):
            validate_contract(schema, "#Report", json.dumps({"s": "", "a": []}))

    def test_qualifier_question_and_calendar_instruction_survive_reader_projection(self):
        case = self.case("unresolved-qualifier")
        view = self.view(case, value="2031-08-14", consumer="evidence-use")
        self.assertTrue(view["qualifications"])
        self.assertTrue(all(r["atom"]["operator"] == "one-provisional" and r["atom"]["alternatives"] == ["b0", "b1"] for r in view["qualifications"]))
        self.assertTrue(any(r["atom"]["kind"] == "question" and r["atom"]["value"] == "2031-08-14" for r in view["source_acts"]))
        text = meaning.render(view)
        self.assertIn("one-provisional", text)
        self.assertIn("before making travel plans", text)
        self.assertFalse(self.view(case, "b2", "Juniper studio")["qualifications"])

    def test_preservation_check_detects_projection_loss_without_judging_extraction(self):
        case = self.case("hunch-only")
        original = meaning.project
        def lossy(*args, **kwargs):
            view = original(*args, **kwargs)
            view["speculations"] = []
            return view
        with patch.object(meaning, "project", side_effect=lossy), self.assertRaisesRegex(ValueError, "lost an interpreted"):
            meaning.check_projection(case["compiled"], case["context"])

    def test_offline_check_has_no_generation_or_approval_capability(self):
        with patch("urllib.request.OpenerDirector.open", side_effect=AssertionError("network called")), redirect_stdout(io.StringIO()) as out:
            self.assertEqual(meaning.main(["--check"]), 0)
        result = json.loads(out.getvalue())
        self.assertEqual(result["paid_calls"], 0)
        self.assertFalse(result["canonical_acceptance"] or result["archived_results_rescored"])


if __name__ == "__main__":
    unittest.main()
