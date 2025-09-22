import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from src.services.cast_service import CastService
from src.config.settings import Settings
import pychromecast
import zeroconf
from tests.helpers import create_mock_cast_info, create_mock_chromecast
import httpx

@pytest.fixture(autouse=True)
def mock_discord_handler_httpx_client(mocker):
    mocker.patch("src.utils.discord_handler.httpx.Client")

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

@pytest.mark.asyncio
async def test_cast_service_host_ip(settings, mocker):
    # Test when settings.HOST is 0.0.0.0
    settings.HOST = "0.0.0.0"
    mock_get_local_ip = mocker.patch("src.services.cast_service.get_local_ip", return_value="192.168.1.1")
    cast_service = CastService(settings)
    assert cast_service.host_ip == "192.168.1.1"
    mock_get_local_ip.assert_called_once()

    # Test when settings.HOST is a specific IP
    settings.HOST = "192.168.1.100"
    mock_get_local_ip.reset_mock()
    cast_service = CastService(settings)
    assert cast_service.host_ip == "192.168.1.100"
    mock_get_local_ip.assert_not_called()

@pytest.mark.asyncio
async def test_cast_service_play_audio_stop_media(cast_service, mocker):
    mock_chromecast = create_mock_chromecast("Test Device", "test-uuid")
    mock_media_controller = MagicMock()
    mock_media_controller.status = MagicMock()
    mock_media_controller.status.player_is_playing = True
    mock_media_controller.status.player_is_paused = False
    mock_media_controller.stop = MagicMock()
    mock_media_controller.play_media = MagicMock()
    mock_media_controller.block_until_active = MagicMock()
    mock_chromecast.media_controller = mock_media_controller

    cast_service.chromecast = mock_chromecast
    mocker.patch("asyncio.sleep", new_callable=AsyncMock)
    mocker.patch.object(cast_service, "discover_and_connect", new_callable=AsyncMock, return_value=True)

    audio_url = "http://example.com/audio.mp3"
    await cast_service.play_audio(audio_url, "Test Device")

    mock_media_controller.stop.assert_called_once()
    mock_media_controller.play_media.assert_called_once_with(audio_url, "audio/wav")
    mock_media_controller.block_until_active.assert_called_once()

@pytest.mark.asyncio
async def test_cast_service_discover_and_connect_exception(cast_service, mock_browser_and_listener, mock_zeroconf, mocker):
    mock_browser, mock_listener = mock_browser_and_listener
    mock_cast_info = create_mock_cast_info("Living Room Speaker", "uuid-123")
    mock_listener.devices = [mock_cast_info]

    mocker.patch("pychromecast.get_chromecast_from_cast_info", side_effect=Exception("Test exception"))
    mock_log_error = mocker.patch("src.utils.logger.log.error")

    connected = await cast_service.discover_and_connect("Living Room Speaker")

    assert connected is False
    mock_log_error.assert_called_once()
    assert "An error occurred during device discovery" in mock_log_error.call_args[0][0]

@pytest.fixture
def tts_service(settings):
    from src.services.tts_service import TTSService
    return TTSService(settings)

@pytest.mark.asyncio
async def test_tts_service_generate_audio_http_error(tts_service, mocker):
    mock_deepgram_speak_rest_v = MagicMock()
    mock_deepgram_speak_rest_v.save = AsyncMock()
    mocker.patch("src.services.tts_service.asyncio.to_thread", side_effect=httpx.HTTPStatusError("Test HTTP Error", request=httpx.Request("POST", "url"), response=httpx.Response(400)))
    mocker.patch.object(tts_service.deepgram.speak.rest, "v", return_value=mock_deepgram_speak_rest_v)
    mock_log_error = mocker.patch.object(tts_service.log, "error")
    mocker.patch("src.utils.discord_handler.DiscordHandler.emit")

    tts_request = MagicMock()
    tts_request.text = "Test text"
    tts_request.voice = "test-voice"

    with pytest.raises(httpx.HTTPStatusError):
        await tts_service.generate_audio(tts_request)

    mock_log_error.assert_called_once()
    assert "Deepgram API error" in mock_log_error.call_args[0][0]

@pytest.mark.asyncio
async def test_tts_service_generate_audio_general_exception(tts_service, mocker):
    mock_deepgram_speak_rest_v = MagicMock()
    mock_deepgram_speak_rest_v.save = AsyncMock()
    mocker.patch("src.services.tts_service.asyncio.to_thread", side_effect=Exception("General error"))
    mocker.patch.object(tts_service.deepgram.speak.rest, "v", return_value=mock_deepgram_speak_rest_v)
    mock_log_error = mocker.patch.object(tts_service.log, "error")
    mocker.patch("src.utils.discord_handler.DiscordHandler.emit")

    tts_request = MagicMock()
    tts_request.text = "Test text"
    tts_request.voice = "test-voice"

    with pytest.raises(Exception, match="General error"):
        await tts_service.generate_audio(tts_request)

    mock_log_error.assert_called_once()
    assert "Error generating audio" in mock_log_error.call_args[0][0]

