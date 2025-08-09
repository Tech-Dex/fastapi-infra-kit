from contextlib import asynccontextmanager
from datetime import datetime, timezone

from alembic import command
from alembic.config import Config
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi_pagination import add_pagination
from loguru import logger
from pydantic import ValidationError
from starlette.responses import FileResponse

from app.api.v1.router import PREFIX
from app.api.v1.router import router_http as api_v1_router_http
from app.core.config import settings
from app.core.exception_handlers import (api_exception_handler,
                                         generic_exception_handler,
                                         method_not_allowed_exception_handler,
                                         not_found_exception_handler,
                                         validation_exception_handler)
from app.core.logger import setup_logging
from app.core.middleware.request_logger import RequestLoggerMiddleware
from app.exceptions.api_exceptions import APIException

# Setup logging
setup_logging()
logger_startup = logger.bind(source="startup")

startup_time = datetime.now(timezone.utc)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger_startup.info("Starting up Event Management System")

    try:
        logger_startup.info("Running database migrations")
        alembic_cfg = Config("app/alembic/alembic.ini")
        alembic_cfg.set_main_option("script_location", "app/alembic")
        alembic_cfg.set_main_option("sqlalchemy.url", settings.DB_URL_SYNC)

        command.upgrade(alembic_cfg, "head")
        logger_startup.info("Database migrations completed successfully")
    except Exception as e:
        logger_startup.error(
            "Failed to run database migrations", error=str(e), exc_info=True
        )
        raise

    yield
    logger_startup.info("Shutting down Event Management System")


app = FastAPI(
    title="Event Management System",
    description="A system for managing events in buckets",
    version="1.0.0",
    lifespan=lifespan,
)

add_pagination(app)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RequestLoggerMiddleware)

# Exception handlers
app.add_exception_handler(APIException, api_exception_handler)  # extends HTTPException

app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(ValidationError, validation_exception_handler)

app.add_exception_handler(404, not_found_exception_handler)
app.add_exception_handler(405, method_not_allowed_exception_handler)

app.add_exception_handler(Exception, generic_exception_handler)


# Routers
app.include_router(api_v1_router_http, prefix=PREFIX, tags=["v1"])


@app.get("/")
async def root():
    return {"message": "Event Management System API"}


@app.get("/health")
async def health_check():
    uptime = datetime.now(timezone.utc) - startup_time
    uptime_seconds = uptime.total_seconds()

    return {
        "status": "healthy",
        "service": "event-management-system",
        "uptime_seconds": uptime_seconds,
        "uptime_human": str(uptime).split(".")[
            0
        ],  # Remove microseconds for readability
    }


@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return FileResponse("static/favicon.ico")


# TODO: redis
# TODO: later: communicate with loki for logs, add prometheus metric
