"""
Unit tests for the AutoForge Lambda Telemetry Validator.

Tests cover:
  - Valid events pass through cleanly
  - Missing envelope fields → quarantine
  - Missing machine-specific fields → quarantine
  - Out-of-range values → quarantine
  - Unknown machine type → quarantine
  - Decode errors handled gracefully
"""

import sys
import os
import unittest
from unittest.mock import MagicMock, patch, call
from datetime import datetime, timezone
import base64
import json

# Use the alias pre-loaded by conftest.py to avoid module collision
import sys as _sys
h = _sys.modules["lambda_validator_handler"]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_cnc_event(**overrides) -> dict:
    event = {
        "event_id": "test-001",
        "machine_id": "M001",
        "machine_type": "cnc_machine",
        "factory_id": "AUTOFORGE_01",
        "timestamp": "2026-06-03T10:00:00Z",
        "status": "healthy",
        "telemetry": {
            "spindle_speed": 8000.0,
            "temperature": 42.0,
            "tool_wear": 5.0,
            "vibration": 2.1,
        },
        "anomaly_detected": False,
        "anomaly_type": None,
        "anomaly_severity": 0.0,
        "degradation_level": 0.01,
    }
    event.update(overrides)
    return event


def _make_kinesis_record(event: dict) -> dict:
    return {
        "kinesis": {
            "data": base64.b64encode(json.dumps(event).encode()).decode(),
            "sequenceNumber": "seq-001",
        }
    }


def _lambda_event(records: list) -> dict:
    return {"Records": [_make_kinesis_record(r) for r in records]}


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestValidation(unittest.TestCase):

    def test_valid_cnc_passes(self):
        h.validate(_make_cnc_event())  # should not raise

    def test_missing_envelope_field_raises(self):
        evt = _make_cnc_event()
        del evt["machine_id"]
        with self.assertRaises(h.ValidationError) as ctx:
            h.validate(evt)
        self.assertEqual(ctx.exception.reason, "missing_envelope_fields")

    def test_missing_telemetry_field_raises(self):
        evt = _make_cnc_event()
        del evt["telemetry"]["spindle_speed"]
        with self.assertRaises(h.ValidationError) as ctx:
            h.validate(evt)
        self.assertEqual(ctx.exception.reason, "missing_telemetry_fields")

    def test_out_of_range_temperature_raises(self):
        evt = _make_cnc_event()
        evt["telemetry"]["temperature"] = 9999.0  # above max 500
        with self.assertRaises(h.ValidationError) as ctx:
            h.validate(evt)
        self.assertEqual(ctx.exception.reason, "out_of_range")

    def test_negative_temperature_raises(self):
        evt = _make_cnc_event()
        evt["telemetry"]["temperature"] = -50.0  # below min -10
        with self.assertRaises(h.ValidationError) as ctx:
            h.validate(evt)
        self.assertEqual(ctx.exception.reason, "out_of_range")

    def test_unknown_machine_type_raises(self):
        evt = _make_cnc_event(machine_type="laser_cutter")
        with self.assertRaises(h.ValidationError) as ctx:
            h.validate(evt)
        self.assertEqual(ctx.exception.reason, "unknown_machine_type")

    def test_invalid_status_raises(self):
        evt = _make_cnc_event(status="broken")
        with self.assertRaises(h.ValidationError) as ctx:
            h.validate(evt)
        self.assertEqual(ctx.exception.reason, "invalid_status")

    def test_invalid_timestamp_raises(self):
        evt = _make_cnc_event(timestamp="not-a-date")
        with self.assertRaises(h.ValidationError) as ctx:
            h.validate(evt)
        self.assertEqual(ctx.exception.reason, "invalid_timestamp")

    def test_conveyor_motor_passes(self):
        evt = {
            "event_id": "test-002",
            "machine_id": "M005",
            "machine_type": "conveyor_motor",
            "factory_id": "AUTOFORGE_01",
            "timestamp": "2026-06-03T10:00:00Z",
            "status": "healthy",
            "telemetry": {"rpm": 1500.0, "temperature": 45.0, "power_consumption": 5.2},
            "anomaly_detected": False,
            "anomaly_type": None,
            "anomaly_severity": 0.0,
            "degradation_level": 0.0,
        }
        h.validate(evt)  # no exception

    def test_hydraulic_press_missing_pressure_raises(self):
        evt = {
            "event_id": "test-003",
            "machine_id": "M006",
            "machine_type": "hydraulic_press",
            "factory_id": "AUTOFORGE_01",
            "timestamp": "2026-06-03T10:00:00Z",
            "status": "warning",
            "telemetry": {"temperature": 55.0, "cycle_time": 12.5},
            # hydraulic_pressure missing
            "anomaly_detected": False,
            "anomaly_type": None,
            "anomaly_severity": 0.0,
            "degradation_level": 0.0,
        }
        with self.assertRaises(h.ValidationError) as ctx:
            h.validate(evt)
        self.assertEqual(ctx.exception.reason, "missing_telemetry_fields")


class TestHandlerRouting(unittest.TestCase):

    def test_valid_record_goes_to_raw_bucket(self):
        mock_s3 = MagicMock()
        evt = _lambda_event([_make_cnc_event()])
        with patch.object(h, "s3", mock_s3):
            stats = h.handler(evt, None)
        self.assertEqual(stats["valid"], 1)
        self.assertEqual(stats["quarantined"], 0)
        call_kwargs = mock_s3.put_object.call_args[1]
        self.assertEqual(call_kwargs["Bucket"], "test-data-lake")
        self.assertIn("raw/", call_kwargs["Key"])

    def test_invalid_record_goes_to_quarantine(self):
        mock_s3 = MagicMock()
        bad_evt = _make_cnc_event()
        del bad_evt["machine_id"]
        evt = _lambda_event([bad_evt])
        with patch.object(h, "s3", mock_s3):
            stats = h.handler(evt, None)
        self.assertEqual(stats["quarantined"], 1)
        self.assertEqual(stats["valid"], 0)
        call_kwargs = mock_s3.put_object.call_args[1]
        self.assertEqual(call_kwargs["Bucket"], "test-quarantine")

    def test_decode_error_handled_gracefully(self):
        mock_s3 = MagicMock()
        bad_record = {
            "kinesis": {
                "data": "this-is-not-base64!!!",
                "sequenceNumber": "seq-bad",
            }
        }
        evt = {"Records": [bad_record]}
        with patch.object(h, "s3", mock_s3):
            stats = h.handler(evt, None)
        self.assertEqual(stats["decode_errors"], 1)
        self.assertEqual(stats["valid"], 0)

    def test_mixed_batch_routes_correctly(self):
        mock_s3 = MagicMock()
        good = _make_cnc_event(event_id="good-1")
        bad = _make_cnc_event(event_id="bad-1")
        del bad["machine_id"]
        evt = _lambda_event([good, bad])
        with patch.object(h, "s3", mock_s3):
            stats = h.handler(evt, None)
        self.assertEqual(stats["total"], 2)
        self.assertEqual(stats["valid"], 1)
        self.assertEqual(stats["quarantined"], 1)

    def test_enqueue_epoch_stripped_before_s3_write(self):
        """_enqueue_epoch internal metadata must not appear in S3 payloads."""
        mock_s3 = MagicMock()
        evt_with_epoch = _make_cnc_event()
        evt_with_epoch["_enqueue_epoch"] = 1234567890.123
        evt = _lambda_event([evt_with_epoch])
        with patch.object(h, "s3", mock_s3):
            h.handler(evt, None)
        written_body = json.loads(mock_s3.put_object.call_args[1]["Body"].decode())
        self.assertNotIn("_enqueue_epoch", written_body)


if __name__ == "__main__":
    unittest.main()
