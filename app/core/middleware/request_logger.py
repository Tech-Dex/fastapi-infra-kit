import time
import uuid

from fastapi import Request
from loguru import logger
from starlette.middleware.base import BaseHTTPMiddleware

logger_http = logger.bind(source="http")


class RequestLoggerMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
        start = time.time()
        request.state.timestamp = start
        request.state.correlation_id = correlation_id
        logger_http.bind(
            correlation_id=correlation_id,
            request_url=request.url,
        ).info(f"Request start: {request.method} {request.url}")
        response = await call_next(request)
        duration = (time.time() - start) * 1000
        logger_http.bind(
            correlation_id=correlation_id,
            request_url=request.url,
        ).info(
            f"Request end: {request.method} {request.url} status={response.status_code} duration={duration:.2f}ms"
        )
        response.headers["X-Correlation-ID"] = correlation_id
        response.headers["X-Processing-Time-Ms"] = f"{duration:.2f}"
        return response
