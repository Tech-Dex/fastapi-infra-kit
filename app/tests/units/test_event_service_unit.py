import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.event_service import EventService
from app.models.event import Event
from app.exceptions.api_exceptions import NotFoundException
import uuid

@pytest.mark.asyncio
@pytest.mark.unit
class TestEventService:
    async def test_get_event_by_id_found(self):
        session = AsyncMock(spec=AsyncSession)
        event = Event(id=uuid.uuid4())
        mock_scalars = MagicMock()
        mock_scalars.one.return_value = event
        session.execute.return_value = MagicMock(scalars=MagicMock(return_value=mock_scalars))
        result = await EventService.get_event_by_id(session, event.id)
        assert result == event
        session.execute.assert_awaited_once()

    async def test_get_event_by_id_not_found(self):
        session = AsyncMock(spec=AsyncSession)
        mock_scalars = MagicMock()
        mock_scalars.one.side_effect = NotFoundException("Event not found")
        session.execute.return_value = MagicMock(scalars=MagicMock(return_value=mock_scalars))
        with pytest.raises(NotFoundException):
            await EventService.get_event_by_id(session, uuid.uuid4())

    async def test_get_event_in_bucket_found(self):
        session = AsyncMock(spec=AsyncSession)
        event = Event(id=uuid.uuid4())
        bucket = MagicMock(id=1)
        with patch('app.services.event_service.BucketService.get_bucket_by_name', return_value=bucket):
            mock_scalars = MagicMock()
            mock_scalars.one.return_value = event
            session.execute.return_value = MagicMock(scalars=MagicMock(return_value=mock_scalars))
            result = await EventService.get_event_in_bucket(session, "bucket1", event.id)
            assert result == event
            session.execute.assert_awaited()

    async def test_get_event_in_bucket_not_found(self):
        session = AsyncMock(spec=AsyncSession)
        bucket = MagicMock(id=1)
        with patch('app.services.event_service.BucketService.get_bucket_by_name', return_value=bucket):
            mock_scalars = MagicMock()
            mock_scalars.one.side_effect = NotFoundException("Event not found")
            session.execute.return_value = MagicMock(scalars=MagicMock(return_value=mock_scalars))
            with pytest.raises(NotFoundException):
                await EventService.get_event_in_bucket(session, "bucket1", uuid.uuid4())

    async def test_get_event_in_bucket_bucket_not_found(self):
        session = AsyncMock(spec=AsyncSession)
        with patch('app.services.event_service.BucketService.get_bucket_by_name', side_effect=NotFoundException("Bucket not found")):
            with pytest.raises(NotFoundException):
                await EventService.get_event_in_bucket(session, "bucket1", uuid.uuid4())

