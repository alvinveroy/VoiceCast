from fastapi import APIRouter, Depends, Request
from src.api.security import get_api_key
from src.services.device_registry import DeviceRegistry

router = APIRouter(dependencies=[Depends(get_api_key)])

@router.get("/devices")
async def get_devices(request: Request):
    device_registry: DeviceRegistry = request.app.state.device_registry
    return device_registry.get_devices()

@router.get("/devices/refresh")
async def refresh_devices(request: Request):
    device_registry: DeviceRegistry = request.app.state.device_registry
    await device_registry.refresh_devices()
    return {"message": "Device discovery refresh triggered."}
