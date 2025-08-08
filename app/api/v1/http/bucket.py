from fastapi import APIRouter, Depends
from fastapi_pagination.cursor import CursorPage

from app.schemas.bucket import BucketResponse
from app.schemas.event import EventCreate
from app.schemas.mixin import BucketEventMixin
from app.services.bucket_service import BucketService
from app.services.deps import (SessionDep,
                               check_alphanumeric_dash_underscore_path_params,
                               set_pagination)

router: APIRouter = APIRouter()


@router.get(
    "/",
    response_model=CursorPage[BucketResponse],
    dependencies=[Depends(set_pagination(BucketResponse))],
)
async def fetch_buckets(session: SessionDep) -> CursorPage[BucketResponse]:
    """
    Retrieve all buckets.

    :param session: Database session dependency.
    :param cursor: Cursor for pagination - used in set_pagination.
    :param params: Pagination parameters - used in set_pagination.
    :return: List of all buckets.
    """
    return await BucketService.get_all_buckets(session)


@router.put(
    "/{name}",
    dependencies=[Depends(check_alphanumeric_dash_underscore_path_params(["name"]))],
)
async def send_event_to_bucket(
    name: str, event: EventCreate, session: SessionDep
) -> BucketEventMixin:
    """
    Send an event to a specific bucket.

    :param session: Database session dependency.
    :param name: The name of the bucket, which must be alphanumeric, dash, or underscore.
    :param event: The event data to be sent to the bucket.
    """
    return await BucketService.create_bucket_with_event(session, name, event)
