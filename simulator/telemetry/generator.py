"""
Telemetry generation orchestrator.

This module is a convenience bridge that Phase 1 originally used for
direct telemetry generation.  Phase 2 re-exports the streaming
serialiser so that downstream code has a single import point.
"""

from simulator.streaming.serializer import (
    serialize_telemetry_event,
    event_to_json,
    event_to_pretty_json,
)

__all__ = [
    "serialize_telemetry_event",
    "event_to_json",
    "event_to_pretty_json",
]
