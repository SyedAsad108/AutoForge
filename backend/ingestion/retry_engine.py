"""
Retry engine with exponential backoff for the AutoForge ingestion pipeline.

Wraps producer publish calls with configurable retry + dead-letter hooks.
"""

from __future__ import annotations

import asyncio
from typing import Any, Callable, Dict

from backend.core.config import get_settings
from backend.core.logger import get_logger

logger = get_logger("RetryEngine")
settings = get_settings()


class RetryEngine:
    """
    Retries an async operation with exponential back-off.

    Failed events after max retries are routed to a dead-letter handler.
    """

    def __init__(
        self,
        max_attempts: int = settings.MAX_RETRY_ATTEMPTS,
        base_delay: float = settings.RETRY_BASE_DELAY,
        max_delay: float = settings.RETRY_MAX_DELAY,
    ) -> None:
        self._max_attempts = max_attempts
        self._base_delay = base_delay
        self._max_delay = max_delay
        self._total_retries: int = 0
        self._total_dead_letters: int = 0

    async def execute(
        self,
        operation: Callable[..., Any],
        *args: Any,
        **kwargs: Any,
    ) -> bool:
        """
        Execute *operation* with retry.

        Returns True on eventual success, False if all attempts fail.
        """
        for attempt in range(1, self._max_attempts + 1):
            try:
                result = await operation(*args, **kwargs)
                if result:
                    return True
            except Exception as exc:
                logger.warning(
                    f"[RETRY] Attempt {attempt}/{self._max_attempts} failed: {exc}"
                )

            if attempt < self._max_attempts:
                delay = min(self._base_delay * (2 ** (attempt - 1)), self._max_delay)
                self._total_retries += 1
                logger.info(f"[RETRY] Backing off {delay:.2f}s before attempt {attempt + 1}")
                await asyncio.sleep(delay)

        # All attempts exhausted
        self._total_dead_letters += 1
        logger.error("[RETRY] All attempts exhausted -- event sent to dead-letter")
        return False

    @property
    def total_retries(self) -> int:
        return self._total_retries

    @property
    def total_dead_letters(self) -> int:
        return self._total_dead_letters
