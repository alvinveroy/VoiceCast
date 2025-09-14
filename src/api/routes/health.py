from fastapi import APIRouter
from src.models.responses import HealthResponse

router = APIRouter()

@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Provide a health check for the service."""
    return HealthResponse(
        status="healthy",
        services={
            "deepgram": "ok",
            "cast": "ok"
        }
    )
