import pytest

from app.schemas.event import EventCreate


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.api
class TestCreateBucketIntegration:
    @pytest.fixture
    def default_path(self):
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

    @pytest.fixture
    def sample_detail_event_title_required(self):
        return {
            "field": "body -> title",
            "message": "Field required",
            "type": "missing",
            "input": {},
        }

    @pytest.fixture
    def sample_detail_event_message_required(self):
        return {
            "field": "body -> message",
            "message": "Field required",
            "type": "missing",
            "input": {},
        }

    @pytest.fixture
    def sample_detail_event_title_invalid(self):
        return {
            "field": "body -> title",
            "message": "Input should be a valid string",
            "type": "string_type",
            "input": 1,
        }

    @pytest.fixture
    def sample_detail_event_message_invalid(self):
        return {
            "field": "body -> message",
            "message": "Input should be a valid string",
            "type": "string_type",
            "input": 1,
        }

    @pytest.fixture
    def sample_body_invalid_type(self):
        return {
            "field": "body",
            "message": "Input should be a valid dictionary or object to extract fields from",
            "type": "model_attributes_type",
            "input": [],
        }

    async def test_create_bucket_with_event_accepts_valid_bucket_name(
        self, async_client, default_path, sample_bucket_name_valid, sample_event_create
    ):
        response = await async_client.put(
            f"{default_path}/{sample_bucket_name_valid}",
            json=sample_event_create.model_dump(),
        )
        response_data = response.json()
        assert response.status_code == 201
        assert response_data.get("name") == sample_bucket_name_valid

    async def test_create_bucket_with_event_rejects_invalid_bucket_name(
        self,
        async_client,
        default_path,
        sample_bucket_name_invalid,
        sample_event_create,
    ):
        response = await async_client.put(
            f"{default_path}/{sample_bucket_name_invalid}",
            json=sample_event_create.model_dump(),
        )
        response_data = response.json()
        assert response.status_code == 422
        assert response_data.get("error").get("message") == (
            f"Invalid value for bucket_name: {sample_bucket_name_invalid}. Only alphanumeric characters, dashes, and underscores are allowed."
        )

    async def test_create_bucket_with_event_rejects_empty_bucket_name(
        self, async_client, default_path, sample_event_create
    ):
        response = await async_client.put(
            f"{default_path}/", json=sample_event_create.model_dump()
        )
        response_data = response.json()
        assert response.status_code == 405
        assert response_data.get("error").get("message") == "Method not allowed"

    async def test_create_bucket_with_event_rejects_missing_body(
        self,
        async_client,
        default_path,
        sample_bucket_name_valid,
        sample_detail_event_title_required,
        sample_detail_event_message_required,
    ):
        response = await async_client.put(
            f"{default_path}/{sample_bucket_name_valid}", json={}
        )
        response_data = response.json()
        assert response.status_code == 422
        assert response_data.get("error").get("message") == "Validation failed"
        assert sample_detail_event_title_required in response_data["error"]["details"]
        assert sample_detail_event_message_required in response_data["error"]["details"]

    async def test_create_bucket_with_event_rejects_missing_title(
        self,
        async_client,
        default_path,
        sample_bucket_name_valid,
        sample_event_create,
        sample_detail_event_title_required,
    ):
        event_data = sample_event_create.model_dump()
        del event_data["title"]
        sample_detail_event_title_required["input"] = {"message": event_data["message"]}

        response = await async_client.put(
            f"{default_path}/{sample_bucket_name_valid}", json=event_data
        )
        response_data = response.json()
        assert response.status_code == 422
        assert response_data.get("error").get("message") == "Validation failed"
        assert sample_detail_event_title_required in response_data.get("error").get(
            "details"
        )

    async def test_create_bucket_with_event_rejects_missing_message(
        self,
        async_client,
        default_path,
        sample_bucket_name_valid,
        sample_event_create,
        sample_detail_event_message_required,
    ):
        event_data = sample_event_create.model_dump()
        del event_data["message"]
        sample_detail_event_message_required["input"] = {"title": event_data["title"]}

        response = await async_client.put(
            f"{default_path}/{sample_bucket_name_valid}", json=event_data
        )
        response_data = response.json()
        assert response.status_code == 422
        assert response_data.get("error").get("message") == "Validation failed"
        assert sample_detail_event_message_required in response_data.get("error").get(
            "details"
        )

    async def test_create_bucket_with_event_rejects_invalid_title(
        self,
        async_client,
        default_path,
        sample_bucket_name_valid,
        sample_event_create,
        sample_detail_event_title_invalid,
    ):
        event_data = sample_event_create.model_dump()
        event_data["title"] = 123
        sample_detail_event_title_invalid["input"] = event_data["title"]

        response = await async_client.put(
            f"{default_path}/{sample_bucket_name_valid}", json=event_data
        )
        response_data = response.json()
        assert response.status_code == 422
        assert response_data.get("error").get("message") == "Validation failed"
        assert sample_detail_event_title_invalid in response_data.get("error").get(
            "details"
        )

    async def test_create_bucket_with_event_rejects_invalid_message(
        self,
        async_client,
        default_path,
        sample_bucket_name_valid,
        sample_event_create,
        sample_detail_event_message_invalid,
    ):
        event_data = sample_event_create.model_dump()
        event_data["message"] = 123
        sample_detail_event_message_invalid["input"] = event_data["message"]

        response = await async_client.put(
            f"{default_path}/{sample_bucket_name_valid}", json=event_data
        )
        response_data = response.json()
        assert response.status_code == 422
        assert response_data.get("error").get("message") == "Validation failed"
        assert sample_detail_event_message_invalid in response_data.get("error").get(
            "details"
        )

    async def test_create_bucket_with_event_rejects_invalid_body(
        self,
        async_client,
        default_path,
        sample_bucket_name_valid,
        sample_event_create,
        sample_body_invalid_type,
    ):
        sample_body_invalid_type["input"] = "invalid body"
        response = await async_client.put(
            f"{default_path}/{sample_bucket_name_valid}", json="invalid body"
        )
        response_data = response.json()
        assert response.status_code == 422
        assert response_data.get("error").get("message") == "Validation failed"
        assert sample_body_invalid_type in response_data.get("error").get("details")


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.api
class TestFetchBucketIntegration:
    @pytest.fixture
    def sample_event_create(self):
        return EventCreate(title="New Event", message="New event message")

    @pytest.fixture
    def sample_bucket_name_valid(self):
        return "Test-Bucket_123"

    @pytest.fixture
    def default_path(self):
        return "/v1/buckets"

    async def test_fetch_buckets_empty(self, async_client, default_path):
        response = await async_client.get(f"{default_path}/")
        response_data = response.json()
        assert response.status_code == 200
        assert response_data.get("items") == []

    async def test_fetch_buckets_with_data(
        self, async_client, default_path, sample_bucket_name_valid, sample_event_create
    ):
        put_response = await async_client.put(
            f"{default_path}/{sample_bucket_name_valid}",
            json=sample_event_create.model_dump(),
        )
        assert put_response.status_code == 201

        response = await async_client.get(f"{default_path}/")
        response_data = response.json()
        assert response.status_code == 200
        assert any(
            bucket["name"] == sample_bucket_name_valid
            for bucket in response_data["items"]
        )
