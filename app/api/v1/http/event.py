import uuid

from fastapi import APIRouter, Depends

from app.schemas.bucket import BucketResponse
from app.schemas.event import EventResponse
from app.schemas.mixin import BucketEventsMixin
from app.services.bucket_service import BucketService
from app.services.deps import SessionDep, set_pagination
from app.services.event_service import EventService

router: APIRouter = APIRouter()


@router.get(
    "/",
    response_model=BucketEventsMixin,
    dependencies=[Depends(set_pagination(EventResponse))],
)
async def fetch_bucket_events(
    session: SessionDep,
    bucket_name: str,
) -> BucketEventsMixin:
    """
    Retrieve bucket with its events.
    :param bucket_name: Name of the bucket to fetch events for.
    :param session: Database session dependency.
    :param cursor: Cursor for pagination - used in set_pagination.
    :param params: Pagination parameters - used in set_pagination.
    :return: Bucket with its events.
    """
    bucket, events = await BucketService.get_bucket_with_events(session, bucket_name)

    return BucketEventsMixin(
        **BucketResponse.model_validate(bucket).model_dump(), events=events
    )


@router.get("/{event_ID}")
async def fetch_event(
    bucket_name: str,
    event_ID: uuid.UUID,
    session: SessionDep,
) -> EventResponse:
    """
    Retrieve a specific event by its ID within a bucket.
    :param bucket_name: Name of the bucket containing the event.
    :param event_ID: ID of the event to fetch.
    :param session: Database session dependency.
    :return: Event details.
    """
    event = await EventService.get_event_in_bucket(session, bucket_name, event_ID)
    return EventResponse.model_validate(event)
