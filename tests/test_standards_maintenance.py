import copy
from contextlib import redirect_stderr, redirect_stdout
import io
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from scripts import provenance, standards_maintenance as loop, workbench as wb


def proposal(prepared, *, claim_id="draft-four-field", text="Draft 04 defines a Problem HTTP field.", evidence=None, retire=None):
    frozen = prepared["protocol"]["frozen"]
    source = frozen["batch"][0]
    quote = "4.  The Problem HTTP Field" if source == "draft-04" else "1.  Introduction"
    evidence = evidence or [{"source": source, "quote": quote}]
    claim = {"id": claim_id, "text": text, "scope": "Specific supplied working-draft version; not a released requirement or universal rule",
             "attribution": "expressed", "evidence": evidence}
    operations = [{"op": "add", "assertion": claim}]
    if retire:
        operations.append({"op": "retire", "id": retire, "replacement": claim_id, "reason": "Authored mechanical integration exercise; preserve version scope and historical access."})
    return {"baseRevision": frozen["before"]["revision"], "accounting": {source: {"mode": "represented", "claims": [claim_id], "reason": "Authored saved-response fixture, not model evidence."}},
            "operations": operations, "rationale": "Authored test patch; reference validity is not a semantic grade."}


def inspect(prepared, value):
    return loop.inspect_proposal(prepared, json.dumps(value).encode())


class StandardsMaintenanceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with patch("urllib.request.urlopen", side_effect=AssertionError("offline only")):
            cls.first = loop.prepare("checkpoint-02", source_id="draft-04")
            cls.applied = inspect(cls.first, proposal(cls.first))

    def test_real_cutoff_intake_preserves_whole_artifacts_actor_ranges_and_rights(self):
        frozen = self.first["protocol"]["frozen"]
        self.assertEqual(frozen["batch"], ["draft-04"])
        self.assertEqual(len(frozen["before"]["received"]), 31)
        self.assertEqual(frozen["before"]["processed"], [])
        source = frozen["before"]["received"]["draft-04"]
        self.assertEqual(len(source["excerpts"]), 2)
        self.assertEqual(source["origin"]["artifact"], "draft-04")
        self.assertIn("IETF Trust", source["origin"]["legalNotice"])
        context = json.loads(frozen["messages"][1]["content"])
        self.assertNotIn("text", context["sources"]["draft-04"])
        self.assertEqual(context["sources"]["draft-04"]["excerpts"], source["excerpts"])
        self.assertEqual(context["coverage"]["pending_outside_batch"], 30)
        self.assertTrue(any("attributedTo" in s for s in frozen["before"]["received"].values()))
        self.assertFalse(self.first["canonical_acceptance"])

    def test_saved_patch_commits_projects_and_actually_round_trips(self):
        result = self.applied
        self.assertEqual(result["status"], "applied-in-isolated-copy")
        self.assertEqual(result["state"]["processed"], ["draft-04"])
        self.assertEqual(len(result["state"]["claims"]), 1)
        self.assertEqual(result["recovery"]["status"], "exercised")
        self.assertTrue(result["recovery"]["material_recovered"])
        self.assertEqual(wb.material(result["recovery"]["state"]), wb.material(result["state"]))
        self.assertEqual(result["state"]["received"], self.first["protocol"]["frozen"]["before"]["received"])
        handbook = result["after"]["projection"]["handbook"]
        self.assertTrue(handbook.startswith("# HTTP problem details\n"))
        self.assertIn("IETF Trust", handbook)
        self.assertIn("Source attribution and separate terms", handbook)
        self.assertIn("unreconciled", handbook)
        self.assertEqual(result["semantic_judgment"], "pending-human-review")
        self.assertFalse(result["canonical_acceptance"])
        graph = provenance.project(result["state"], dataset_id="standards-batch-test", projection_title=loop.TITLE)
        self.assertTrue(any("# HTTP problem details" in n.get("prov:value", "") for n in graph["@graph"]))

    def test_second_intake_retirement_keeps_old_payload_alias_source_paths_and_pending(self):
        before = copy.deepcopy(self.applied["state"])
        prepared = loop.prepare("checkpoint-06", state=before, source_id="draft-05")
        context = json.loads(prepared["protocol"]["frozen"]["messages"][1]["content"])
        self.assertEqual(set(context["sources"]), {"draft-04", "draft-05"})
        self.assertEqual(context["current_claims"], list(before["claims"].values()))
        evidence = [{"source": "draft-04", "quote": "4.  The Problem HTTP Field"}, {"source": "draft-05", "quote": "1.  Introduction"}]
        candidate = proposal(prepared, claim_id="draft-version-history", text="Keep the draft-version distinction and earlier field proposal recoverable.", evidence=evidence, retire="draft-four-field")
        result = inspect(prepared, candidate)
        self.assertEqual(result["status"], "applied-in-isolated-copy")
        self.assertEqual(result["state"]["processed"], ["draft-04", "draft-05"])
        self.assertEqual(len(result["state"]["claims"]), 1)
        self.assertEqual(result["state"]["history"]["draft-four-field"], before["history"]["draft-four-field"])
        self.assertEqual(wb.resolve(result["state"], "draft-four-field")["id"], "draft-version-history")
        self.assertTrue(wb.discover(result["state"], "Problem HTTP field")["hits"])
        self.assertEqual(result["recovery"]["status"], "exercised")
        self.assertEqual(before, self.applied["state"])

    def test_gap_spanning_or_changed_excerpt_is_never_accepted_as_source_prose(self):
        source = copy.deepcopy(self.first["protocol"]["frozen"]["before"]["received"]["draft-04"])
        quote = source["excerpts"][0]["text"][-80:] + "\n\n" + source["excerpts"][1]["text"][:80]
        self.assertIn(quote, source["text"])
        with self.assertRaises(ValueError):
            wb.check_evidence({"evidence": [{"source": "draft-04", "quote": quote}]}, {"draft-04": source}, canonical=True)
        source["excerpts"][0]["text"] += "changed"
        state = wb.new_state()
        with self.assertRaises(ValueError):
            wb.receive(state, "draft-04", source)
        self.assertFalse(state["received"])
        candidate = proposal(self.first, evidence=[{"source": "draft-04", "quote": quote}])
        self.assertEqual(inspect(self.first, candidate)["status"], "rejected-not-applied")

    def test_repeated_intake_future_cutoff_and_wrong_source_cannot_change_state(self):
        original = copy.deepcopy(self.applied["state"])
        a = loop.prepare("checkpoint-02", state=original)
        b = loop.prepare("checkpoint-02", state=original)
        self.assertEqual(a, b)
        self.assertEqual(a["protocol"]["frozen"]["before"], original)
        self.assertEqual(a["protocol"]["frozen"]["batch"], ["rfc7807"])
        for checkpoint, source in (("checkpoint-01", None), ("checkpoint-05", "draft-05"), ("checkpoint-02", "draft-04")):
            with self.assertRaises(ValueError):
                loop.prepare(checkpoint, state=original, source_id=source)
        self.assertEqual(original, self.applied["state"])

    def test_full_protection_and_byte_bound_failure_never_truncates_or_processes(self):
        original_export = wb.export_cue
        state = copy.deepcopy(self.applied["state"])
        def tiny(paths):
            value = original_export(paths)
            if "standardsMaintenance" in value:
                value["standardsMaintenance"]["maxPromptBytes"] = 1
            return value
        with patch.object(wb, "export_cue", side_effect=tiny), self.assertRaisesRegex(ValueError, "no source/claim truncation"):
            loop.prepare("checkpoint-06", state=state, source_id="draft-05")
        self.assertEqual(state, self.applied["state"])
        frozen = self.first["protocol"]["frozen"]
        self.assertLessEqual(len(json.dumps(frozen["messages"]).encode()), 131072)
        self.assertEqual(set(frozen["shown_sources"]), {"draft-04"})

    def test_source_free_noop_has_no_fake_intake_revision_or_recovery_claim(self):
        state = self.applied["state"]
        prepared = loop.prepare("checkpoint-02", state=state, maintenance=True)
        candidate = {"baseRevision": state["revision"], "operations": [], "accounting": {}, "rationale": "Authored no-op test, not a usefulness verdict."}
        result = inspect(prepared, candidate)
        self.assertEqual(result["status"], "no-op-in-isolated-copy")
        self.assertEqual(result["state"], state)
        self.assertEqual(result["recovery"]["status"], "not-exercised-no-change")
        self.assertEqual(prepared["protocol"]["frozen"]["batch"], [])
        with self.assertRaises(ValueError):
            loop.prepare("checkpoint-01", maintenance=True)

    def dependent(self):
        prepared = loop.prepare("checkpoint-02", state=self.applied["state"], source_id="draft-03")
        candidate = {"baseRevision": 1, "operations": [], "rationale": "Mechanical dependency-counter exercise; not a semantic dependency pass.",
                     "accounting": {"draft-03": {"mode": "dependent-no-op", "claims": ["draft-four-field"], "reason": "Authored accounting fixture.",
                                                 "basis": [{"source": "draft-04", "quote": "4.  The Problem HTTP Field"}]}}}
        return inspect(prepared, candidate)

    def test_processing_only_noop_exercises_recovery_without_claiming_semantic_change(self):
        result = self.dependent()
        self.assertEqual(result["status"], "processing-only-in-isolated-copy")
        self.assertEqual(result["state"]["revision"], 1)
        self.assertEqual(result["state"]["claims"], self.applied["state"]["claims"])
        self.assertEqual(result["state"]["processed"], ["draft-03", "draft-04"])
        self.assertEqual(result["recovery"]["status"], "exercised")
        self.assertEqual(result["recovery"]["restored"]["processed"], 1)

    def test_cannot_cite_processed_but_untransmitted_material(self):
        prepared = loop.prepare("checkpoint-02", state=self.dependent()["state"], source_id="rfc7807")
        self.assertNotIn("draft-03", prepared["protocol"]["frozen"]["shown_sources"])
        candidate = proposal(prepared, claim_id="hidden-source", evidence=[{"source": "rfc7807", "quote": "1.  Introduction"},
                                                                          {"source": "draft-03", "quote": "1.  Introduction"}])
        self.assertEqual(inspect(prepared, candidate)["status"], "rejected-not-applied")

    def test_private_full_context_approvals_and_pending_sources_do_not_leak(self):
        prepared = loop.prepare("checkpoint-06", state=self.applied["state"], source_id="draft-05")
        frozen = prepared["protocol"]["frozen"]
        self.assertEqual(loop.model_messages(prepared), frozen["messages"])
        detached = loop.model_messages(prepared)
        detached[0]["content"] = "caller mutation"
        self.assertNotEqual(detached, frozen["messages"])
        messages = json.dumps(frozen["messages"])
        self.assertNotIn("rfc9457", messages)
        self.assertNotIn("yes, seems pretty good", messages)
        for meaning in frozen["evaluation"]["original_full_context_approval"]["reviewed_meanings"].values():
            self.assertNotIn(meaning, messages)
        self.assertIn("not this partial working view", frozen["evaluation"]["boundary"])
        self.assertEqual(frozen["plan"]["plannedCalls"], 0)
        self.assertIsNone(frozen["plan"]["model"])
        self.assertIsNone(frozen["plan"]["provider"])

    def test_rejected_duplicate_nonfinite_stale_and_oversized_proposals_preserve_bytes(self):
        values = [b'{"baseRevision":0,"baseRevision":1}', b'{"x": NaN}', b'{"x": 1e999}']
        for raw in values:
            result = loop.inspect_proposal(self.first, raw)
            self.assertEqual(result["status"], "invalid-json-not-applied")
            self.assertEqual(result["state"], self.first["protocol"]["frozen"]["before"])
        candidate = proposal(self.first)
        candidate["baseRevision"] = 99
        self.assertEqual(inspect(self.first, candidate)["status"], "rejected-not-applied")
        result = loop.inspect_proposal(self.first, b"x" * (1048576 + 1))
        self.assertEqual(result["status"], "oversized-not-applied")
        self.assertFalse(result["input"]["complete"])
        changed = copy.deepcopy(self.first)
        changed["protocol"]["frozen"]["before"]["revision"] = 1
        with self.assertRaises(ValueError):
            loop.inspect_proposal(changed, b"{}")

    def test_reference_complete_false_prose_still_passes_mechanics_not_semantics(self):
        result = inspect(self.first, proposal(self.first, text="All HTTP headers are now forbidden."))
        self.assertEqual(result["status"], "applied-in-isolated-copy")
        self.assertEqual(result["recovery"]["status"], "exercised")
        self.assertFalse(result["canonical_acceptance"])
        self.assertEqual(result["semantic_judgment"], "pending-human-review")

    def test_offline_cli_saved_response_and_context_flags(self):
        with TemporaryDirectory() as directory, redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            path, raw, output = [Path(directory) / name for name in ("prepared.json", "patch.json", "inspection.json")]
            with patch("urllib.request.urlopen", side_effect=AssertionError("offline only")):
                self.assertEqual(loop.main(["--checkpoint", "checkpoint-02", "--source-id", "draft-04", "--output", str(path)]), 0)
                saved = json.loads(path.read_text())
                raw.write_text(json.dumps(proposal(saved)))
                self.assertEqual(loop.main(["--prepared", str(path), "--proposal", str(raw), "--output", str(output)]), 0)
            self.assertEqual(json.loads(output.read_text())["status"], "applied-in-isolated-copy")
            graph_path = Path(directory) / "view.jsonld"
            self.assertEqual(provenance.main(["--input", str(output), "--dataset-id", "public-cli-test",
                                              "--projection-title", loop.TITLE, "--output", str(graph_path)]), 0)
            self.assertTrue(any("# HTTP problem details" in n.get("prov:value", "")
                                for n in json.loads(graph_path.read_text())["@graph"]))
            with self.assertRaises(ValueError):
                loop.main(["--checkpoint", "checkpoint-02", "--output", str(output)])
            with self.assertRaises(SystemExit):
                loop.main(["--prepared", str(path), "--proposal", str(raw), "--checkpoint", "checkpoint-01", "--output", "not-written"])
