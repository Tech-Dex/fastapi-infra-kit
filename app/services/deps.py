from typing import Annotated

from fastapi import Depends, Query
from fastapi_pagination import set_page, set_params
from fastapi_pagination.cursor import CursorPage, CursorParams
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.requests import Request

from app.core.database import get_db
from app.core.redis import get_redis
from app.exceptions.api_exceptions import UnprocessableEntityException

SessionDep = Annotated[AsyncSession, Depends(get_db)]
RedisDep = Annotated[Redis, Depends(get_redis)]


def check_alphanumeric_dash_underscore_path_params(
    path_params: list[str],
):
    """
    Check if path parameters contain only alphanumeric characters, dashes, and underscores.
    :param path_params:
    :return:
    """

    async def _callback(request: Request):
        for param in path_params:
            value = request.path_params.get(param)
            print(value)

            # Faster than using regex?
            if value and not value.replace("-", "").replace("_", "").isalnum():
                raise UnprocessableEntityException(
                    f"Invalid value for {param}: {value}. "
                    "Only alphanumeric characters, dashes, and underscores are allowed."
                )
        return request

    return _callback


def set_pagination(model: type):
    """
    Pagination dependency for FastAPI using CursorPage and CursorParams.
    This function sets up pagination parameters for a given model.
    :param model:
    :return: A callback function that sets pagination parameters.
    """

    async def _callback(
        cursor: str = Query(None, description="Cursor for pagination"),
        size: int = Query(10, description="Page size"),
    ):
        set_page(CursorPage[model])
        set_params(CursorParams(cursor=cursor, size=size))

    return _callback
