import pytest
from src.utils.logger import setup_logging
from src.config.settings import Settings
from unittest.mock import patch, MagicMock

@pytest.fixture
def mock_settings():
    settings = MagicMock(spec=Settings)
    settings.LOG_LEVEL = "INFO"
    settings.LOG_FILE = "/tmp/test_log.log"
    settings.LOG_MAX_SIZE = 10485760
    settings.LOG_BACKUP_COUNT = 5
    settings.DISCORD_WEBHOOK_URL = None
    return settings

@patch("logging.config.dictConfig")
def test_setup_logging_formatters(mock_dictConfig, mock_settings):
    setup_logging(mock_settings)

    config = mock_dictConfig.call_args[0][0]

    # Assert console formatter configuration
    assert config["formatters"]["console"]["()"] == "structlog.stdlib.ProcessorFormatter"
    assert config["formatters"]["console"]["processor"].__class__.__name__ == "ConsoleRenderer"

    # Assert JSON formatter configuration
    assert config["formatters"]["json"]["()"] == "structlog.stdlib.ProcessorFormatter"
    assert config["formatters"]["json"]["processor"].__class__.__name__ == "JSONRenderer"

    # Assert handlers use correct formatters
    assert config["handlers"]["console"]["formatter"] == "console"
    assert config["handlers"]["file"]["formatter"] == "json"

@patch("logging.config.dictConfig")
def test_setup_logging_log_level(mock_dictConfig, mock_settings):
    mock_settings.LOG_LEVEL = "DEBUG"
    setup_logging(mock_settings)

    config = mock_dictConfig.call_args[0][0]

    # Assert log level is applied to handlers and root logger
    assert config["handlers"]["console"]["level"] == "DEBUG"
    assert config["handlers"]["file"]["level"] == "DEBUG"
    assert config["loggers"][""]["level"] == "DEBUG"

@patch("logging.config.dictConfig")
def test_setup_logging_file_handler_config(mock_dictConfig, mock_settings):
    mock_settings.LOG_FILE = "/var/log/my_app.log"
    mock_settings.LOG_MAX_SIZE = 20 * 1024 * 1024 # 20 MB
    mock_settings.LOG_BACKUP_COUNT = 10
    setup_logging(mock_settings)

    config = mock_dictConfig.call_args[0][0]
    file_handler = config["handlers"]["file"]
    assert file_handler["class"] == "logging.handlers.RotatingFileHandler"
    assert file_handler["filename"] == "/var/log/my_app.log"
    assert file_handler["maxBytes"] == 20 * 1024 * 1024
    assert file_handler["backupCount"] == 10

@patch("logging.config.dictConfig")
def test_setup_logging_discord_handler(mock_dictConfig, mock_settings):
    mock_settings.DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/123/abc"
    setup_logging(mock_settings)

    config = mock_dictConfig.call_args[0][0]

    # Assert discord handler is configured
    assert "discord" in config["handlers"]
    discord_handler = config["handlers"]["discord"]
    assert discord_handler["class"] == "src.utils.discord_handler.DiscordHandler"
    assert discord_handler["webhook_url"] == "https://discord.com/api/webhooks/123/abc"
    assert discord_handler["level"] == "ERROR"

    # Assert discord handler is added to the root logger
    assert "discord" in config["loggers"][""]["handlers"]

@patch("src.utils.discord_handler.DiscordHandler.emit")
def test_discord_handler_sends_log(mock_emit, mock_settings):
    import logging

    mock_settings.DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/123/abc"
    setup_logging(mock_settings)

    log = logging.getLogger("test_logger")
    log.error("This is a test error.")

    mock_emit.assert_called_once()