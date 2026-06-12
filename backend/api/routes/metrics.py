"""
Operational metrics route for the AutoForge backend.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends

from backend.api.dependencies import get_metrics_service
from backend.models.response_models import MetricsResponse
from backend.services.metrics_service import MetricsService

router = APIRouter(tags=["Metrics"])


@router.get("/metrics", response_model=MetricsResponse, summary="Ingestion metrics")
async def ingestion_metrics(
    svc: MetricsService = Depends(get_metrics_service),
):
    """
    Returns operational ingestion metrics: throughput, latency,
    validation failures, anomaly counts, and queue depth.
    """
    return svc.get_metrics()
