"""
FastAPI dependency injection for the AutoForge backend.

Provides singleton instances of services to route handlers via
``Depends(...)``.
"""

from __future__ import annotations

from functools import lru_cache

from backend.ingestion.ingestion_service import IngestionService
from backend.services.health_service import HealthService
from backend.services.metrics_service import MetricsService
from backend.services.telemetry_service import TelemetryService
from backend.services.athena_client import AthenaClient
from backend.services.analytics_service import AnalyticsService


# ---------------------------------------------------------------------------
# Singleton service instances (created once on first access)
# ---------------------------------------------------------------------------

_ingestion_service: IngestionService | None = None
_telemetry_service: TelemetryService | None = None
_health_service: HealthService | None = None
_metrics_service: MetricsService | None = None
_athena_client: AthenaClient | None = None
_analytics_service: AnalyticsService | None = None



def _ensure_services() -> None:
    global _ingestion_service, _telemetry_service, _health_service, _metrics_service, _athena_client, _analytics_service
    if _ingestion_service is None:
        _ingestion_service = IngestionService()
        _telemetry_service = TelemetryService(_ingestion_service)
        _health_service = HealthService(_ingestion_service)
        _metrics_service = MetricsService(_ingestion_service)
        _athena_client = AthenaClient()
        _analytics_service = AnalyticsService(_athena_client)



def get_ingestion_service() -> IngestionService:
    _ensure_services()
    return _ingestion_service  # type: ignore[return-value]


def get_telemetry_service() -> TelemetryService:
    _ensure_services()
    return _telemetry_service  # type: ignore[return-value]


def get_health_service() -> HealthService:
    _ensure_services()
    return _health_service  # type: ignore[return-value]


def get_metrics_service() -> MetricsService:
    _ensure_services()
    return _metrics_service  # type: ignore[return-value]


def get_analytics_service() -> AnalyticsService:
    _ensure_services()
    return _analytics_service  # type: ignore[return-value]




