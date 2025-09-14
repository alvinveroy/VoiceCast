from fastapi import APIRouter, Depends
from src.api.security import get_api_key
from src.utils.logger import log
import os
import signal

router = APIRouter()

@router.get("/admin/stop", summary="Stop the VoiceCast daemon")
async def stop_daemon(api_key: str = Depends(get_api_key)):
    log.info("Received stop request. Shutting down server.")
    # This will stop the uvicorn server
    os.kill(os.getpid(), signal.SIGINT)
    return {"message": "Server is shutting down."}