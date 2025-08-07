from fastapi import APIRouter, Depends

from app.models.event import Event
from app.schemas.event import EventCreate, EventResponse
from app.services.deps import SessionDep, check_alphanumeric_dash_underscore_path_params
from app.models.bucket import Bucket

router: APIRouter = APIRouter()


@router.put(
    "/{name}",
    dependencies=[Depends(check_alphanumeric_dash_underscore_path_params(["name"]))],
)
async def send_event_to_bucket(name: str, event: EventCreate, session: SessionDep):
    """
    Send an event to a specific bucket.

    :param session: Database session dependency.
    :param name: The name of the bucket, which must be alphanumeric, dash, or underscore.
    :param event: The event data to be sent to the bucket.
    :param bucket_service: Dependency for bucket service.
    """
    bucket = Bucket(name=name)
    session.add(bucket)

    event_orm = Event(
        title=event.title,
        message=event.message,
    )
    bucket.events.append(event_orm)

    await session.commit()
    await session.refresh(bucket)
    await session.refresh(event_orm)

    resp = EventResponse.model_validate(event_orm)

    return {
        "message": f"Event sent to bucket '{name}'",
        "bucket": bucket,
        "event": resp,
    }
