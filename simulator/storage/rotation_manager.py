"""
File rotation manager for the AutoForge local storage layer.

Creates date-partitioned directories and time-stamped NDJSON files.
Rotates the active file at a configurable interval.

Example output:
  data/raw_stream/2026-04-26/telemetry_12-00.ndjson
  data/raw_stream/2026-04-26/telemetry_12-05.ndjson
"""

import datetime
import os
from typing import Optional

from simulator.storage.local_writer import LocalWriter
from simulator.utils.constants import LOCAL_STORAGE_BASE_DIR, FILE_ROTATION_INTERVAL_SECONDS
from simulator.utils.logger import setup_logger

logger = setup_logger("RotationManager")


class RotationManager:
    """
    Manages the lifecycle of ``LocalWriter`` instances, rotating to a
    new file whenever the configured interval elapses.
    """

    def __init__(
        self,
        base_dir: str = LOCAL_STORAGE_BASE_DIR,
        rotation_seconds: int = FILE_ROTATION_INTERVAL_SECONDS,
    ):
        self._base_dir = base_dir
        self._rotation_seconds = rotation_seconds
        self._current_writer: Optional[LocalWriter] = None
        self._rotation_due: Optional[datetime.datetime] = None

    @property
    def current_writer(self) -> LocalWriter:
        """Return the active writer, rotating if necessary."""
        now = datetime.datetime.now(datetime.timezone.utc)
        if self._current_writer is None or (self._rotation_due and now >= self._rotation_due):
            self._rotate(now)
        return self._current_writer  # type: ignore[return-value]

    def _rotate(self, now: datetime.datetime) -> None:
        """Close the old writer and open a fresh one."""
        if self._current_writer is not None:
            self._current_writer.flush()
            self._current_writer.close()
            logger.info(
                f"[PERSISTENCE] Rotated file  "
                f"wrote {self._current_writer.events_written} events to "
                f"{self._current_writer.file_path}"
            )

        date_str = now.strftime("%Y-%m-%d")
        time_str = now.strftime("%H-%M")
        dir_path = os.path.join(self._base_dir, date_str)
        file_path = os.path.join(dir_path, f"telemetry_{time_str}.ndjson")

        self._current_writer = LocalWriter(file_path)
        self._current_writer.open()
        self._rotation_due = now + datetime.timedelta(seconds=self._rotation_seconds)
        logger.info(f"[PERSISTENCE] Opened new stream file: {file_path}")

    def close(self) -> None:
        """Flush and close the current writer."""
        if self._current_writer is not None:
            self._current_writer.flush()
            self._current_writer.close()
