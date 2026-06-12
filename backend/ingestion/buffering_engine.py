"""
Async ingestion buffer for the AutoForge backend.

Sits between the API layer and the producer layer, absorbing bursts
of incoming telemetry and draining them in controlled batches.
"""

from __future__ import annotations

import asyncio
import time
from typing import Any, Dict, List

from backend.core.config import get_settings
from backend.core.logger import get_logger
from backend.ingestion.producer_interface import ProducerInterface

logger = get_logger("BufferingEngine")
settings = get_settings()


class BufferingEngine:
    """
    Bounded async queue that drains events to a ``ProducerInterface``.
    """

    def __init__(self, producer: ProducerInterface) -> None:
        self._producer = producer
        self._queue: asyncio.Queue[Dict[str, Any]] = asyncio.Queue(
            maxsize=settings.INGESTION_BUFFER_SIZE
        )
        self._is_running = False
        self._total_buffered: int = 0
        self._total_drained: int = 0
        self._total_dropped: int = 0

    # ------------------------------------------------------------------
    # Enqueue
    # ------------------------------------------------------------------
    async def enqueue(self, event: Dict[str, Any]) -> bool:
        """
        Push an event into the buffer.

        If the queue is full, the oldest event is evicted.
        Returns True if the event was accepted.
        """
        if self._queue.full():
            try:
                self._queue.get_nowait()
                self._total_dropped += 1
                logger.warning("[BUFFER] Queue overflow -- oldest event evicted")
            except asyncio.QueueEmpty:
                pass

        await self._queue.put(event)
        self._total_buffered += 1
        return True

    # ------------------------------------------------------------------
    # Background drain loop
    # ------------------------------------------------------------------
    async def start_drain_loop(self) -> None:
        """
        Continuously drain the queue in batches and publish to the producer.
        Intended to be run as a background ``asyncio.Task``.
        """
        self._is_running = True
        logger.info("[BUFFER] Drain loop started")
        try:
            while self._is_running:
                batch = await self._drain_batch(settings.INGESTION_BATCH_SIZE)
                if batch:
                    published = await self._producer.publish_batch(batch)
                    self._total_drained += published
                await asyncio.sleep(0.05)  # yield, ~20 drain cycles/sec
        except asyncio.CancelledError:
            logger.info("[SHUTDOWN] Drain loop cancellation received")
        finally:
            # Final drain before exiting
            logger.info(f"[SHUTDOWN] Final buffer drain: {self.depth} events remaining...")
            while self.depth > 0:
                batch = await self._drain_batch(settings.INGESTION_BATCH_SIZE)
                if batch:
                    published = await self._producer.publish_batch(batch)
                    self._total_drained += published
            self._is_running = False
            logger.info("[SHUTDOWN] Ingestion buffer drained and stopped")

    async def _drain_batch(self, size: int) -> List[Dict[str, Any]]:
        items: List[Dict[str, Any]] = []
        for _ in range(size):
            try:
                items.append(self._queue.get_nowait())
            except asyncio.QueueEmpty:
                break
        return items

    def stop(self) -> None:
        self._is_running = False
        logger.info("[BUFFER] Drain loop stopped")

    # ------------------------------------------------------------------
    # Metrics
    # ------------------------------------------------------------------
    @property
    def depth(self) -> int:
        return self._queue.qsize()

    @property
    def total_buffered(self) -> int:
        return self._total_buffered

    @property
    def total_drained(self) -> int:
        return self._total_drained

    @property
    def total_dropped(self) -> int:
        return self._total_dropped
