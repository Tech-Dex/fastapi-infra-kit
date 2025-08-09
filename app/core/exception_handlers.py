import traceback

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from loguru import logger
from pydantic import ValidationError

from app.exceptions.api_exceptions import APIException

logger_exception_handler = logger.bind(source="exception_handler")


async def api_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle HTTPException errors"""
    if isinstance(exc, APIException):
        logger_exception_handler.error(
            f"HTTP {exc.status_code} error on {request.url}: {exc.detail}"
        )
        status_code = exc.status_code
        detail = exc.detail
    else:
        logger_exception_handler.error(
            f"Non-HTTPException passed to http_exception_handler: {exc}"
        )
        status_code = 500
        detail = "Internal Server Error"

    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "type": "api_error",
                "code": status_code,
                "message": detail,
                "path": str(request.url),
                "method": request.method,
                "timestamp": str(request.state.timestamp)
                if hasattr(request.state, "timestamp")
                else None,
            }
        },
    )


async def validation_exception_handler(
    request: Request, exc: Exception
) -> JSONResponse:
    """Handle Pydantic validation errors"""
    if isinstance(exc, RequestValidationError):
        errors = exc.errors()
    elif isinstance(exc, ValidationError):
        errors = exc.errors()
    else:
        errors = [{"loc": [], "msg": str(exc), "type": "unknown"}]

    logger_exception_handler.error(f"Validation error on {request.url}: {errors}")

    formatted_errors = []
    for error in errors:
        field = " -> ".join(str(x) for x in error.get("loc", []))
        formatted_errors.append(
            {
                "field": field,
                "message": error.get("msg"),
                "type": error.get("type"),
                "input": error.get("input"),
            }
        )

    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "type": "validation_error",
                "code": 422,
                "message": "Validation failed",
                "details": formatted_errors,
                "path": str(request.url),
                "method": request.method,
                "timestamp": str(request.state.timestamp)
                if hasattr(request.state, "timestamp")
                else None,
            }
        },
    )


async def not_found_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle 404 Not Found errors"""
    # Check before if it is instance of APIException and if so let http_exception_handler handle it
    if isinstance(exc, APIException) and exc.status_code == 404:
        logger_exception_handler.error(
            f"APIException 404 on {request.url}: {exc.detail}"
        )
        return await api_exception_handler(request, exc)

    logger_exception_handler.error(f"Not Found error on {request.url}: {str(exc)}")

    return JSONResponse(
        status_code=404,
        content={
            "error": {
                "type": "not_found",
                "code": 404,
                "message": "Resource not found",
                "path": str(request.url),
                "method": request.method,
                "timestamp": str(request.state.timestamp)
                if hasattr(request.state, "timestamp")
                else None,
            }
        },
    )


async def method_not_allowed_exception_handler(
    request: Request, exc: Exception
) -> JSONResponse:
    """Handle 405 Method Not Allowed errors"""
    logger_exception_handler.error(
        f"Method Not Allowed error on {request.url}: {str(exc)}"
    )

    return JSONResponse(
        status_code=405,
        content={
            "error": {
                "type": "method_not_allowed",
                "code": 405,
                "message": "Method not allowed",
                "path": str(request.url),
                "method": request.method,
                "timestamp": str(request.state.timestamp)
                if hasattr(request.state, "timestamp")
                else None,
            }
        },
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected exceptions"""
    logger_exception_handler.error(f"Unexpected error on {request.url}: {str(exc)}")
    logger_exception_handler.error(f"Traceback: {traceback.format_exc()}")

    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "type": "internal_error",
                "code": 500,
                "message": "An unexpected error occurred",
                "path": str(request.url),
                "method": request.method,
                "timestamp": str(request.state.timestamp)
                if hasattr(request.state, "timestamp")
                else None,
            }
        },
    )
