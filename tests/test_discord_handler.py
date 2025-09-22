
import logging
import pytest
from unittest.mock import patch
from src.utils.discord_handler import DiscordHandler

@pytest.fixture
def discord_handler():
    return DiscordHandler(webhook_url="https://discord.com/api/webhooks/123/abc")

def test_emit(discord_handler):
    with patch("httpx.Client") as mock_client:
        record = logging.LogRecord(
            name="test",
            level=logging.ERROR,
            pathname="test.py",
            lineno=1,
            msg="test message",
            args=(),
            exc_info=None,
        )
        discord_handler.emit(record)

        mock_client.return_value.__enter__.return_value.post.assert_called_once_with(
            discord_handler.webhook_url,
            json={"content": f"```\n{discord_handler.format(record)}```"},
        )

