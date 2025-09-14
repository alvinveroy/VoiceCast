import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from src.services.cast_service import CastService
from src.config.settings import Settings
import pychromecast
import zeroconf
from tests.helpers import create_mock_cast_info, create_mock_chromecast

@pytest.fixture(autouse=True)
def reset_singletons():
    from src.utils import singleton
    singleton._zeroconf_instance = None
    singleton._cast_browser = None
    singleton._cast_listener = None

@pytest.fixture
def settings():
    return Settings(DEEPGRAM_API_KEY="test", GOOGLE_CAST_DEVICE_NAME="Test Device", CAST_DISCOVERY_TIMEOUT=0.1)

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

@pytest.fixture
def cast_service(settings, mock_browser_and_listener, mock_zeroconf):
    return CastService(settings)

@pytest.mark.asyncio
async def test_cast_service_discover_and_connect(cast_service, mock_browser_and_listener, mock_zeroconf):
    mock_browser, mock_listener = mock_browser_and_listener
    mock_cast_info = create_mock_cast_info("Living Room Speaker", "uuid-123")
    mock_chromecast = create_mock_chromecast("Living Room Speaker", "uuid-123")

    mock_listener.devices = [mock_cast_info]

    with patch("pychromecast.get_chromecast_from_cast_info", return_value=mock_chromecast) as mock_get_chromecast:
        connected = await cast_service.discover_and_connect("Living Room Speaker")

        assert connected is True
        assert cast_service.chromecast is not None
        assert cast_service.chromecast.name == "Living Room Speaker"
        mock_get_chromecast.assert_called_once_with(mock_cast_info, mock_zeroconf)
        mock_chromecast.wait.assert_called_once()
        mock_browser.start_discovery.assert_called_once()

@pytest.mark.asyncio
async def test_cast_service_play_audio(cast_service, mocker):
    mock_chromecast = create_mock_chromecast("Test Device", "test-uuid")
    cast_service.chromecast = mock_chromecast
    cast_service.chromecast.is_idle = True

    mocker.patch("asyncio.sleep", new_callable=AsyncMock)

    audio_url = "http://example.com/audio.mp3"
    await cast_service.play_audio(audio_url, "Test Device")

    mock_chromecast.media_controller.play_media.assert_called_once_with(audio_url, "audio/wav")
    mock_chromecast.media_controller.block_until_active.assert_called_once()

@pytest.mark.asyncio
async def test_cast_service_play_audio_no_device_name(cast_service, mocker):
    mock_chromecast = create_mock_chromecast("Bedroom speaker", "test-uuid")
    cast_service.chromecast = mock_chromecast
    cast_service.chromecast.is_idle = True

    mocker.patch("asyncio.sleep", new_callable=AsyncMock)

    audio_url = "http://example.com/audio.com/audio.mp3"
    await cast_service.play_audio(audio_url)

    cast_service.chromecast.media_controller.play_media.assert_called_once_with(audio_url, "audio/wav")

@pytest.mark.asyncio
async def test_cast_service_play_audio_device_not_found(cast_service, mocker):
    mocker.patch.object(cast_service, "discover_and_connect", new_callable=AsyncMock, return_value=False)

    audio_url = "http://example.com/audio.mp3"
    await cast_service.play_audio(audio_url, "Non Existent Device")

    cast_service.discover_and_connect.assert_called_once_with("Non Existent Device")
    assert cast_service.chromecast is None or not cast_service.chromecast.media_controller.play_media.called

@pytest.mark.asyncio
async def test_cast_service_play_audio_connection_error(cast_service, mocker):
    mocker.patch.object(
        cast_service,
        "discover_and_connect",
        new_callable=AsyncMock,
        side_effect=pychromecast.error.ChromecastConnectionError("Connection failed")
    )

    audio_url = "http://example.com/audio.mp3"
    with pytest.raises(pychromecast.error.ChromecastConnectionError, match="Connection failed"):
        await cast_service.play_audio(audio_url, "Test Device")

    cast_service.discover_and_connect.assert_called_once_with("Test Device")
