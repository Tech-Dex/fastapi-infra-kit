from typing import AsyncGenerator

from redis import asyncio as aioredis
from redis.asyncio import Redis

from app.core.config import settings

redis_client: aioredis.Redis = aioredis.from_url(
    settings.REDIS_URL,
    decode_responses=True,
)


async def get_redis() -> AsyncGenerator[Redis, None]:
    yield redis_client
