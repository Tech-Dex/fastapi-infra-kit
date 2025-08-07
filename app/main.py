import structlog
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
import time
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from alembic.config import Config
from alembic import command

from starlette.responses import FileResponse

from app.core.config import settings
from app.core.logging import setup_logging, get_logger
from app.api.v1.router import PREFIX, router_http as api_v1_router_http

# Setup logging
setup_logging()
logger = get_logger(__name__)
startup_time = datetime.now(timezone.utc)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up Event Management System")

    try:
        logger.info("Running database migrations")
        alembic_cfg = Config("app/alembic/alembic.ini")
        alembic_cfg.set_main_option("script_location", "app/alembic")
        alembic_cfg.set_main_option("sqlalchemy.url", settings.DB_URL_SYNC)

        command.upgrade(alembic_cfg, "head")
        logger.info("Database migrations completed successfully")
    except Exception as e:
        logger.error("Failed to run database migrations", error=str(e), exc_info=True)
        raise

    yield
    logger.info("Shutting down Event Management System")


app = FastAPI(
    title="Event Management System",
    description="A system for managing events in buckets",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    request_id = str(uuid.uuid4())

    # Add request ID to context
    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(request_id=request_id)

    start_time = time.time()

    # Log request
    logger.info(
        "Request started",
        method=request.method,
        url=str(request.url),
        path=request.url.path,
        query_params=dict(request.query_params),
        client_host=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )

    try:
        response: Response = await call_next(request)

        # Calculate response time
        process_time = time.time() - start_time

        # Log response
        logger.info(
            "Request completed",
            status_code=response.status_code,
            process_time=process_time,
        )

        # Add response time header
        response.headers["X-Process-Time"] = str(process_time)
        response.headers["X-Request-ID"] = request_id

        return response

    except Exception as e:
        process_time = time.time() - start_time

        # Log error
        logger.error(
            "Request failed",
            error=str(e),
            error_type=type(e).__name__,
            process_time=process_time,
            exc_info=True,
        )
        raise


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
