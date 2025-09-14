from fastapi import APIRouter, Depends, HTTPException, Request
from src.models.requests import TTSRequest
from src.api.dependencies import get_queue_service, get_device_registry
from src.services.queue_service import QueueService
from src.config.settings import Settings, get_settings
from src.services.device_registry import DeviceRegistry
from src.api.security import get_api_key
import structlog # Import structlog

router = APIRouter(dependencies=[Depends(get_api_key)])

@router.post("/tts")
async def text_to_speech(
    request: Request,
    tts_request: TTSRequest,
    queue_service: QueueService = Depends(get_queue_service),
    settings: Settings = Depends(get_settings),
    device_registry: DeviceRegistry = Depends(get_device_registry),
):
    """Receive text and generate speech, then cast to a device."""
    log = structlog.get_logger(__name__) # Get logger after setup_logging is called

    if tts_request.device_name and not device_registry.get_device_by_name(tts_request.device_name):
        raise HTTPException(status_code=404, detail={"error": "No device available with the given device name"})

    try:
        log.info("Received TTS request", text=tts_request.text)
        
        task = {
            "tts_request": tts_request,
            "port": request.url.port or settings.PORT,
        }
        task_id = queue_service.add_to_queue(task)

        return {"message": "TTS request added to queue", "task_id": task_id}
    except Exception as e:
        log.error("Error adding TTS request to queue", error=repr(e))
        raise HTTPException(status_code=500, detail="An error occurred while adding request to queue.")
