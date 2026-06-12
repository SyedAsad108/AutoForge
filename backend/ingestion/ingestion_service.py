"""
Ingestion Service -- the central orchestrator of the backend pipeline.

Coordinates:
  ValidationEngine -> EnrichmentEngine -> BufferingEngine -> Producer

All telemetry API routes delegate to this service.
"""

from __future__ import annotations

import datetime
import time
from typing import Any, Dict, Optional

from backend.core.config import get_settings
from backend.core.logger import get_logger
from backend.ingestion.buffering_engine import BufferingEngine
from backend.ingestion.enrichment_engine import EnrichmentEngine
from backend.ingestion.local_producer import LocalProducer
from backend.ingestion.retry_engine import RetryEngine
from backend.ingestion.validation_engine import ValidationEngine
from backend.models.telemetry_models import TelemetryEvent
from backend.models.validation_models import ValidationResult

logger = get_logger("IngestionService")
settings = get_settings()


class IngestionService:
    """
    Singleton-style service wired up at application startup.

    Provides ``ingest_event`` which runs the full pipeline:
      validate -> enrich -> buffer -> (async drain to producer)
    """

    def __init__(self) -> None:
        self._validator = ValidationEngine()
        self._enricher = EnrichmentEngine()
        self._producer = LocalProducer()
        self._buffer = BufferingEngine(producer=self._producer)
        self._retry = RetryEngine()

        # Metrics
        self._total_ingested: int = 0
        self._total_failed: int = 0
        self._anomaly_count: int = 0
        self._machine_ids: set[str] = set()
        self._start_time: float = time.monotonic()
        self._latency_sum: float = 0.0

    # ------------------------------------------------------------------
    # Pipeline entry point
    # ------------------------------------------------------------------
    async def ingest_event(
        self, event: TelemetryEvent, request_id: str
    ) -> tuple[bool, Optional[ValidationResult]]:
        """
        Full ingestion pipeline for a single event.

        Returns ``(accepted: bool, validation_result | None)``.
        """
        tick = time.monotonic()

        # 1. Range validation
        vr = self._validator.validate(event)
        if not vr.is_valid:
            self._total_failed += 1
            logger.warning(
                f"[INGESTION] Rejected event {event.event_id} from {event.machine_id}"
            )
            return False, vr

        # 2. Enrich
        event_dict = event.model_dump()
        self._enricher.enrich(event_dict, request_id=request_id)

        # 3. Buffer (async)
        await self._buffer.enqueue(event_dict)

        # 4. Bookkeeping
        self._total_ingested += 1
        self._machine_ids.add(event.machine_id)
        if event.anomaly_detected:
            self._anomaly_count += 1
        self._latency_sum += (time.monotonic() - tick) * 1000  # ms

        logger.info(
            f"[INGESTION] Event {event.event_id} from {event.machine_id} accepted"
        )
        return True, None

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------
    @property
    def buffer(self) -> BufferingEngine:
        return self._buffer

    def close(self) -> None:
        self._buffer.stop()
        self._producer.close()

    # ------------------------------------------------------------------
    # Metrics accessors
    # ------------------------------------------------------------------
    @property
    def total_ingested(self) -> int:
        return self._total_ingested

    @property
    def total_failed(self) -> int:
        return self._total_failed

    @property
    def anomaly_count(self) -> int:
        return self._anomaly_count

    @property
    def active_machine_count(self) -> int:
        return len(self._machine_ids)

    @property
    def uptime(self) -> float:
        return time.monotonic() - self._start_time

    @property
    def events_per_second(self) -> float:
        elapsed = self.uptime
        return self._total_ingested / elapsed if elapsed > 0 else 0.0

    @property
    def avg_latency_ms(self) -> float:
        return (
            self._latency_sum / self._total_ingested
            if self._total_ingested > 0
            else 0.0
        )

    @property
    def queue_depth(self) -> int:
        return self._buffer.depth
