import json
from datetime import timedelta
from enum import Enum
from functools import wraps
from typing import Callable, Optional, Union

from loguru import logger

logger_redis = logger.bind(name="redis")


class CacheInvalidationEvent(Enum):
    EVENT_CREATED = "event_created"
    EVENT_UPDATED = "event_updated"
    EVENT_DELETED = "event_deleted"
    BUCKET_UPDATED = "bucket_updated"


def redis_cache(
    key_template: str,
    ttl: Optional[Union[int, timedelta]] = None,
    serializer: str = "json",
):
    """
    Decorator for automatic Redis caching

    Args:
        key_template: Template for cache key, e.g., "bucket_events:{bucket_name}"
        ttl: Time to live for the cache entry
        serializer: Serialization method ("json" or "pickle")
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            redis = kwargs.get("redis")
            if not redis:
                return await func(*args, **kwargs)

            cache_key = key_template.format(**kwargs)

            # Try to get from cache
            cached_data = await redis.get(cache_key)
            if cached_data:
                logger_redis.info(f"Cache hit for key: {cache_key}")
                if serializer == "json":
                    return_type = func.__annotations__.get("return", dict)
                    if hasattr(return_type, "model_validate"):
                        return return_type.model_validate(json.loads(cached_data))

                    return json.loads(cached_data)

            result = await func(*args, **kwargs)

            if serializer == "json":
                if hasattr(result, "model_dump_json"):
                    cache_value = result.model_dump_json()
                else:
                    cache_value = json.dumps(result)

            if ttl:
                await redis.setex(cache_key, ttl, cache_value)
            else:
                await redis.set(cache_key, cache_value)

            return result

        return wrapper

    return decorator


def invalidate_cache(
    key_template: str,
    event: CacheInvalidationEvent,
    recursive: bool = False,
):
    """
    Decorator for cache invalidation

    Args:
        key_template: Template for cache key to invalidate
        event: Event that triggers the invalidation
        recursive: If True, invalidates all keys matching the pattern
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            redis = kwargs.get("redis")
            if not redis:
                return await func(*args, **kwargs)

            cache_key = key_template.format(**kwargs)

            if recursive:
                pattern = cache_key + "*"
                logger_redis.info(
                    f"Recursively invalidating cache for pattern: {pattern} due to event {event.value}"
                )
                async for key in redis.scan_iter(match=pattern):
                    await redis.delete(key)
            else:
                logger_redis.info(
                    f"Invalidating cache for key: {cache_key} due to event {event.value}"
                )
                await redis.delete(cache_key)

            return await func(*args, **kwargs)

        return wrapper

    return decorator
