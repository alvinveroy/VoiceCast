import os
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
from src.services.watchdog_service import watchdog_loop
from contextlib import asynccontextmanager
import asyncio

@asynccontextmanager
async def lifespan(app: FastAPI, settings: Settings, skip_watchdog: bool = False):
    # Load the ML model
    app.state.device_registry = DeviceRegistry(settings)
    app.state.cast_service = CastService(settings)
    await app.state.device_registry.discover_devices()

    # Start the watchdog service
    watchdog_task = None
    if not skip_watchdog:
        watchdog_task = asyncio.create_task(watchdog_loop(app.state.device_registry, settings))

    log = structlog.get_logger(__name__)
    try:
        yield
    finally:
        # Clean up the ML model and release the resources
        app.state.device_registry = None
        app.state.cast_service = None

        # Cancel the watchdog task
        if watchdog_task:
            watchdog_task.cancel()
            try:
                await watchdog_task
            except asyncio.CancelledError:
                log.info("Watchdog task cancelled.")

def create_app(settings: Settings, skip_logging: bool = False, skip_watchdog: bool = False) -> FastAPI:
    load_dotenv()
    if not skip_logging:
        pass # setup_logging is now called in main.py

    # Create logs and audio directories if they don't exist
    os.makedirs(os.path.join(settings.PROJECT_ROOT, "logs"), exist_ok=True)
    os.makedirs(settings.AUDIO_OUTPUT_DIR, exist_ok=True)

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
        lifespan=lambda app: lifespan(app, settings, skip_watchdog), # Pass settings to lifespan
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
