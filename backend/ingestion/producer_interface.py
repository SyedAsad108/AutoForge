"""
Producer abstraction for the AutoForge ingestion pipeline.

Defines the ``ProducerInterface`` that all concrete producers must
implement.  This enables swapping local persistence for Kinesis / Kafka
in later phases without touching any ingestion logic.
"""

from __future__ import annotations

import abc
from typing import Any, Dict, List


class ProducerInterface(abc.ABC):
    """
    Abstract producer that downstream sinks must implement.
    """

    @abc.abstractmethod
    async def publish_event(self, event: Dict[str, Any]) -> bool:
        """Publish a single event.  Return True on success."""
        ...

    @abc.abstractmethod
    async def publish_batch(self, events: List[Dict[str, Any]]) -> int:
        """
        Publish a batch of events.

        Returns the number of events successfully published.
        """
        ...

    @abc.abstractmethod
    async def health_check(self) -> bool:
        """Return True if the producer sink is healthy."""
        ...
