from fastapi import FastAPI, Request, Depends
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from src.config.settings import Settings
from src.api.routes import tts, health, admin, devices
from src.api.middleware import LoggingMiddleware
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from dotenv import load_dotenv
import structlog # Import structlog
from src.services.device_registry import DeviceRegistry
from src.services.cast_service import CastService
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI, settings: Settings):
    # Load the ML model
    app.state.device_registry = DeviceRegistry(settings)
    app.state.cast_service = CastService(settings)
    await app.state.device_registry.discover_devices()
    yield
    # Clean up the ML model and release the resources
    app.state.device_registry = None
    app.state.cast_service = None

def create_app(settings: Settings, skip_logging: bool = False) -> FastAPI:
    load_dotenv()
    if not skip_logging:
        pass # setup_logging is now called in main.py

    log = structlog.get_logger(__name__) # Get logger after setup_logging is called
    log.info(f"Creating app with settings: {settings.model_dump_json()}")

    limiter = Limiter(
        key_func=get_remote_address,
        default_limits=[f"{settings.RATE_LIMIT_REQUESTS} per {settings.RATE_LIMIT_WINDOW} seconds"]
    )

    from src.api.security import verify_cloudflare_access

    app = FastAPI(
        title=settings.TITLE,
        description=settings.DESCRIPTION,
        version=settings.VERSION,
        docs_url=settings.DOCS_URL,
        redoc_url=settings.REDOC_URL,
        lifespan=lambda app: lifespan(app, settings), # Pass settings to lifespan
        dependencies=[Depends(verify_cloudflare_access)]
    )

    app.state.settings = settings
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    app.add_middleware(SlowAPIMiddleware)

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        log.error("Unhandled exception", exc_info=exc)
        return JSONResponse(
            status_code=500,
            content={"detail": "An internal server error occurred."},
        )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.add_middleware(LoggingMiddleware) # Use class-based middleware

    app.mount("/audio", StaticFiles(directory=settings.AUDIO_OUTPUT_DIR), name="audio")

    app.include_router(tts.router, prefix="/api/v1", tags=["tts"])
    app.include_router(health.router, prefix="/api/v1", tags=["health"])
    app.include_router(admin.router, prefix="/api/v1", tags=["admin"])
    app.include_router(devices.router, prefix="/api/v1", tags=["devices"])

    return app
