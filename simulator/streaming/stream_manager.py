"""
Stream Manager for the AutoForge telemetry pipeline.

Coordinates the relationship between the event queue, the local
persistence layer, and future downstream consumers.

Runs as a background asyncio task that:
  1. Drains events from the ``EventQueue``
  2. Persists them to local NDJSON storage (if enabled)
  3. Periodically logs queue and persistence stats
"""

import asyncio
import time
from typing import Any, Dict, Optional

from simulator.streaming.event_queue import EventQueue
from simulator.storage.rotation_manager import RotationManager
from simulator.utils.constants import LOCAL_STORAGE_ENABLED
from simulator.utils.logger import setup_logger

logger = setup_logger("StreamManager")


class StreamManager:
    """
    Background consumer that drains the event queue and persists
    events to the local NDJSON store.
    """

    def __init__(self, event_queue: EventQueue):
        self._queue = event_queue
        self._rotation_mgr: Optional[RotationManager] = (
            RotationManager() if LOCAL_STORAGE_ENABLED else None
        )
        self._is_running = False
        self._events_persisted: int = 0
        self._last_stats_time: float = time.time()

    async def start(self) -> None:
        """Run the drain loop until stopped."""
        self._is_running = True
        logger.info("[STREAM] StreamManager started — draining event queue")
        try:
            while self._is_running:
                batch = await self._queue.get_batch(batch_size=100)
                for event in batch:
                    self._persist(event)

                # Log stats every ~10 seconds
                now = time.time()
                if now - self._last_stats_time >= 10.0:
                    self._log_stats()
                    self._last_stats_time = now

                # Yield to event loop
                await asyncio.sleep(0.1)
        except asyncio.CancelledError:
            logger.info("[SHUTDOWN] StreamManager cancellation received.")
        finally:
            # Drain remaining queue before exiting
            logger.info(f"[SHUTDOWN] Final drain: {self._queue.size} events remaining...")
            while self._queue.size > 0:
                batch = await self._queue.get_batch(batch_size=100)
                for event in batch:
                    self._persist(event)
            self.stop()
            logger.info("[SHUTDOWN] StreamManager cleanup complete.")

    def _persist(self, event: Dict[str, Any]) -> None:
        """Write a single event to the rotation-managed NDJSON file."""
        if self._rotation_mgr is None:
            return
        writer = self._rotation_mgr.current_writer
        writer.write_event(event)
        self._events_persisted += 1

    def _log_stats(self) -> None:
        logger.info(
            f"[QUEUE] buffer_size={self._queue.size}  "
            f"total_enqueued={self._queue.total_enqueued}  "
            f"total_dropped={self._queue.total_dropped}  "
            f"persisted={self._events_persisted}"
        )

    def stop(self) -> None:
        """Signal the drain loop to exit and close resources."""
        if not self._is_running and self._rotation_mgr is None:
             return
             
        self._is_running = False
        if self._rotation_mgr:
            self._rotation_mgr.close()
            self._rotation_mgr = None
        logger.info(
            f"[STREAM] StreamManager stopped  "
            f"total_persisted={self._events_persisted}"
        )
