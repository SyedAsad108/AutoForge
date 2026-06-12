"""
Telemetry service -- thin facade over IngestionService for API routes.
"""

from __future__ import annotations

import datetime
from typing import Any, Dict, Optional, Tuple

from backend.ingestion.ingestion_service import IngestionService
from backend.models.telemetry_models import TelemetryEvent
from backend.models.validation_models import ValidationResult


class TelemetryService:
    """
    Called by telemetry API routes to process incoming events.
    """

    def __init__(self, ingestion: IngestionService) -> None:
        self._ingestion = ingestion

    async def process_event(
        self, event: TelemetryEvent, request_id: str
    ) -> Tuple[bool, Optional[ValidationResult], str]:
        """
        Process a single telemetry event.

        Returns (accepted, validation_result, ingestion_timestamp).
        """
        now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        accepted, vr = await self._ingestion.ingest_event(event, request_id)
        return accepted, vr, now
