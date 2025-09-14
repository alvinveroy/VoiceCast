import pytest
import os
from src.config.settings import get_settings
from unittest.mock import patch

pytest_plugins = ["pytest_env"]

@pytest.fixture(scope="session", autouse=True)
def set_test_env_vars():
    os.environ["API_KEY"] = "test_api_key"
    os.environ["DEEPGRAM_API_KEY"] = "test_deepgram_key"

@pytest.fixture(autouse=True, scope="session")
def mock_get_local_ip_session():
    with patch("src.utils.network_utils.get_local_ip", return_value="127.0.0.1"):
        yield

@pytest.fixture(autouse=True)
def clear_settings_cache():
    get_settings.cache_clear()