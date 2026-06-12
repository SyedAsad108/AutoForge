"""
Pydantic v2 models for incoming telemetry events.

These models mirror the Phase 2 event envelope produced by
``simulator.streaming.serializer`` and enforce schema-level validation
at the API boundary.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from pydantic import BaseModel, Field, field_validator

from backend.core.constants import VALID_MACHINE_TYPES, VALID_STATUSES, VALID_ANOMALY_TYPES


class TelemetryEvent(BaseModel):
    """
    Represents a single telemetry event ingested from the factory
    simulator or any compatible upstream producer.
    """

    event_id: str = Field(..., min_length=1, description="UUID identifying this event")
    machine_id: str = Field(..., min_length=1, description="Machine identifier, e.g. M001")
    machine_type: str = Field(..., description="Machine category")
    factory_id: str = Field(..., min_length=1, description="Factory identifier")
    timestamp: str = Field(..., description="ISO 8601 UTC timestamp")
    status: str = Field(..., description="Machine operational status")
    telemetry: Dict[str, Any] = Field(..., description="Machine-specific telemetry payload")
    anomaly_detected: bool = Field(False, description="Whether an anomaly is active")
    anomaly_type: Optional[str] = Field(None, description="Active anomaly type")
    anomaly_severity: float = Field(0.0, ge=0.0, le=1.0)
    degradation_level: float = Field(0.0, ge=0.0, le=1.0)

    # Accept but ignore internal fields from Phase 2
    model_config = {"extra": "ignore"}

    @field_validator("machine_type")
    @classmethod
    def validate_machine_type(cls, v: str) -> str:
        if v not in VALID_MACHINE_TYPES:
            raise ValueError(f"Unknown machine_type: {v}")
        return v

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        if v not in VALID_STATUSES:
            raise ValueError(f"Invalid status: {v}. Must be one of {VALID_STATUSES}")
        return v

    @field_validator("anomaly_type")
    @classmethod
    def validate_anomaly_type(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in VALID_ANOMALY_TYPES:
            raise ValueError(f"Unknown anomaly_type: {v}")
        return v


class TelemetryBatch(BaseModel):
    """Batch of telemetry events for bulk ingestion."""

    events: list[TelemetryEvent] = Field(
        ..., min_length=1, max_length=500, description="List of telemetry events"
    )
