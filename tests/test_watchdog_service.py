import asyncio
import httpx
import pytest
from unittest.mock import AsyncMock, MagicMock, ANY
from src.services.watchdog_service import (
    send_discord_notification,
    check_internet_connection,
    watchdog_loop,
)
from src.config.settings import Settings
import src.services.watchdog_service

@pytest.fixture
def settings():
    return Settings(
        DISCORD_WEBHOOK_URL="https://discord.com/api/webhooks/123/abc",
        WATCHDOG_INTERVAL=1,
        CHROMECAST_DISCOVERY_INTERVAL=1,
        CHROMECAST_REFRESH_INTERVAL=1,
    )

@pytest.mark.asyncio
async def test_send_discord_notification(mocker, settings):
    mock_settings_instance = MagicMock(spec=Settings)
    mock_settings_instance.DISCORD_WEBHOOK_URL = settings.DISCORD_WEBHOOK_URL
    mocker.patch("src.services.watchdog_service.settings", new=mock_settings_instance)

    mock_post = mocker.patch("httpx.post", new_callable=AsyncMock)
    mock_post.return_value = MagicMock()
    mock_post.return_value.raise_for_status = lambda: None

    await send_discord_notification("test message")

    mock_post.assert_awaited_once_with(
        settings.DISCORD_WEBHOOK_URL, json={"content": "test message"}
    )

@pytest.mark.asyncio
async def test_send_discord_notification_no_webhook_url(mocker, settings):
    mock_settings_instance = MagicMock(spec=Settings)
    mock_settings_instance.DISCORD_WEBHOOK_URL = None
    mocker.patch("src.services.watchdog_service.settings", new=mock_settings_instance)

    mock_post = mocker.patch("httpx.post", new_callable=AsyncMock)

    await send_discord_notification("test message")

    mock_post.assert_not_awaited()

@pytest.mark.asyncio
async def test_check_internet_connection_success(mocker):
    mock_get = mocker.patch("httpx.get", new_callable=AsyncMock)
    mock_get.return_value = MagicMock()
    mock_get.return_value.raise_for_status = lambda: None

    result = await check_internet_connection()

    assert result is True
    mock_get.assert_awaited_once_with("https://8.8.8.8")

@pytest.mark.asyncio
async def test_check_internet_connection_failure(mocker):
    mock_get = mocker.patch("httpx.get", new_callable=AsyncMock)
    mock_get.side_effect = httpx.RequestError("test error", request=httpx.Request("GET", "https://8.8.8.8"))

    result = await check_internet_connection()

    assert result is False

@pytest.mark.asyncio
async def test_send_discord_notification_request_error(mocker, settings):
    mock_settings_instance = MagicMock(spec=Settings)
    mock_settings_instance.DISCORD_WEBHOOK_URL = settings.DISCORD_WEBHOOK_URL
    mocker.patch("src.services.watchdog_service.settings", new=mock_settings_instance)

    mock_post = mocker.patch("httpx.post", new_callable=AsyncMock)
    mock_post.side_effect = httpx.RequestError("Test request error", request=httpx.Request("POST", settings.DISCORD_WEBHOOK_URL))
    mock_log_error = mocker.patch("src.utils.logger.log.error")

    await send_discord_notification("test message")

    mock_post.assert_awaited_once()
    mock_log_error.assert_called_once()
    assert "Failed to send Discord notification." in mock_log_error.call_args[0][0]

@pytest.mark.asyncio
async def test_watchdog_loop(mocker, settings):
    mock_settings_instance = MagicMock(spec=Settings)
    mock_settings_instance.CHROMECAST_DISCOVERY_INTERVAL = settings.CHROMECAST_DISCOVERY_INTERVAL
    mock_settings_instance.CHROMECAST_REFRESH_INTERVAL = settings.CHROMECAST_REFRESH_INTERVAL
    mock_settings_instance.WATCHDOG_INTERVAL = settings.WATCHDOG_INTERVAL
    mock_settings_instance.DISCORD_WEBHOOK_URL = settings.DISCORD_WEBHOOK_URL
    mocker.patch("src.services.watchdog_service.settings", new=mock_settings_instance)

    mocker.patch("asyncio.sleep", side_effect=asyncio.TimeoutError)
    mocker.patch("src.services.watchdog_service.check_internet_connection", new_callable=AsyncMock)
    mocker.patch("src.services.watchdog_service.send_discord_notification", new_callable=AsyncMock)

    mock_device_registry = MagicMock()
    mock_device_registry.get_all_devices.return_value = []
    mock_device_registry.discover_devices = AsyncMock()
    mock_device_registry.refresh_devices = AsyncMock()

    with pytest.raises(asyncio.TimeoutError):
        await watchdog_loop(mock_device_registry)

    # Assert that the functions were called
    src.services.watchdog_service.check_internet_connection.assert_called()
    src.services.watchdog_service.send_discord_notification.assert_called()
    mock_device_registry.get_all_devices.assert_called()
    mock_device_registry.discover_devices.assert_called()

@pytest.mark.asyncio
async def test_watchdog_loop_refreshes_devices(mocker, settings):
    mock_settings_instance = MagicMock(spec=Settings)
    mock_settings_instance.CHROMECAST_REFRESH_INTERVAL = settings.CHROMECAST_REFRESH_INTERVAL
    mock_settings_instance.WATCHDOG_INTERVAL = settings.WATCHDOG_INTERVAL
    mock_settings_instance.CHROMECAST_DISCOVERY_INTERVAL = settings.CHROMECAST_DISCOVERY_INTERVAL
    mock_settings_instance.DISCORD_WEBHOOK_URL = settings.DISCORD_WEBHOOK_URL
    mocker.patch("src.services.watchdog_service.settings", new=mock_settings_instance)

    mocker.patch("asyncio.sleep", side_effect=asyncio.TimeoutError)
    mocker.patch("src.services.watchdog_service.check_internet_connection", new_callable=AsyncMock)
    mocker.patch("src.services.watchdog_service.send_discord_notification", new_callable=AsyncMock)

    mock_device_registry = MagicMock()
    mock_device_registry.get_all_devices.return_value = [{"name": "test_device"}]
    mock_device_registry.refresh_devices = AsyncMock()
    
    with pytest.raises(asyncio.TimeoutError):
        await watchdog_loop(mock_device_registry)

    # Assert that the functions were called
    src.services.watchdog_service.check_internet_connection.assert_called()
    src.services.watchdog_service.send_discord_notification.assert_called()
    mock_device_registry.refresh_devices.assert_called()

@pytest.mark.asyncio
async def test_watchdog_loop_internet_down(mocker, settings):
    mock_settings_instance = MagicMock(spec=Settings)
    mock_settings_instance.WATCHDOG_INTERVAL = 0.01 # Small interval for quick test
    mock_settings_instance.DISCORD_WEBHOOK_URL = settings.DISCORD_WEBHOOK_URL
    mock_settings_instance.CHROMECAST_DISCOVERY_INTERVAL = settings.CHROMECAST_DISCOVERY_INTERVAL
    mock_settings_instance.CHROMECAST_REFRESH_INTERVAL = settings.CHROMECAST_REFRESH_INTERVAL
    mocker.patch("src.services.watchdog_service.settings", new=mock_settings_instance)

    mock_check_internet_connection = mocker.patch("src.services.watchdog_service.check_internet_connection", new_callable=AsyncMock, side_effect=[False, False])
    mock_send_discord_notification = mocker.patch("src.services.watchdog_service.send_discord_notification", new_callable=AsyncMock)
    mocker.patch("asyncio.sleep", new_callable=AsyncMock, side_effect=[None, asyncio.TimeoutError]) # Allow two iterations

    mock_device_registry = MagicMock()
    mock_device_registry.discover_devices = AsyncMock()
    mock_device_registry.refresh_devices = AsyncMock()

    with pytest.raises(asyncio.TimeoutError):
        await watchdog_loop(mock_device_registry)

    mock_check_internet_connection.assert_called()
    mock_send_discord_notification.assert_any_call("Internet connection is down.")

@pytest.mark.asyncio
async def test_watchdog_loop_internet_comes_back_up(mocker, settings):
    mock_settings_instance = MagicMock(spec=Settings)
    mock_settings_instance.WATCHDOG_INTERVAL = 0.01 # Small interval for quick test
    mock_settings_instance.DISCORD_WEBHOOK_URL = settings.DISCORD_WEBHOOK_URL
    mock_settings_instance.CHROMECAST_DISCOVERY_INTERVAL = settings.CHROMECAST_DISCOVERY_INTERVAL
    mock_settings_instance.CHROMECAST_REFRESH_INTERVAL = settings.CHROMECAST_REFRESH_INTERVAL
    mocker.patch("src.services.watchdog_service.settings", new=mock_settings_instance)

    mock_check_internet_connection = mocker.patch("src.services.watchdog_service.check_internet_connection", new_callable=AsyncMock, side_effect=[False, True])
    mock_send_discord_notification = mocker.patch("src.services.watchdog_service.send_discord_notification", new_callable=AsyncMock)
    mocker.patch("asyncio.sleep", new_callable=AsyncMock, side_effect=[None, asyncio.TimeoutError]) # Allow two iterations

    mock_device_registry = MagicMock()
    mock_device_registry.discover_devices = AsyncMock()
    mock_device_registry.refresh_devices = AsyncMock()

    with pytest.raises(asyncio.TimeoutError):
        await watchdog_loop(mock_device_registry)

    mock_check_internet_connection.assert_called()
    mock_send_discord_notification.assert_any_call("Internet connection is down.")
    mock_send_discord_notification.assert_any_call(ANY) # Check that it was called with some argument
    assert any("Internet connection is back online after" in call_args[0][0] for call_args in mock_send_discord_notification.call_args_list)