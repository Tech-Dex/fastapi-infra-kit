# app/services/error_handler.py
import functools
import inspect

from fastapi import HTTPException
from loguru import logger
from psycopg2.errors import UniqueViolation
from sqlalchemy.exc import NoResultFound

from app.exceptions.custom_exceptions import (AlreadyExistsException,
                                              CustomHTTPException,
                                              NotFoundException)

logger_exception = logger.bind(name="error_handler")


def exception_handler(func):
    sig = inspect.signature(func)
    return_type = sig.return_annotation
    resource_type = getattr(return_type, "__name__", "Resource")

    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except CustomHTTPException as exception:  # already handled, nested exceptions
            raise exception
        except NoResultFound as exception:
            raise NotFoundException(
                resource=resource_type,
            ) from exception
        except UniqueViolation as exception:
            raise AlreadyExistsException(
                resource=resource_type,
            ) from exception
        except Exception as exception:
            logger.error("Unexpected error: %s", str(exception), exc_info=True)
            raise HTTPException(
                status_code=500, detail="Something went wrong, please contact support."
            ) from exception

    return wrapper
