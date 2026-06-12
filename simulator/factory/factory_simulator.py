"""
Factory Simulator — the top-level orchestrator for the AutoForge plant.

Phase 1: instantiates all machines and runs a simple print-loop.
Phase 2: delegates telemetry generation to the ``TelemetryStreamingEngine``
          and routes events through ``EventQueue`` → ``StreamManager``
          for local persistence.
"""

import asyncio
from typing import List

from simulator.machines.base_machine import BaseMachine
from simulator.factory.machine_registry import MachineRegistry
from simulator.streaming.event_queue import EventQueue
from simulator.streaming.streaming_engine import TelemetryStreamingEngine
from simulator.streaming.stream_manager import StreamManager
from simulator.utils.constants import FACTORY_COMPOSITION
from simulator.utils.logger import setup_logger

logger = setup_logger("FactorySimulator")


class FactorySimulator:
    """
    Orchestrates the entire factory simulation.

    Instantiates all machines per ``FACTORY_COMPOSITION`` and wires up
    the Phase 2 streaming pipeline:
      Machine fleet → StreamingEngine → EventQueue → StreamManager → NDJSON
    """

    def __init__(self):
        self.machines: List[BaseMachine] = []
        self.is_running = False

        # Phase 2 components (created after machines are initialised)
        self._event_queue: EventQueue | None = None
        self._streaming_engine: TelemetryStreamingEngine | None = None
        self._stream_manager: StreamManager | None = None
        self._background_tasks: set[asyncio.Task] = set()

        self._initialize_factory()

    # ------------------------------------------------------------------
    # Factory bootstrap
    # ------------------------------------------------------------------
    def _initialize_factory(self) -> None:
        logger.info("Initializing Factory Simulator...")
        machine_counter = 1

        for machine_type, count in FACTORY_COMPOSITION.items():
            machine_class = MachineRegistry.get_machine_class(machine_type)
            for _ in range(count):
                machine_id = f"M{machine_counter:03d}"
                machine = machine_class(machine_id)
                self.machines.append(machine)
                machine_counter += 1

        logger.info(f"Initialized {len(self.machines)} machines.")

        # Wire up Phase 2 pipeline
        self._event_queue = EventQueue()
        self._streaming_engine = TelemetryStreamingEngine(
            machines=self.machines,
            event_queue=self._event_queue,
        )
        self._stream_manager = StreamManager(event_queue=self._event_queue)

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------
    async def start(self) -> None:
        """Start the factory simulation with the full Phase 2 pipeline."""
        logger.info("Starting Factory Simulation. Press Ctrl+C to stop.")
        self.is_running = True

        # Run streaming engine and stream manager as concurrent tasks
        engine_task = asyncio.create_task(self._streaming_engine.start())
        manager_task = asyncio.create_task(self._stream_manager.start())

        self._background_tasks.add(engine_task)
        self._background_tasks.add(manager_task)

        # Cleanup reference when done
        engine_task.add_done_callback(self._background_tasks.discard)
        manager_task.add_done_callback(self._background_tasks.discard)

        try:
            await asyncio.gather(engine_task, manager_task)
        except asyncio.CancelledError:
            logger.info("[SHUTDOWN] Simulation cancellation received.")
        finally:
            await self.shutdown()

    async def shutdown(self) -> None:
        """Stop the factory simulation and clean up resources gracefully."""
        if not self.is_running:
            return

        logger.info("[SHUTDOWN] Initializing graceful shutdown...")
        self.is_running = False

        # 1. Stop components (set flags)
        if self._streaming_engine:
            self._streaming_engine.stop()
        if self._stream_manager:
            self._stream_manager.stop()

        # 2. Cancel background tasks
        if self._background_tasks:
            logger.info(f"[SHUTDOWN] Cancelling {len(self._background_tasks)} background tasks...")
            for task in self._background_tasks:
                task.cancel()

            # Wait for tasks to terminate with a timeout
            from simulator.utils.constants import SHUTDOWN_GRACE_PERIOD_SECONDS
            await asyncio.gather(*self._background_tasks, return_exceptions=True)
            self._background_tasks.clear()

        logger.info("[SHUTDOWN] Simulator shutdown complete.")

    def stop(self) -> None:
        """Synchronous bridge to trigger shutdown (for legacy/signal compatibility)."""
        # Note: In a pure async world, we should await shutdown().
        # This is kept for the KeyboardInterrupt block in main.py.
        self.is_running = False

