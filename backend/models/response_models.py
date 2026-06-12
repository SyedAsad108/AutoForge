"""
API response models for the AutoForge Backend.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Telemetry Ingestion Responses
# ---------------------------------------------------------------------------
class IngestionResponse(BaseModel):
    """Returned after a single telemetry event is accepted."""

    status: str = Field("accepted", description="Ingestion outcome")
    event_id: str = Field(..., description="Echo of the ingested event ID")
    ingestion_timestamp: str = Field(..., description="Server-side ingestion time")
    pipeline_status: str = Field("buffered", description="Where the event is in the pipeline")


class BatchIngestionResponse(BaseModel):
    """Returned after a batch of telemetry events is accepted."""

    status: str = "accepted"
    total_received: int = 0
    total_accepted: int = 0
    total_rejected: int = 0
    ingestion_timestamp: str = ""
    errors: list[Dict[str, Any]] = Field(default_factory=list)


class ValidationErrorResponse(BaseModel):
    """Returned when a telemetry event fails validation."""

    status: str = "rejected"
    event_id: Optional[str] = None
    errors: list[Dict[str, Any]] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Health / Metrics Responses
# ---------------------------------------------------------------------------
class HealthResponse(BaseModel):
    status: str = "ok"
    version: str = ""
    uptime_seconds: float = 0.0
    ingestion_queue_depth: int = 0
    throughput_events_per_sec: float = 0.0
    backend_node: str = ""


class ReadinessResponse(BaseModel):
    ready: bool = True
    checks: Dict[str, bool] = Field(default_factory=dict)


class MetricsResponse(BaseModel):
    total_events_ingested: int = 0
    events_per_second: float = 0.0
    failed_validations: int = 0
    active_machine_ids: int = 0
    queue_depth: int = 0
    anomaly_event_count: int = 0
    avg_ingestion_latency_ms: float = 0.0
