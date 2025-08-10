import asyncio
from typing import AsyncGenerator, Generator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (AsyncEngine, AsyncSession,
                                    create_async_engine)
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
from testcontainers.postgres import PostgresContainer
from testcontainers.redis import RedisContainer

from app.core.database import Base, get_db
from app.core.redis import get_redis
from app.main import app
from redis import asyncio as aioredis



class DatabaseManager:
    """Manages database connections and cleanup properly"""

    def __init__(self):
        self.engine: AsyncEngine = None
        self.session_factory = None
        self.container: PostgresContainer = None

    async def setup(self, container: PostgresContainer):
        """Setup database engine and session factory"""
        self.container = container

        # Build the connection URL
        db_url = (
            f"postgresql+asyncpg://{container.username}:{container.password}"
            f"@{container.get_container_host_ip()}:{container.get_exposed_port(5432)}"
            f"/{container.dbname}"
        )

        # Create engine with proper configuration for testing
        self.engine = create_async_engine(
            db_url,
            echo=False,
            future=True,
            poolclass=NullPool,  # Use NullPool to avoid connection pooling issues
            connect_args={
                "server_settings": {
                    "application_name": "test_app",
                }
            },
        )

        # Create session factory
        self.session_factory = sessionmaker(
            bind=self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
            autocommit=False,
        )

        # Create tables
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def get_session(self) -> AsyncSession:
        """Get a new database session"""
        return self.session_factory()

    async def cleanup(self):
        """Properly cleanup database connections"""
        if self.engine:
            # Close all connections properly
            await self.engine.dispose()
            self.engine = None
        self.session_factory = None


class RedisManager:
    """Manages Redis container for integration tests"""

    def __init__(self):
        self.container: RedisContainer = None
        self.url = None

    async def setup(self):
        self.container = RedisContainer()
        self.container.start()
        self.url = f"redis://{self.container.get_container_host_ip()}:{self.container.get_exposed_port(6379)}/0"
        print(self.url)
        return self.container

    def get_url(self):
        return self.url

    async def teardown(self):
        if self.container:
            self.container.stop()
            self.container = None


@pytest_asyncio.fixture(scope="session")
async def redis_container():
    await redis_manager.setup()
    try:
        yield redis_manager.get_url()
    finally:
        await redis_manager.teardown()


# Global database manager instance
db_manager = DatabaseManager()
redis_manager = RedisManager()


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an instance of the default event loop for the test session."""
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        yield loop
    finally:
        # Ensure all tasks are completed before closing
        pending_tasks = [task for task in asyncio.all_tasks(loop) if not task.done()]
        if pending_tasks:
            loop.run_until_complete(
                asyncio.gather(*pending_tasks, return_exceptions=True)
            )
        loop.close()


@pytest.fixture(scope="session")
def postgres_container() -> Generator[PostgresContainer, None, None]:
    """Start PostgreSQL container for the test session."""
    container = PostgresContainer("postgres:16", driver="psycopg2").with_env(
        "POSTGRES_INITDB_ARGS", "--auth-host=md5"
    )

    container.start()

    try:
        yield container
    finally:
        container.stop()


@pytest_asyncio.fixture(scope="session")
async def setup_database(
    postgres_container: PostgresContainer,
) -> AsyncGenerator[DatabaseManager, None]:
    """Setup database for the test session."""
    await db_manager.setup(postgres_container)

    try:
        yield db_manager
    finally:
        await db_manager.cleanup()


@pytest_asyncio.fixture(scope="function")
async def db_session(
    setup_database: DatabaseManager,
) -> AsyncGenerator[AsyncSession, None]:
    """Create a database session for each test with proper transaction handling."""
    session = await setup_database.get_session()

    try:
        # Start a transaction
        await session.begin()
        yield session
    except Exception:
        # Rollback on any exception
        await session.rollback()
        raise
    else:
        # Rollback to ensure clean state for next test
        await session.rollback()
    finally:
        # Always close the session
        await session.close()


@pytest_asyncio.fixture
async def app_with_db(db_session: AsyncSession):
    """Create FastAPI app with overridden database dependency."""
    # Store original dependency
    original_get_db = app.dependency_overrides.get(get_db)

    # Override get_db to return our test session
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    try:
        yield app
    finally:
        # Restore original dependency
        if original_get_db:
            app.dependency_overrides[get_db] = original_get_db
        else:
            app.dependency_overrides.pop(get_db, None)

@pytest_asyncio.fixture
def app_with_db_and_redis(app_with_db, redis_container):
    """Override get_redis to use the test Redis container."""

    async def override_get_redis():
        client = aioredis.from_url(redis_container, decode_responses=True)
        yield client
        await client.aclose()

    app_with_db.dependency_overrides[get_redis] = override_get_redis
    try:
        yield app_with_db
    finally:
        app_with_db.dependency_overrides.pop(get_redis, None)


@pytest_asyncio.fixture
async def async_client(app_with_db_and_redis) -> AsyncGenerator[AsyncClient, None]:
    """Create async HTTP client with proper timeout and configuration."""
    timeout_config = {
        "timeout": 30.0,
        "connect": 5.0,
        "read": 10.0,
        "write": 5.0,
        "pool": 5.0,
    }

    async with AsyncClient(
        transport=ASGITransport(app=app_with_db_and_redis),
        base_url="http://testserver",
        timeout=timeout_config,
        follow_redirects=True,
    ) as client:
        yield client


# Alternative fixtures for different test scenarios

@pytest_asyncio.fixture
async def clean_redis(redis_container):
    """Flush all data in the test Redis before each test."""

    client = aioredis.from_url(redis_container, decode_responses=True)
    await client.flushall()
    yield client
    await client.close()


@pytest_asyncio.fixture
async def clean_db_session(
    setup_database: DatabaseManager,
) -> AsyncGenerator[AsyncSession, None]:
    """Create a clean database session that commits changes (for integration tests)."""
    session = await setup_database.get_session()

    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()


@pytest_asyncio.fixture
async def isolated_db_session(
    setup_database: DatabaseManager,
) -> AsyncGenerator[AsyncSession, None]:
    """Create an isolated database session with savepoints for nested transactions."""
    session = await setup_database.get_session()

    try:
        # Create a savepoint for isolation
        savepoint = await session.connection()
        trans = await savepoint.begin_nested()

        yield session

        # Rollback to savepoint
        await trans.rollback()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()


# Configuration for different test types


@pytest.fixture(autouse=True)
def configure_test_environment():
    """Configure test environment variables."""
    import os

    # Set test environment variables
    test_env = {
        "TESTING": "true",
        "LOG_LEVEL": "DEBUG",
        "DATABASE_URL": "",  # Will be overridden by fixtures
    }

    # Store original values
    original_env = {}
    for key, value in test_env.items():
        original_env[key] = os.environ.get(key)
        os.environ[key] = value

    yield

    # Restore original environment
    for key, value in original_env.items():
        if value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = value


# Markers and test collection configuration


def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line("markers", "slow: marks tests as slow")
    config.addinivalue_line("markers", "integration: marks tests as integration tests")
    config.addinivalue_line("markers", "unit: marks tests as unit tests")
    config.addinivalue_line("markers", "database: marks tests that require database")
    config.addinivalue_line("markers", "api: marks tests for API endpoints")


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers automatically."""
    for item in items:
        # Add integration marker to tests using database fixtures
        if any(
            fixture in item.fixturenames
            for fixture in ["db_session", "async_client", "setup_database"]
        ):
            item.add_marker(pytest.mark.integration)

        # Add database marker to tests using database
        if any(
            fixture in item.fixturenames
            for fixture in ["db_session", "clean_db_session", "isolated_db_session"]
        ):
            item.add_marker(pytest.mark.database)

        # Add API marker to tests using async_client
        if "async_client" in item.fixturenames:
            item.add_marker(pytest.mark.api)


class AsyncTestHelper:
    """Helper class for async testing utilities."""

    @staticmethod
    async def wait_for_condition(condition, timeout=5.0, interval=0.1):
        """Wait for a condition to become true."""
        import asyncio
        import time

        start_time = time.time()
        while time.time() - start_time < timeout:
            if (
                await condition()
                if asyncio.iscoroutinefunction(condition)
                else condition()
            ):
                return True
            await asyncio.sleep(interval)
        return False

    @staticmethod
    async def run_with_timeout(coro, timeout=10.0):
        """Run a coroutine with a timeout."""
        return await asyncio.wait_for(coro, timeout=timeout)


@pytest.fixture
def async_test_helper():
    """Provide async test helper utilities."""
    return AsyncTestHelper()
