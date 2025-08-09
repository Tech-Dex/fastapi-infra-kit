import sys
import time
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional

from loguru import logger
from sqlalchemy import event
from sqlalchemy.exc import (DataError, DisconnectionError, IntegrityError,
                            OperationalError, SQLAlchemyError, TimeoutError)
from sqlalchemy.ext.asyncio import (AsyncSession, async_sessionmaker,
                                    create_async_engine)
from sqlalchemy.orm import declarative_base

from app.core.config import settings

logger_database = logger.bind(source="database")


class DatabaseConnectionError(Exception):
    """Raised when database connection fails"""

    pass


class DatabaseTransactionError(Exception):
    """Raised when database transaction fails"""

    pass


class DatabaseQueryError(Exception):
    """Raised when database query fails"""

    pass


def create_database_engine():
    """Create database engine with comprehensive error handling"""
    try:
        logger_database.info("Creating database engine")

        engine = create_async_engine(
            settings.DB_URL,
            pool_size=5,
            max_overflow=10,
            echo=False,
            pool_pre_ping=True,
            pool_recycle=3600,  # Recycle connections every hour
            pool_timeout=30,  # Timeout for getting connection from pool
        )

        logger_database.info("Database engine created successfully")
        return engine

    except Exception as e:
        logger_database.error(f"Failed to create database engine: {e}")
        raise DatabaseConnectionError(f"Failed to create database engine: {e}") from e


try:
    engine = create_database_engine()
except DatabaseConnectionError:
    logger_database.critical("Critical error: Could not initialize database engine")
    sys.exit(1)

AsyncSessionLocal = async_sessionmaker(
    autocommit=False, expire_on_commit=False, autoflush=False, bind=engine
)

Base = declarative_base()


@event.listens_for(engine.sync_engine, "before_cursor_execute")
def receive_before_cursor_execute(
    conn, cursor, statement, parameters, context, executemany
):
    """Log query start with error handling"""
    try:
        context._query_start_time = time.time()

        params_info = "No parameters"
        if parameters:
            if executemany:
                params_info = f"executemany: {len(parameters)} rows"
            else:
                params_str = str(parameters)
                if len(params_str) > 500:
                    params_info = f"{params_str[:500]}... (truncated)"
                else:
                    params_info = params_str

        sql_preview = statement[:200] + "..." if len(statement) > 200 else statement
        logger_database.debug(
            f"Database query started - SQL: {sql_preview} | Parameters: {params_info}"
        )

    except Exception as e:
        logger_database.warning(f"Error in before_cursor_execute handler: {e}")


@event.listens_for(engine.sync_engine, "after_cursor_execute")
def receive_after_cursor_execute(
    conn, cursor, statement, parameters, context, executemany
):
    """Log query completion with error handling"""
    try:
        total_time = time.time() - getattr(context, "_query_start_time", time.time())
        rowcount = getattr(cursor, "rowcount", -1)
        sql_preview = statement[:200] + "..." if len(statement) > 200 else statement

        if total_time > 10.0:  # Very slow query threshold
            logger_database.bind(sql_preview=sql_preview).error(
                f"VERY SLOW QUERY ({total_time:.4f}s) - Rows: {rowcount}"
            )
        elif total_time > 5.0:  # Slow query threshold
            logger_database.bind(sql_preview=sql_preview).warning(
                f"SLOW QUERY ({total_time:.4f}s) - Rows: {rowcount}"
            )
        else:
            logger_database.bind(sql_preview=sql_preview).info(
                f"Query completed ({total_time:.4f}s) - Rows: {rowcount}"
            )

    except Exception as e:
        logger_database.warning(f"Error in after_cursor_execute handler: {e}")


@event.listens_for(engine.sync_engine, "handle_error")
def receive_handle_error(exception_context):
    """Enhanced error handling with categorization"""
    try:
        original_exception = exception_context.original_exception
        error_type = type(original_exception).__name__
        sql = getattr(exception_context, "statement", "Unknown")
        params = str(getattr(exception_context, "parameters", "Unknown"))[:200]

        # Categorize errors for better handling
        if isinstance(original_exception, (DisconnectionError, OperationalError)):
            logger_database.error(
                f"DATABASE CONNECTION ERROR [{error_type}]: {original_exception}"
            )
        elif isinstance(original_exception, IntegrityError):
            logger_database.warning(
                f"DATABASE INTEGRITY ERROR [{error_type}]: {original_exception}"
            )
        elif isinstance(original_exception, DataError):
            logger_database.warning(
                f"DATABASE DATA ERROR [{error_type}]: {original_exception}"
            )
        elif isinstance(original_exception, TimeoutError):
            logger_database.error(
                f"DATABASE TIMEOUT ERROR [{error_type}]: {original_exception}"
            )
        else:
            logger_database.error(
                f"DATABASE ERROR [{error_type}]: {original_exception}"
            )

        logger_database.debug(f"Error details - SQL: {sql} | Parameters: {params}")

    except Exception as e:
        logger_database.critical(f"Critical error in database error handler: {e}")


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Enhanced database session generator with comprehensive error handling
    """
    session: Optional[AsyncSession] = None
    session_id = None

    try:
        session = AsyncSessionLocal()
        session_id = id(session)

        logger_database.debug(f"Database session created (ID: {session_id})")

        yield session

        try:
            await session.commit()
            logger_database.debug(
                f"Database transaction committed successfully (ID: {session_id})"
            )
        except IntegrityError as e:
            logger_database.warning(
                f"Database integrity error during commit (ID: {session_id}): {e}"
            )
            await session.rollback()
            raise DatabaseTransactionError(f"Integrity error: {e}") from e
        except Exception as e:
            logger_database.error(f"Database commit failed (ID: {session_id}): {e}")
            await session.rollback()
            raise DatabaseTransactionError(f"Commit failed: {e}") from e

    except SQLAlchemyError as e:
        if session:
            try:
                await session.rollback()
                logger_database.info(
                    f"Database transaction rolled back (ID: {session_id})"
                )
            except Exception as rollback_error:
                logger_database.error(
                    f"Failed to rollback transaction (ID: {session_id}): {rollback_error}"
                )

        # Handle specific SQLAlchemy errors
        if isinstance(e, DisconnectionError):
            logger_database.error(
                f"Database disconnection detected (ID: {session_id}): {e}"
            )
            raise DatabaseConnectionError(f"Database disconnected: {e}") from e
        elif isinstance(e, TimeoutError):
            logger_database.error(
                f"Database operation timed out (ID: {session_id}): {e}"
            )
            raise DatabaseQueryError(f"Query timeout: {e}") from e
        elif isinstance(e, OperationalError):
            logger_database.error(f"Database operational error (ID: {session_id}): {e}")
            raise DatabaseQueryError(f"Operational error: {e}") from e
        else:
            logger_database.error(f"Unexpected database error (ID: {session_id}): {e}")
            raise DatabaseQueryError(f"Database error: {e}") from e

    except Exception as e:
        if session:
            try:
                await session.rollback()
                logger_database.info(
                    f"Database transaction rolled back after unexpected error (ID: {session_id})"
                )
            except Exception as rollback_error:
                logger_database.critical(
                    f"Critical: Failed to rollback after unexpected error (ID: {session_id}): {rollback_error}"
                )

        logger_database.error(
            f"Unexpected error in database session (ID: {session_id}): {e}"
        )
        raise

    finally:
        if session:
            try:
                await session.close()
                logger_database.debug(f"Database session closed (ID: {session_id})")
            except Exception as e:
                logger_database.warning(
                    f"Error closing database session (ID: {session_id}): {e}"
                )


# Context manager for manual session handling
@asynccontextmanager
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Context manager for manual database session handling
    Use when you need more control over the session lifecycle
    Usage:
        async with get_db_session() as session:
            # Perform database operations with session
            ...
    """
    session_id = None
    async with AsyncSessionLocal() as session:
        session_id = id(session)
        try:
            logger_database.debug(f"Manual database session started (ID: {session_id})")
            yield session
        except Exception as e:
            logger_database.error(
                f"Error in manual database session (ID: {session_id}): {e}"
            )
            raise
        finally:
            logger_database.debug(f"Manual database session ended (ID: {session_id})")
