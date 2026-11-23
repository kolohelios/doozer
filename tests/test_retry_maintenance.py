import copy
from contextlib import redirect_stderr, redirect_stdout
import io
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from scripts import retry_maintenance as experiment, workbench as wb
from scripts.workbench_models import RecordedBackend


class RetryMaintenanceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with patch("urllib.request.urlopen", side_effect=AssertionError("offline only")):
            cls.result = experiment.run()
        cls.scenario = wb.export_cue(sorted((wb.ROOT / "corpus").glob("*.cue")))["scenarios"]["retry-safety"]
        cls.settings = cls.result["settings"]
        cls.rounds = {r["step"]: r for r in cls.result["rounds"]}
        cls.before = wb.run(cls.scenario, RecordedBackend())["state"]
        cls.final = cls.result["policies"]["maintained"]["state"]

    def consolidate(self, state, change=None):
        proposal = copy.deepcopy(self.settings["consolidation"])
        if change:
            change(proposal)
        return wb.maintain(state, proposal["patch"], proposal["analysis"], proposal["route"])

    def restored(self):
        return wb.restore(self.final, {"baseRevision": self.final["revision"], "targetPosition": 3, "reason": "Test local recovery."})

    def test_nine_rounds_compare_same_additions_with_only_retirements_ablated(self):
        self.assertEqual(len(self.result["rounds"]), 9)
        for name, expected in self.settings["expected"].items():
            self.assertEqual(self.rounds[name]["maintained"]["active_claims"], expected["maintained"])
            self.assertEqual(self.rounds[name]["append_only"]["active_claims"], expected["appendOnly"])
        maintained, baseline = (self.result["policies"][p]["state"] for p in ("maintained", "append_only"))
        self.assertEqual(maintained["history"], baseline["history"])
        self.assertEqual(maintained["received"], baseline["received"])
        self.assertEqual(maintained["processed"], baseline["processed"])
        self.assertEqual(len(maintained["history"]), 7)
        self.assertEqual(baseline["redirects"], {})
        for a, b in zip(maintained["journal"], baseline["journal"]):
            expected = copy.deepcopy(a["patch"])
            expected["operations"] = [op for op in expected["operations"] if op["op"] != "retire"]
            self.assertEqual(expected, b["patch"])

    def test_source_free_many_to_one_consolidation_retains_context_and_ambiguity(self):
        self.assertEqual((len(self.before["claims"]), len(self.final["claims"])), (3, 2))
        self.assertEqual(self.before["received"], self.final["received"])
        self.assertEqual(self.before["processed"], self.final["processed"])
        self.assertEqual(self.final["journal"][-1]["batch"], [])
        self.assertTrue(self.final["journal"][-1]["maintenance"])
        current = self.final["claims"]["retry-safety-current"]
        self.assertEqual(current["text"], self.before["claims"]["retry-safety-scoped"]["text"] + " " + self.before["claims"]["automatic-retry-boundary"]["text"])
        for phrase in ("manual-replay path suppresses", "notification side effects can duplicate", "No rejects extending", "does not revoke database-write deduplication"):
            self.assertIn(phrase, current["text"])
        self.assertIn("detached-stop", self.final["claims"])
        self.assertEqual({c["source"] for c in current["evidence"]}, {"guide", "retry", "code", "incident", "clarification", "manual", "proposal", "no"})
        self.assertEqual(self.final["received"]["no"]["replyTo"], "proposal")

    def test_structural_compactness_is_not_reported_as_semantic_accuracy(self):
        final = self.rounds["maintenance-consolidation"]
        self.assertLess(final["maintained"]["claim_words"], final["append_only"]["claim_words"])
        self.assertEqual(final["maintained"]["active_source_ids"], final["append_only"]["active_source_ids"])
        self.assertTrue(all(r["semantic_judgment"] == "pending-human-review" and r["required"] and r["forbidden"] for r in self.result["rounds"]))
        self.assertEqual(self.result["network_calls"], 0)
        self.assertTrue(all(not t["network"] for p in self.result["policies"].values() for t in p["trace"]))

    def test_reader_probes_and_both_projections_survive_each_round(self):
        for round_ in self.result["rounds"]:
            for policy in ("maintained", "append_only"):
                view = round_[policy]
                self.assertEqual(set(view["reader_probes"]), set(self.settings["queries"]))
                absent = view["reader_probes"]["payments"]
                self.assertEqual(absent["status"], "no-matching-knowledge")
                self.assertIn("does not establish global absence", absent["coverage"]["boundary"])
        projection = wb.project(self.final)
        for claim in self.final["claims"].values():
            for consumer in ("handbook", "agentContext"):
                self.assertIn(claim["text"], projection[consumer])
                for citation in claim["evidence"]:
                    self.assertIn(self.final["received"][citation["source"]]["anchor"], projection[consumer])

    def test_former_wording_and_every_old_reference_reach_current_or_history(self):
        hits = wb.discover(self.final, "implementation")["hits"]
        self.assertEqual(hits[0]["claim"]["id"], "retry-safety-current")
        self.assertNotIn("implementation", hits[0]["claim"]["text"])
        self.assertIn("database-writes", hits[0]["historical_matches"])
        for ref in self.final["history"]:
            self.assertIsNotNone(wb.resolve(self.final, ref))
        for ref in ("retry-guidance", "database-writes", "notification-exception", "retry-safety-scoped", "automatic-retry-boundary"):
            self.assertEqual(wb.resolve(self.final, ref)["id"], "retry-safety-current")
            self.assertIn(ref, self.final["history"])

    def test_pending_incident_is_not_silently_included_as_current_evidence(self):
        received = self.rounds["received-not-processed"]["maintained"]
        self.assertEqual(received["pending"], ["incident"])
        self.assertNotIn("incident", received["active_source_ids"])
        self.assertEqual(received["reader_probes"]["notifications"]["pending"], ["incident"])
        self.assertNotIn("fixture://retry/incident/7", received["projection"]["handbook"])
        for consumer in ("handbook", "agentContext"):
            self.assertIn("3 of 4 locally received", received["projection"][consumer])
            self.assertIn("Received evidence remains unreconciled", received["projection"][consumer])

    def test_repeated_delivery_echo_projection_and_maintenance_do_not_grow_view(self):
        self.assertEqual(self.rounds["duplicate-delivery"]["maintained"]["projection"], self.rounds["scoped-mitigation"]["maintained"]["projection"])
        echo = self.rounds["echo-and-projection"]["maintained"]["projection"]
        previous = self.rounds["contextual-no"]["maintained"]["projection"]
        self.assertEqual(echo["claims"], previous["claims"])
        self.assertEqual(echo["revision"], previous["revision"])
        for consumer in ("handbook", "agentContext"):
            # Processing coverage changes from 9/9 to 11/11, not the knowledge.
            material_body = lambda text: [p for p in text.split("\n\n") if not p.startswith("Processed source snapshot:")]
            self.assertEqual(material_body(echo[consumer]), material_body(previous[consumer]))
            self.assertIn("11 of 11 locally received", echo[consumer])
        c = self.settings["consolidation"]
        again = wb.maintain(self.final, c["repeatPatch"], c["analysis"], c["route"])
        self.assertEqual(again, self.final)
        self.assertTrue(self.result["repeated_maintenance_unchanged"])
        self.assertFalse({"echo", "handbook"} & {citation["source"] for claim in self.final["claims"].values() for citation in claim["evidence"]})

    def test_rollback_is_a_monotonic_journal_event_not_history_erasure(self):
        original = copy.deepcopy(self.final)
        restored = self.restored()
        prefix = wb.run(self.scenario, RecordedBackend(), through="incident-reconciled")["state"]
        self.assertEqual(wb.material(restored), wb.material(prefix))
        self.assertEqual(restored["revision"], self.final["revision"] + 1)
        self.assertEqual(restored["received"], self.final["received"])
        self.assertEqual(restored["history"], self.final["history"])
        self.assertEqual(restored["journal"][:-1], self.final["journal"])
        self.assertEqual(restored["journal"][-1]["kind"], "restore")
        self.assertIn("manual", wb.discover(restored, "notifications")["pending"])
        for consumer in ("handbook", "agentContext"):
            self.assertIn("4 of 11 locally received", wb.project(restored)[consumer])
            self.assertIn("Received evidence remains unreconciled", wb.project(restored)[consumer])
        self.assertIsNone(wb.resolve(restored, "retry-safety-current"))
        self.assertIn("retry-safety-current", restored["history"])
        self.assertEqual(self.final, original)

    def test_exact_replay_recovers_material_view_with_new_revisions(self):
        current = self.restored()
        for index in range(3, len(self.final["journal"])):
            current = wb.replay(current, index, base_revision=current["revision"])
        self.assertEqual(wb.material(current), wb.material(self.final))
        self.assertEqual(current["received"], self.final["received"])
        self.assertEqual(current["history"], self.final["history"])
        self.assertGreater(current["revision"], self.final["revision"])
        self.assertEqual(wb.project(current)["handbook"], wb.project(self.final)["handbook"])
        self.assertEqual([r["replayOf"] for r in current["journal"][-4:]], [3, 4, 5, 6])
        self.assertTrue(self.result["recovery"]["material_recovered"])

    def test_stale_restore_and_replay_fail_without_partial_changes(self):
        original = copy.deepcopy(self.final)
        with self.assertRaisesRegex(ValueError, "stale restore"):
            wb.restore(self.final, {"baseRevision": 0, "targetPosition": 3, "reason": "Stale."})
        with self.assertRaisesRegex(ValueError, "stale replay"):
            wb.replay(self.final, 3, base_revision=0)
        self.assertEqual(self.final, original)
        restored = self.restored()
        entry = self.final["journal"][3]
        with self.assertRaisesRegex(ValueError, "stale neighborhood"):
            wb.commit(restored, entry["patch"], entry["batch"], entry["analysis"], entry["route"])

    def test_replay_cannot_change_payload_or_reactivate_ids_in_changed_neighborhood(self):
        restored = self.restored()
        entry = copy.deepcopy(self.final["journal"][3])
        entry["patch"]["baseRevision"] = restored["revision"]
        entry["patch"]["operations"][0]["assertion"]["text"] = "A different interpretation."
        before = copy.deepcopy(restored)
        with self.assertRaisesRegex(ValueError, "exact accepted patch"):
            wb.commit(restored, entry["patch"], entry["batch"], entry["analysis"], entry["route"], replay_of=3)
        self.assertEqual(restored, before)
        next(iter(restored["claims"].values()))["text"] = "A changed neighborhood."
        with self.assertRaisesRegex(ValueError, "original material preconditions"):
            wb.replay(restored, 3, base_revision=restored["revision"])

    def test_maintenance_cannot_consume_pending_sources_or_drop_old_paths(self):
        restored = self.restored()
        proposal = copy.deepcopy(self.settings["consolidation"])
        proposal["patch"]["baseRevision"] = restored["revision"]
        with self.assertRaisesRegex(ValueError, "unavailable"):
            wb.maintain(restored, proposal["patch"], proposal["analysis"], proposal["route"])
        before = copy.deepcopy(self.before)
        def drop_source(p):
            p["patch"]["operations"][0]["assertion"]["evidence"] = [c for c in p["patch"]["operations"][0]["assertion"]["evidence"] if c["source"] != "no"]
        with self.assertRaisesRegex(ValueError, "drops source"):
            self.consolidate(self.before, drop_source)
        self.assertEqual(self.before, before)

    def test_source_free_mode_cannot_fake_ingestion_accounting(self):
        proposal = copy.deepcopy(self.settings["consolidation"])
        proposal["patch"]["accounting"] = {"manual": {"mode": "represented", "claims": ["retry-safety-current"], "reason": "False intake."}}
        with self.assertRaisesRegex(ValueError, "unaccounted"):
            wb.maintain(self.before, proposal["patch"], proposal["analysis"], proposal["route"])
        with self.assertRaisesRegex(ValueError, "cannot pretend"):
            wb.commit(self.before, proposal["patch"], ["manual"], proposal["analysis"], proposal["route"], maintenance=True)

    def test_legacy_incomplete_journals_invalid_positions_and_restore_events_not_replayed(self):
        state = copy.deepcopy(self.final)
        del state["journal"][0]["beforeProcessed"]
        with self.assertRaisesRegex(ValueError, "legacy journal"):
            wb.restore(state, {"baseRevision": state["revision"], "targetPosition": 0, "reason": "No inferred recovery metadata."})
        for position in (-1, True, 1000):
            with self.subTest(position=position), self.assertRaises(ValueError):
                wb.historical_view(self.final, position)
        restored = self.restored()
        with self.assertRaisesRegex(ValueError, "not a restore event"):
            wb.replay(restored, len(self.final["journal"]), base_revision=restored["revision"])

    def test_restore_of_current_material_view_is_noop_and_history_is_immutable(self):
        self.assertEqual(wb.restore(self.final, {"baseRevision": self.final["revision"], "targetPosition": len(self.final["journal"]), "reason": "Already current."}), self.final)
        restored = self.restored()
        back = wb.restore(restored, {"baseRevision": restored["revision"], "targetPosition": len(self.final["journal"]), "reason": "Undo the recovery through its own journal prefix."})
        self.assertEqual(wb.material(back), wb.material(self.final))
        self.assertGreater(back["revision"], restored["revision"])
        state = copy.deepcopy(self.final)
        state["journal"][3]["before"]["notification-exception"]["text"] = "Forged historical interpretation."
        with self.assertRaisesRegex(ValueError, "immutable claim history"):
            wb.restore(state, {"baseRevision": state["revision"], "targetPosition": 3, "reason": "Reject tampered target."})

    def test_literal_source_checks_still_do_not_prove_semantic_preservation(self):
        # Deliberately preserve this counterexample, not a keyword-based oracle.
        def lose_meaning(p):
            p["patch"]["operations"][0]["assertion"]["text"] = "All retry paths are safe."
        bad = self.consolidate(self.before, lose_meaning)
        self.assertEqual(bad["claims"]["retry-safety-current"]["text"], "All retry paths are safe.")
        self.assertEqual(bad["claims"]["retry-safety-current"]["evidence"], self.final["claims"]["retry-safety-current"]["evidence"])
        self.assertEqual(len(bad["claims"]), len(self.final["claims"]))

    def test_offline_cli_no_overwrite_or_live_option(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "maintenance.json"
            with redirect_stdout(io.StringIO()):
                self.assertEqual(experiment.main(["--output", str(path)]), 0)
            self.assertEqual(json.loads(path.read_text())["network_calls"], 0)
            with self.assertRaises(ValueError):
                experiment.main(["--output", str(path)])
            with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
                experiment.main(["--output", str(path), "--live"])
