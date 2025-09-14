import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from fastapi.testclient import TestClient
from src.api.app import create_app
from src.config.settings import Settings

@pytest.fixture
def settings():
    return Settings(DEEPGRAM_API_KEY="test", GOOGLE_CAST_DEVICE_NAME="Test Device", API_KEY="test_api_key")

@pytest.fixture
def client(mocker, settings):
    # Mock DeviceRegistry and CastService classes before app creation
    mock_device_registry_class = mocker.patch("src.api.app.DeviceRegistry")
    mock_cast_service_class = mocker.patch("src.api.app.CastService")

    mock_device_registry_instance = mock_device_registry_class.return_value
    mock_device_registry_instance.discover_devices = AsyncMock()
    mock_device_registry_instance.close = AsyncMock()
    mock_device_registry_instance.get_devices.return_value = {"generation": 1, "devices": []}
    mock_device_registry_instance.refresh_devices = AsyncMock()

    mock_cast_service_instance = mock_cast_service_class.return_value
    mock_cast_service_instance.close = AsyncMock()

    app = create_app(settings, skip_logging=True)
    with TestClient(app) as c:
        yield c, mock_device_registry_instance

def test_get_devices_unauthorized(client):
    client_instance, _ = client
    response = client_instance.get("/api/v1/devices")
    assert response.status_code == 403

def test_get_devices_authorized(client):
    client_instance, _ = client
    with patch('src.api.security.get_api_key', return_value="test_api_key"):
        response = client_instance.get("/api/v1/devices", headers={"X-API-Key": "test_api_key"})
        assert response.status_code == 200
        assert "devices" in response.json()

def test_refresh_devices_unauthorized(client):
    client_instance, _ = client
    response = client_instance.get("/api/v1/devices/refresh")
    assert response.status_code == 403

def test_refresh_devices_authorized(client):
    client_instance, mock_device_registry_instance = client
    with patch('src.api.security.get_api_key', return_value="test_api_key"):
        response = client_instance.get("/api/v1/devices/refresh", headers={"X-API-Key": "test_api_key"})
        assert response.status_code == 200
        assert response.json() == {"message": "Device discovery refresh triggered."}
        mock_device_registry_instance.refresh_devices.assert_called_once()
