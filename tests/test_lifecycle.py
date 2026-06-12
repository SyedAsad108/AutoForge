import asyncio
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from simulator.factory.factory_simulator import FactorySimulator
from simulator.streaming.streaming_engine import TelemetryStreamingEngine
from simulator.streaming.stream_manager import StreamManager
from simulator.streaming.event_queue import EventQueue

@pytest.mark.asyncio
async def test_factory_simulator_shutdown():
    """Verify FactorySimulator shutdown cancels tasks and waits for them."""
    simulator = FactorySimulator()
    
    # Mock engines
    mock_engine = AsyncMock()
    mock_manager = AsyncMock()
    
    simulator._streaming_engine = mock_engine
    simulator._stream_manager = mock_manager
    
    # Simulate running
    simulator.is_running = True
    
    # Add a dummy task
    task = asyncio.create_task(asyncio.sleep(10))
    simulator._background_tasks.add(task)
    
    await simulator.shutdown()
    
    assert simulator.is_running is False
    assert task.cancelled()
    assert len(simulator._background_tasks) == 0
    mock_engine.stop.assert_called_once()
    mock_manager.stop.assert_called_once()

@pytest.mark.asyncio
async def test_streaming_engine_cancellation():
    """Verify TelemetryStreamingEngine handles cancellation and closes client."""
    mock_client = AsyncMock()
    engine = TelemetryStreamingEngine(machines=[], event_queue=EventQueue())
    engine._api_client = mock_client
    
    # Run in a task and cancel it
    task = asyncio.create_task(engine.start())
    await asyncio.sleep(0.1)
    task.cancel()
    
    try:
        await task
    except asyncio.CancelledError:
        pass
        
    assert engine._is_running is False
    mock_client.close.assert_called_once()

@pytest.mark.asyncio
async def test_stream_manager_drain_on_shutdown():
    """Verify StreamManager drains the queue on shutdown."""
    queue = EventQueue()
    await queue.put({"event_id": "1"})
    await queue.put({"event_id": "2"})
    
    manager = StreamManager(event_queue=queue)
    manager._persist = MagicMock()
    
    # Start and immediately cancel
    task = asyncio.create_task(manager.start())
    await asyncio.sleep(0.1)
    task.cancel()
    
    try:
        await task
    except asyncio.CancelledError:
        pass
        
    # Check if persist was called for both events
    assert manager._persist.call_count == 2
    assert queue.size == 0

@pytest.mark.asyncio
async def test_backend_drain_on_shutdown():
    """Verify backend drain loop drains the queue on shutdown."""
    from backend.ingestion.buffering_engine import BufferingEngine
    
    mock_producer = AsyncMock()
    mock_producer.publish_batch.return_value = 2
    
    engine = BufferingEngine(producer=mock_producer)
    await engine.enqueue({"id": 1})
    await engine.enqueue({"id": 2})
    
    # Start and stop
    task = asyncio.create_task(engine.start_drain_loop())
    await asyncio.sleep(0.1)
    engine.stop()
    await task
    
    assert mock_producer.publish_batch.called
    assert engine.depth == 0
