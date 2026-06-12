"""
Validation result models used internally by the validation engine.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class ValidationResult:
    """Outcome of validating a single telemetry event."""

    is_valid: bool = True
    errors: List[Dict[str, Any]] = field(default_factory=list)

    def add_error(self, field_name: str, message: str) -> None:
        self.is_valid = False
        self.errors.append({"field": field_name, "message": message})
