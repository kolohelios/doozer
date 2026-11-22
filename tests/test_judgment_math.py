"""Probability geometry is diagnostic, never proof of semantic correctness."""

import hashlib
import io
import json
import math
from pathlib import Path
import tempfile
from unittest import TestCase, mock

from scripts import judgment_math as metrics, jev_multipass as multi


def rounded(value):
    if isinstance(value, float):
        return round(value, 12)
    if isinstance(value, list):
        return [rounded(item) for item in value]
    if isinstance(value, dict):
        return {key: rounded(item) for key, item in value.items()}
    return value


class JudgmentMathTests(TestCase):
    def test_entropy_and_js_have_known_limits_and_symmetry(self):
        left = {"probabilities": {"a": 1.0, "b": 0.0}}
        right = {"probabilities": {"a": 0.0, "b": 1.0}}
        uniform = {"probabilities": {"a": 0.5, "b": 0.5}}
        self.assertEqual(metrics.entropy(left), 0)
        self.assertEqual(metrics.entropy(uniform), 1)
        self.assertEqual(metrics.js_divergence(left, left), 0)
        self.assertEqual(metrics.js_divergence(left, right), 1)
        self.assertEqual(metrics.js_divergence(left, uniform), metrics.js_divergence(uniform, left))

    def test_missing_probabilities_are_not_replaced_with_confidence(self):
        self.assertIsNone(metrics.entropy({"confidence": 0.99}))
        self.assertIsNone(metrics.js_divergence(None, {"probabilities": {"a": 1}}))
        normalized = metrics.probabilities({"probabilities": {"a": 0.49, "b": 0.5}})
        self.assertAlmostEqual(sum(normalized.values()), 1)

    def test_invalid_probabilities_cannot_silently_become_diagnostics(self):
        for values in ({"a": -1}, {"a": 2}, {"a": 0}, {"a": math.nan}, {"a": True}, {"a": 0.8, "b": 0.8}):
            with self.subTest(values=values), self.assertRaises(ValueError):
                metrics.probabilities({"probabilities": values})

    def test_saved_posthoc_analysis_recomputes_without_models(self):
        data = multi.export_cue(sorted(multi.DIRECTORY.glob("*.cue")))
        observation = data["observations"]
        report = metrics.load(multi.ROOT / observation["artifact"])
        path = multi.ROOT / observation["probabilityDiagnostics"]["artifact"]
        self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), observation["probabilityDiagnostics"]["artifactSHA256"])
        diagnostic = metrics.diagnose(report)
        self.assertEqual(rounded(diagnostic), rounded(json.loads(path.read_text())))
        self.assertEqual(diagnostic["analyst_skeptic"], {"valid_agreement": 12, "valid_disagreement": 0, "unavailable": 6})
        self.assertAlmostEqual(max(item["repeat_js_bits"] for item in diagnostic["controls"]), observation["probabilityDiagnostics"]["maximumIdenticalRepeatJSBits"])
        trajectory = next(item for item in diagnostic["claim_trajectories"] if item["id"] == "epistemic-scope/v1" and item["claim"] == "c1")
        self.assertGreater(trajectory["after_entropy_bits"], trajectory["before_entropy_bits"])
        self.assertEqual(hashlib.sha256((multi.ROOT / "scripts/judgment_math.py").read_bytes()).hexdigest(), observation["probabilityDiagnostics"]["implementationSHA256"])

    def test_cli_is_new_only_and_has_no_live_mode(self):
        data = multi.export_cue(sorted(multi.DIRECTORY.glob("*.cue")))
        artifact = multi.ROOT / data["observations"]["artifact"]
        with tempfile.TemporaryDirectory() as directory, mock.patch("sys.stdout", new_callable=io.StringIO):
            path = Path(directory) / "diagnostics.json"
            self.assertEqual(metrics.main([str(artifact), "--output", str(path)]), 0)
            before = path.read_bytes()
            self.assertEqual(metrics.main([str(artifact), "--output", str(path)]), 2)
            self.assertEqual(before, path.read_bytes())
