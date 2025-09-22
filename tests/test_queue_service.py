import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from src.services.queue_service import QueueService
from src.services.tts_service import TTSService
from src.services.cast_service import CastService

@pytest.fixture(autouse=True)
def mock_discord_handler_httpx_client(mocker):
    mocker.patch("src.utils.discord_handler.httpx.Client")

@pytest.fixture
def mock_tts_service():
    return AsyncMock(spec=TTSService)

@pytest.fixture
def mock_cast_service():
    return AsyncMock(spec=CastService)

@pytest.fixture
def queue_service(mock_tts_service, mock_cast_service, mocker):
    mock_settings = MagicMock()
    return QueueService(mock_tts_service, mock_cast_service, mock_settings)

@pytest.mark.asyncio
async def test_add_to_queue(queue_service, mock_tts_service, mock_cast_service, mocker):
    tts_request = MagicMock()
    tts_request.device_name = "Test Device"
    task = {
        "tts_request": tts_request,
        "port": 8080,
    }
    queue_service.add_to_queue(task)

    assert len(queue_service.queue) == 1
    assert queue_service.queue[0][1] == task

    # Allow the task to run and complete
    await asyncio.sleep(0.1)

    mock_tts_service.generate_audio.assert_called_once_with(tts_request)
    mock_cast_service.play_audio.assert_called_once() # We can't assert the exact URL here without more mocking
    assert len(queue_service.queue) == 0
    assert queue_service.processing is False

@pytest.mark.asyncio
async def test_process_queue_empty(queue_service):
    queue_service.processing = True # Simulate it being set by add_to_queue
    await queue_service._process_queue()
    assert queue_service.processing is False

@pytest.mark.asyncio
async def test_process_queue_multiple_items(queue_service, mock_tts_service, mock_cast_service, mocker):
    tts_request1 = MagicMock()
    tts_request1.device_name = "Device 1"
    task1 = {"tts_request": tts_request1, "port": 8080}

    tts_request2 = MagicMock()
    tts_request2.device_name = "Device 2"
    task2 = {"tts_request": tts_request2, "port": 8080}

    queue_service.add_to_queue(task1)
    queue_service.add_to_queue(task2)

    # Allow tasks to process
    await asyncio.sleep(0.1)

    mock_tts_service.generate_audio.assert_any_call(tts_request1)
    mock_tts_service.generate_audio.assert_any_call(tts_request2)
    assert mock_tts_service.generate_audio.call_count == 2

    mock_cast_service.play_audio.assert_any_call(mocker.ANY, tts_request1.device_name)
    mock_cast_service.play_audio.assert_any_call(mocker.ANY, tts_request2.device_name)
    assert mock_cast_service.play_audio.call_count == 2
    assert len(queue_service.queue) == 0
    assert queue_service.processing is False

@pytest.mark.asyncio
async def test_process_queue_exception_handling(queue_service, mock_tts_service, mock_cast_service, mocker):
    tts_request = MagicMock()
    tts_request.device_name = "Test Device"
    task = {"tts_request": tts_request, "port": 8080}

    mock_tts_service.generate_audio.side_effect = Exception("TTS error")

    queue_service.processing = False # Ensure clean state

    queue_service.add_to_queue(task)

    await asyncio.sleep(0.5) # Allow task to process

    mock_tts_service.generate_audio.assert_called_once_with(tts_request)
    mock_cast_service.play_audio.assert_not_called() # play_audio should not be called if TTS fails
    assert len(queue_service.queue) == 0
    assert queue_service.processing is False

@pytest.mark.asyncio
async def test_add_to_queue_already_processing(queue_service, mock_tts_service, mock_cast_service, mocker):
    tts_request1 = MagicMock()
    tts_request1.device_name = "Device 1"
    task1 = {"tts_request": tts_request1, "port": 8080}

    tts_request2 = MagicMock()
    tts_request2.device_name = "Device 2"
    task2 = {"tts_request": tts_request2, "port": 8080}

    # Manually set processing to True to simulate ongoing processing
    queue_service.processing = True

    queue_service.add_to_queue(task1)
    queue_service.add_to_queue(task2)

    assert len(queue_service.queue) == 2
    # generate_audio and play_audio should not be called immediately if processing is True
    mock_tts_service.generate_audio.assert_not_called()
    mock_cast_service.play_audio.assert_not_called()

    # Simulate processing finishing, which should trigger the queue processing
    queue_service.processing = False
    await queue_service._process_queue()

    mock_tts_service.generate_audio.assert_any_call(tts_request1)
    mock_tts_service.generate_audio.assert_any_call(tts_request2)
    assert mock_tts_service.generate_audio.call_count == 2

    mock_cast_service.play_audio.assert_any_call(mocker.ANY, tts_request1.device_name)
    mock_cast_service.play_audio.assert_any_call(mocker.ANY, tts_request2.device_name)
    assert mock_cast_service.play_audio.call_count == 2
    assert len(queue_service.queue) == 0
    assert queue_service.processing is False