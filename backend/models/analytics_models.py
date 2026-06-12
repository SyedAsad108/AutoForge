"""
Pydantic v2 models for Analytics API response schemas.
Exposes structured schema information for FastAPI/Swagger.
"""

from __future__ import annotations
from typing import List, Optional
from pydantic import BaseModel, Field


class FactorySummaryResponse(BaseModel):
    """Overall factory machinery status summary."""
    total_machines: int = Field(..., description="Total active machines in the factory")
    healthy: int = Field(..., description="Number of healthy machines")
    warning: int = Field(..., description="Number of machines with warnings")
    critical: int = Field(..., description="Number of critical machines")


class AlertEvent(BaseModel):
    """Represents a historical or active anomaly event record."""
    event_id: str = Field(..., description="UUID identifying the event")
    machine_id: str = Field(..., description="Machine ID")
    machine_type: str = Field(..., description="Machine Type")
    timestamp: str = Field(..., description="ISO 8601 UTC timestamp")
    anomaly_type: str = Field(..., description="Anomaly failure mode")
    severity: float = Field(..., description="Anomaly severity score")
    status: str = Field(..., description="Operational status during alert")


class MachineHealthRecord(BaseModel):
    """Aggregate health profile of a single machine."""
    machine_id: str = Field(..., description="Machine identifier")
    machine_type: str = Field(..., description="Machine type")
    total_events: int = Field(..., description="Total telemetry packets received")
    anomaly_events: int = Field(..., description="Total anomalous events")
    anomaly_rate_percent: float = Field(..., description="Percentage of anomalous events")
    avg_temperature: Optional[float] = Field(None, description="Average temperature in Celsius")
    max_degradation_level: float = Field(..., description="Maximum degradation score (0.0 to 1.0)")
    health_status: str = Field(..., description="Determined status: healthy, warning, critical")
    health_score: Optional[float] = Field(None, description="Weighted health score (0-100)")



class MachineHistoryRecord(BaseModel):
    """Point-in-time historical metrics for a specific machine."""
    timestamp: str = Field(..., description="ISO 8601 UTC timestamp")
    temperature: Optional[float] = Field(None, description="Temperature in Celsius")
    degradation_level: float = Field(..., description="Degradation level (0.0 to 1.0)")
    anomaly_detected: bool = Field(..., description="Anomaly status flag")
    status: str = Field(..., description="Operational status")
    pressure: Optional[float] = Field(None, description="Pressure in bar")
    power_consumption: Optional[float] = Field(None, description="Power in kW")
    vibration: Optional[float] = Field(None, description="Vibration in mm/s")
    cycle_efficiency: Optional[float] = Field(None, description="Efficiency percentage")


class MachineExplanationDetail(BaseModel):
    problem: str
    confidence: float
    possible_causes: List[str]
    operational_impact: str
    recommended_action: str


class RootCauseItem(BaseModel):
    cause: str
    confidence: float
    explanation: str


class PredictiveMaintenanceDetail(BaseModel):
    failure_risk_pct: float
    maintenance_recommendation: str
    remaining_useful_life_days: float
    health_trend: str


class LiveOperatingConditions(BaseModel):
    temperature: Optional[float] = None
    pressure: Optional[float] = None
    power_consumption: Optional[float] = None
    vibration: Optional[float] = None
    degradation: float


class RiskTimelineEvent(BaseModel):
    timestamp: str
    event_type: str  # 'anomaly', 'warning', 'critical'
    description: str
    severity: float


class MachineAnalyticsResponse(BaseModel):
    """Extended statistics and history of a single machine."""
    machine_id: str = Field(..., description="Machine ID")
    machine_type: str = Field(..., description="Machine type")
    total_events: int = Field(..., description="Total events")
    anomaly_events: int = Field(..., description="Total anomaly events")
    anomaly_rate_percent: float = Field(..., description="Anomaly rate percentage")
    avg_temperature: Optional[float] = Field(None, description="Average temperature")
    max_degradation_level: float = Field(..., description="Maximum degradation level")
    health_status: str = Field(..., description="Health status")
    history: List[MachineHistoryRecord] = Field(..., description="Recent historical telemetry records")
    health_score: float = Field(..., description="Machine health score (0-100)")
    last_updated: str = Field(..., description="ISO 8601 or relative string")
    current_conditions: LiveOperatingConditions = Field(..., description="Live operating conditions")
    predictive_maintenance: PredictiveMaintenanceDetail = Field(..., description="Predictive maintenance stats")
    active_anomaly: Optional[MachineExplanationDetail] = Field(None, description="Latest active anomaly explanation")
    root_cause_analysis: List[RootCauseItem] = Field(..., description="Ranked likely root causes")
    risk_timeline: List[RiskTimelineEvent] = Field(..., description="Chronological risk/anomaly events")



class DailySummaryRecord(BaseModel):
    """Performance aggregation for a single calendar day."""
    date: str = Field(..., description="ISO-8601 date string YYYY-MM-DD")
    total_events: int = Field(..., description="Total daily events")
    active_machines: int = Field(..., description="Active unique machines count")
    total_anomalies: int = Field(..., description="Total anomaly count")
    avg_degradation_level: float = Field(..., description="Average degradation level across all machines")


class AnomalyDistributionRecord(BaseModel):
    """Categorized occurrences of a specific anomaly classification."""
    anomaly_type: str = Field(..., description="Failure mode name")
    machine_type: str = Field(..., description="Machine class")
    anomaly_count: int = Field(..., description="Number of times this anomaly occurred")
    avg_anomaly_severity: float = Field(..., description="Average severity score")


class AggregatedAnalyticsResponse(BaseModel):
    """Complete collection of daily summary trends and anomaly distributions."""
    daily_summaries: List[DailySummaryRecord] = Field(..., description="Daily factory aggregates")
    anomaly_distribution: List[AnomalyDistributionRecord] = Field(..., description="Anomaly summary by type")


# ---------------------------------------------------------------------------
# Phase 10.5 — Analytics Center Upgrade Models
# ---------------------------------------------------------------------------

class HourlyTrendRecord(BaseModel):
    """Aggregated telemetry bucket for a specific hour or day period."""
    time_label: str = Field(..., description="Time bucket label e.g. '2026-06-04 14:00'")
    total_events: int = Field(..., description="Total telemetry events in this period")
    anomaly_count: int = Field(..., description="Number of anomalous events in this period")
    anomaly_rate_pct: float = Field(..., description="Anomaly rate as a percentage (0-100)")
    healthy_count: int = Field(0, description="Machines in healthy state during period")
    warning_count: int = Field(0, description="Machines in warning state during period")
    critical_count: int = Field(0, description="Machines in critical state during period")


class EnergyProfileRecord(BaseModel):
    """Energy consumption profile for a specific machine type."""
    machine_type: str = Field(..., description="Machine type identifier")
    total_energy: float = Field(..., description="Total aggregated energy consumption units")
    avg_power: float = Field(0.0, description="Average power consumption per event")
    event_count: int = Field(0, description="Number of measurement events")


class BusinessKPIResponse(BaseModel):
    """Computed executive-level manufacturing KPIs derived from fleet telemetry."""
    factory_health_score: float = Field(..., description="Weighted factory health score 0-100")
    production_efficiency_score: float = Field(..., description="Operational efficiency score 0-100")
    overall_anomaly_rate_pct: float = Field(..., description="Fleet-wide anomaly rate percentage")
    production_risk_score: float = Field(..., description="Estimated production risk score 0-100")
    most_affected_machine_id: Optional[str] = Field(None, description="Machine ID with highest anomaly rate")
    most_affected_machine_type: Optional[str] = Field(None, description="Type of most affected machine")
    most_affected_anomaly_rate: float = Field(0.0, description="Anomaly rate of most affected machine")
    energy_leader_type: Optional[str] = Field(None, description="Machine type consuming most energy")
    energy_leader_value: float = Field(0.0, description="Total energy units of the top consumer")
    total_machines: int = Field(0, description="Total machines tracked")
    healthy_count: int = Field(0, description="Healthy machine count")
    warning_count: int = Field(0, description="Warning machine count")
    critical_count: int = Field(0, description="Critical machine count")


class OperationalRecommendation(BaseModel):
    """Rule-based operational recommendation for maintenance and operations teams."""
    priority: str = Field(..., description="Priority level: critical, warning, info")
    machine_id: Optional[str] = Field(None, description="Specific machine ID if applicable")
    machine_type: Optional[str] = Field(None, description="Machine type if applicable")
    recommendation: str = Field(..., description="Human-readable recommendation text")
    reason: str = Field(..., description="Rule-based rationale for the recommendation")
    metric_value: Optional[float] = Field(None, description="The triggering metric value")
    metric_name: Optional[str] = Field(None, description="Name of the triggering metric")


class TelemetryActivityKPIs(BaseModel):
    """Operational summary KPIs for telemetry activity."""
    total_events: int = Field(..., description="Total events in this period")
    telemetry_rate_per_min: float = Field(..., description="Average telemetry rate per minute")
    peak_rate_per_min: float = Field(..., description="Peak telemetry rate per minute")
    anomaly_rate_pct: float = Field(..., description="Anomaly rate as percentage")
    trend_pct: float = Field(..., description="Trend percentage from previous period")


class TelemetryActivitySeriesRecord(BaseModel):
    """Individual data point for telemetry time series."""
    time_label: str = Field(..., description="Time bucket label")
    total_events: int = Field(..., description="Total events in this interval")
    anomaly_count: int = Field(..., description="Number of anomalies")
    healthy_count: int = Field(..., description="Number of healthy events")
    warning_count: int = Field(..., description="Number of warning events")
    critical_count: int = Field(..., description="Number of critical events")


class MachineActivityBreakdown(BaseModel):
    """Telemetry activity percentage contribution per machine type."""
    machine_type: str = Field(..., description="Machine type identifier")
    event_count: int = Field(..., description="Number of events")
    percentage: float = Field(..., description="Share percentage of total activity")


class TelemetryPipelineHealth(BaseModel):
    """Ingestion pipeline components status derived from data freshness."""
    simulator: str = Field(..., description="Status of the simulator")
    kinesis: str = Field(..., description="Status of the Kinesis Data Stream")
    lambda_validator: str = Field(..., description="Status of the Lambda validator")
    glue_etl: str = Field(..., description="Status of the Glue ETL catalog")
    athena_engine: str = Field(..., description="Status of the Athena query engine")
    freshness_seconds: float = Field(..., description="Seconds since the last received event")


class TelemetryActivityResponse(BaseModel):
    """Enveloping response schema for telemetry activity analysis."""
    selected_window: str = Field(..., description="The time window analyzed")
    auto_suggested_window: str = Field(..., description="The recommended time window based on data")
    time_span_seconds: float = Field(..., description="Total span of time in data")
    kpis: TelemetryActivityKPIs = Field(..., description="Operational summary KPIs")
    series: List[TelemetryActivitySeriesRecord] = Field(..., description="Telemetry volume over time series")
    machine_breakdown: List[MachineActivityBreakdown] = Field(..., description="Top active machine types breakdown")
    pipeline_health: TelemetryPipelineHealth = Field(..., description="Pipeline health monitoring status")
    insights: List[str] = Field(..., description="Factory activity insights")
    collection_progress_pct: float = Field(..., description="Progress percentage towards full analytics collection")
    estimated_time_remaining_minutes: float = Field(..., description="Estimated minutes remaining until rich analytics available")

