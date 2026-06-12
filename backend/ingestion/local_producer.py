"""
Local NDJSON producer for the AutoForge ingestion pipeline.

Implements ``ProducerInterface`` and writes enriched events to
date-partitioned, time-rotated NDJSON files under
``data/ingestion/``.

This is the default development producer; in Phase 4 it will be
replaced by an Amazon Kinesis producer while the ingestion service
code remains unchanged.
"""

from __future__ import annotations

import datetime
import json
import os
from typing import Any, Dict, List

from backend.core.config import get_settings
from backend.core.logger import get_logger
from backend.ingestion.producer_interface import ProducerInterface

logger = get_logger("LocalProducer")
settings = get_settings()


class LocalProducer(ProducerInterface):
    """
    Appends events to rotated NDJSON files on the local filesystem.
    """

    def __init__(self) -> None:
        self._base_dir = settings.LOCAL_INGESTION_DIR
        self._rotation_seconds = settings.INGESTION_ROTATION_SECONDS
        self._current_path: str | None = None
        self._handle = None
        self._rotation_due: datetime.datetime | None = None
        self._events_written: int = 0

    # ------------------------------------------------------------------
    # ProducerInterface
    # ------------------------------------------------------------------
    async def publish_event(self, event: Dict[str, Any]) -> bool:
        try:
            self._ensure_file()
            line = json.dumps(event, separators=(",", ":"))
            self._handle.write(line + "\n")
            self._events_written += 1
            return True
        except Exception as exc:
            logger.error(f"[PRODUCER] Write failed: {exc}")
            return False

    async def publish_batch(self, events: List[Dict[str, Any]]) -> int:
        count = 0
        for ev in events:
            if await self.publish_event(ev):
                count += 1
        self._flush()
        return count

    async def health_check(self) -> bool:
        return True  # local filesystem is always "up"

    # ------------------------------------------------------------------
    # File management
    # ------------------------------------------------------------------
    def _ensure_file(self) -> None:
        now = datetime.datetime.now(datetime.timezone.utc)
        if self._handle is None or self._handle.closed or (
            self._rotation_due and now >= self._rotation_due
        ):
            self._rotate(now)

    def _rotate(self, now: datetime.datetime) -> None:
        self._flush()
        if self._handle and not self._handle.closed:
            self._handle.close()
            logger.info(
                f"[PERSISTENCE] Rotated ingestion file  "
                f"wrote={self._events_written} path={self._current_path}"
            )

        date_str = now.strftime("%Y-%m-%d")
        time_str = now.strftime("%H-%M")
        dir_path = os.path.join(self._base_dir, date_str)
        os.makedirs(dir_path, exist_ok=True)
        self._current_path = os.path.join(dir_path, f"ingestion_{time_str}.ndjson")
        self._handle = open(self._current_path, "a", encoding="utf-8")
        self._rotation_due = now + datetime.timedelta(seconds=self._rotation_seconds)
        self._events_written = 0
        logger.info(f"[PERSISTENCE] Opened ingestion file: {self._current_path}")

    def _flush(self) -> None:
        if self._handle and not self._handle.closed:
            self._handle.flush()

    def close(self) -> None:
        self._flush()
        if self._handle and not self._handle.closed:
            self._handle.close()
