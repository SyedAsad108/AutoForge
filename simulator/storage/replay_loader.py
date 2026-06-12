"""
Replay loader for the AutoForge storage layer.

Reads NDJSON files produced by the local writer and yields events
for the replay engine.
"""

import json
import os
from typing import Any, Dict, Generator, List, Optional

from simulator.utils.logger import setup_logger

logger = setup_logger("ReplayLoader")


class ReplayLoader:
    """
    Scans date-partitioned directories for NDJSON telemetry files and
    yields events in chronological order.
    """

    def __init__(self, base_dir: str):
        self._base_dir = base_dir

    def list_available_dates(self) -> List[str]:
        """Return sorted list of date directories available for replay."""
        if not os.path.isdir(self._base_dir):
            return []
        dates = sorted(
            d for d in os.listdir(self._base_dir)
            if os.path.isdir(os.path.join(self._base_dir, d))
        )
        return dates

    def list_files_for_date(self, date_str: str) -> List[str]:
        """Return sorted NDJSON file paths for a given date."""
        date_dir = os.path.join(self._base_dir, date_str)
        if not os.path.isdir(date_dir):
            return []
        return sorted(
            os.path.join(date_dir, f)
            for f in os.listdir(date_dir)
            if f.endswith(".ndjson")
        )

    def load_events(
        self,
        date_str: Optional[str] = None,
        machine_id: Optional[str] = None,
    ) -> Generator[Dict[str, Any], None, None]:
        """
        Yield events from NDJSON files, optionally filtered by date
        and/or machine_id.
        """
        dates = [date_str] if date_str else self.list_available_dates()
        for d in dates:
            for fpath in self.list_files_for_date(d):
                yield from self._read_file(fpath, machine_id)

    def _read_file(
        self, file_path: str, machine_id: Optional[str] = None
    ) -> Generator[Dict[str, Any], None, None]:
        """Parse a single NDJSON file and yield matching events."""
        logger.info(f"[REPLAY] Loading events from {file_path}")
        with open(file_path, "r", encoding="utf-8") as fh:
            for line_no, line in enumerate(fh, start=1):
                line = line.strip()
                if not line:
                    continue
                try:
                    event = json.loads(line)
                except json.JSONDecodeError:
                    logger.warning(f"Skipping malformed JSON at {file_path}:{line_no}")
                    continue
                if machine_id and event.get("machine_id") != machine_id:
                    continue
                yield event
