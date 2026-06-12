"""
FastAPI router for Athena analytics endpoints.
Exposes factory aggregates, alerts, registries, machine details, and summary metrics.
Phase 10.5: Added hourly-trends, energy-profile, business-kpis, recommendations endpoints.
"""

from __future__ import annotations

from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query

from backend.api.dependencies import get_analytics_service
from backend.core.security import verify_api_key
from backend.services.analytics_service import AnalyticsService
from backend.models.analytics_models import (
    FactorySummaryResponse,
    AlertEvent,
    MachineHealthRecord,
    MachineAnalyticsResponse,
    AggregatedAnalyticsResponse,
    HourlyTrendRecord,
    EnergyProfileRecord,
    BusinessKPIResponse,
    OperationalRecommendation,
    TelemetryActivityResponse,
)
from backend.models.diagnostic_models import DiagnosticRecord, RootCauseDistribution
from backend.services.pipeline_metrics_service import PipelineMetricsService

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get(
    "/factory-summary",
    response_model=FactorySummaryResponse,
    summary="Get factory machinery summary",
    description="Returns aggregated machine counts categorized by operational health status.",
)
async def get_factory_summary(
    _api_key: str = Depends(verify_api_key),
    svc: AnalyticsService = Depends(get_analytics_service),
):
    return await svc.get_factory_summary()


@router.get(
    "/alerts",
    response_model=List[AlertEvent],
    summary="Get recent anomalies",
    description="Returns a chronological list of recent anomaly alerts from the curated dataset.",
)
async def get_alerts(
    limit: int = Query(50, ge=1, le=500, description="Maximum number of alerts to retrieve"),
    _api_key: str = Depends(verify_api_key),
    svc: AnalyticsService = Depends(get_analytics_service),
):
    return await svc.get_alerts(limit=limit)


@router.get(
    "/machines",
    response_model=List[MachineHealthRecord],
    summary="List machine inventory",
    description="Lists all machines with cumulative event counts, temperatures, degradation, and health status.",
)
async def get_machines(
    _api_key: str = Depends(verify_api_key),
    svc: AnalyticsService = Depends(get_analytics_service),
):
    return await svc.get_machines()


@router.get(
    "/machine/{machine_id}",
    response_model=MachineAnalyticsResponse,
    summary="Get machine details",
    description="Returns comprehensive details and recent telemetry history for a specific machine ID.",
)
async def get_machine_details(
    machine_id: str,
    window: str = Query("24h", description="Time range for trends (15m, 1h, 24h, 7d)"),
    _api_key: str = Depends(verify_api_key),
    svc: AnalyticsService = Depends(get_analytics_service),
):
    analytics = await svc.get_machine_analytics(machine_id, window=window)
    if not analytics:
        raise HTTPException(status_code=404, detail=f"Machine {machine_id} not found in analytics catalog")
    return analytics


@router.get(
    "/diagnostics",
    response_model=List[DiagnosticRecord],
    summary="Get diagnostics logs",
    description="Returns a chronological list of industrial diagnostics for anomalous events.",
)
async def get_diagnostics(
    limit: int = Query(50, ge=1, le=500, description="Maximum number of records to retrieve"),
    _api_key: str = Depends(verify_api_key),
    svc: AnalyticsService = Depends(get_analytics_service),
):
    return await svc.get_diagnostics(limit=limit)


@router.get(
    "/diagnostics/{machine_id}",
    response_model=List[DiagnosticRecord],
    summary="Get diagnostics logs for a machine",
    description="Returns a list of industrial diagnostics for a specific machine ID.",
)
async def get_machine_diagnostics(
    machine_id: str,
    limit: int = Query(50, ge=1, le=500, description="Maximum number of records to retrieve"),
    _api_key: str = Depends(verify_api_key),
    svc: AnalyticsService = Depends(get_analytics_service),
):
    return await svc.get_diagnostics(limit=limit, machine_id=machine_id)


@router.get(
    "/root-causes",
    response_model=List[RootCauseDistribution],
    summary="Get root cause distribution",
    description="Returns aggregated distributions and average confidence scores for diagnosed root causes.",
)
async def get_root_causes(
    _api_key: str = Depends(verify_api_key),
    svc: AnalyticsService = Depends(get_analytics_service),
):
    return await svc.get_root_causes()


# ---------------------------------------------------------------------------
# Phase 10.5 — Analytics Center Upgrade Endpoints
# ---------------------------------------------------------------------------

@router.get(
    "/hourly-trends",
    response_model=List[HourlyTrendRecord],
    summary="Get hourly/minute-level telemetry trends",
    description=(
        "Returns time-series telemetry aggregated by hour bucket (falling back to minute-level "
        "when there is less than one day of data). Powers the 'Are Anomalies Increasing?' chart."
    ),
)
async def get_hourly_trends(
    _api_key: str = Depends(verify_api_key),
    svc: AnalyticsService = Depends(get_analytics_service),
):
    return await svc.get_hourly_trends()


@router.get(
    "/energy-profile",
    response_model=List[EnergyProfileRecord],
    summary="Get energy consumption profile by machine type",
    description="Returns real Athena-derived energy consumption aggregated by machine type.",
)
async def get_energy_profile(
    _api_key: str = Depends(verify_api_key),
    svc: AnalyticsService = Depends(get_analytics_service),
):
    return await svc.get_energy_profile()


@router.get(
    "/business-kpis",
    response_model=BusinessKPIResponse,
    summary="Get executive-grade manufacturing KPIs",
    description=(
        "Returns computed business KPIs including Factory Health Score, Production Efficiency, "
        "Anomaly Rate, Production Risk, Most Affected Machine, and Energy Leader."
    ),
)
async def get_business_kpis(
    _api_key: str = Depends(verify_api_key),
    svc: AnalyticsService = Depends(get_analytics_service),
):
    return await svc.get_business_kpis()


@router.get(
    "/recommendations",
    response_model=List[OperationalRecommendation],
    summary="Get rule-based operational recommendations",
    description=(
        "Returns prioritized maintenance and operational recommendations derived from "
        "machine health data using rule-based thresholds. No machine learning."
    ),
)
async def get_recommendations(
    _api_key: str = Depends(verify_api_key),
    svc: AnalyticsService = Depends(get_analytics_service),
):
    return await svc.get_recommendations()


@router.get(
    "/telemetry-activity",
    response_model=TelemetryActivityResponse,
    summary="Get telemetry activity aggregates and pipeline health",
    description="Returns dynamic time-series data, rate/anomaly KPIs, active machine breakdown, and pipeline status.",
)
async def get_telemetry_activity(
    window: str = Query("24h", description="Time window filter (15m, 1h, 24h, 7d)"),
    _api_key: str = Depends(verify_api_key),
    svc: AnalyticsService = Depends(get_analytics_service),
):
    return await svc.get_telemetry_activity(window=window)


@router.get(
    "",
    response_model=AggregatedAnalyticsResponse,
    summary="Get daily summaries and distributions",
    description="Returns daily historical factory summaries and overall anomaly counts by category.",
)
async def get_analytics(
    _api_key: str = Depends(verify_api_key),
    svc: AnalyticsService = Depends(get_analytics_service),
):
    return await svc.get_aggregated_analytics()

@router.get(
    "/pipeline/realtime",
    summary="Get real-time pipeline metrics",
    description="Returns live metrics from AWS infrastructure regarding pipeline throughput, lag, and S3 totals.",
)
async def get_pipeline_realtime(
    _api_key: str = Depends(verify_api_key),
    svc: AnalyticsService = Depends(get_analytics_service),
):
    pipeline_svc = PipelineMetricsService(svc.athena)
    return await pipeline_svc.get_realtime_metrics()
