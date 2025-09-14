from unittest.mock import MagicMock

def create_mock_cast_info(friendly_name, uuid, host=None, port=None, cast_type=None):
    mock_ci = MagicMock()
    mock_ci.friendly_name = friendly_name
    mock_ci.uuid = uuid
    mock_ci.host = host
    mock_ci.port = port
    mock_ci.cast_type = cast_type
    return mock_ci

def create_mock_chromecast(name="Test Device", uuid="test-uuid"):
    mock_cc = MagicMock()
    mock_cc.name = name
    mock_cc.uuid = uuid
    mock_cc.is_idle = True
    mock_cc.wait = MagicMock()
    mock_cc.media_controller = MagicMock()
    mock_cc.media_controller.status = MagicMock()
    mock_cc.media_controller.status.player_is_playing = False
    mock_cc.media_controller.status.player_is_paused = False
    mock_cc.media_controller.play_media = MagicMock()
    mock_cc.media_controller.stop = MagicMock()
    mock_cc.media_controller.block_until_active = MagicMock()
    mock_cc.media_controller.block_until_status = MagicMock()
    return mock_cc
