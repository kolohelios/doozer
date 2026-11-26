from contextlib import redirect_stdout
import io
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from scripts import source_inbox as inbox, watch_workbench as watch
from tests.test_source_inbox import SOURCE, reconciliation


class WatchWorkbenchTests(unittest.TestCase):
    def test_playback_shows_real_receipts_commits_and_projection_diffs(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "watch.sqlite"
            lines, pauses = [], []
            with patch("urllib.request.urlopen", side_effect=AssertionError("offline only")):
                status = watch.play(path, emit=lines.append, pause=lambda: pauses.append(len(lines)))
            snapshot = inbox.snapshot(path)
            projection = inbox.projection(path)
        self.assertEqual(status, 0)
        self.assertEqual(len(pauses), 7)
        commits = [line.strip() for line in lines if line.startswith("  Committed")]
        self.assertEqual(len(commits), len(snapshot["state"]["journal"]))
        for position, (line, record) in enumerate(zip(commits, snapshot["state"]["journal"]), 1):
            self.assertEqual(line, f"Committed · position {position}, revision {record['revision']}")
        self.assertTrue(any(line.startswith("  Received · no #") and line.endswith('"No."') for line in lines))
        self.assertIn("  Pending   · incident", lines)
        self.assertIn("  No commit · receipt only", lines)
        self.assertIn("  No commit · batch already processed", lines)
        self.assertTrue(any(line.startswith("  Redelivery · incident #") for line in lines))
        self.assertTrue(any(line.startswith("    +") and "automatic-retr" in line for line in lines))
        self.assertTrue(any(line.startswith("    -") and "fixture://" in line for line in lines))
        self.assertEqual(projection["status"], "caught-up")

    def test_maintenance_playback_shows_consolidation_noop_and_recovery(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "watch.sqlite"
            lines, checkpoints = [], []

            def pause():
                checkpoints.append((inbox.snapshot(path), inbox.projection(path)))

            with patch("urllib.request.urlopen", side_effect=AssertionError("offline only")):
                self.assertEqual(watch.play(path, emit=lines.append, pause=pause, maintenance=True), 0)
            final, projection = inbox.snapshot(path), inbox.projection(path)
        before, inspected, consolidated, no_change, restored = checkpoints[-5:]
        self.assertEqual([item[0]["reconciliation_position"] for item in checkpoints[-5:]], [6, 6, 7, 7, 8])
        self.assertEqual(inspected, before)
        self.assertIn("  Inspected · 3 → 2 active claims in a copy; not committed", lines)
        notice = "    Exact-scope search · 2 active labels would disappear; see history separately"
        self.assertEqual(lines.count(notice), 1)
        maintained = lines.index("  Maintained · position 7, revision 6")
        history = "  History   · 2 inactive records found by former exact scope; not active guidance"
        self.assertLess(lines.index(notice), maintained)
        rehearsal = "    Recovery  · restore and exact replay checked in a copy"
        self.assertEqual(lines.count(rehearsal), 1)
        self.assertLess(lines.index(rehearsal), maintained)
        self.assertEqual(lines.count(history), 1)
        self.assertLess(maintained, lines.index(history))
        self.assertLess(lines.index(history), lines.index("\nMaintenance · recorded no-op"))
        self.assertIn("    new-1 → claim-slot-1", lines)
        self.assertIn("claim-slot-1", consolidated[0]["state"]["claims"])
        self.assertEqual(no_change, consolidated)
        self.assertEqual(restored[0]["state"]["claims"], before[0]["state"]["claims"])
        self.assertEqual(final["state"]["claims"], consolidated[0]["state"]["claims"])
        self.assertEqual(final["state"]["received"], before[0]["state"]["received"])
        self.assertEqual(final["state"]["processed"], before[0]["state"]["processed"])
        self.assertEqual(final["state"]["journal"][-1]["replayOf"], 6)
        self.assertEqual([len(item[1]["projection"]["claims"]) for item in (before, consolidated, restored)], [3, 2, 3])
        self.assertEqual(projection["projection"]["handbook"], consolidated[1]["projection"]["handbook"])
        self.assertEqual(projection["status"], "caught-up")
        self.assertIn("  No commit · position 7, revision 6", lines)
        self.assertIn("\nComplete · 9 durable commits, no model calls.", lines)

    def test_exact_duplicate_demo_shows_only_real_cleanup_and_recovery(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "duplicates.sqlite"
            lines, checkpoints = [], []
            with patch("urllib.request.urlopen", side_effect=AssertionError("offline only")):
                self.assertEqual(watch.play_exact_duplicates(path, emit=lines.append,
                                 pause=lambda: checkpoints.append(inbox.snapshot(path))), 0)
            activity = inbox.activity(path)
            self.assertEqual([row["kind"] for row in activity["commits"]],
                             ["patch", "maintenance", "maintenance", "restore", "replay"])
            self.assertEqual([row["reconciliation_position"] for row in checkpoints], [2, 3, 4, 5])
            for index, entry in enumerate(checkpoints):
                claims = entry["state"]["claims"]
                self.assertEqual("east-vent-copy" in claims, index in (0, 2))
                self.assertIn("west-fan", claims)
            self.assertEqual([line for line in lines if line.startswith("Repeat")], ["Repeat    · no-change; 0 retirements"])
            self.assertEqual(sum(line.startswith(("Committed", "Maintained", "Restored", "Replayed")) for line in lines), 5)
            self.assertEqual(inbox.projection(path)["status"], "caught-up")
            physical = path.read_bytes()
            with redirect_stdout(io.StringIO()) as output:
                self.assertEqual(inbox.main(["--db", str(path), "claim-timeline", "--claim", "east-vent-copy"]), 0)
            timeline = json.loads(output.getvalue())
            self.assertEqual(timeline["reconciliation_position"], 5)
            self.assertEqual([(row["position"], row["kind"], row["after"]) for row in timeline["events"]], [
                (2, "maintenance", {"active": True, "resolves_to": "east-vent-copy"}),
                (3, "maintenance", {"active": False, "resolves_to": "east-vent"}),
                (4, "restore", {"active": True, "resolves_to": "east-vent-copy"}),
                (5, "replay", {"active": False, "resolves_to": "east-vent"}),
            ])
            self.assertEqual([row["position"] for row in inbox.claim_timeline(path, "west-fan")["events"]], [1])
            self.assertEqual(inbox.claim_timeline(path, "unknown")["status"], "unknown-claim")
            self.assertEqual(path.read_bytes(), physical)

    def test_prepared_batch_demo_does_not_commit_before_apply(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "batch.sqlite"
            lines, pauses = [], []

            def pause():
                pauses.append((path.read_bytes(), inbox.pending(path), inbox.snapshot(path)))

            with patch("urllib.request.urlopen", side_effect=AssertionError("offline only")):
                self.assertEqual(watch.play_prepared_batch(path, emit=lines.append, pause=pause), 0)
            before, inspected, applied, restored = pauses
            self.assertEqual(before, inspected)
            self.assertEqual(inspected[1]["pending_count"], 2)
            self.assertEqual(inspected[2]["state"]["claims"], {})
            self.assertEqual(applied[1]["pending_count"], 0)
            self.assertEqual(restored[1]["pending_count"], 2)
            self.assertEqual(restored[2]["state"]["claims"], {})
            self.assertEqual(inbox.pending(path)["pending_count"], 0)
            current = inbox.projection(path)
            self.assertEqual(current["status"], "caught-up")
            self.assertEqual(current["projection"]["claims"], ["east-fan", "east-vent", "west-fan"])
            final = inbox.snapshot(path)["state"]
            self.assertEqual(final["claims"], applied[2]["state"]["claims"])
            self.assertEqual(final["processed"], applied[2]["state"]["processed"])
            self.assertEqual(final["received"], before[2]["state"]["received"])
            activity = inbox.activity(path)
            self.assertEqual(activity["positions"], (3, 2))
            self.assertEqual([row["kind"] for row in activity["commits"]], ["patch", "restore", "replay"])
        self.assertEqual([line for line in lines if line.startswith("Pending")], [
            "Pending   · 2 sources", "Pending   · 0 sources; 3 active claims",
            "Pending   · 2 sources; 0 active claims", "Pending   · 0 sources; 3 active claims",
        ])
        preview = lines.index("Inspected · 0 → 3 active claims in a copy; not committed")
        commit, = [i for i, line in enumerate(lines) if line.startswith("Committed")]
        rehearsal = lines.index("Recovery  · restore and exact replay checked in a copy")
        self.assertLess(preview, rehearsal)
        self.assertLess(rehearsal, commit)
        self.assertNotIn("circulation fan", "\n".join(lines))

    def test_contextual_reply_demo_restores_and_replays_scoped_discovery(self):
        scope = "automatic-retries"
        with TemporaryDirectory() as directory:
            path = Path(directory) / "reply.sqlite"
            lines, views = [], []

            def pause():
                views.append(inbox.browse(path, scope))

            self.assertEqual(watch.play_prepared_batch(path, emit=lines.append, pause=pause, contextual_reply=True), 0)
            self.assertEqual([len(view["claims"]) for view in views], [0, 0, 1, 0])
            self.assertEqual([view["positions"]["intake"] for view in views], [9] * 4)
            final = inbox.browse(path, scope)
            self.assertEqual(final["claims"], views[2]["claims"])
            self.assertEqual(final["positions"], {"reconciliation": 7, "intake": 9})
            evidence = inbox.evidence(path, "automatic-retry-boundary")
            self.assertEqual({row["source"]: row["reply_to"] for row in evidence["citations"] if "reply_to" in row},
                             {"no": "proposal"})
            self.assertIn("no recoverable referent", inbox.evidence(path, "detached-stop")["claim"]["text"])
        self.assertIn("Context   · no replies to proposal; both selected in the batch", lines)
        self.assertIn("Search    · automatic-retries scope would gain: automatic-retry-boundary", lines)

    def test_existing_inbox_watch_reports_durable_changes_only(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "watch.sqlite"
            lines = []
            inbox.receive(path, "count-one", SOURCE)
            previous = watch.poll(path, emit=lines.append)
            self.assertEqual(lines[0], "Received  · intake 1: count-one")
            self.assertIn("Reader    · missing", lines[1])
            self.assertNotIn(SOURCE["text"], "\n".join(lines))
            lines.clear()
            before = inbox.snapshot(path)
            cached = inbox.projection(path)
            inbox.receive(path, "count-one", SOURCE)
            invalid = reconciliation()
            invalid["patch"]["accounting"] = {}
            invalid["patch"]["rationale"] = "synthetic-body-not-retained"
            with self.assertRaises(ValueError):
                inbox.commit(path, "invalid", **invalid)
            previous = watch.poll(path, emit=lines.append, previous=previous)
            self.assertEqual(lines, ["Rejected  · attempt 1 at reconciliation 0: invalid (patch not applied)"])
            self.assertEqual(inbox.snapshot(path), before)
            self.assertEqual(inbox.projection(path), cached)
            self.assertNotIn(b"synthetic-body-not-retained", path.read_bytes())
            lines.clear()
            previous = watch.poll(path, emit=lines.append, previous=previous)
            self.assertEqual(lines, [])

            inbox.commit(path, "apply-one", **reconciliation())
            inbox.refresh_projection(path)
            inbox.restore(path, "undo-one", base_position=1,
                          request={"baseRevision": 1, "targetPosition": 0, "reason": "Undo."})
            previous = watch.poll(path, emit=lines.append, previous=previous)
            self.assertEqual(lines[:2], ["Committed · reconciliation 1, revision 1: apply-one",
                                         "Restored  · reconciliation 2, revision 2: undo-one"])
            self.assertIn("behind", lines[-1])
            lines.clear()
            inbox.replay(path, "redo-one", base_position=2, journal_position=0, base_revision=2)
            previous = watch.poll(path, emit=lines.append, previous=previous)
            self.assertEqual(lines[0], "Replayed  · reconciliation 3, revision 3: redo-one")
            lines.clear()
            inbox.refresh_projection(path)
            watch.poll(path, emit=lines.append, previous=previous)
            self.assertEqual(len(lines), 1)
            self.assertIn("caught-up", lines[0])

    def test_explain_reads_original_effects_after_restore_and_replay(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "watch.sqlite"
            inbox.receive(path, "count-one", SOURCE)
            inbox.commit(path, "apply-one", **reconciliation())
            original = inbox.explain(path, 1)
            inbox.receive(path, "count-two", SOURCE)
            inbox.restore(path, "undo-one", base_position=1,
                          request={"baseRevision": 1, "targetPosition": 0, "reason": "Undo."})
            inbox.replay(path, "redo-one", base_position=2, journal_position=0, base_revision=2)
            before = path.read_bytes()
            self.assertEqual(inbox.explain(path, 1), original)
            self.assertEqual(original["processed"], ["count-one"])
            self.assertEqual(original["source_anchors"], {"count-one": SOURCE["anchor"]})
            self.assertEqual(original["added_claims"]["claim-count-one"]["evidence"][0]["quote"], SOURCE["text"])
            restored = inbox.explain(path, 2)
            self.assertEqual(restored["reason"], "Undo.")
            self.assertEqual(restored["target_prefix"], 0)
            self.assertEqual(restored["returned_to_pending"], ["count-one"])
            self.assertEqual(restored["removed_claims"], original["added_claims"])
            with redirect_stdout(io.StringIO()) as output:
                self.assertEqual(watch.main(["--db", str(path), "--explain", "3"]), 0)
            replayed = json.loads(output.getvalue())
            self.assertEqual(replayed["replayed_position"], 1)
            self.assertEqual(replayed["added_claims"], original["added_claims"])
            with self.assertRaisesRegex(ValueError, "unknown reconciliation position"):
                inbox.explain(path, 4)
            self.assertEqual(path.read_bytes(), before)

    def test_rejected_commit_is_not_reported_as_applied(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "watch.sqlite"
            lines = []
            with patch.object(inbox, "commit", side_effect=ValueError("test rejection")):
                self.assertEqual(watch.play(path, emit=lines.append), 2)
            snapshot = inbox.snapshot(path)
        self.assertTrue(any(line.startswith("  Proposed") for line in lines))
        self.assertIn("  Rejected  · test rejection", lines)
        self.assertFalse(any(line.startswith(("  Committed", "  Refreshed", "\nComplete")) for line in lines))
        self.assertEqual(set(snapshot["state"]["received"]), {"guide", "retry"})
        self.assertEqual(snapshot["reconciliation_position"], 0)
