from __future__ import annotations

from typing import List, Optional
from pydantic import BaseModel, Field

class DiagnosticRecord(BaseModel):
    """Diagnostic analysis for an anomalous telemetry event."""
    event_id: str = Field(..., description="Unique event identifier")
    machine_id: str = Field(..., description="Identifier of the target asset")
    machine_type: str = Field(..., description="Industrial class of the machine")
    timestamp: str = Field(..., description="Timestamp when the event occurred")
    anomaly_type: str = Field(..., description="Raw category of the anomaly")
    explanation: str = Field(..., description="Human-readable explanation of the trigger condition")
    evidence: str = Field(..., description="Sensor evidence value that violated threshold rules")
    probable_causes: List[str] = Field(..., description="Ranked list of potential root causes with probabilities")
    recommendations: List[str] = Field(..., description="Actions that operations/maintenance should perform")
    confidence: float = Field(..., description="Heuristic diagnostic confidence coefficient [0.0 - 1.0]")

class RootCauseDistribution(BaseModel):
    """Aggregate distribution of identified root causes across the plant fleet."""
    cause: str = Field(..., description="Name of the root cause candidate")
    count: int = Field(..., description="Number of times this cause was diagnosed")
    avg_confidence: float = Field(..., description="Average diagnostic confidence score for this cause")
