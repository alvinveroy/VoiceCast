import pytest
from unittest.mock import MagicMock
from src.services.device_registry import DeviceRegistry
from src.config.settings import Settings
import zeroconf
from tests.helpers import create_mock_cast_info

@pytest.fixture(autouse=True)
def reset_singletons():
    from src.utils import singleton
    singleton._zeroconf_instance = None
    singleton._cast_browser = None
    singleton._cast_listener = None

@pytest.fixture
def mock_settings():
    settings = MagicMock(spec=Settings)
    settings.CAST_DISCOVERY_TIMEOUT = 0.1
    return settings

@pytest.fixture
def mock_browser_and_listener(mocker):
    mock_browser = MagicMock()
    mock_browser.is_discovering = False
    mock_listener = MagicMock()
    mock_listener.devices = []
    mocker.patch("src.utils.singleton.create_cast_browser", return_value=(mock_browser, mock_listener))
    return mock_browser, mock_listener

@pytest.fixture
def mock_zeroconf(mocker):
    mock_zconf = MagicMock(spec=zeroconf.Zeroconf)
    mocker.patch("zeroconf.Zeroconf", return_value=mock_zconf)
    return mock_zconf


@pytest.mark.asyncio
async def test_discover_devices(mock_settings, mock_browser_and_listener, mock_zeroconf):
    mock_browser, mock_listener = mock_browser_and_listener
    mock_cast_info1 = create_mock_cast_info("Test Device 1", "uuid1", "1.1.1.1", 8009, "audio")
    mock_cast_info2 = create_mock_cast_info("Test Device 2", "uuid2", "2.2.2.2", 8009, "video")

    mock_listener.devices = [mock_cast_info1, mock_cast_info2]

    registry = DeviceRegistry(mock_settings)
    await registry.discover_devices()

    devices = registry.get_devices()
    assert len(devices["devices"]) == 2
    assert devices["generation"] == 1

    device1 = registry.get_device_by_name("Test Device 1")
    assert device1["friendly_name"] == "Test Device 1"
    mock_browser.start_discovery.assert_called_once()

@pytest.mark.asyncio
async def test_refresh_devices(mock_settings, mock_browser_and_listener, mock_zeroconf):
    mock_browser, mock_listener = mock_browser_and_listener
    mock_cast_info1 = create_mock_cast_info("Test Device 1", "uuid1", "1.1.1.1", 8009, "audio")
    mock_cast_info2 = create_mock_cast_info("Test Device 2", "uuid2", "2.2.2.2", 8009, "video")
    mock_cast_info3 = create_mock_cast_info("Test Device 3", "uuid3", "3.3.3.3", 8009, "audio")

    registry = DeviceRegistry(mock_settings)

    # Initial discovery
    mock_listener.devices = [mock_cast_info1]
    await registry.discover_devices()
    assert len(registry.get_devices()["devices"]) == 1
    assert registry.get_devices()["generation"] == 1

    # Simulate new devices after refresh
    mock_listener.devices.clear()
    mock_listener.devices.extend([mock_cast_info1, mock_cast_info2, mock_cast_info3])

    await registry.refresh_devices()
    devices = registry.get_devices()
    assert len(devices["devices"]) == 3
    assert registry.get_devices()["generation"] == 2
    assert mock_browser.start_discovery.call_count == 2

@pytest.mark.asyncio
async def test_discover_devices_already_in_progress(mock_settings, mock_browser_and_listener, mock_zeroconf, mocker):
    registry = DeviceRegistry(mock_settings)
    mock_lock = mocker.patch.object(registry, "_discovery_lock")
    mock_lock.acquire.return_value = False
    mock_log_info = mocker.patch("src.services.device_registry.log.info")

    await registry.discover_devices()

    mock_lock.acquire.assert_called_once_with(blocking=False)
    mock_log_info.assert_called_once_with("Discovery is already in progress.")
    # Ensure no further discovery actions are taken
    mock_browser_and_listener[0].start_discovery.assert_not_called()






