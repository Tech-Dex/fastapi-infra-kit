# app/services/event_service.py
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions.sqlalchemy_exception_handler import \
    sqlalchemy_exception_handler
from app.models.event import Event
from app.services.bucket_service import BucketService


class EventService:
    @staticmethod
    @sqlalchemy_exception_handler(resource_name="Event")
    async def get_event_by_id(session: AsyncSession, event_id: uuid.UUID) -> Event:
        """
        Retrieve an event by its ID.

        :param session: Database session
        :param event_id: UUID of the event
        :return: Event object
        :raises EventNotFoundException: If event is not found
        """
        result = await session.execute(select(Event).where(Event.id == event_id))
        return result.scalars().one()

    @staticmethod
    @sqlalchemy_exception_handler(resource_name="Event")
    async def get_event_in_bucket(
        session: AsyncSession, bucket_name: str, event_id: uuid.UUID
    ) -> Event:
        """
        Retrieve an event by ID within a specific bucket.

        :param session: Database session
        :param bucket_name: Name of the bucket
        :param event_id: UUID of the event
        :return: Event object
        :raises BucketNotFoundException: If bucket is not found
        :raises EventNotFoundException: If event is not found
        """
        bucket = await BucketService.get_bucket_by_name(session, bucket_name)

        result = await session.execute(
            select(Event).where(Event.id == event_id, Event.bucket_id == bucket.id)
        )
        return result.scalars().one()
