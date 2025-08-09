from fastapi import APIRouter, Depends, Query
from fastapi_pagination.cursor import CursorPage
from starlette import status

from app.schemas.bucket import BucketResponse
from app.schemas.event import EventCreate
from app.schemas.mixin import BucketEventMixin
from app.services.bucket_service import BucketService
from app.services.deps import (RedisDep, SessionDep,
                               check_alphanumeric_dash_underscore_path_params,
                               set_pagination)
from app.services.redis_service import (CacheInvalidationEvent,
                                        invalidate_cache, redis_cache)

router: APIRouter = APIRouter()


@router.get(
    "/",
    name="Fetch All Buckets",
    description="Fetch all buckets with pagination support. The response is paginated using cursor-based pagination.",
    response_model=CursorPage[BucketResponse],
    dependencies=[Depends(set_pagination(BucketResponse))],
    status_code=status.HTTP_200_OK,
)
@redis_cache("buckets:cursor={cursor}:size={size}", ttl=3600)
async def fetch_buckets(
    session: SessionDep,
    redis: RedisDep,
    cursor: str = Query(None, description="Cursor for pagination"),
    size: int = Query(10, description="Page size"),
) -> CursorPage[BucketResponse]:
    """
    Retrieve all buckets.

    :param session: Database session dependency.
    :param redis: Redis dependency for caching.
    :param cursor: Cursor for pagination - used in set_pagination.
    :param size: Pagination parameters - used in set_params.
    :return: List of all buckets.
    """
    return await BucketService.get_all_buckets(session)


@router.put(
    "/{bucket_name}",
    name="Send Event to Bucket",
    description="Send event to bucket. The bucket name must be alphanumeric, dash, or underscore. Creates the bucket if it does not exist.",
    status_code=status.HTTP_201_CREATED,
    dependencies=[
        Depends(check_alphanumeric_dash_underscore_path_params(["bucket_name"]))
    ],
)
@invalidate_cache(
    "bucket_events:{bucket_name}", CacheInvalidationEvent.EVENT_UPDATED, recursive=True
)
@invalidate_cache("buckets", CacheInvalidationEvent.EVENT_CREATED, recursive=True)
async def send_event_to_bucket(
    bucket_name: str, event: EventCreate, session: SessionDep, redis: RedisDep
) -> BucketEventMixin:
    """
    Send an event to a specific bucket.

    :param session: Database session dependency.
    :param redis: Redis dependency for caching.
    :param bucket_name: The name of the bucket, which must be alphanumeric, dash, or underscore.
    :param event: The event data to be sent to the bucket.
    """
    return await BucketService.create_bucket_with_event(session, bucket_name, event)
