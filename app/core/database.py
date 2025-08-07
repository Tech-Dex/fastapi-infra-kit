from typing import AsyncGenerator

from sqlalchemy import event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
import time
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

engine = create_async_engine(
    settings.DB_URL,
    pool_size=5,
    max_overflow=10,
    echo=False,  # Disable SQL echo, custom logging is used
    pool_pre_ping=True,
)

AsyncSessionLocal = async_sessionmaker(
    autocommit=False, expire_on_commit=False, autoflush=False, bind=engine
)

Base = declarative_base()


@event.listens_for(engine.sync_engine, "before_cursor_execute")
def receive_before_cursor_execute(
    conn, cursor, statement, parameters, context, executemany
):
    context._query_start_time = time.time()
    logger.debug(
        "Database query started",
        sql=statement,
        parameters=parameters
        if not executemany
        else f"executemany: {len(parameters)} rows",
    )


@event.listens_for(engine.sync_engine, "after_cursor_execute")
def receive_after_cursor_execute(
    conn, cursor, statement, parameters, context, executemany
):
    total = time.time() - context._query_start_time
    logger.info(
        "Database query completed",
        sql=statement,
        query_time=total,
        rowcount=cursor.rowcount,
    )


@event.listens_for(engine.sync_engine, "handle_error")
def receive_handle_error(exception_context):
    logger.error(
        "Database error",
        error=str(exception_context.original_exception),
        error_type=type(exception_context.original_exception).__name__,
        sql=exception_context.statement,
        parameters=exception_context.parameters,
        exc_info=True,
    )


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            logger.error("Error in database session", exc_info=True)
            await session.rollback()
            raise e
        finally:
            await session.close()
