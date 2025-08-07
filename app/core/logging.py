import logging
import sys
from typing import Any
import structlog
from pythonjsonlogger import json as json_logger
from app.core.config import settings


class ColoredConsoleFormatter(logging.Formatter):
    """Logging Formatter to add colors for console output"""

    # Color codes
    BLUE = "\033[94m"
    GREY = "\x1b[38;21m"
    GREEN = "\x1b[32;21m"
    YELLOW = "\x1b[33;21m"
    RED = "\x1b[31;21m"
    BOLD_RED = "\x1b[31;1m"
    CYAN = "\x1b[36;21m"
    WHITE = "\x1b[37;21m"
    RESET = "\x1b[0m"

    FORMAT = "%(asctime)s [%(threadName)s] - %(message)s (%(filename)s:%(lineno)d)"

    FORMATS = {
        logging.DEBUG: f"{GREY}%(levelname)s{RESET}: {FORMAT}",
        logging.INFO: f"{GREEN}%(levelname)s{RESET}: {FORMAT}",
        logging.WARNING: f"{YELLOW}%(levelname)s{RESET}: {FORMAT}",
        logging.ERROR: f"{RED}%(levelname)s{RESET}: {FORMAT}",
        logging.CRITICAL: f"{BOLD_RED}%(levelname)s{RESET}: {FORMAT}",
    }

    def format(self, record) -> str:
        log_fmt = self.FORMATS.get(record.levelno, self.FORMAT)
        formatter = logging.Formatter(log_fmt, datefmt="%H:%M:%S")
        return formatter.format(record)


def setup_logging():
    """Setup structured logging with JSON output for Loki or colorful console output"""

    if settings.LOG_FORMAT == "json":
        # Configure structlog for JSON output
        structlog.configure(
            processors=[
                structlog.contextvars.merge_contextvars,
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.processors.add_log_level,
                structlog.processors.StackInfoRenderer(),
                structlog.dev.set_exc_info,
                structlog.processors.CallsiteParameterAdder(
                    [
                        structlog.processors.CallsiteParameter.PATHNAME,
                        structlog.processors.CallsiteParameter.LINENO,
                    ]
                ),
                structlog.processors.JSONRenderer(),
            ],
            wrapper_class=structlog.make_filtering_bound_logger(
                getattr(logging, settings.LOG_LEVEL.upper())
            ),
            context_class=dict,
            logger_factory=structlog.WriteLoggerFactory(),
            cache_logger_on_first_use=True,
        )

        # JSON formatter for standard logging
        formatter = json_logger.JsonFormatter(
            "%(asctime)s %(name)s %(levelname)s %(pathname)s %(lineno)d %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    else:
        # Configure structlog for console output (disable JSON rendering)
        structlog.configure(
            processors=[
                structlog.contextvars.merge_contextvars,
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.processors.add_log_level,
                structlog.processors.StackInfoRenderer(),
                structlog.dev.set_exc_info,
                # Remove JSONRenderer for console output
                structlog.dev.ConsoleRenderer(colors=True),
            ],
            wrapper_class=structlog.make_filtering_bound_logger(
                getattr(logging, settings.LOG_LEVEL.upper())
            ),
            context_class=dict,
            logger_factory=structlog.WriteLoggerFactory(),
            cache_logger_on_first_use=True,
        )

        # Colored console formatter for standard logging
        formatter = ColoredConsoleFormatter()

    # Setup handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    # Root logger configuration
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper()))
    root_logger.handlers.clear()
    root_logger.addHandler(handler)

    # Suppress some library loggers to reduce noise
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)


def get_logger(name: str) -> Any:
    """Get a structured logger instance"""
    if settings.LOG_FORMAT == "json":
        return structlog.get_logger(name)
    else:
        return logging.getLogger(name)


def get_structured_logger(name: str) -> Any:
    """Get a structured logger instance (always returns structlog)"""
    return structlog.get_logger(name)
