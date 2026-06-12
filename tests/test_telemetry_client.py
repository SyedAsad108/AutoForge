import pytest
import asyncio
import httpx
from unittest.mock import patch, MagicMock, AsyncMock
from simulator.streaming.transport.telemetry_client import TelemetryAPIClient

@pytest.fixture
def sample_event():
    return {
        "event_id": "test-uuid",
        "machine_id": "M001",
        "machine_type": "conveyor_motor",
        "factory_id": "AUTOFORGE_01",
        "timestamp": "2023-10-25T10:00:00Z",
        "status": "healthy",
        "telemetry": {"temperature": 45.0},
        "anomaly_detected": False,
        "anomaly_type": None,
        "anomaly_severity": 0.0,
        "degradation_level": 0.0
    }

@pytest.mark.asyncio
async def test_successful_delivery(sample_event):
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        client = TelemetryAPIClient()
        success = await client.send_event(sample_event)
        
        assert success is True
        mock_post.assert_called_once()
        assert mock_post.call_args[1]["json"] == sample_event
        await client.close()

@pytest.mark.asyncio
async def test_batch_sending(sample_event):
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        client = TelemetryAPIClient()
        batch = [sample_event, sample_event]
        success = await client.send_batch(batch)
        
        assert success is True
        mock_post.assert_called_once()
        assert mock_post.call_args[1]["json"] == {"events": batch}
        await client.close()

@pytest.mark.asyncio
async def test_backend_unavailable(sample_event):
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        # Simulate connection error
        mock_post.side_effect = httpx.RequestError("Connection refused")
        
        client = TelemetryAPIClient()
        client.retries = 2 # Speed up test
        
        with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            success = await client.send_event(sample_event)
            
            assert success is False
            assert mock_post.call_count == 2
            mock_sleep.assert_called_once_with(1)
            
        await client.close()

@pytest.mark.asyncio
async def test_timeout_handling(sample_event):
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        # Simulate timeout error
        mock_post.side_effect = httpx.TimeoutException("Timeout")
        
        client = TelemetryAPIClient()
        client.retries = 1 # Speed up test
        
        success = await client.send_event(sample_event)
        
        assert success is False
        assert mock_post.call_count == 1
        await client.close()

@pytest.mark.asyncio
async def test_retry_behavior(sample_event):
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        # First attempt fails, second succeeds
        mock_response_fail = MagicMock()
        mock_response_fail.raise_for_status.side_effect = httpx.HTTPStatusError("500 Error", request=MagicMock(), response=MagicMock(status_code=500, text="Error"))
        
        mock_response_success = MagicMock()
        mock_response_success.raise_for_status.return_value = None
        
        mock_post.side_effect = [httpx.RequestError("Connection error"), mock_response_success]
        
        client = TelemetryAPIClient()
        client.retries = 2
        
        with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            success = await client.send_event(sample_event)
            
            assert success is True
            assert mock_post.call_count == 2
            mock_sleep.assert_called_once_with(1)
            
        await client.close()

@pytest.mark.asyncio
async def test_no_retry_on_400(sample_event):
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_response = MagicMock(status_code=400, text="Bad Request")
        mock_post.side_effect = httpx.HTTPStatusError("400 Bad Request", request=MagicMock(), response=mock_response)
        
        client = TelemetryAPIClient()
        client.retries = 3
        
        success = await client.send_event(sample_event)
        
        assert success is False
        assert mock_post.call_count == 1 # Should not retry on 4xx
        await client.close()
