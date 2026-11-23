"""Offline retry-safety maintenance, append-only ablation, and local recovery."""

import argparse
import copy
import hashlib
import json
from pathlib import Path

from scripts import workbench as wb
from scripts.workbench_models import RecordedBackend


class AppendOnlyBackend(RecordedBackend):
    def reason(self, step, context):
        patch = super().reason(step, context)
        patch["operations"] = [op for op in patch["operations"] if op["op"] != "retire"]
        return patch


def execute(scenario, backend):
    states = []
    def capture(state, snapshots, trace):
        if len(snapshots) > len(states):
            states.append(copy.deepcopy(state))
    result = wb.run(scenario, backend, checkpoint=capture)
    return result, states


def view(state, settings):
    projection = wb.project(state)
    return {"revision": state["revision"], "active_claims": len(state["claims"]),
            "claim_words": sum(len(c["text"].split()) for c in state["claims"].values()),
            "active_source_ids": sorted({c["source"] for a in state["claims"].values() for c in a["evidence"]}),
            "pending": sorted(set(state["received"]) - set(state["processed"])),
            "projection": projection,
            "reader_probes": {query: wb.discover(state, query) for query in settings["queries"]},
            "references": {ref: {"historical": copy.deepcopy(state["history"].get(ref)), "current": wb.resolve(state, ref)} for ref in settings["references"]}}


def run():
    corpus = wb.export_cue(sorted((wb.ROOT / "corpus").glob("*.cue")))
    settings = wb.export_cue(sorted((wb.ROOT / "experiments/workbench").glob("*.cue")))["maintenance"]
    scenario = corpus["scenarios"][settings["scenario"]]
    expectations = {step["id"]: step["expect"] for step in scenario["steps"]}
    maintained, states = execute(scenario, RecordedBackend())
    baseline, baseline_states = execute(scenario, AppendOnlyBackend())
    rounds = [{"step": step["id"], "maintained": view(a, settings), "append_only": view(b, settings),
               "required": copy.deepcopy(step["expect"]["must"]), "forbidden": copy.deepcopy(step["expect"]["mustNot"]),
               "semantic_judgment": "pending-human-review"}
              for step, a, b in zip(scenario["steps"], states, baseline_states)]
    consolidation = settings["consolidation"]
    for policy, result in (("maintained", maintained), ("append_only", baseline)):
        patch = copy.deepcopy(consolidation["patch"])
        if policy == "append_only":
            patch["operations"] = [op for op in patch["operations"] if op["op"] != "retire"]
        result["state"] = wb.maintain(result["state"], patch, consolidation["analysis"], consolidation["route"])
    rounds.append({"step": "maintenance-consolidation", "maintained": view(maintained["state"], settings),
                   "append_only": view(baseline["state"], settings),
                   "required": copy.deepcopy(expectations["scoped-mitigation"]["must"] + expectations["contextual-no"]["must"]),
                   "forbidden": copy.deepcopy(expectations["scoped-mitigation"]["mustNot"] + expectations["contextual-no"]["mustNot"]),
                   "semantic_judgment": "pending-human-review"})
    original = maintained["state"]
    repeated = wb.maintain(original, consolidation["repeatPatch"], consolidation["analysis"], consolidation["route"])
    if repeated != original:
        raise ValueError("no-op maintenance caused state or journal churn")
    position = settings["rollbackPosition"]
    restored = wb.restore(original, {"baseRevision": original["revision"], "targetPosition": position,
                                     "reason": "Offline recovery exercise: restore the pre-mitigation view without erasing later sources or history."})
    replayed = restored
    for index in range(position, len(original["journal"])):
        replayed = wb.replay(replayed, index, base_revision=replayed["revision"])
    if wb.material(replayed) != wb.material(original) or replayed["history"] != original["history"]:
        raise ValueError("exact local replay did not recover the original material view")
    if restored["received"] != original["received"] or restored["history"] != original["history"]:
        raise ValueError("recovery erased source or claim history")
    return {"settings": settings, "rounds": rounds, "policies": {"maintained": maintained, "append_only": baseline},
            "recovery": {"target_position": position, "restored": view(restored, settings), "replayed": view(replayed, settings),
                         "material_recovered": True, "state": replayed},
            "repeated_maintenance_unchanged": True,
            "implementation_sha256": {name: hashlib.sha256((wb.ROOT / "scripts" / name).read_bytes()).hexdigest() for name in ("workbench.py", "retry_maintenance.py")},
            "network_calls": 0, "canonical_scope": "Isolated local fixture state only; no external knowledge publication."}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True)
    args = parser.parse_args(argv)
    path = Path(args.output)
    if path.exists():
        raise ValueError("output exists; no overwrite")
    result = run()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x") as stream:
        stream.write(json.dumps(result, indent=2, allow_nan=False) + "\n")
    print(json.dumps({"output": str(path), "rounds": len(result["rounds"]), "network_calls": 0,
                      "final_active_claims": {p: len(r["state"]["claims"]) for p, r in result["policies"].items()},
                      "recovery": result["recovery"]["material_recovered"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
