"""
In-memory event queue (telemetry buffer) for the AutoForge streaming pipeline.

Simulates the buffering layer that sits between event generation and a
downstream consumer (e.g. AWS Kinesis, Kafka, or local persistence).

Features:
  • bounded capacity with configurable max size
  • overflow protection (oldest events evicted on overflow)
  • batch retrieval for downstream consumers
  • time-based retention pruning
"""

import asyncio
import time
from collections import deque
from typing import Any, Deque, Dict, List, Optional

from simulator.utils.constants import STREAM_BUFFER_SIZE, EVENT_RETENTION_SECONDS
from simulator.utils.logger import setup_logger

logger = setup_logger("EventQueue")


class EventQueue:
    """
    Thread-safe, bounded, in-memory event buffer.

    Uses an ``asyncio.Queue`` for producer/consumer hand-off and maintains a
    secondary ``deque`` for historical inspection and batch retrieval.
    """

    def __init__(
        self,
        max_size: int = STREAM_BUFFER_SIZE,
        retention_seconds: int = EVENT_RETENTION_SECONDS,
    ):
        self._max_size = max_size
        self._retention_seconds = retention_seconds
        self._queue: asyncio.Queue[Dict[str, Any]] = asyncio.Queue(maxsize=max_size)
        self._history: Deque[Dict[str, Any]] = deque(maxlen=max_size)
        self._total_enqueued: int = 0
        self._total_dropped: int = 0

    # ------------------------------------------------------------------
    # Producer interface
    # ------------------------------------------------------------------
    async def put(self, event: Dict[str, Any]) -> None:
        """
        Enqueue a telemetry event.

        If the queue is full the oldest event is dropped to make room
        (back-pressure strategy).
        """
        if self._queue.full():
            try:
                self._queue.get_nowait()
                self._total_dropped += 1
            except asyncio.QueueEmpty:
                pass

        await self._queue.put(event)
        self._history.append(event)
        self._total_enqueued += 1

    def put_nowait(self, event: Dict[str, Any]) -> None:
        """Non-async enqueue with overflow eviction."""
        if self._queue.full():
            try:
                self._queue.get_nowait()
                self._total_dropped += 1
            except asyncio.QueueEmpty:
                pass
        self._queue.put_nowait(event)
        self._history.append(event)
        self._total_enqueued += 1

    # ------------------------------------------------------------------
    # Consumer interface
    # ------------------------------------------------------------------
    async def get(self) -> Dict[str, Any]:
        """Block until an event is available, then return it."""
        return await self._queue.get()

    def get_nowait(self) -> Optional[Dict[str, Any]]:
        """Return an event immediately or ``None``."""
        try:
            return self._queue.get_nowait()
        except asyncio.QueueEmpty:
            return None

    async def get_batch(self, batch_size: int = 50) -> List[Dict[str, Any]]:
        """
        Drain up to *batch_size* events from the queue.

        Returns immediately with whatever is available (possibly empty).
        """
        batch: List[Dict[str, Any]] = []
        for _ in range(batch_size):
            try:
                batch.append(self._queue.get_nowait())
            except asyncio.QueueEmpty:
                break
        return batch

    # ------------------------------------------------------------------
    # Inspection helpers
    # ------------------------------------------------------------------
    @property
    def size(self) -> int:
        return self._queue.qsize()

    @property
    def total_enqueued(self) -> int:
        return self._total_enqueued

    @property
    def total_dropped(self) -> int:
        return self._total_dropped

    def recent_events(self, n: int = 100) -> List[Dict[str, Any]]:
        """Return the *n* most recent events from history."""
        return list(self._history)[-n:]

    def prune_history(self) -> int:
        """
        Remove events from history older than the retention window.

        Returns the number of pruned events.
        """
        cutoff = time.time() - self._retention_seconds
        pruned = 0
        while self._history:
            oldest = self._history[0]
            ts = oldest.get("_enqueue_epoch", 0)
            if ts < cutoff:
                self._history.popleft()
                pruned += 1
            else:
                break
        return pruned
