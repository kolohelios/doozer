"""Offline fixture integrity tests; these do not grade engine/model semantics."""

import copy
import datetime
import json
from pathlib import Path
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "corpus/schema.cue"


def validate_schedule(corpus):
    """Check temporal/reference invariants beyond CUE's structural contract."""
    for name, scenario in corpus["scenarios"].items():
        sources = scenario["sources"]
        anchors = [source["anchor"] for source in sources.values()]
        if len(anchors) != len(set(anchors)):
            raise ValueError(f"{name}: duplicate source anchor")
        for source_id, source in sources.items():
            datetime.datetime.strptime(source["saidAt"], "%Y-%m-%dT%H:%M:%SZ")
            # All lineage edges must be acyclic; replies are context, not proof.
            def visit(node, path):
                if node in path:
                    raise ValueError(f"{name}: cyclic source lineage at {node}")
                current = sources[node]
                parents = current.get("derivedFrom", [])
                if "replyTo" in current:
                    parents = parents + [current["replyTo"]]
                for parent in parents:
                    visit(parent, path | {node})
            visit(source_id, set())

        received, processed, previous = set(), set(), set()
        for step in scenario["steps"]:
            context = f"{name}/{step['id']}"
            if step["id"] in previous:
                raise ValueError(f"{context}: duplicate step ID")
            received.update(step["receive"])
            if not set(step["reconcile"]) <= received:
                raise ValueError(f"{context}: reconciled before receipt")
            processed.update(step["reconcile"])
            expected = step["expect"]
            pending = expected["pending"]
            if len(pending) != len(set(pending)) or set(pending) != received - processed:
                raise ValueError(f"{context}: incorrect pending set")
            equivalent = expected.get("equivalentTo")
            if equivalent is not None and equivalent not in previous:
                raise ValueError(f"{context}: equivalence must reference an earlier step")
            checks = expected["must"] + expected["mustNot"]
            ids = [check["id"] for check in checks]
            if len(ids) != len(set(ids)):
                raise ValueError(f"{context}: duplicate outcome ID")
            for outcome in expected["must"]:
                if not set(outcome["evidence"]) <= processed:
                    raise ValueError(f"{context}: outcome cites unprocessed evidence")
            for query in expected.get("queries", []):
                allowed = received if query["state"] == "pending" else processed
                if not set(query["evidence"]) <= allowed:
                    raise ValueError(f"{context}: query cites unavailable evidence")
                if query["state"] == "pending" and not pending:
                    raise ValueError(f"{context}: pending query without a backlog")
            previous.add(step["id"])
        if received != set(sources):
            raise ValueError(f"{name}: unused sources")


class CorpusTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        files = sorted((ROOT / "corpus").glob("*.cue"))
        result = subprocess.run(
            ["cue", "export", *map(str, files)],
            check=True, capture_output=True, text=True,
        )
        cls.corpus = json.loads(result.stdout)

    def test_fixture_schedule(self):
        validate_schedule(self.corpus)

    def test_initial_domains_and_coverage(self):
        self.assertEqual(set(self.corpus["scenarios"]), {
            "retry-safety", "cnpg-rds", "breaking-changes", "code-review", "visitor-access",
        })
        tags = {tag for scenario in self.corpus["scenarios"].values() for tag in scenario["tags"]}
        self.assertTrue({
            "replay", "out-of-order", "freshness", "one-word-reversal", "ambiguity",
            "projection-feedback", "echo", "nonengineering", "exception-preservation",
        } <= tags)

    def assert_schema_rejects(self, mutate):
        corpus = copy.deepcopy(self.corpus)
        mutate(corpus["scenarios"]["retry-safety"])
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "invalid.json"
            path.write_text(json.dumps(corpus))
            result = subprocess.run(
                ["cue", "vet", "-c", str(SCHEMA), str(path), "-d", "#Corpus"],
                capture_output=True, text=True,
            )
        self.assertNotEqual(result.returncode, 0, "invalid fixture passed CUE validation")

    def test_schema_accepts_exported_corpus(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "valid.json"
            path.write_text(json.dumps(self.corpus))
            subprocess.run(
                ["cue", "vet", "-c", str(SCHEMA), str(path), "-d", "#Corpus"], check=True,
            )

    def test_unknown_source_is_rejected(self):
        self.assert_schema_rejects(lambda s: s["steps"][0]["receive"].append("missing"))

    def test_unknown_evidence_is_rejected(self):
        self.assert_schema_rejects(
            lambda s: s["steps"][0]["expect"]["must"][0]["evidence"].append("missing")
        )

    def test_unknown_reply_target_is_rejected(self):
        self.assert_schema_rejects(lambda s: s["sources"]["no"].update(replyTo="missing"))

    def test_unknown_lineage_is_rejected(self):
        self.assert_schema_rejects(
            lambda s: s["sources"]["handbook"]["derivedFrom"].append("missing")
        )

    def test_empty_outcomes_are_rejected(self):
        self.assert_schema_rejects(lambda s: s["steps"][0]["expect"].update(must=[]))

    def test_empty_forbidden_outcomes_are_rejected(self):
        self.assert_schema_rejects(lambda s: s["steps"][0]["expect"].update(mustNot=[]))

    def test_empty_evidence_is_rejected(self):
        self.assert_schema_rejects(
            lambda s: s["steps"][0]["expect"]["must"][0].update(evidence=[])
        )

    def test_real_data_marker_is_rejected(self):
        self.assert_schema_rejects(lambda s: s.update(synthetic=False))

    def test_unknown_fields_are_rejected(self):
        self.assert_schema_rejects(lambda s: s["steps"][0]["expect"].update(musst=[]))

    def test_missing_anchor_is_rejected(self):
        self.assert_schema_rejects(lambda s: s["sources"]["guide"].pop("anchor"))

    def assert_schedule_rejects(self, mutate, message):
        corpus = copy.deepcopy(self.corpus)
        mutate(corpus["scenarios"]["retry-safety"])
        with self.assertRaisesRegex(ValueError, message):
            validate_schedule(corpus)

    def test_reconciliation_before_receipt_is_rejected(self):
        self.assert_schedule_rejects(
            lambda s: s["steps"][0]["reconcile"].append("incident"), "before receipt"
        )

    def test_missing_backlog_is_rejected(self):
        self.assert_schedule_rejects(
            lambda s: s["steps"][2]["expect"].update(pending=[]), "pending set"
        )

    def test_future_evidence_is_rejected(self):
        self.assert_schedule_rejects(
            lambda s: s["steps"][0]["expect"]["must"][0]["evidence"].append("incident"),
            "unprocessed evidence",
        )

    def test_forward_equivalence_is_rejected(self):
        self.assert_schedule_rejects(
            lambda s: s["steps"][0]["expect"].update(equivalentTo="duplicate-delivery"),
            "earlier step",
        )

    def test_duplicate_step_is_rejected(self):
        self.assert_schedule_rejects(
            lambda s: s["steps"][1].update(id=s["steps"][0]["id"]), "duplicate step"
        )

    def test_duplicate_outcome_is_rejected(self):
        self.assert_schedule_rejects(
            lambda s: s["steps"][0]["expect"]["mustNot"][0].update(id="expressed-not-proven"),
            "duplicate outcome",
        )

    def test_circular_lineage_is_rejected(self):
        self.assert_schedule_rejects(
            lambda s: s["sources"]["no"].update(replyTo="no"), "cyclic source lineage"
        )


if __name__ == "__main__":
    unittest.main()
