"""
Telemetry Streaming Engine — the heart of Phase 2.

Orchestrates the full real-time telemetry pipeline:
  1. Runs each machine's state update + telemetry generation concurrently
  2. Serialises events into stream-ready JSON envelopes
  3. Pushes events into the EventQueue
  4. Applies correlation, degradation, and anomaly engines each tick
  5. Computes factory-wide metrics periodically
  6. Prints live structured telemetry to stdout

Designed for non-blocking asyncio execution scalable to 1 000+ machines.
"""

import asyncio
import json
import time
from typing import Any, Dict, List

from simulator.machines.base_machine import BaseMachine
from simulator.streaming.event_queue import EventQueue
from simulator.streaming.serializer import serialize_telemetry_event, event_to_json
from simulator.telemetry.correlation_engine import CorrelationEngine
from simulator.telemetry.degradation_engine import DegradationEngine
from simulator.telemetry.anomaly_engine import AnomalyEngine
from simulator.telemetry.metrics_engine import MetricsEngine
from simulator.streaming.transport.telemetry_client import TelemetryAPIClient
from simulator.streaming.transport.kinesis_client import KinesisTransportClient
from simulator.utils.constants import (
    TELEMETRY_INTERVAL_SECONDS,
    ENABLE_BACKEND_FORWARDING,
    KINESIS_FORWARDING_ENABLED,
)
from simulator.utils.logger import setup_logger

logger = setup_logger("StreamingEngine")


class TelemetryStreamingEngine:
    """
    Collects telemetry from every machine in the fleet, serialises it,
    and pushes it into the event queue.

    This class replaces the simple print-loop that Phase 1's
    ``FactorySimulator._run_machine`` used.
    """

    def __init__(
        self,
        machines: List[BaseMachine],
        event_queue: EventQueue,
    ):
        self._machines = machines
        self._queue = event_queue
        self._is_running = False

        # Sub-engines
        self._correlation = CorrelationEngine(machines)
        self._degradation = DegradationEngine(machines)
        self._anomaly = AnomalyEngine(machines)
        self._metrics = MetricsEngine(machines)

        self._tick: int = 0

        # --- Legacy FastAPI transport (Phase 3, off by default) ---
        self._api_client = None
        if ENABLE_BACKEND_FORWARDING:
            self._api_client = TelemetryAPIClient()

        # --- Phase 4.3: Kinesis transport (primary, on by default) ---
        self._kinesis_client = None
        if KINESIS_FORWARDING_ENABLED:
            self._kinesis_client = KinesisTransportClient()

        self._transport_tasks: set[asyncio.Task] = set()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    async def start(self) -> None:
        """
        Run the continuous streaming loop.

        Each tick:
          1. Apply degradation, anomaly, and correlation engines.
          2. Update every machine's state.
          3. Serialise and enqueue events.
          4. Print events + periodic metrics.
        """
        self._is_running = True
        logger.info("[STREAM] Telemetry Streaming Engine started")

        try:
            while self._is_running:
                tick_start = time.monotonic()
                self._tick += 1

                # --- Phase engines --- #
                self._degradation.tick()
                self._anomaly.tick()
                self._correlation.apply_correlations()

                # --- Generate & stream telemetry --- #
                batch_events = []
                for machine in self._machines:
                    machine.update_state()
                    event = serialize_telemetry_event(machine)
                    event["_enqueue_epoch"] = time.time()  # for retention pruning

                    # Enqueue
                    await self._queue.put(event)

                    # Emit to stdout
                    print(event_to_json(event))
                    
                    if self._api_client or self._kinesis_client:
                        batch_events.append(event)

                # --- Dispatch batch to active transports ---
                if batch_events:
                    if self._kinesis_client:
                        # Primary path: Kinesis (fire-and-forget, tracked)
                        task = asyncio.create_task(
                            self._kinesis_client.send_batch(batch_events)
                        )
                        self._transport_tasks.add(task)
                        task.add_done_callback(self._transport_tasks.discard)

                    if self._api_client:
                        # Legacy FastAPI path (only if explicitly re-enabled)
                        task = asyncio.create_task(
                            self._api_client.send_batch(batch_events)
                        )
                        self._transport_tasks.add(task)
                        task.add_done_callback(self._transport_tasks.discard)

                # --- Factory metrics (every 10 ticks) --- #
                if self._tick % 10 == 0:
                    metrics = self._metrics.compute()
                    logger.info(
                        f"[METRICS] tick={self._tick}  "
                        f"efficiency={metrics['operational_efficiency_pct']:.1f}%  "
                        f"avg_temp={metrics['avg_temperature']:.1f}°C  "
                        f"anomalies={metrics['active_anomalies']}  "
                        f"critical={metrics['critical_machines']}  "
                        f"offline={metrics['offline_machines']}"
                    )

                # --- Write heartbeat --- #
                try:
                    with open("logs/simulator.heartbeat", "w") as hb:
                        hb.write(str(time.time()))
                except Exception:
                    pass

                # --- Pace the loop to honour the interval --- #
                elapsed = time.monotonic() - tick_start
                sleep_time = max(0, TELEMETRY_INTERVAL_SECONDS - elapsed)
                await asyncio.sleep(sleep_time)
        except asyncio.CancelledError:
            logger.info("[SHUTDOWN] Streaming loop cancelled.")
        finally:
            self._is_running = False
            
            # Wait for pending transport tasks to complete
            if self._transport_tasks:
                logger.info(f"[SHUTDOWN] Waiting for {len(self._transport_tasks)} pending transport tasks...")
                await asyncio.gather(*self._transport_tasks, return_exceptions=True)
                self._transport_tasks.clear()

            if self._kinesis_client:
                logger.info("[SHUTDOWN] Closing Kinesis transport client...")
                await self._kinesis_client.close()

            if self._api_client:
                logger.info("[SHUTDOWN] Closing FastAPI transport client...")
                await self._api_client.close()
            logger.info("[SHUTDOWN] Telemetry Streaming Engine cleanup complete.")

    def stop(self) -> None:
        """Signal the streaming loop to exit."""
        self._is_running = False
        logger.info("[STREAM] Telemetry Streaming Engine stop signal received")

    # ------------------------------------------------------------------
    # Metrics accessor (for external consumers)
    # ------------------------------------------------------------------
    def get_latest_metrics(self) -> Dict[str, Any]:
        """Return the most recent factory-wide metrics snapshot."""
        return self._metrics.compute()
