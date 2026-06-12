"""
Industrial-grade telemetry validation engine.

Performs two layers of validation:
  1. Schema validation  -- handled by Pydantic at the API boundary
  2. Range validation   -- per-machine-type telemetry field bounds

The range rules are defined in ``backend.core.constants.TELEMETRY_RANGES``.
"""

from __future__ import annotations

from backend.core.constants import TELEMETRY_RANGES
from backend.core.logger import get_logger
from backend.models.telemetry_models import TelemetryEvent
from backend.models.validation_models import ValidationResult

logger = get_logger("ValidationEngine")


class ValidationEngine:
    """
    Validates telemetry events beyond what Pydantic enforces.

    Checks that every numeric telemetry field falls within the
    machine-specific industrial range.
    """

    def validate(self, event: TelemetryEvent) -> ValidationResult:
        """
        Run range validation on a parsed TelemetryEvent.

        Returns a ``ValidationResult`` indicating success or itemised errors.
        """
        result = ValidationResult()
        ranges = TELEMETRY_RANGES.get(event.machine_type)

        if ranges is None:
            # No range rules for this machine type -- pass through
            return result

        for field_name, (lo, hi) in ranges.items():
            value = event.telemetry.get(field_name)
            if value is None:
                # Field missing -- acceptable (partial telemetry updates)
                continue
            if not isinstance(value, (int, float)):
                result.add_error(field_name, f"Expected numeric, got {type(value).__name__}")
                continue
            if value < lo or value > hi:
                result.add_error(
                    field_name,
                    f"Value {value} outside range [{lo}, {hi}]",
                )

        if not result.is_valid:
            logger.warning(
                f"[VALIDATION] Event {event.event_id} from {event.machine_id} "
                f"failed range checks: {result.errors}"
            )
        return result
