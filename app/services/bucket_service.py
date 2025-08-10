from fastapi_pagination.cursor import CursorPage
from fastapi_pagination.ext.sqlalchemy import apaginate
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.exceptions.api_exceptions import NotFoundException
from app.exceptions.sqlalchemy_exception_handler import \
    sqlalchemy_exception_handler
from app.models.bucket import Bucket
from app.models.event import Event
from app.schemas.bucket import BucketResponse
from app.schemas.event import EventCreate, EventResponse


class BucketService:
    @staticmethod
    @sqlalchemy_exception_handler(resource_name="Buckets")
    async def get_all_buckets(session: AsyncSession) -> CursorPage[BucketResponse]:
        """
        Retrieve all buckets with pagination.

        :param session: Database session
        :return: Paginated list of buckets
        """
        return await apaginate(
            session,
            select(Bucket).order_by(Bucket.updated_at),
        )

    @staticmethod
    @sqlalchemy_exception_handler(resource_name="Bucket")
    async def get_bucket_by_name(session: AsyncSession, bucket_name: str) -> Bucket:
        """
        Retrieve a bucket by name.

        :param session: Database session
        :param bucket_name: Name of the bucket
        :return: Bucket object
        :raises BucketNotFoundException: If bucket is not found
        """
        result = await session.execute(
            select(Bucket)
            .options(selectinload(Bucket.events))
            .where(Bucket.name == bucket_name)
        )

        return result.scalars().one()

    @staticmethod
    @sqlalchemy_exception_handler(resource_name="Bucket")
    async def create_bucket_with_event(
        session: AsyncSession, name: str, event_create: EventCreate
    ) -> tuple[Bucket, Event]:
        """
        Create or update a bucket and add an event to it.

        :param session: Database session
        :param name: Bucket name
        :param event_create: Event data to add
        :return: Bucket with the newly created event
        """
        # Try to get existing bucket or create new one
        try:
            bucket = await BucketService.get_bucket_by_name(session, name)
        except NotFoundException:
            bucket = Bucket(name=name)
            session.add(bucket)

        event = Event(
            title=event_create.title,
            message=event_create.message,
        )
        bucket.events.append(event)

        await session.commit()
        await session.refresh(event)
        await session.refresh(event)

        return bucket, event

    @staticmethod
    @sqlalchemy_exception_handler(resource_name="Events")
    async def get_bucket_with_events(
        session: AsyncSession, bucket_name: str
    ) -> tuple[Bucket, CursorPage[EventResponse]]:
        """
        Get a bucket and its paginated events.

        :param session: Database session
        :param bucket_name: Name of the bucket
        :return: Tuple of (bucket, paginated_events)
        """
        bucket = await BucketService.get_bucket_by_name(session, bucket_name)

        events = await apaginate(
            session,
            select(Event)
            .where(Event.bucket_id == bucket.id)
            .order_by(Event.created_at),
        )

        return bucket, events
