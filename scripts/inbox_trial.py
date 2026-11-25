"""Fixed synthetic durable-inbox checkpoint for the one-call maintenance trial."""

from pathlib import Path

from scripts import maintenance_handoff as handoff, maintenance_proposer as proposer, source_inbox as inbox


VERSIONS = {"retry": "synthetic-inbox-maintenance-v4", "closure": "synthetic-inbox-closure-v1"}
CASES = {version: case for case, version in VERSIONS.items()}
wb = proposer.wb
CLOSURE = wb.ROOT / "experiments/workbench/inbox-closure.cue"


def reference_snapshot(case="retry"):
    if case == "retry":
        state = proposer.prepare(append_only=True)["protocol"]["frozen"]["before"]
    elif case == "closure":
        fixture = wb.export_cue([wb.CONTRACTS, CLOSURE])["inboxClosure"]
        state = wb.new_state()
        for key, record in sorted(fixture["sources"].items()):
            wb.receive(state, key, record)
        state = wb.commit(state, fixture["seed"], sorted(fixture["sources"]),
                          {"assertions": fixture["claimRecords"]}, {"action": "analyze"})
    else:
        raise ValueError("unknown synthetic inbox case")
    return {"state": state, "reconciliation_position": len(state["journal"])}


def seed(path, case="retry"):
    expected = reference_snapshot(case)
    with Path(path).open("xb"):
        pass
    state = expected["state"]
    for key, value in state["received"].items():
        inbox.receive(path, key, value)
    for position, entry in enumerate(state["journal"]):
        inbox.commit(path, f"trial-seed-{position + 1}", base_position=position,
                     patch=entry["patch"], batch=entry["batch"], analysis=entry["analysis"], route=entry["route"])
    actual = inbox.snapshot(path)
    actual = {key: actual[key] for key in expected}
    if actual != expected:
        raise ValueError("durable seed differs from the recorded synthetic fixture")
    return checkpoint(actual)


def checkpoint(snapshot):
    return {"snapshot": snapshot, "prepared": handoff.prepare_snapshot(snapshot)}


def messages(value, case):
    if value != checkpoint(reference_snapshot(case)):
        raise ValueError("inbox trial requires the fixed synthetic checkpoint")
    return value["prepared"]["preparation"]["messages"]


def inspect(value, raw):
    try:
        result = handoff.inspect_snapshot(value["snapshot"], raw, prepared=value["prepared"])
    except (ValueError, TypeError, KeyError, RecursionError) as error:
        return {"status": "rejected-not-applied", "failure": str(error), "semantic_judgment": "not-evaluated"}
    result["status"] = "applicable-in-isolated-copy" if result["inspection"]["changed"] else "no-change-in-isolated-copy"
    return result
