"""Frozen split-judgment experiment; default preparation is completely offline."""

import argparse
import copy
import hashlib
import json
import math
import os
from pathlib import Path
import re
import subprocess
from collections import Counter

from scripts import calibration, calibration_pilot as pilot
from scripts.evaluation_client import Contracts, OutputFailure
from scripts.jev_probe import ENDPOINT as DECISIONS, is_number
from scripts.workbench_models import CHAT_ENDPOINT, transport

EMBEDDINGS = "https://openrouter.ai/api/v1/embeddings"
CONTRACT = calibration.DIRECTORY / "split.cue"


def sentences(text):
    # Preserve every non-whitespace character, including negation; no paraphrasing.
    return [{"id": f"s{index}", "text": part} for index, part in enumerate(re.split(r"(?<=[.!?])\s+", text))]


def provider(role):
    return {"only": [role["provider"]], "allow_fallbacks": False, "data_collection": "deny",
            "max_price": {"prompt": role["promptPrice"], "completion": role["completionPrice"]}}


def chat_payload(plan, contracts, kind, context):
    definition = "#Coverage" if kind == "coverage" else "#Grounding"
    return {"model": plan["roles"][kind]["model"], "temperature": plan["temperature"],
            "max_tokens": plan["maxOutputTokens"], "response_format": {"type": "json_object"},
            "provider": provider(plan["roles"][kind]), "messages": [
                {"role": "system", "content": plan[kind + "Instructions"] + "\nReturn JSON satisfying:\n" + contracts.describe(definition)},
                {"role": "user", "content": json.dumps(context, sort_keys=True)}]}


def prepare(data, contracts, budget, calls):
    plan = copy.deepcopy(data["splitPlan"])
    if not is_number(budget) or not 0 < budget <= plan["maxBudgetUSD"] or type(calls) is not int or not 1 <= calls <= plan["maxCalls"]:
        raise ValueError("invalid experiment limits")
    approved = pilot.prepare(data, Contracts(pilot.CONTRACT), 0.10, 10)["protocol"]["frozen"]
    baseline_bytes = (calibration.ROOT / data["pilotObservations"]["artifact"]).read_bytes()
    if hashlib.sha256(baseline_bytes).hexdigest() != data["pilotObservations"]["artifactSHA256"]:
        raise ValueError("baseline artifact changed")
    baseline = json.loads(baseline_bytes)
    samples = copy.deepcopy(approved["samples"])
    groups = {group["thread"]: group for group in data["threadContrasts"]}
    membership = {candidate["id"]: key for key, group in groups.items() for candidate in group["candidates"]}
    if set(data["splitChecks"]) != set(groups):
        raise ValueError("check cards must cover all approved threads")
    samples.sort(key=lambda sample: pilot.digest([plan["orderSeed"], sample["id"]]))
    operations, texts = [], {}
    for sample in samples:
        original = sample["judge_input"]
        sample["sentences"] = sentences(original["candidate"])
        sample["checks"] = copy.deepcopy(data["splitChecks"][membership[sample["id"]]])
        if not sample["checks"] or len({check["id"] for check in sample["checks"]}) != len(sample["checks"]):
            raise ValueError("empty or duplicate coverage checks")
        contexts = {
            "coverage": {"candidateSentences": sample["sentences"], "requirements": sample["checks"]},
            "grounding": {"candidateSentences": sample["sentences"], "authoritative_sources": original["authoritative_sources"]},
        }
        for kind, context in contexts.items():
            operations.append({"kind": kind, "sample": sample["id"], "endpoint": CHAT_ENDPOINT,
                               "payload": chat_payload(plan, contracts, kind, context)})
        operations.append({"kind": "jev", "sample": sample["id"], "endpoint": DECISIONS,
                           "payload": {"model": plan["roles"]["jev"]["model"], "state": original,
                                       "questions": {"verdict": {"type": "choice", "instructions": plan["jevInstructions"], "criteria": plan["jevCriteria"]}},
                                       "provider": provider(plan["roles"]["jev"])}})
        for text in [original["candidate"], *[item["text"] for item in sample["sentences"]],
                     *[item["requirement"] for item in sample["checks"]], *[item["text"] for item in original["authoritative_sources"]]]:
            texts[hashlib.sha256(text.encode()).hexdigest()] = text
    embedding_inputs = [{"id": key, "text": value} for key, value in sorted(texts.items())]
    operations.append({"kind": "embedding", "sample": None, "endpoint": EMBEDDINGS,
                       "payload": {"model": plan["roles"]["embedding"]["model"], "input": [item["text"] for item in embedding_inputs],
                                   "encoding_format": "float", "dimensions": plan["embeddingDimensions"], "provider": provider(plan["roles"]["embedding"])}})
    if len(operations) > calls or any(len(json.dumps(op["payload"]).encode()) > plan["maxRequestBytes"] for op in operations):
        raise ValueError("cannot accommodate frozen operations")
    names = ["split_judgment.py", "calibration.py", "calibration_pilot.py", "evaluation_client.py", "jev_probe.py", "workbench_models.py"]
    frozen = {"plan": plan, "contract": contracts.schema, "approval": approved["approval"], "samples": samples,
              "operations": operations, "embedding_inputs": embedding_inputs, "limits": {"budget_usd": budget, "max_calls": calls, "retries": 0},
              "baseline_artifact_sha256": data["pilotObservations"]["artifactSHA256"],
              "baseline_decisions": {row["id"]: {"status": row["status"], "result": row.get("judgment", {}).get("result")} for row in baseline["rows"]},
              "implementation_sha256": {name: hashlib.sha256((calibration.ROOT / "scripts" / name).read_bytes()).hexdigest() for name in names}}
    return {"protocol": {"sha256": pilot.digest(frozen), "frozen": frozen}, "source_commit": pilot.source_commit(),
            "status": "prepared", "trace": [], "rows": [{"id": sample["id"], "cohort": sample["cohort"], "reference": sample["reference"]} for sample in samples],
            "lexical_math": vector_diagnostics(samples, tfidf(embedding_inputs)),
            "warning": "Development-only adaptation to known failures; check decomposition is proposed, not separately approved gold. No canonical writes."}


def normalize(values):
    if not values or any(type(value) not in (int, float) or not math.isfinite(value) for value in values):
        raise OutputFailure("invalid vector")
    magnitude = math.sqrt(sum(value * value for value in values))
    if not magnitude or not math.isfinite(magnitude):
        raise OutputFailure("zero or nonfinite vector norm")
    return [value / magnitude for value in values]


def tfidf(items):
    counts = {item["text"]: Counter(re.findall(r"[\w-]+", item["text"].lower())) for item in items}
    vocabulary = sorted({term for count in counts.values() for term in count})
    idf = {term: math.log((1 + len(counts)) / (1 + sum(term in count for count in counts.values()))) + 1 for term in vocabulary}
    return {text: normalize([count[term] * idf[term] for term in vocabulary]) for text, count in counts.items()}


def cosine(left, right):
    if len(left) != len(right):
        raise OutputFailure("vector dimensions differ")
    return max(-1.0, min(1.0, sum(a * b for a, b in zip(left, right))))


def vector_diagnostics(samples, vectors):
    result = []
    for sample in samples:
        original = sample["judge_input"]
        result.append({"id": sample["id"], "required_meaning_similarity": {
            check["id"]: max(cosine(vectors[check["requirement"]], vectors[sentence["text"]]) for sentence in sample["sentences"]) for check in sample["checks"]},
            "sentence_source_similarity": {sentence["id"]: max(cosine(vectors[sentence["text"]], vectors[source["text"]]) for source in original["authoritative_sources"]) for sentence in sample["sentences"]},
            "same_criterion_answer_similarity": {other["id"]: cosine(vectors[original["candidate"]], vectors[other["judge_input"]["candidate"]]) for other in samples if other["id"] != sample["id"] and other["judge_input"]["criterion"] == original["criterion"]}})
    return result


class Ledger:
    def __init__(self, report, checkpoint, sender=transport):
        self.report, self.checkpoint, self.sender = report, checkpoint, sender
        self.frozen = report["protocol"]["frozen"]
        self.token = os.environ.get("OPENROUTER_API_KEY", "").strip()
        if not self.token:
            raise ValueError("missing OpenRouter token")
        self.spent, self.halted = 0.0, False

    def submit(self, operation):
        trace, frozen = self.report["trace"], self.frozen
        limits, plan = frozen["limits"], frozen["plan"]
        if self.halted or len(trace) >= limits["max_calls"]:
            raise ValueError("ledger halted or exhausted")
        encoded = json.dumps(operation["payload"], allow_nan=False).encode()
        role = plan["roles"][operation["kind"]]
        output = operation["payload"].get("max_tokens", 0)
        reserve = ((len(encoded) + 8192) * float(role["promptPrice"]) + output * float(role["completionPrice"])) / 1_000_000
        if len(encoded) > plan["maxRequestBytes"] or self.spent + reserve > limits["budget_usd"]:
            raise ValueError("cannot reserve request within limits")
        record = {"kind": operation["kind"], "sample": operation["sample"], "request_sha256": hashlib.sha256(encoded).hexdigest(),
                  "status": "submitted", "reserved_usd": reserve}
        trace.append(record)
        self.spent += reserve
        self.report["accounted_or_reserved_usd"] = self.spent
        self.checkpoint()
        try:
            response = self.sender(operation["endpoint"], operation["payload"], self.token)
            record["response"] = json.loads(json.dumps(response, allow_nan=False).replace(self.token, "[REDACTED]"))
            usage = response.get("usage", {})
            count = usage.get("input_tokens", usage.get("prompt_tokens", usage.get("total_tokens")))
            out = usage.get("output_tokens", usage.get("completion_tokens", 0 if operation["kind"] == "embedding" else None))
            if usage.get("is_byok") or type(count) is not int or count < 0 or type(out) is not int or out < 0:
                raise ValueError("unknown accounting")
            cost = usage.get("cost")
            if cost is None and operation["kind"] == "embedding":
                charge, basis = count * float(role["promptPrice"]) / 1_000_000, "tokens-times-price-ceiling"
            elif is_number(cost):
                charge, basis = cost, "reported"
            else:
                raise ValueError("unknown accounting")
            self.spent += charge - reserve
            record.update(status="received", accounted_usd=charge, reported_cost_usd=cost, cost_basis=basis, input_tokens=count, output_tokens=out)
            self.report["accounted_or_reserved_usd"] = self.spent
            if self.spent > limits["budget_usd"]:
                raise ValueError("budget exceeded; stop")
            self.checkpoint()
            return record["response"]
        except (ValueError, KeyError, TypeError, AttributeError, OSError, OverflowError):
            self.halted = True
            record["status"] = "failed-or-unaccounted"
            self.checkpoint()
            raise ValueError("transport/accounting stopped; no retry") from None


def validate_stage(kind, value, sample, contracts):
    definition, field = ("#Coverage", "checks") if kind == "coverage" else ("#Grounding", "sentences")
    contracts.validate(definition, value)
    expected = sample["checks"] if kind == "coverage" else sample["sentences"]
    if len(value[field]) != len(expected) or {item["id"] for item in value[field]} != {item["id"] for item in expected}:
        raise OutputFailure("omitted or invented check/sentence")
    sources = {source["id"]: source for source in sample["judge_input"]["authoritative_sources"]}
    for item in value[field]:
        if not item["rationale"].strip():
            raise OutputFailure("empty rationale")
        if kind == "coverage":
            if item["result"] in {"conveyed", "contradicted"} and not item["answerQuotes"]:
                raise OutputFailure("unanchored coverage")
            if any(not quote.strip() or not any(quote in sentence["text"] for sentence in sample["sentences"]) for quote in item["answerQuotes"]):
                raise OutputFailure("coverage misquotes candidate")
        else:
            if item["result"] in {"supported", "contradicted"} and not item["citations"]:
                raise OutputFailure("unanchored grounding")
            for cite in item["citations"]:
                if cite["source"] not in sources or not cite["quote"].strip() or cite["quote"] not in sources[cite["source"]]["text"]:
                    raise OutputFailure("grounding misquotes source")


def generation_result(row):
    coverage, grounding = row.get("coverage", {}), row.get("grounding", {})
    if coverage.get("status") == "valid" and any(item["result"] in {"absent", "contradicted"} for item in coverage["value"]["checks"]):
        return "fail"
    if grounding.get("status") == "valid" and any(item["result"] in {"unsupported", "contradicted"} for item in grounding["value"]["sentences"]):
        return "fail"
    if coverage.get("status") == grounding.get("status") == "valid" and all(item["result"] == "conveyed" for item in coverage["value"]["checks"]) and all(item["result"] in {"supported", "nonfactual"} for item in grounding["value"]["sentences"]):
        return "pass"
    return "uncertain"


def decide(rows):
    for row in rows:
        generative = generation_result(row)
        jev = row.get("jev", {}).get("value", {}).get("choice", "uncertain") if row.get("jev", {}).get("status") == "valid" else "uncertain"
        row["decisions"] = {"generative": generative, "jev": jev, "combined": generative if generative == jev else "uncertain"}


def summarize(rows):
    result = {}
    for cohort in ("primary", "robustness"):
        group = [row for row in rows if row["cohort"] == cohort]
        policies = {}
        for policy in ("generative", "jev", "combined"):
            matrix = {reference: {label: 0 for label in ("pass", "fail", "uncertain")} for reference in ("pass", "fail")}
            for row in group:
                matrix[row["reference"]][row.get("decisions", {}).get(policy, "uncertain")] += 1
            policies[policy] = matrix
        result[cohort] = {"planned": len(group), "decisions": policies,
                          "invalid_stages": sum(stage.get("status") == "invalid" for row in group for stage in (row.get(kind, {}) for kind in ("coverage", "grounding", "jev"))),
                          "call_failed_stages": sum(row.get(kind, {}).get("status") == "call-failed" for row in group for kind in ("coverage", "grounding", "jev")),
                          "unattempted_stages": sum(kind not in row or row[kind].get("status") == "not-attempted" for row in group for kind in ("coverage", "grounding", "jev"))}
    return result


def run(report, contracts, checkpoint, sender=transport):
    frozen = report["protocol"]["frozen"]
    if report["status"] != "prepared" or report["trace"] or pilot.digest(frozen) != report["protocol"]["sha256"] or contracts.schema != frozen["contract"]:
        raise ValueError("run changed or already attempted")
    rows = {row["id"]: row for row in report["rows"]}
    if report["rows"] != [{"id": sample["id"], "cohort": sample["cohort"], "reference": sample["reference"]} for sample in frozen["samples"]]:
        raise ValueError("prepared rows changed")
    samples = {sample["id"]: sample for sample in frozen["samples"]}
    ledger = Ledger(report, checkpoint, sender)
    report["status"] = "running"
    checkpoint()
    for operation in frozen["operations"]:
        kind = operation["kind"]
        target = report if kind == "embedding" else rows[operation["sample"]]
        stage = {"status": "pending-request"}
        target[kind] = stage
        before = len(report["trace"])
        try:
            response = ledger.submit(operation)
        except ValueError:
            stage["status"] = "call-failed" if len(report["trace"]) > before else "not-attempted"
            checkpoint()
            raise
        stage["status"] = "invalid"
        try:
            model = response.get("model", "")
            requested = operation["payload"]["model"]
            if not (model == requested or model.startswith(requested + "-") or (kind == "embedding" and model == requested.split("/", 1)[1])):
                raise OutputFailure("unexpected served model")
            if kind in {"coverage", "grounding"}:
                choice = response["choices"][0]
                if choice["finish_reason"] != "stop":
                    raise OutputFailure("truncated or refused output")
                stage["value"] = json.loads(choice["message"]["content"])
                validate_stage(kind, stage["value"], samples[operation["sample"]], contracts)
            elif kind == "jev":
                if set(response["answers"]) != {"verdict"}:
                    raise OutputFailure("unexpected decision fields")
                answer = response["answers"]["verdict"]
                if answer["type"] != "choice" or answer["choice"] not in {"pass", "fail", "uncertain"}:
                    raise OutputFailure("refused or invalid decision")
                if answer.get("confidence") is not None and not is_number(answer["confidence"], maximum=1):
                    raise OutputFailure("invalid diagnostic confidence")
                stage["value"] = answer
            else:
                items = response["data"]
                inputs = frozen["embedding_inputs"]
                if len(items) != len(inputs) or any(type(item["index"]) is not int for item in items) or {item["index"] for item in items} != set(range(len(inputs))):
                    raise OutputFailure("missing or duplicate vectors")
                vectors = {}
                for item in items:
                    if len(item["embedding"]) != frozen["plan"]["embeddingDimensions"]:
                        raise OutputFailure("wrong embedding dimensions")
                    vectors[inputs[item["index"]]["text"]] = normalize(item["embedding"])
                report["dense_math"] = vector_diagnostics(frozen["samples"], vectors)
            stage["status"] = "valid"
        except (ValueError, KeyError, TypeError, IndexError, AttributeError, OverflowError):
            stage["failure_reason"] = "stage validation failed; retained raw response, no replacement"
        decide(report["rows"])
        checkpoint()
    report["status"] = "completed"
    report["summary"] = summarize(report["rows"])
    checkpoint()
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True)
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--budget-usd", type=float, default=0.50)
    parser.add_argument("--max-calls", type=int, default=40)
    args = parser.parse_args(argv)
    path, report, owned = Path(args.output), None, False
    try:
        if path.exists():
            raise ValueError("output exists")
        data, _, _ = calibration.load()
        contracts = Contracts(CONTRACT)
        report = prepare(data, contracts, args.budget_usd, args.max_calls)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("x") as stream:
            owned = True
            stream.write(json.dumps(report, indent=2, allow_nan=False) + "\n")
        if args.live:
            run(report, contracts, lambda: pilot.checkpoint(path, report))
        print(json.dumps({"output": str(path), "status": report["status"], "protocol_sha256": report["protocol"]["sha256"],
                          "calls": len(report["trace"]), "accounted_or_reserved_usd": report.get("accounted_or_reserved_usd"), "summary": report.get("summary")}, indent=2))
        return 0
    except (ValueError, KeyError, TypeError, OSError, OverflowError, subprocess.CalledProcessError):
        if owned:
            report["status"] = "stopped-no-retry"
            decide(report["rows"])
            report["summary"] = summarize(report["rows"])
            pilot.checkpoint(path, report)
        print("Split experiment stopped or output exists; no retry. Inspect the artifact; no canonical knowledge changed.")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
