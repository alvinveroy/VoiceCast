import pytest
from src.api.dependencies import get_tts_service, get_cast_service, get_queue_service, get_device_registry
from src.services.tts_service import TTSService
from src.services.cast_service import CastService
from src.services.device_registry import DeviceRegistry
from src.config.settings import Settings
from unittest.mock import MagicMock
from fastapi import Request
from src.services.tts_service import TTSService
from src.services.cast_service import CastService
from src.services.device_registry import DeviceRegistry
from src.config.settings import Settings
from unittest.mock import MagicMock
from fastapi import Request
from src.config.settings import Settings

def test_get_tts_service():
    settings = Settings(DEEPGRAM_API_KEY="test")
    tts_service = get_tts_service(settings)
    assert isinstance(tts_service, TTSService)

def test_get_cast_service():
    request = MagicMock(spec=Request)
    request.app.state.cast_service = "test"
    cast_service = get_cast_service(request)
    assert cast_service == "test"

def test_get_device_registry():
    request = MagicMock(spec=Request)
    request.app.state.device_registry = "test"
    device_registry = get_device_registry(request)
    assert device_registry == "test"
