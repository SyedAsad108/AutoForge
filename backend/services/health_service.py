"""
Health service for the AutoForge backend.
"""

from __future__ import annotations

from backend.core.config import get_settings
from backend.ingestion.ingestion_service import IngestionService

settings = get_settings()


class HealthService:
    """Provides health-check data for the ``/health`` endpoint."""

    def __init__(self, ingestion: IngestionService) -> None:
        self._ingestion = ingestion

    def get_health(self) -> dict:
        return {
            "status": "ok",
            "version": settings.APP_VERSION,
            "uptime_seconds": round(self._ingestion.uptime, 2),
            "ingestion_queue_depth": self._ingestion.queue_depth,
            "throughput_events_per_sec": round(self._ingestion.events_per_second, 2),
            "backend_node": settings.BACKEND_NODE_ID,
        }
