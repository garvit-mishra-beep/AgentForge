"""
Redis dependencies.

Provides Redis client dependencies for route handlers.
"""

import logging
from typing import AsyncGenerator

from redis.asyncio import Redis
import redis.asyncio as redis

from apps.api.core.config import settings
from apps.api.core.redis import create_redis_client, close_redis, redis_pool

logger = logging.getLogger(__name__)


# ===============================
# REDIS DEPENDENCIES
# ===============================


async def get_redis() -> AsyncGenerator[Redis, None]:
    """
    Get Redis client from pool.

    Yields:
        Redis: Connected Redis client
    """
    if redis_pool is None:
        redis_pool = create_redis_client()

    try:
        yield redis_pool
    except Exception as e:
        logger.error(f"Redis error: {e}")
        raise
    finally:
        await close_redis()


# ===============================
# PUB/SUB DEPENDENCY
# ===============================


class RedisPubSub:
    """
    Redis Pub/Sub wrapper.
    """

    def __init__(self, client: Redis):
        """
        Initialize pub/sub wrapper.

        Args:
            client: Redis client
        """
        self.client = client
        self.pubsub = None

    async def connect(self, channel: str) -> None:
        """
        Connect to pub/sub channel.

        Args:
            channel: Channel name
        """
        self.pubsub = await self.client.publish_subscribe()

    async def subscribe(self, *channels: str) -> None:
        """
        Subscribe to channels.

        Args:
            *channels: Channel names
        """
        if self.pubsub:
            await self.pubsub.subscribe(*channels)

    async def unsubscribe(self, *channels: str) -> None:
        """
        Unsubscribe from channels.

        Args:
            *channels: Channel names
        """
        if self.pubsub:
            await self.pubsub.unsubscribe(*channels)

    async def publish(self, channel: str, message) -> int:
        """
        Publish message to channel.

        Args:
            channel: Channel name
            message: Message to publish

        Returns:
            Number of subscribers
        """
        if self.pubsub:
            return await self.pubsub.publish(channel, message)
        return 0

    async def disconnect(self) -> None:
        """Disconnect from pub/sub."""
        if self.pubsub:
            await self.pubsub.unsubscribe()
            self.pubsub = None


async def get_pubsub() -> AsyncGenerator[RedisPubSub, None]:
    """
    Get Redis pub/sub instance.

    Yields:
        RedisPubSub: Pub/sub wrapper
    """
    redis_client = await get_redis()
    pubsub = RedisPubSub(redis_client)

    try:
        yield pubsub
    finally:
        await pubsub.disconnect()
