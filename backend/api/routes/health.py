"""
Health and readiness routes for the AutoForge backend.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends

from backend.api.dependencies import get_health_service
from backend.models.response_models import HealthResponse, ReadinessResponse
from backend.services.health_service import HealthService

router = APIRouter(tags=["Health"])


from backend.core.logger import get_logger
logger = get_logger("HealthAPI")

@router.get("/health", response_model=HealthResponse, summary="Service health check")
async def health_check():
    """Returns basic liveness status."""
    try:
        logger.info("[HEALTH] Liveness probe requested")
        from backend.core.config import get_settings
        settings = get_settings()
        response = {
            "status": "ok",
            "version": settings.APP_VERSION,
            "uptime_seconds": 0.0,
            "ingestion_queue_depth": 0,
            "throughput_events_per_sec": 0.0,
            "backend_node": settings.BACKEND_NODE_ID,
        }
        logger.info(f"[HEALTH] Liveness probe successful: {response['status']}")
        return response
    except Exception as e:
        logger.error(f"[HEALTH] Liveness probe failed: {e}")
        raise

@router.get("/ready", response_model=ReadinessResponse, summary="Readiness probe")
async def readiness_probe(
    svc: HealthService = Depends(get_health_service),
):
    """
    Kubernetes-style readiness probe.

    Returns ``ready: true`` when the ingestion pipeline is operational.
    """
    try:
        logger.info("[HEALTH] Readiness probe requested")
        health = svc.get_health()
        response = ReadinessResponse(
            ready=health["status"] == "ok",
            checks={
                "api": True,
                "ingestion_queue": health["ingestion_queue_depth"] < 9000,
                "producer": True,
            },
        )
        logger.info(f"[HEALTH] Readiness probe successful: ready={response.ready}")
        return response
    except Exception as e:
        logger.error(f"[HEALTH] Readiness probe failed: {e}")
        raise

@router.get("/health/performance", summary="Performance and Cache stats")
async def performance_metrics():
    from backend.services.cache_service import cache_service
    return cache_service.get_stats()


