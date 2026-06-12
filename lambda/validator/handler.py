"""
AutoForge Telemetry Validator — AWS Lambda Function
Phase 5: Kinesis → Lambda → S3 Raw / S3 Quarantine

Responsibilities:
  1. Schema validation  — required envelope fields present
  2. Range validation   — numeric telemetry values in sane bounds
  3. Machine-specific validation — type-specific required fields
  4. Anomaly tagging    — preserve anomaly metadata from simulator
  5. Routing:
       valid   → s3://autoforge-data-lake/raw/<machine_type>/<date>/
       invalid → s3://autoforge-quarantine/<date>/<reason>/

S3 key pattern (raw):
  raw/machine_type=<type>/year=YYYY/month=MM/day=DD/<event_id>.json

S3 key pattern (quarantine):
  year=YYYY/month=MM/day=DD/reason=<code>/<event_id>.json

Environment variables:
  DATA_LAKE_BUCKET   — target bucket for valid records
  QUARANTINE_BUCKET  — target bucket for invalid records
"""

import base64
import json
import logging
import os
import re
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Tuple

import boto3

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
logger = logging.getLogger()
logger.setLevel(logging.INFO)

DATA_LAKE_BUCKET = os.environ["DATA_LAKE_BUCKET"]
QUARANTINE_BUCKET = os.environ["QUARANTINE_BUCKET"]

s3 = boto3.client("s3")

# ---------------------------------------------------------------------------
# Validation constants
# ---------------------------------------------------------------------------

# Every valid event MUST carry these envelope fields
REQUIRED_ENVELOPE_FIELDS = {"machine_id", "timestamp", "machine_type", "factory_id", "status"}

# machine_type → required telemetry sub-fields
MACHINE_REQUIRED_FIELDS: Dict[str, set] = {
    "cnc_machine":        {"spindle_speed", "temperature", "tool_wear", "vibration"},
    "conveyor_motor":     {"rpm", "temperature", "power_consumption"},
    "hydraulic_press":    {"hydraulic_pressure", "temperature", "cycle_time"},
    "robotic_arm":        {"joint_load", "movement_delay", "motor_temperature", "positional_accuracy"},
    "industrial_turbine": {"rpm", "vibration", "temperature", "energy_output"},
    "cooling_system":     {"coolant_flow_rate", "temperature", "pressure"},
    "welding_unit":       {"arc_stability", "temperature", "energy_usage"},
    "assembly_robot":     {"task_completion_rate", "alignment_accuracy", "cycle_efficiency", "temperature"},
}

# Generic numeric telemetry range rules: field → (min, max)
# Applied across any machine_type that exposes the field.
RANGE_RULES: Dict[str, Tuple[float, float]] = {
    "temperature":          (-10.0,  500.0),
    "rpm":                  (0.0,    20000.0),
    "spindle_speed":        (0.0,    20000.0),
    "tool_wear":            (0.0,    100.0),
    "vibration":            (0.0,    100.0),
    "hydraulic_pressure":   (0.0,    6000.0),
    "cycle_time":           (0.0,    3600.0),
    "joint_load":           (0.0,    500.0),
    "movement_delay":       (0.0,    60.0),
    "positional_accuracy":  (0.0,    100.0),
    "energy_output":        (0.0,    10000.0),
    "coolant_flow_rate":    (0.0,    500.0),
    "pressure":             (0.0,    1000.0),
    "arc_stability":        (0.0,    100.0),
    "energy_usage":         (0.0,    1000.0),
    "task_completion_rate": (0.0,    200.0),
    "alignment_accuracy":   (0.0,    100.0),
    "cycle_efficiency":     (0.0,    100.0),
    "power_consumption":    (0.0,    1000.0),
    "motor_temperature":    (-10.0,  500.0),
}

# Valid machine statuses
VALID_STATUSES = {"healthy", "warning", "critical", "offline"}

# ISO-8601 timestamp regex (basic check)
_TS_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}")

# ---------------------------------------------------------------------------
# Validation logic
# ---------------------------------------------------------------------------

class ValidationError(Exception):
    """Carries a short machine-readable reason code."""
    def __init__(self, reason: str, detail: str = ""):
        super().__init__(detail or reason)
        self.reason = reason  # used as S3 prefix
        self.detail = detail


def _validate_envelope(event: Dict[str, Any]) -> None:
    missing = REQUIRED_ENVELOPE_FIELDS - event.keys()
    if missing:
        raise ValidationError("missing_envelope_fields", f"Missing: {sorted(missing)}")

    if not _TS_RE.match(str(event.get("timestamp", ""))):
        raise ValidationError("invalid_timestamp", f"Bad timestamp: {event.get('timestamp')}")

    if event.get("status") not in VALID_STATUSES:
        raise ValidationError("invalid_status", f"Unknown status: {event.get('status')}")

    machine_id = event.get("machine_id", "")
    if not machine_id or not isinstance(machine_id, str):
        raise ValidationError("invalid_machine_id", "machine_id must be a non-empty string")


def _validate_machine_specific(event: Dict[str, Any]) -> None:
    machine_type = event.get("machine_type", "")
    required = MACHINE_REQUIRED_FIELDS.get(machine_type)

    if required is None:
        raise ValidationError("unknown_machine_type", f"Unrecognised machine_type: {machine_type}")

    telemetry = event.get("telemetry", {})
    if not isinstance(telemetry, dict):
        raise ValidationError("missing_telemetry", "telemetry field must be a dict")

    missing = required - telemetry.keys()
    if missing:
        raise ValidationError(
            "missing_telemetry_fields",
            f"{machine_type} missing: {sorted(missing)}"
        )


def _validate_ranges(event: Dict[str, Any]) -> None:
    telemetry = event.get("telemetry", {})
    for field, (lo, hi) in RANGE_RULES.items():
        if field not in telemetry:
            continue
        val = telemetry[field]
        if not isinstance(val, (int, float)):
            raise ValidationError("non_numeric_field", f"{field}={val!r} is not numeric")
        if not (lo <= val <= hi):
            raise ValidationError(
                "out_of_range",
                f"{field}={val} out of range [{lo}, {hi}]"
            )


def validate(event: Dict[str, Any]) -> None:
    """Run all validators; raise ValidationError on first failure."""
    _validate_envelope(event)
    _validate_machine_specific(event)
    _validate_ranges(event)


# ---------------------------------------------------------------------------
# S3 routing helpers
# ---------------------------------------------------------------------------

def _now_parts() -> Tuple[str, str, str]:
    now = datetime.now(tz=timezone.utc)
    return now.strftime("%Y"), now.strftime("%m"), now.strftime("%d")


def _raw_key(event: Dict[str, Any]) -> str:
    year, month, day = _now_parts()
    machine_type = event.get("machine_type", "unknown")
    event_id = event.get("event_id", "no-event-id")
    return (
        f"raw/machine_type={machine_type}"
        f"/year={year}/month={month}/day={day}"
        f"/{event_id}.json"
    )


def _quarantine_key(event: Dict[str, Any], reason: str) -> str:
    year, month, day = _now_parts()
    event_id = event.get("event_id", "no-event-id")
    return (
        f"year={year}/month={month}/day={day}"
        f"/reason={reason}"
        f"/{event_id}.json"
    )


def _write_s3(bucket: str, key: str, body: Dict[str, Any]) -> None:
    s3.put_object(
        Bucket=bucket,
        Key=key,
        Body=json.dumps(body).encode("utf-8"),
        ContentType="application/json",
    )


# ---------------------------------------------------------------------------
# Lambda handler
# ---------------------------------------------------------------------------

def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Entry point for Kinesis → Lambda trigger.

    Each invocation receives a batch of Kinesis records.
    We process each record independently:
      - Valid   → raw S3
      - Invalid → quarantine S3 with error metadata attached
    """
    records = event.get("Records", [])
    stats = {"total": len(records), "valid": 0, "quarantined": 0, "decode_errors": 0}

    logger.info(f"[VALIDATOR] Processing batch of {len(records)} records")

    for kinesis_record in records:
        # --- 1. Base64 decode the Kinesis payload ---
        raw_payload: Optional[Dict[str, Any]] = None
        try:
            data_bytes = base64.b64decode(kinesis_record["kinesis"]["data"])
            raw_payload = json.loads(data_bytes.decode("utf-8"))
        except Exception as exc:
            logger.warning(f"[VALIDATOR] Decode error: {exc}")
            stats["decode_errors"] += 1
            # Write raw bytes as quarantine record
            error_record = {
                "error": "decode_failure",
                "detail": str(exc),
                "raw_data": kinesis_record["kinesis"].get("data", ""),
            }
            key = f"year={datetime.now(tz=timezone.utc).strftime('%Y')}/decode_error/{kinesis_record['kinesis'].get('sequenceNumber','unknown')}.json"
            try:
                _write_s3(QUARANTINE_BUCKET, key, error_record)
            except Exception as s3_err:
                logger.error(f"[VALIDATOR] Failed to write decode error to quarantine: {s3_err}")
            continue

        # --- 2. Strip internal simulator metadata before S3 write ---
        raw_payload.pop("_enqueue_epoch", None)

        # --- 3. Validate ---
        try:
            validate(raw_payload)
        except ValidationError as ve:
            logger.warning(
                f"[VALIDATOR] QUARANTINE machine_id={raw_payload.get('machine_id','?')} "
                f"reason={ve.reason} detail={ve.detail}"
            )
            stats["quarantined"] += 1
            quarantine_record = {
                **raw_payload,
                "_validation_error": ve.reason,
                "_validation_detail": ve.detail,
                "_quarantined_at": datetime.now(tz=timezone.utc).isoformat(),
            }
            key = _quarantine_key(raw_payload, ve.reason)
            try:
                _write_s3(QUARANTINE_BUCKET, key, quarantine_record)
            except Exception as s3_err:
                logger.error(f"[VALIDATOR] S3 quarantine write failed: {s3_err}")
            continue

        # --- 4. Valid record → raw S3 ---
        stats["valid"] += 1
        
        # Run Diagnostics Engine
        try:
            from diagnostics_engine import diagnose_telemetry
            raw_payload = diagnose_telemetry(raw_payload)
        except Exception as de_err:
            logger.error(f"[VALIDATOR] Diagnostics engine failure: {de_err}")

        key = _raw_key(raw_payload)
        try:
            _write_s3(DATA_LAKE_BUCKET, key, raw_payload)
            logger.debug(
                f"[VALIDATOR] RAW machine_id={raw_payload.get('machine_id')} key={key}"
            )
        except Exception as s3_err:
            logger.error(f"[VALIDATOR] S3 raw write failed for key={key}: {s3_err}")
            # Demote to quarantine on S3 write failure
            stats["valid"] -= 1
            stats["quarantined"] += 1
            fallback_record = {
                **raw_payload,
                "_validation_error": "s3_write_failure",
                "_validation_detail": str(s3_err),
            }
            fallback_key = _quarantine_key(raw_payload, "s3_write_failure")
            try:
                _write_s3(QUARANTINE_BUCKET, fallback_key, fallback_record)
            except Exception:
                pass  # best-effort; don't crash the whole batch

    logger.info(
        f"[VALIDATOR] Batch complete — "
        f"total={stats['total']} valid={stats['valid']} "
        f"quarantined={stats['quarantined']} decode_errors={stats['decode_errors']}"
    )
    return stats
