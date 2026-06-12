"""
Telemetry ingestion routes for the AutoForge backend.

POST /telemetry       -- ingest a single telemetry event
POST /telemetry/batch -- ingest a batch of events
"""

from __future__ import annotations

import datetime

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse

from backend.api.dependencies import get_telemetry_service
from backend.core.security import verify_api_key
from backend.models.telemetry_models import TelemetryBatch, TelemetryEvent
from backend.models.response_models import (
    BatchIngestionResponse,
    IngestionResponse,
    ValidationErrorResponse,
)
from backend.services.telemetry_service import TelemetryService

router = APIRouter(tags=["Telemetry"])


@router.post(
    "/telemetry",
    response_model=IngestionResponse,
    responses={422: {"model": ValidationErrorResponse}},
    summary="Ingest a single telemetry event",
)
async def ingest_telemetry(
    event: TelemetryEvent,
    request: Request,
    _api_key: str = Depends(verify_api_key),
    svc: TelemetryService = Depends(get_telemetry_service),
):
    """
    Receive and validate a single machine telemetry event.

    The event passes through schema validation, range validation,
    metadata enrichment, and is buffered for downstream persistence.
    """
    req_id = getattr(request.state, "request_id", "unknown")
    accepted, vr, ts = await svc.process_event(event, request_id=req_id)

    if not accepted and vr is not None:
        return JSONResponse(
            status_code=422,
            content={
                "status": "rejected",
                "event_id": event.event_id,
                "errors": vr.errors,
            },
        )

    return IngestionResponse(
        status="accepted",
        event_id=event.event_id,
        ingestion_timestamp=ts,
        pipeline_status="buffered",
    )


@router.post(
    "/telemetry/batch",
    response_model=BatchIngestionResponse,
    summary="Ingest a batch of telemetry events",
)
async def ingest_batch(
    batch: TelemetryBatch,
    request: Request,
    _api_key: str = Depends(verify_api_key),
    svc: TelemetryService = Depends(get_telemetry_service),
):
    """Ingest multiple telemetry events in a single request."""
    req_id = getattr(request.state, "request_id", "unknown")
    now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    accepted_count = 0
    rejected_count = 0
    errors = []

    for ev in batch.events:
        ok, vr, _ = await svc.process_event(ev, request_id=req_id)
        if ok:
            accepted_count += 1
        else:
            rejected_count += 1
            if vr:
                errors.append({"event_id": ev.event_id, "errors": vr.errors})

    return BatchIngestionResponse(
        status="accepted" if rejected_count == 0 else "partial",
        total_received=len(batch.events),
        total_accepted=accepted_count,
        total_rejected=rejected_count,
        ingestion_timestamp=now,
        errors=errors,
    )
