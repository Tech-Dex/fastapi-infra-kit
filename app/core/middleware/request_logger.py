import time
import uuid

from fastapi import Request
from loguru import logger
from starlette.middleware.base import BaseHTTPMiddleware

logger_http = logger.bind(source="http")


class RequestLoggerMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())
        start = time.time()
        logger_http.bind(
            request_id=request_id,
            request_url=request.url,
        ).info(f"Request start: {request.method} {request.url}")
        response = await call_next(request)
        duration = (time.time() - start) * 1000
        logger_http.bind(
            request_id=request_id,
            request_url=request.url,
        ).info(
            f"Request end: {request.method} {request.url} status={response.status_code} duration={duration:.2f}ms"
        )
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Processing-Time-Ms"] = f"{duration:.2f}"
        return response
