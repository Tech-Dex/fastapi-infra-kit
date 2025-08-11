import pytest

from app.schemas.event import EventCreate


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.api
class TestFetchEventsInBucketIntegration:
    @pytest.fixture
    def default_path(self, sample_bucket_name_valid):
        return f"/v1/buckets/{sample_bucket_name_valid}/events"

    @pytest.fixture
    def default_invalid_path(self, sample_bucket_name_invalid):
        return f"/v1/buckets/{sample_bucket_name_invalid}/events"

    @pytest.fixture
    def buckets_path(self):
        return "/v1/buckets"

    @pytest.fixture
    def sample_bucket_name_valid(self):
        return "Test-Bucket_123"

    @pytest.fixture
    def sample_bucket_name_invalid(self):
        return "Test-Bucket@123"

    @pytest.fixture
    def sample_event_create(self):
        return EventCreate(title="New Event", message="New event message")

    async def test_fetch_events_in_bucket_empty(self, async_client, default_path):
        response = await async_client.get(default_path)
        response_data = response.json()
        assert response.status_code == 404
        assert response_data.get("error").get("message") == "Bucket not found"

    async def test_fetch_events_in_bucket_invalid_bucket(
        self,
        async_client,
        default_invalid_path,
        sample_bucket_name_invalid,
    ):
        response = await async_client.get(default_invalid_path)
        response_data = response.json()
        print(response_data)
        assert response.status_code == 422
        assert response_data.get("error").get("message") == (
            f"Invalid value for bucket_name: {sample_bucket_name_invalid}. Only alphanumeric characters, dashes, and underscores are allowed."
        )

    async def test_fetch_events_in_bucket(
        self,
        async_client,
        default_path,
        buckets_path,
        sample_bucket_name_valid,
        sample_event_create,
    ):
        response = await async_client.put(
            f"{buckets_path}/{sample_bucket_name_valid}",
            json=sample_event_create.model_dump(),
        )
        response_data = response.json()
        assert response.status_code == 201
        assert response_data.get("name") == sample_bucket_name_valid

        response = await async_client.get(default_path)
        response_data = response.json()
        assert response.status_code == 200
        assert response_data.get("name") == sample_bucket_name_valid
        assert response_data.get("events") is not None
        assert len(response_data.get("events").get("items")) == 1
        assert (
            response_data.get("events").get("items")[0].get("title")
            == sample_event_create.title
        )
        assert (
            response_data.get("events").get("items")[0].get("message")
            == sample_event_create.message
        )


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.api
class TestFetchEventInBucketIntegration:
    @pytest.fixture
    def default_path(self, sample_bucket_name_valid):
        return f"/v1/buckets/{sample_bucket_name_valid}/events"

    @pytest.fixture
    def buckets_path(self):
        return "/v1/buckets"

    @pytest.fixture
    def sample_bucket_name_valid(self):
        return "Test-Bucket_123"

    @pytest.fixture
    def sample_bucket_name_invalid(self):
        return "Test-Bucket@123"

    @pytest.fixture
    def sample_event_id_invalid(self):
        return "not-a-valid-uuid"

    @pytest.fixture
    def sample_event_id_valid_not_found(self):
        return "123e4567-e89b-12d3-a456-426614174000"

    @pytest.fixture
    def sample_event_create(self):
        return EventCreate(title="New Event", message="New event message")

    async def test_fetch_event_in_bucket_valid(
        self,
        async_client,
        default_path,
        buckets_path,
        sample_bucket_name_valid,
        sample_event_create,
    ):
        response = await async_client.put(
            f"{buckets_path}/{sample_bucket_name_valid}",
            json=sample_event_create.model_dump(),
        )

        response_data = response.json()

        response = await async_client.get(
            f"{default_path}/{response_data.get('event').get('id')}"
        )
        response_data = response.json()
        assert response.status_code == 200
        print(response_data)
        assert response_data.get("title") == sample_event_create.title
        assert response_data.get("message") == sample_event_create.message

    async def test_fetch_event_in_bucket_invalid_event_uuid(
        self,
        async_client,
        default_path,
        sample_event_create,
        sample_bucket_name_valid,
        sample_event_id_invalid,
    ):
        # Data was already created in previous test, no need to create it again

        response = await async_client.get(f"{default_path}/{sample_event_id_invalid}")
        response_data = response.json()
        assert response.status_code == 422
        assert response_data.get("error").get("message") == ("Validation failed")
        assert (
            response_data.get("error").get("details")[0].get("field")
            == "path -> event_ID"
        )
        assert (
            response_data.get("error").get("details")[0].get("type") == "uuid_parsing"
        )
        assert (
            response_data.get("error").get("details")[0].get("input")
            == sample_event_id_invalid
        )

    async def test_fetch_event_in_bucket_not_found_event(
        self, async_client, default_path, sample_event_id_valid_not_found
    ):
        response = await async_client.get(
            f"{default_path}/{sample_event_id_valid_not_found}"
        )
        response_data = response.json()
        assert response.status_code == 404
        assert response_data.get("error").get("message") == "Event not found"
