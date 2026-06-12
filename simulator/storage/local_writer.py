"""
Local NDJSON writer for the AutoForge telemetry streaming pipeline.

Writes serialised telemetry events to rotated NDJSON files on disk.
"""

import json
import os
from typing import Any, Dict

from simulator.utils.logger import setup_logger

logger = setup_logger("LocalWriter")


class LocalWriter:
    """
    Appends JSON-serialised events (one per line) to a local file.

    The active file handle is managed externally by ``RotationManager``.
    This class only cares about writing to a given path.
    """

    def __init__(self, file_path: str):
        self._file_path = file_path
        self._handle = None
        self._events_written: int = 0
        self._ensure_dir()

    def _ensure_dir(self) -> None:
        os.makedirs(os.path.dirname(self._file_path), exist_ok=True)

    @property
    def events_written(self) -> int:
        return self._events_written

    def open(self) -> None:
        """Open the file for appending."""
        if self._handle is None or self._handle.closed:
            self._handle = open(self._file_path, "a", encoding="utf-8")

    def write_event(self, event: Dict[str, Any]) -> None:
        """Write a single event as one NDJSON line."""
        if self._handle is None or self._handle.closed:
            self.open()
        line = json.dumps(event, separators=(",", ":"))
        self._handle.write(line + "\n")
        self._events_written += 1

    def flush(self) -> None:
        if self._handle and not self._handle.closed:
            self._handle.flush()

    def close(self) -> None:
        if self._handle and not self._handle.closed:
            self._handle.close()

    @property
    def file_path(self) -> str:
        return self._file_path
