"""Fixed synthetic durable-inbox checkpoint for the one-call maintenance trial."""

from pathlib import Path

from scripts import maintenance_handoff as handoff, maintenance_proposer as proposer, source_inbox as inbox


VERSION = "synthetic-inbox-maintenance-v1"


def reference_snapshot():
    state = proposer.prepare(append_only=True)["protocol"]["frozen"]["before"]
    return {"state": state, "reconciliation_position": len(state["journal"])}


def seed(path):
    expected = reference_snapshot()
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


def messages(value):
    if value != checkpoint(reference_snapshot()):
        raise ValueError("inbox trial requires the fixed synthetic checkpoint")
    return value["prepared"]["preparation"]["messages"]


def inspect(value, raw):
    try:
        result = handoff.inspect_snapshot(value["snapshot"], raw, prepared=value["prepared"])
    except (ValueError, TypeError, KeyError, RecursionError) as error:
        return {"status": "rejected-not-applied", "failure": str(error), "semantic_judgment": "not-evaluated"}
    result["status"] = "applicable-in-isolated-copy" if result["inspection"]["changed"] else "no-change-in-isolated-copy"
    return result
