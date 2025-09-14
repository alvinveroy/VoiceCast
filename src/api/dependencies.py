from src.services.tts_service import TTSService
from src.services.cast_service import CastService
from src.services.queue_service import QueueService # Import QueueService
from src.services.device_registry import DeviceRegistry
from src.config.settings import Settings, get_settings
from fastapi import Depends, Request

def get_tts_service(settings: Settings = Depends(get_settings)) -> TTSService:
    return TTSService(settings)

def get_cast_service(request: Request) -> CastService:
    return request.app.state.cast_service

def get_queue_service(
    tts_service: TTSService = Depends(get_tts_service),
    cast_service: CastService = Depends(get_cast_service),
    settings: Settings = Depends(get_settings)
) -> QueueService:
    return QueueService(tts_service, cast_service, settings)

def get_device_registry(request: Request) -> DeviceRegistry:
    return request.app.state.device_registry
