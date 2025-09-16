import pytest
from fastapi.testclient import TestClient
from src.api.app import create_app
from src.config.settings import Settings
from unittest.mock import AsyncMock
import httpx
from src.utils.network_utils import get_local_ip

@pytest.fixture
def settings():
    return Settings(DEEPGRAM_API_KEY="test", GOOGLE_CAST_DEVICE_NAME="Test Device", API_KEY="test_api_key")

@pytest.fixture
def client(mocker, settings):
    # Mock DeviceRegistry and CastService classes before app creation
    mock_device_registry_class = mocker.patch("src.api.app.DeviceRegistry")
    mock_cast_service_class = mocker.patch("src.api.app.CastService")

    # Create instances of the mocks
    mock_device_registry_instance = mock_device_registry_class.return_value
    mock_cast_service_instance = mock_cast_service_class.return_value

    # Configure the mock instances
    mock_device_registry_instance.discover_devices = AsyncMock()
    mock_device_registry_instance.close = AsyncMock()
    mock_device_registry_instance.get_devices.return_value = {"generation": 1, "devices": []}
    mock_device_registry_instance.get_device_by_name.return_value = {
        "uuid": "mock_uuid",
        "friendly_name": "Living Room Speaker",
        "host": "192.168.1.100",
        "port": 8009,
        "cast_type": "audio",
        "last_seen": 1234567890,
    }

    mock_cast_service_instance.host_ip = get_local_ip()
    mock_cast_service_instance.discover_and_connect = AsyncMock(return_value=True)
    mock_cast_service_instance.play_audio = AsyncMock(return_value=None)
    mock_cast_service_instance.close = AsyncMock()

    app = create_app(settings, skip_logging=True)

    with TestClient(app) as c:
        yield c, mock_cast_service_instance, mock_device_registry_instance

def test_read_main(client):
    client_instance, _, _ = client
    response = client_instance.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy", "services": {"deepgram": "ok", "cast": "ok"}}

@pytest.mark.asyncio
async def test_tts_endpoint(client, mocker):
    client_instance, mock_cast_service_instance, mock_device_registry_instance = client
    response = client_instance.post(
        "/api/v1/tts",
        headers={"X-API-Key": "test_api_key"},
        json={
            "text": "Hello, world!",
            "voice": "aura-2-helena-en",
            "device_name": "Living Room Speaker"
        }
    )

    assert response.status_code == 200
    response_json = response.json()
    assert response_json["message"] == "TTS request added to queue"
    assert "task_id" in response_json
    assert isinstance(response_json["task_id"], str)
    mock_device_registry_instance.get_device_by_name.assert_called_with("Living Room Speaker")

@pytest.mark.asyncio
async def test_tts_endpoint_with_device_name(client, mocker):
    client_instance, mock_cast_service_instance, mock_device_registry_instance = client
    response = client_instance.post(
        "/api/v1/tts",
        headers={"X-API-Key": "test_api_key"},
        json={
            "text": "Hello, world!",
            "voice": "aura-2-helena-en",
            "device_name": "Living Room Speaker"
        }
    )

    assert response.status_code == 200
    response_json = response.json()
    assert response_json["message"] == "TTS request added to queue"
    assert "task_id" in response_json
    assert isinstance(response_json["task_id"], str)
    mock_device_registry_instance.get_device_by_name.assert_called_with("Living Room Speaker")

@pytest.mark.asyncio
async def test_tts_endpoint_deepgram_401_error(client, mocker):
    client_instance, _, mock_device_registry_instance = client
    mocker.patch("src.services.tts_service.TTSService.generate_audio", side_effect=httpx.HTTPStatusError("Invalid credentials", request=httpx.Request("POST", "url"), response=httpx.Response(401)))

    response = client_instance.post(
        "/api/v1/tts",
        headers={"X-API-Key": "test_api_key"},
        json={
            "text": "Hello, world!",
            "voice": "aura-2-helena-en",
            "device_name": "Living Room Speaker"
        }
    )

    assert response.status_code == 200
    response_json = response.json()
    assert response_json["message"] == "TTS request added to queue"
    assert "task_id" in response_json
    assert isinstance(response_json["task_id"], str)
    mock_device_registry_instance.get_device_by_name.assert_called_with("Living Room Speaker")

@pytest.mark.asyncio
async def test_tts_endpoint_deepgram_other_http_error(client, mocker):
    client_instance, _, mock_device_registry_instance = client
    mocker.patch("src.services.tts_service.TTSService.generate_audio", side_effect=httpx.HTTPStatusError("Internal Server Error", request=httpx.Request("POST", "url"), response=httpx.Response(500)))

    response = client_instance.post(
        "/api/v1/tts",
        headers={"X-API-Key": "test_api_key"},
        json={
            "text": "Hello, world!",
            "voice": "aura-2-helena-en",
            "device_name": "Living Room Speaker"
        }
    )

    assert response.status_code == 200
    response_json = response.json()
    assert response_json["message"] == "TTS request added to queue"
    assert "task_id" in response_json
    assert isinstance(response_json["task_id"], str)
    mock_device_registry_instance.get_device_by_name.assert_called_with("Living Room Speaker")

@pytest.mark.asyncio
async def test_tts_endpoint_device_not_found(client, mocker):
    client_instance, _, mock_device_registry_instance = client
    mock_device_registry_instance.get_device_by_name.return_value = None

    response = client_instance.post(
        "/api/v1/tts",
        headers={"X-API-Key": "test_api_key"},
        json={
            "text": "Hello, world!",
            "voice": "aura-2-helena-en",
            "device_name": "Unknown Device"
        }
    )

    assert response.status_code == 404
    assert response.json() == {"detail": {"error": "No device available with the given device name"}}
    mock_device_registry_instance.get_device_by_name.assert_called_with("Unknown Device")

@pytest.mark.asyncio
async def test_tts_endpoint_general_exception(client, mocker):
    client_instance, _, mock_device_registry_instance = client
    mocker.patch("src.services.tts_service.TTSService.generate_audio", side_effect=Exception("Something went wrong"))

    response = client_instance.post(
        "/api/v1/tts",
        headers={"X-API-Key": "test_api_key"},
        json={
            "text": "Hello, world!",
            "voice": "aura-2-helena-en",
            "device_name": "Living Room Speaker"
        }
    )

    assert response.status_code == 200
    response_json = response.json()
    assert response_json["message"] == "TTS request added to queue"
    assert "task_id" in response_json
    assert isinstance(response_json["task_id"], str)
    mock_device_registry_instance.get_device_by_name.assert_called_with("Living Room Speaker")

@pytest.mark.asyncio
async def test_tts_endpoint_no_voice(client, mocker, settings):
    client_instance, _, _ = client
    mock_add_to_queue = mocker.patch("src.services.queue_service.QueueService.add_to_queue", return_value="mock_task_id")

    response = client_instance.post(
        "/api/v1/tts",
        headers={"X-API-Key": "test_api_key"},
        json={
            "text": "Hello, world!",
            "device_name": "Living Room Speaker"
        }
    )

    assert response.status_code == 200
    response_json = response.json()
    assert response_json["message"] == "TTS request added to queue"
    assert response_json["task_id"] == "mock_task_id"

    mock_add_to_queue.assert_called_once()
    call_args = mock_add_to_queue.call_args[0][0]
    assert call_args['tts_request'].voice == settings.DEEPGRAM_MODEL
