import uuid

from fastapi import APIRouter, Depends, Query
from starlette import status

from app.schemas.bucket import BucketResponse
from app.schemas.event import EventResponse
from app.schemas.mixin import BucketEventsMixin
from app.services.bucket_service import BucketService
from app.services.deps import (RedisDep, SessionDep,
                               check_alphanumeric_dash_underscore_path_params,
                               set_pagination)
from app.services.event_service import EventService
from app.services.redis_service import redis_cache

router: APIRouter = APIRouter()


@router.get(
    "/",
    summary="Fetch Events in a Bucket",
    description="Retrieve all events in a specific bucket with pagination support.  The response is paginated using cursor-based pagination.",
    response_model=BucketEventsMixin,
    dependencies=[
        Depends(set_pagination(EventResponse)),
        Depends(check_alphanumeric_dash_underscore_path_params(["bucket_name"])),
    ],
    status_code=status.HTTP_200_OK,
)
@redis_cache("bucket_events:{bucket_name}:cursor={cursor}:size={size}", ttl=3600)
async def fetch_bucket_events(
    session: SessionDep,
    redis: RedisDep,
    bucket_name: str,
    cursor: str = Query(None, description="Cursor for pagination"),
    size: int = Query(10, description="Page size"),
) -> BucketEventsMixin:
    """
    Retrieve bucket with its events.
    :param bucket_name: Name of the bucket to fetch events for.
    :param session: Database session dependency.
    :param redis: Redis dependency for caching.
    :param cursor: Cursor for pagination - used in set_pagination.
    :param size: Pagination parameters - used in set_params
    :return: Bucket with its events.
    """
    bucket, events = await BucketService.get_bucket_with_events(session, bucket_name)

    return BucketEventsMixin(
        **BucketResponse.model_validate(bucket).model_dump(), events=events
    )


@router.get(
    "/{event_ID}",
    summary="Fetch Event by ID in a Bucket",
    description="Retrieve a specific event by its ID within a bucket.",
    response_model=EventResponse,
    dependencies=[
        Depends(check_alphanumeric_dash_underscore_path_params(["bucket_name"])),
    ],
    status_code=status.HTTP_200_OK,
)
@redis_cache("event:{bucket_name}:{event_ID}", ttl=3600)
async def fetch_event(
    bucket_name: str,
    event_ID: uuid.UUID,
    session: SessionDep,
    redis: RedisDep,
) -> EventResponse:
    """
    Retrieve a specific event by its ID within a bucket.
    :param bucket_name: Name of the bucket containing the event.
    :param event_ID: ID of the event to fetch.
    :param session: Database session dependency.
    :param redis: Redis dependency for caching.
    :return: Event details.
    """
    event = await EventService.get_event_in_bucket(session, bucket_name, event_ID)

    return EventResponse.model_validate(event)
