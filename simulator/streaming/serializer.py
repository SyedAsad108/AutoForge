"""
Event serialization for the AutoForge telemetry streaming pipeline.

Transforms raw machine telemetry dictionaries into stream-ready event
envelopes with UUID event IDs, factory context, and anomaly metadata.
"""

import json
import uuid
from typing import Any, Dict

from simulator.machines.base_machine import BaseMachine
from simulator.telemetry.anomalies import AnomalyType
from simulator.utils.constants import FACTORY_ID
from simulator.utils.helpers import get_current_timestamp


def serialize_telemetry_event(machine: BaseMachine) -> Dict[str, Any]:
    """
    Builds a stream-ready event envelope from a machine's current state.

    The envelope wraps the machine-specific telemetry inside a standardised
    structure suitable for downstream ingestion (Kinesis, Kafka, etc.).

    Returns:
        A JSON-serialisable dictionary.
    """
    raw = machine.generate_telemetry()

    # Separate the machine-specific metrics from the envelope fields
    envelope_keys = {"machine_id", "machine_type", "status", "timestamp"}
    telemetry_payload = {k: v for k, v in raw.items() if k not in envelope_keys}

    anomaly_active = machine.current_anomaly != AnomalyType.NONE

    event: Dict[str, Any] = {
        "event_id": str(uuid.uuid4()),
        "machine_id": raw["machine_id"],
        "machine_type": raw["machine_type"],
        "factory_id": FACTORY_ID,
        "timestamp": raw.get("timestamp", get_current_timestamp()),
        "status": raw["status"],
        "telemetry": telemetry_payload,
        "anomaly_detected": anomaly_active,
        "anomaly_type": machine.current_anomaly.value if anomaly_active else None,
        "anomaly_severity": round(machine.anomaly_severity, 4) if anomaly_active else 0.0,
        "degradation_level": round(machine.degradation_level, 4),
    }
    return event


def event_to_json(event: Dict[str, Any]) -> str:
    """Serialise an event dict to a compact JSON string (NDJSON-safe)."""
    return json.dumps(event, separators=(",", ":"))


def event_to_pretty_json(event: Dict[str, Any]) -> str:
    """Serialise an event dict to indented JSON for human inspection."""
    return json.dumps(event, indent=2)
