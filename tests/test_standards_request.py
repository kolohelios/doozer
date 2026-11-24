import json
import unittest
from unittest.mock import patch

from scripts import maintenance_call, maintenance_proposer, standards_request as request


class StandardsRequestTests(unittest.TestCase):
    def setUp(self):
        self.state = {"processed": ["draft-04"], "claims": {"synthetic-claim": {}}}
        self.batch = {"protocol": {"sha256": "test-binding"}, "evaluation": "PRIVATE_CANARY"}
        self.messages = [{"role": "user", "content": "Synthetic proposal context"}]

    def preview(self):
        with (patch.object(request.loop, "prepare", return_value=self.batch) as prepare,
              patch.object(request.loop, "model_messages", return_value=self.messages),
              patch("urllib.request.urlopen", side_effect=AssertionError("offline only"))):
            result = request.preview(self.state)
        prepare.assert_called_once_with("checkpoint-06", state=self.state, source_id="draft-05")
        return result

    def test_request_binds_exact_payload_and_excludes_private_batch(self):
        result = self.preview()
        protocol = result["protocol"]
        frozen = protocol["frozen"]
        payload = frozen["payload"]
        self.assertEqual(protocol["sha256"], maintenance_proposer.digest(frozen))
        self.assertEqual(frozen["request_bytes"], len(json.dumps(payload).encode()))
        self.assertEqual(payload["messages"], self.messages)
        self.assertNotIn("PRIVATE_CANARY", json.dumps(payload))
        self.assertEqual(payload["provider"]["only"], ["openai"])
        self.assertFalse(payload["provider"]["allow_fallbacks"])
        self.assertEqual(payload["provider"]["data_collection"], "deny")
        self.assertEqual(payload["max_tokens"], 4096)
        self.assertEqual(frozen["input_reservation_units"], frozen["request_bytes"] + 8192)
        self.assertAlmostEqual(frozen["reservation_usd"], (frozen["input_reservation_units"] * 3 + 4096 * 9) / 1_000_000)
        self.assertEqual(result["status"], "offline-preview-not-executable")
        self.assertEqual((result["planned_calls"], result["network_calls"]), (0, 0))
        self.assertEqual(frozen["spending_approval"], "none")
        with self.assertRaises((KeyError, ValueError)):
            maintenance_call.check(result)

    def test_each_limit_fails_without_truncation(self):
        for key, value in (("MAX_REQUEST_BYTES", 1), ("INPUT_ALLOWANCE", 1), ("BUDGET_USD", 0)):
            with self.subTest(key=key), patch.object(request, key, value):
                with self.assertRaisesRegex(ValueError, "no truncation or fallback"):
                    self.preview()

    def test_wrong_processing_position_or_empty_view_fails_before_prepare(self):
        for changes in ({"processed": ["draft-04", "draft-05"]}, {"claims": {}}):
            with patch.object(request.loop, "prepare", side_effect=AssertionError("should not prepare")):
                with self.assertRaisesRegex(ValueError, "draft-04 view"):
                    request.preview({**self.state, **changes})
