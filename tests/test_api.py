import pytest
from fastapi.testclient import TestClient
from src.api.app import create_app
from src.config.settings import Settings
from unittest.mock import patch, AsyncMock, MagicMock
from src.api.security import get_api_key
from fastapi import Depends, HTTPException

@pytest.fixture
def settings():
    return Settings(DEEPGRAM_API_KEY="test", GOOGLE_CAST_DEVICE_NAME="Test Device", API_KEY="test_api_key")

@pytest.fixture
def client(mocker, settings):
    mock_device_registry_class = mocker.patch("src.api.app.DeviceRegistry")
    mock_cast_service_class = mocker.patch("src.api.app.CastService")

    mock_device_registry_instance = mock_device_registry_class.return_value
    mock_device_registry_instance.discover_devices = AsyncMock()
    mock_device_registry_instance.close = AsyncMock()

    mock_cast_service_instance = mock_cast_service_class.return_value
    mock_cast_service_instance.close = AsyncMock()

    app = create_app(settings, skip_logging=True)
    return TestClient(app)

def test_tts_endpoint_unauthorized(client):
    response = client.post("/api/v1/tts", json={"text": "Hello"}, headers={"X-API-Key": "wrong_key"})
    assert response.status_code == 403
    assert response.json() == {"detail": "Could not validate credentials"}

def test_tts_endpoint_no_api_key(client):
    response = client.post("/api/v1/tts", json={"text": "Hello"})
    assert response.status_code == 403
    assert response.json() == {"detail": "Could not validate credentials"}

@pytest.mark.asyncio
async def test_get_api_key_success():
    settings_mock = MagicMock(spec=Settings)
    settings_mock.API_KEY = "correct_api_key"
    
    result = await get_api_key(settings=settings_mock, api_key_header="correct_api_key")
    assert result == "correct_api_key"

@pytest.mark.asyncio
async def test_get_api_key_unauthorized():
    settings_mock = MagicMock(spec=Settings)
    settings_mock.API_KEY = "correct_api_key"
    
    with pytest.raises(HTTPException) as excinfo:
        await get_api_key(settings=settings_mock, api_key_header="wrong_api_key")
    assert excinfo.value.status_code == 403
    assert excinfo.value.detail == "Could not validate credentials"

@pytest.mark.asyncio
async def test_get_api_key_no_header():
    settings_mock = MagicMock(spec=Settings)
    settings_mock.API_KEY = "correct_api_key"
    
    with pytest.raises(HTTPException) as excinfo:
        await get_api_key(settings=settings_mock, api_key_header=None)
    assert excinfo.value.status_code == 403
    assert excinfo.value.detail == "Could not validate credentials"
