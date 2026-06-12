import asyncio
import sys
import os

# Add the project root to python path to allow direct execution
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import signal
from simulator.factory.factory_simulator import FactorySimulator
from simulator.utils.logger import setup_logger

logger = setup_logger("Main")

async def main(simulator: FactorySimulator):
    loop = asyncio.get_running_loop()

    # Handle signals for graceful shutdown
    def signal_handler():
        logger.info(f"Received shutdown signal...")
        # Cancel the main simulator task to trigger the cleanup flow
        for task in asyncio.all_tasks(loop):
            task.cancel()

    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, signal_handler)
        except NotImplementedError:
            # Signal handlers are not implemented on Windows for some signals in asyncio
            pass

    try:
        await simulator.start()
    except asyncio.CancelledError:
        logger.info("Main loop cancelled.")
    finally:
        await simulator.shutdown()

if __name__ == "__main__":
    simulator = FactorySimulator()
    try:
        asyncio.run(main(simulator))
    except KeyboardInterrupt:
        # On Windows, KeyboardInterrupt is the main way to stop.
        # asyncio.run will have already cancelled tasks, but we want 
        # to ensure the simulator's explicit shutdown logic runs.
        logger.info("KeyboardInterrupt received, cleaning up...")
        asyncio.run(simulator.shutdown())
