"""
Metrics service for the AutoForge backend.
"""

from __future__ import annotations

from backend.ingestion.ingestion_service import IngestionService


class MetricsService:
    """Computes operational ingestion metrics for the ``/metrics`` endpoint."""

    def __init__(self, ingestion: IngestionService) -> None:
        self._ingestion = ingestion

    def get_metrics(self) -> dict:
        return {
            "total_events_ingested": self._ingestion.total_ingested,
            "events_per_second": round(self._ingestion.events_per_second, 2),
            "failed_validations": self._ingestion.total_failed,
            "active_machine_ids": self._ingestion.active_machine_count,
            "queue_depth": self._ingestion.queue_depth,
            "anomaly_event_count": self._ingestion.anomaly_count,
            "avg_ingestion_latency_ms": round(self._ingestion.avg_latency_ms, 3),
        }
