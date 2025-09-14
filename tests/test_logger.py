import pytest
from src.utils.logger import setup_logging
from src.config.settings import Settings
from unittest.mock import patch, MagicMock
import logging
import os
from rich.logging import RichHandler

@pytest.fixture
def mock_settings():
    settings = MagicMock(spec=Settings)
    settings.LOG_LEVEL = "INFO"
    settings.LOG_FILE = "/tmp/test_log.log"
    settings.LOG_MAX_SIZE = 10485760
    settings.LOG_BACKUP_COUNT = 5
    settings.LOG_FORMAT = "json" # Default to json for tests
    return settings

@patch("logging.config.dictConfig")
def test_setup_logging_json_format(mock_dictConfig, mock_settings):
    mock_settings.LOG_FORMAT = "json"
    setup_logging(mock_settings)

    config = mock_dictConfig.call_args[0][0]
    assert config["formatters"]["json"]["processor"].__class__.__name__ == "JSONRenderer"
    assert config["handlers"]["file"]["formatter"] == "json"
    assert config["handlers"]["default"]["formatter"] == "json" # Ensure default handler is also json

@patch("logging.basicConfig")
def test_setup_logging_console_format(mock_basicConfig, mock_settings):
    mock_settings.LOG_FORMAT = "console"
    setup_logging(mock_settings)

    mock_basicConfig.assert_called_once()
    args, kwargs = mock_basicConfig.call_args
    assert kwargs["level"] == mock_settings.LOG_LEVEL
    assert kwargs["format"] == "%(message)s"
    assert kwargs["datefmt"] == "[%X]"
    assert isinstance(kwargs["handlers"][0], RichHandler)
    assert kwargs["handlers"][0].rich_tracebacks == True

@patch("logging.config.dictConfig")
@patch("logging.basicConfig")
def test_setup_logging_log_level(mock_basicConfig, mock_dictConfig, mock_settings):
    # Test with JSON format
    mock_settings.LOG_FORMAT = "json"
    mock_settings.LOG_LEVEL = "DEBUG"
    setup_logging(mock_settings)
    config = mock_dictConfig.call_args[0][0]
    assert config["handlers"]["file"]["level"] == "DEBUG"
    assert config["loggers"][""]["level"] == "DEBUG"

    # Test with Console format
    mock_dictConfig.reset_mock() # Reset mock for the next call
    mock_settings.LOG_FORMAT = "console"
    mock_settings.LOG_LEVEL = "WARNING"
    setup_logging(mock_settings)
    args, kwargs = mock_basicConfig.call_args
    assert kwargs["level"] == mock_settings.LOG_LEVEL

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