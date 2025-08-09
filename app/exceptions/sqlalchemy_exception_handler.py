# app/services/sqlalchemy_exception_handler.py
import functools
from typing import Optional

from fastapi import HTTPException
from loguru import logger
from sqlalchemy.exc import IntegrityError, NoResultFound
from starlette import status

from app.exceptions.api_exceptions import (AlreadyExistsException,
                                           APIException, DeveloperException,
                                           NotFoundException)

logger_exception = logger.bind(source="sqlalchemy_exception_handler")


def sqlalchemy_exception_handler(
    resource_name: Optional[str] = None,
):
    """Decorator to handle SQLAlchemy exceptions in FastAPI endpoints.
    Args:
        resource_name (Optional[str]): The name of the resource being accessed, used for error messages.
    Returns:
        Callable: A decorator that wraps the endpoint function to handle exceptions.
    """

    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except APIException as exception:
                # already handled, re-raise it
                raise exception
            except NoResultFound as exception:
                if not resource_name:
                    message = f"NoResultFound raised without a resource name. This error was raised in {func.__name__}. Please contact the developer."
                    logger_exception.warning(message)
                    raise DeveloperException(
                        message=message,
                        status_code=status.HTTP_404_NOT_FOUND,
                    )
                raise NotFoundException(
                    resource=resource_name if resource_name else func.__name__,
                ) from exception
            except IntegrityError as exception:
                if not resource_name:
                    message = f"IntegrityError raised without a resource name. This error was raised in {func.__name__}. Please contact the developer."
                    logger_exception.warning(message)
                    raise DeveloperException(
                        message=message,
                        status_code=status.HTTP_409_CONFLICT,
                    )
                raise AlreadyExistsException(resource=resource_name) from exception
            except Exception as exception:
                logger.error("Unexpected error: %s", str(exception), exc_info=True)
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Something went wrong, please contact support.",
                ) from exception

        return wrapper

    return decorator
