# pyright: basic
import logging
import sys

from loguru import logger

from app.core.config import settings

logger.remove()

logger.add(
    sys.stdout,
    serialize=settings.LOG_JSON_FORMAT,
    enqueue=True,
    level=settings.LOG_LEVEL,
)
logger.add(
    settings.LOG_FILE_PATH,
    rotation=settings.LOG_ROTATION,
    retention=settings.LOG_RETENTION,
    compression=settings.LOG_COMPRESSION,
    level=settings.LOG_LEVEL,
    serialize=settings.LOG_JSON_FORMAT,
    enqueue=True,
)


class InterceptHandler(logging.Handler):
    def emit(self, record: logging.LogRecord) -> None:
        level: str | int
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        frame, depth = logging.currentframe(), 2
        while frame and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )


def setup_logging():
    for name in logging.root.manager.loggerDict:
        if name in ("uvicorn"):
            uvicorn_logger = logging.getLogger(name)
            uvicorn_logger.handlers.clear()
            uvicorn_logger.setLevel(settings.LOG_LEVEL)
            uvicorn_logger.addHandler(InterceptHandler())
