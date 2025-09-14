from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
import time
import structlog # Import structlog

class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        log = structlog.get_logger(__name__) # Get logger after setup_logging is called
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        log.info(f"Request: {request.method} {request.url} - Response: {response.status_code} in {process_time:.2f}ms")
        return response