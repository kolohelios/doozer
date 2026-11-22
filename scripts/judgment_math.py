"""Offline, post-hoc probability diagnostics; never a truth or acceptance score."""

import argparse
import gzip
import itertools
import json
import math
from pathlib import Path

from scripts.calibration import write_new


def probabilities(answer):
    if not isinstance(answer, dict) or not isinstance(answer.get("probabilities"), dict):
        return None
    values = answer["probabilities"]
    if not values or any(type(p) not in (int, float) or not math.isfinite(p) or p < 0 or p > 1 for p in values.values()):
        raise ValueError("invalid probability vector")
    total = sum(values.values())
    if total <= 0 or abs(total - 1) > 0.02:
        raise ValueError("probabilities do not approximately sum to one")
    return {key: p / total for key, p in values.items()}


def entropy(answer):
    values = probabilities(answer)
    return None if values is None else -sum(p * math.log2(p) for p in values.values() if p)


def js_divergence(left, right):
    p, q = probabilities(left), probabilities(right)
    if p is None or q is None:
        return None
    result = 0.0
    for key in sorted(set(p) | set(q)):
        a, b = p.get(key, 0), q.get(key, 0)
        mean = (a + b) / 2
        if a:
            result += 0.5 * a * math.log2(a / mean)
        if b:
            result += 0.5 * b * math.log2(b / mean)
    return max(0.0, min(1.0, result))


def answer(row, stage, question="verdict"):
    value = row.get(stage, {})
    return value.get("value", {}).get(question) if value.get("status") == "valid" else None


def diagnose(report):
    rows = report["rows"]
    result = {"version": "posthoc-probability-diagnostics-v1", "protocol_sha256": report["protocol"]["sha256"],
              "warning": "Exploratory distribution diagnostics, not calibrated confidence, independence, entailment, or acceptance thresholds.",
              "controls": [], "source_swaps": [], "claim_trajectories": [],
              "analyst_skeptic": {"valid_agreement": 0, "valid_disagreement": 0, "unavailable": 0}}
    for row in rows:
        result["controls"].append({"id": row["id"], "repeat_js_bits": js_divergence(answer(row, "direct"), answer(row, "repeat")),
                                   "order_js_bits": js_divergence(answer(row, "direct"), answer(row, "order"))})
        for key in row.get("atoms", {}).get("value", {}):
            if key.startswith("relation-"):
                before, after = answer(row, "atoms", key), answer(row, "recheck", key)
                result["claim_trajectories"].append({"id": row["id"], "claim": key[len("relation-"):],
                                                    "before": before.get("choice") if before else None, "after": after.get("choice") if after else None,
                                                    "before_entropy_bits": entropy(before), "after_entropy_bits": entropy(after),
                                                    "relation_js_bits": js_divergence(before, after)})
        a, b = row.get("analyst", {}), row.get("skeptic", {})
        if a.get("status") != "valid" or b.get("status") != "valid":
            result["analyst_skeptic"]["unavailable"] += 1
        else:
            key = "valid_agreement" if a["value"]["verdict"] == b["value"]["verdict"] else "valid_disagreement"
            result["analyst_skeptic"][key] += 1
    for family in sorted({row["family"] for row in rows}):
        for left, right in itertools.combinations(sorted((row for row in rows if row["family"] == family), key=lambda row: row["variant"]), 2):
            relations = sorted({key for row in (left, right) for key in row.get("atoms", {}).get("value", {}) if key.startswith("relation-")})
            result["source_swaps"].append({"family": family, "left": left["variant"], "right": right["variant"],
                                           "direct_js_bits": js_divergence(answer(left, "direct"), answer(right, "direct")),
                                           "recheck_js_bits": js_divergence(answer(left, "recheck"), answer(right, "recheck")),
                                           "claim_relation_js_bits": {key: js_divergence(answer(left, "atoms", key), answer(right, "atoms", key)) for key in relations}})
    return result


def load(path):
    path = Path(path)
    raw = path.read_bytes()
    return json.loads(gzip.decompress(raw) if path.suffix == ".gz" else raw)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("artifact")
    parser.add_argument("--output", required=True)
    args = parser.parse_args(argv)
    try:
        result = diagnose(load(args.artifact))
        write_new(args.output, json.dumps(result, indent=2, allow_nan=False) + "\n")
        print("Offline diagnostics written; no model calls or acceptance thresholds.")
        return 0
    except (ValueError, KeyError, TypeError, OSError):
        print("Invalid artifact or output exists; nothing overwritten.")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
