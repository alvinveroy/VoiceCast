import pytest
from fastapi.testclient import TestClient
from src.api.app import create_app
from src.config.settings import Settings
from unittest.mock import patch, AsyncMock
import os
import signal

@pytest.fixture
def settings():
    return Settings(API_KEY="test_api_key", DEEPGRAM_API_KEY="test_deepgram_key")

@pytest.fixture
def client(mocker, settings):
    mock_device_registry_class = mocker.patch("src.api.app.DeviceRegistry")
    mock_cast_service_class = mocker.patch("src.api.app.CastService")

    mock_device_registry_instance = mock_device_registry_class.return_value
    mock_device_registry_instance.discover_devices = AsyncMock()
    mock_device_registry_instance.close = AsyncMock()

    mock_cast_service_instance = mock_cast_service_class.return_value
    mock_cast_service_instance.close = AsyncMock()

    mocker.patch("src.api.app.watchdog_loop", new_callable=AsyncMock) # Patch the watchdog loop

    app = create_app(settings, skip_logging=True)
    with TestClient(app) as c:
        yield c

def test_stop_daemon_success(client):
    with patch("os.kill") as mock_kill:
        response = client.get("/api/v1/admin/stop", headers={"X-API-Key": "test_api_key"})
        assert response.status_code == 200
        assert response.json() == {"message": "Server is shutting down."}
        mock_kill.assert_called_once_with(os.getpid(), signal.SIGINT)

def test_stop_daemon_unauthorized(client):
    response = client.get("/api/v1/admin/stop", headers={"X-API-Key": "wrong_api_key"})
    assert response.status_code == 403
    assert response.json() == {"detail": "Could not validate credentials"}

def test_stop_daemon_no_api_key(client):
    response = client.get("/api/v1/admin/stop")
    assert response.status_code == 403
    assert response.json() == {"detail": "Could not validate credentials"}