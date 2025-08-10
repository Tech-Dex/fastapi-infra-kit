import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.bucket_service import BucketService
from app.models.bucket import Bucket
from app.models.event import Event
from app.schemas.event import EventCreate
from app.exceptions.api_exceptions import NotFoundException


@pytest.mark.asyncio
@pytest.mark.unit
class TestBucketService:
    """Literally useless unit tests. Mock everything and test nothing."""

    async def test_get_all_buckets(self):
        session = AsyncMock(spec=AsyncSession)
        with patch('app.services.bucket_service.apaginate', new_callable=AsyncMock) as mock_apaginate:
            mock_apaginate.return_value = 'paginated_buckets'
            result = await BucketService.get_all_buckets(session)
            assert result == 'paginated_buckets'
            mock_apaginate.assert_awaited_once()

    async def test_get_bucket_by_name_found(self):
        session = AsyncMock(spec=AsyncSession)
        bucket = Bucket(name="test_bucket")
        mock_scalars = MagicMock()
        mock_scalars.one.return_value = bucket
        session.execute.return_value = MagicMock(scalars=MagicMock(return_value=mock_scalars))
        result = await BucketService.get_bucket_by_name(session, "test_bucket")
        assert result == bucket
        session.execute.assert_awaited_once()

    async def test_get_bucket_by_name_not_found(self):
        session = AsyncMock(spec=AsyncSession)
        mock_scalars = MagicMock()
        mock_scalars.one.side_effect = NotFoundException("Bucket not found")
        session.execute.return_value = MagicMock(scalars=MagicMock(return_value=mock_scalars))
        with pytest.raises(NotFoundException):
            await BucketService.get_bucket_by_name(session, "missing_bucket")

    async def test_create_bucket_with_event(self):
        session = AsyncMock(spec=AsyncSession)
        event_create = EventCreate(title="event1", message="msg")
        with patch('app.services.bucket_service.Bucket', autospec=True) as MockBucket, \
             patch('app.services.bucket_service.Event', autospec=True) as MockEvent:
            mock_bucket = MockBucket()
            mock_event = MockEvent()
            mock_bucket.events = MagicMock()
            mock_bucket.events.append = MagicMock()
            session.add = MagicMock()
            session.commit = AsyncMock()
            session.refresh = AsyncMock()

            with patch.object(BucketService, 'get_bucket_by_name', side_effect=NotFoundException("bucket")):
                result = await BucketService.create_bucket_with_event(session, "bucket1", event_create)
                assert isinstance(result, tuple)
                assert result[0] == mock_bucket
                assert result[1] == mock_event
                session.add.assert_called()
                session.commit.assert_awaited()
                session.refresh.assert_awaited()
                mock_bucket.events.append.assert_called_with(mock_event)
