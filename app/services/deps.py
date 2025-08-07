from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.requests import Request

from app.core.database import get_db

SessionDep = Annotated[AsyncSession, Depends(get_db)]


def check_alphanumeric_dash_underscore_path_params(
    path_params: list[str],
):
    async def _callback(request: Request):
        for param in path_params:
            value = request.path_params.get(param)

            # Faster than using regex?
            if value and not value.replace("-", "").replace("_", "").isalnum():
                raise ValueError(
                    f"Invalid value for {param}: {value}. "
                    "Only alphanumeric characters, dashes, and underscores are allowed."
                )
        return request

    return _callback
