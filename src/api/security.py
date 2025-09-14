from fastapi import Security, HTTPException, Depends, Request
from fastapi.security.api_key import APIKeyHeader
from starlette.status import HTTP_403_FORBIDDEN
from src.config.settings import Settings, get_settings
import structlog # Import structlog
import secrets

API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)
CF_CLIENT_ID_HEADER = APIKeyHeader(name="CF-Access-Client-Id", auto_error=False)
CF_CLIENT_SECRET_HEADER = APIKeyHeader(name="CF-Access-Client-Secret", auto_error=False)

async def get_api_key(settings: Settings = Depends(get_settings), api_key_header: str = Security(API_KEY_HEADER)):
    log = structlog.get_logger(__name__) # Get logger after setup_logging is called
    log.info(f"API Key from settings: {settings.API_KEY}")
    log.info(f"API Key from header: {api_key_header}")
    if not api_key_header or not secrets.compare_digest(api_key_header, settings.API_KEY):
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN, detail="Could not validate credentials"
        )
    return api_key_header

async def verify_cloudflare_access(
    request: Request,
    settings: Settings = Depends(get_settings),
    cf_client_id: str = Security(CF_CLIENT_ID_HEADER),
    cf_client_secret: str = Security(CF_CLIENT_SECRET_HEADER),
):
    log = structlog.get_logger(__name__)
    if settings.CLOUDFLARE_ACCESS_CLIENT_ID and settings.CLOUDFLARE_ACCESS_CLIENT_SECRET:
        log.info("Cloudflare Access verification enabled.")
        if not cf_client_id or not cf_client_secret:
            raise HTTPException(
                status_code=HTTP_403_FORBIDDEN, detail="Missing Cloudflare Access headers"
            )
        if cf_client_id != settings.CLOUDFLARE_ACCESS_CLIENT_ID or cf_client_secret != settings.CLOUDFLARE_ACCESS_CLIENT_SECRET:
            raise HTTPException(
                status_code=HTTP_403_FORBIDDEN, detail="Invalid Cloudflare Access credentials"
            )
    return True