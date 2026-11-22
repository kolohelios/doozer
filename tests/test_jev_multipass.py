"""Offline multi-pass mechanics and control tests, not independent semantic gold."""

import copy
import gzip
import hashlib
import io
import json
import os
from pathlib import Path
import tempfile
from unittest import TestCase, mock

from scripts import jev_multipass as multi
from scripts.evaluation_client import OutputFailure


class MultipassTests(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = multi.export_cue(sorted(multi.DIRECTORY.glob("*.cue")))

    def prepare(self):
        return multi.prepare(self.data)

    def sender(self, endpoint, payload, token):
        self.assertEqual(token, "SECRET_CANARY")
        self.assertFalse(payload["provider"]["allow_fallbacks"])
        response = {"model": payload["model"], "usage": {"cost": 0.001, "input_tokens": 100, "output_tokens": 100}}
        if endpoint == multi.split.DECISIONS:
            answers = {}
            for key, question in payload["questions"].items():
                choices = question["criteria"]
                label = "pass" if key == "verdict" else "supported" if key.startswith("relation-") else "none"
                self.assertIn(label, choices)
                answers[key] = {"type": "choice", "choice": label, "confidence": 0.9, "probabilities": {label: 1.0}}
            response["answers"] = answers
        else:
            self.assertEqual(payload["response_format"]["type"], "json_schema")
            context = json.loads(payload["messages"][1]["content"])
            evidence = next(iter(context["source_spans"]))
            value = {"verdict": "pass", "rationale": "Recorded mechanics only.", "issues": [],
                     "claims": [{"id": claim_id, "kind": "world", "relation": "supported", "evidence": [evidence], "rationale": "Recorded mechanics only."} for claim_id in context["claims"]]}
            response["choices"] = [{"finish_reason": "stop", "message": {"content": json.dumps(value)}}]
        return response

    def test_saved_archive_preserves_each_request_response_and_refusal(self):
        observation = self.data["observations"]
        compressed = (multi.ROOT / observation["artifact"]).read_bytes()
        self.assertEqual(hashlib.sha256(compressed).hexdigest(), observation["archiveSHA256"])
        raw = gzip.decompress(compressed)
        self.assertEqual(hashlib.sha256(raw).hexdigest(), observation["uncompressedSHA256"])
        report = json.loads(raw)
        frozen = report["protocol"]["frozen"]
        self.assertEqual(multi.pilot.digest(frozen), observation["protocolSHA256"])
        self.assertEqual(report["source_commit"], observation["sourceCommit"])
        self.assertEqual(len(report["trace"]), 126)
        self.assertAlmostEqual(sum(trace["reported_cost_usd"] for trace in report["trace"]), observation["reportedCostUSD"])
        self.assertEqual(multi.summarize(report), report["summary"])
        packets = {packet["id"]: packet for packet in frozen["packets"]}
        rows = {row["id"]: row for row in report["rows"]}
        requests = {(op["sample"], op["kind"]): op for op in report["requests"]}
        refusals = []
        for op, trace in zip(report["requests"], report["trace"]):
            self.assertEqual(hashlib.sha256(json.dumps(op["payload"], allow_nan=False).encode()).hexdigest(), trace["request_sha256"])
            stage = rows[op["sample"]][op["kind"]]
            if stage["status"] == "valid":
                self.assertEqual(multi.validate_response(trace["response"], op, packets[op["sample"]]), stage["value"])
            else:
                self.assertEqual(op["kind"], "skeptic")
                self.assertEqual(trace["response"]["choices"][0]["finish_reason"], "content_filter")
                self.assertEqual(trace["output_tokens"], 0)
                refusals.append(op["sample"])
        self.assertEqual(set(refusals), set(observation["skepticRefusals"]["packets"]))
        for row in report["rows"]:
            self.assertEqual(requests[row["id"], "direct"]["payload"], requests[row["id"], "repeat"]["payload"])
        trajectory = rows["epistemic-scope/v1"]
        self.assertEqual(trajectory["atoms"]["value"]["relation-c1"]["choice"], "not-established")
        self.assertEqual(trajectory["recheck"]["value"]["relation-c1"]["choice"], "meta")
        audit = observation["unknownVersusContradictedAudit"]
        packet, row = packets[audit["packet"]], rows[audit["packet"]]
        self.assertEqual(packet["spans"][audit["sourceSpan"]]["text"], audit["sourceQuote"])
        claim = next(claim for claim in row["analyst"]["value"]["claims"] if claim["id"] == audit["claim"])
        self.assertEqual(claim["relation"], audit["analystRelation"])
        self.assertIn(audit["analystRationaleQuote"], claim["rationale"])
        self.assertEqual(len(packet["packet_math"]["declared_origin_groups"]), audit["declaredOriginGroups"])
        self.assertEqual(len(packet["packet_math"]["sources_without_declared_origin"]), audit["sourcesWithoutDeclaredOrigin"])
        self.assertEqual(len(packet["packet_math"]["echo_edges"]), audit["echoEdges"])

    def test_equivalent_budget_numbers_have_identical_future_protocols(self):
        integer = multi.prepare(self.data, 5, 140)
        floating = multi.prepare(self.data, 5.0, 140)
        self.assertEqual(integer["protocol"], floating["protocol"])

    def test_source_swaps_keep_candidates_constant_and_references_out_of_requests(self):
        report = self.prepare()
        frozen = report["protocol"]["frozen"]
        self.assertEqual(len(frozen["packets"]), 18)
        self.assertEqual(len(frozen["packets"]) * len(multi.PASSES), 126)
        for family in self.data["families"]:
            packets = [packet for packet in frozen["packets"] if packet["family"] == family]
            self.assertEqual(len({packet["candidate"] for packet in packets}), 1)
            self.assertGreater(len({multi.pilot.digest(packet["sources"]) for packet in packets}), 1)
        packet = copy.deepcopy(frozen["packets"][0])
        packet["reference"], packet["reference_reason"], packet["id"] = "LABEL_CANARY", "REASON_CANARY", "IDENTITY_CANARY"
        for kind in multi.PASSES:
            op = multi.operation(packet, {}, kind, frozen["plan"])
            self.assertNotIn("CANARY", json.dumps(op["payload"]))
            self.assertEqual(op["sample"], "IDENTITY_CANARY")

    def test_repeat_is_identical_but_order_changes_only_source_presentation(self):
        frozen = self.prepare()["protocol"]["frozen"]
        packet = next(packet for packet in frozen["packets"] if len(packet["sources"]) > 1)
        direct = multi.operation(packet, {}, "direct", frozen["plan"])["payload"]
        repeated = multi.operation(packet, {}, "repeat", frozen["plan"])["payload"]
        reordered = multi.operation(packet, {}, "order", frozen["plan"])["payload"]
        self.assertEqual(direct, repeated)
        self.assertEqual(direct["state"]["authoritative_sources"], list(reversed(reordered["state"]["authoritative_sources"])))
        reordered["state"]["authoritative_sources"].reverse()
        self.assertEqual(direct, reordered)

    def test_analyst_is_blind_and_recheck_keeps_model_reports_out_of_source_list(self):
        frozen = self.prepare()["protocol"]["frozen"]
        packet = frozen["packets"][0]
        row = {"direct": {"status": "valid", "value": {"verdict": {"choice": "fail"}}},
               "analyst": {"status": "valid", "value": {"rationale": "MODEL_REPORT_CANARY"}}}
        analyst = multi.operation(packet, row, "analyst", frozen["plan"])
        self.assertNotIn("MODEL_REPORT_CANARY", json.dumps(analyst["payload"]))
        recheck = multi.operation(packet, row, "recheck", frozen["plan"])
        self.assertIn("MODEL_REPORT_CANARY", json.dumps(recheck["payload"]["state"]["untrusted_analysis_proposals"]))
        self.assertNotIn("MODEL_REPORT_CANARY", json.dumps(recheck["payload"]["state"]["authoritative_sources"]))

    def test_source_spans_and_missing_reply_context_are_exact(self):
        for packet in self.prepare()["protocol"]["frozen"]["packets"]:
            sources = {source["id"]: source for source in packet["sources"]}
            for span in packet["spans"].values():
                self.assertIn(span["text"], sources[span["source"]]["text"])
            self.assertEqual("".join(packet["candidate"].split()), "".join("".join(text.split()) for text in packet["claims"].values()))
        packet = next(packet for packet in self.prepare()["protocol"]["frozen"]["packets"] if packet["id"] == "epistemic-scope/v1")
        self.assertEqual(packet["packet_math"]["missing_reply_targets"], ["d0"])

    def test_provider_schema_compiles_to_cue_and_blocks_phantom_evidence(self):
        frozen = self.prepare()["protocol"]["frozen"]
        packet = frozen["packets"][0]
        op = multi.operation(packet, {}, "analyst", frozen["plan"])
        response = self.sender(op["endpoint"], op["payload"], "SECRET_CANARY")
        value = multi.validate_response(response, op, packet)
        value["claims"][0]["evidence"] = ["phantom-span"]
        response["choices"][0]["message"]["content"] = json.dumps(value)
        with self.assertRaises(OutputFailure):
            multi.validate_response(response, op, packet)

    def test_new_chat_roles_reserve_output_tokens_in_shared_ledger(self):
        report = self.prepare()
        packet = report["protocol"]["frozen"]["packets"][0]
        op = multi.operation(packet, {}, "skeptic", report["protocol"]["frozen"]["plan"])
        with mock.patch.dict(os.environ, {"OPENROUTER_API_KEY": "SECRET_CANARY"}):
            ledger = multi.split.Ledger(report, lambda: None, sender=self.sender)
            ledger.submit(op)
        expected_output_reserve = op["payload"]["max_tokens"] * 20 / 1_000_000
        self.assertGreater(report["trace"][0]["reserved_usd"], expected_output_reserve)

    def test_full_recorded_depth_does_not_vote_or_retry(self):
        report = self.prepare()
        with mock.patch.dict(os.environ, {"OPENROUTER_API_KEY": "SECRET_CANARY"}):
            multi.run(report, lambda: None, sender=self.sender)
        self.assertEqual(report["status"], "completed")
        self.assertEqual(len(report["trace"]), 126)
        self.assertEqual(len(report["requests"]), 126)
        self.assertAlmostEqual(report["accounted_or_reserved_usd"], 0.126)
        self.assertEqual(report["summary"]["controls"]["repeat"]["stable"], 18)
        self.assertEqual(report["summary"]["controls"]["order"]["stable"], 16)
        self.assertEqual(report["summary"]["controls"]["order"]["no_op"], 2)
        self.assertEqual(report["summary"]["adjudication_changes"], [])
        self.assertNotIn("SECRET_CANARY", json.dumps(report))
        with self.assertRaises(ValueError):
            multi.run(report, lambda: None, sender=self.sender)

    def test_unknown_accounting_stops_without_replacement(self):
        report = self.prepare()
        def bad(endpoint, payload, token):
            value = self.sender(endpoint, payload, token)
            value["usage"].pop("cost")
            return value
        with mock.patch.dict(os.environ, {"OPENROUTER_API_KEY": "SECRET_CANARY"}), self.assertRaises(ValueError):
            multi.run(report, lambda: None, sender=bad)
        self.assertEqual(len(report["trace"]), 1)
        self.assertEqual(report["status"], "stopped-no-retry")

    def test_invalid_known_billed_audits_are_retained_not_replaced(self):
        report = self.prepare()
        def bad(endpoint, payload, token):
            value = self.sender(endpoint, payload, token)
            if endpoint == multi.split.CHAT_ENDPOINT:
                value["choices"][0]["message"]["content"] = "not JSON"
            return value
        with mock.patch.dict(os.environ, {"OPENROUTER_API_KEY": "SECRET_CANARY"}):
            multi.run(report, lambda: None, sender=bad)
        self.assertEqual(len(report["trace"]), 126)
        self.assertTrue(all(row["analyst"]["status"] == row["skeptic"]["status"] == "invalid" for row in report["rows"]))

    def test_limits_and_protocol_tampering_stop_before_calls(self):
        for budget, calls in ((5.01, 140), (5, 141), (5, 125), (float("nan"), 140)):
            with self.subTest(budget=budget, calls=calls), self.assertRaises(ValueError):
                multi.prepare(self.data, budget, calls)
        report = self.prepare()
        report["protocol"]["frozen"]["packets"][0]["candidate"] += " changed"
        sender = mock.Mock()
        with self.assertRaises(ValueError):
            multi.run(report, lambda: None, sender=sender)
        sender.assert_not_called()

    def test_default_cli_is_offline_and_never_overwrites_an_existing_artifact(self):
        with tempfile.TemporaryDirectory() as directory, mock.patch.object(multi, "bounded_transport") as sender, mock.patch("sys.stdout", new_callable=io.StringIO):
            path = Path(directory) / "plan.json"
            self.assertEqual(multi.main(["--output", str(path)]), 0)
            before = path.read_bytes()
            self.assertEqual(multi.main(["--output", str(path)]), 2)
            self.assertEqual(before, path.read_bytes())
            sender.assert_not_called()
