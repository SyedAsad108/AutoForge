"""
Telemetry Replay Engine for AutoForge.

Loads historical NDJSON telemetry from local storage and re-emits it
as a simulated live stream at a configurable speed multiplier.

Use cases:
  • analytics testing without running a live simulation
  • benchmarking downstream consumers
  • replaying specific machine streams for debugging
"""

import asyncio
import json
from typing import Optional

from simulator.storage.replay_loader import ReplayLoader
from simulator.utils.constants import LOCAL_STORAGE_BASE_DIR, DEFAULT_REPLAY_SPEED
from simulator.utils.logger import setup_logger

logger = setup_logger("ReplayEngine")


class TelemetryReplayEngine:
    """
    Re-emits historical events at configurable speed.

    Args:
        base_dir: root of the NDJSON storage tree.
        speed: replay speed multiplier (2.0 = 2× faster than real-time).
    """

    def __init__(
        self,
        base_dir: str = LOCAL_STORAGE_BASE_DIR,
        speed: float = DEFAULT_REPLAY_SPEED,
    ):
        self._loader = ReplayLoader(base_dir)
        self._speed = speed
        self._is_running = False

    async def replay(
        self,
        date_str: Optional[str] = None,
        machine_id: Optional[str] = None,
    ) -> None:
        """
        Begin replaying events.

        Events are printed to stdout as JSON.  The interval between
        events is derived from their timestamps divided by the speed
        multiplier.
        """
        self._is_running = True
        events = list(self._loader.load_events(date_str=date_str, machine_id=machine_id))
        total = len(events)
        if total == 0:
            logger.warning("[REPLAY] No events found for the specified criteria.")
            return

        logger.info(
            f"[REPLAY] Starting replay of {total} events  "
            f"speed={self._speed}x  date={date_str}  machine={machine_id}"
        )

        for idx, event in enumerate(events):
            if not self._is_running:
                break
            print(json.dumps(event))

            # Throttle: base interval is 1 s (the generation frequency)
            interval = 1.0 / self._speed
            await asyncio.sleep(interval)

            if (idx + 1) % 100 == 0:
                logger.info(f"[REPLAY] Replayed {idx + 1}/{total} events")

        logger.info("[REPLAY] Replay complete.")
        self._is_running = False

    def stop(self) -> None:
        self._is_running = False
