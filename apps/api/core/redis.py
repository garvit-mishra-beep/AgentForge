"""
Redis client configuration for AgentOS API.

Async Redis setup with connection pooling and pub/sub support.
"""

import logging
from typing import Any

import redis.asyncio as redis
from redis.asyncio import Redis
from redis.exceptions import RedisError

from apps.api.core.config import settings

logger = logging.getLogger(__name__)


# ===============================
# REDIS CLIENT FACTORY
# ===============================


def create_redis_client() -> Redis:
    """
    Create async Redis client with pool settings.

    Returns:
        Redis: Async Redis client instance
    """
    try:
        pool = redis.ConnectionPool.from_url(
            settings.REDIS_URL,
            db=settings.REDIS_DB,
            max_connections=settings.REDIS_MAX_CONNECTIONS,
            socket_timeout=settings.REDIS_SOCKET_TIMEOUT,
            retry_on_timeout=settings.REDIS_RETRY_ON_TIMEOUT,
        )

        client = redis.Redis(connection_pool=pool, db=settings.REDIS_DB)
        logger.info(f"Redis client connected to {settings.REDIS_URL}")

        return client

    except RedisError as e:
        logger.error(f"Failed to connect to Redis: {e}")
        raise


# ===============================
# GLOBAL REDIS CLIENT
# ===============================

redis_pool: Redis = create_redis_client()


async def get_redis() -> Redis:
    """
    Get or create global Redis client.

    Returns:
        Redis: Connected Redis client

    Raises:
        ConnectionError: If Redis connection fails
    """
    global redis_pool

    if redis_pool is None:
        redis_pool = create_redis_client()

    try:
        await redis_pool.ping()
        logger.debug("Redis connection verified")
    except RedisError as e:
        logger.error(f"Redis ping failed: {e}")
        raise

    return redis_pool


async def close_redis() -> None:
    """
    Close Redis client connection.
    """
    global redis_pool

    if redis_pool:
        try:
            await redis_pool.close()
            logger.info("Redis connection closed")
        except Exception as e:
            logger.warning(f"Error closing Redis connection: {e}")
        finally:
            redis_pool = None


# ===============================
# PUB/SUB HELPER
# ===============================


class RedisPubSub:
    """
    Redis Pub/Sub wrapper for event broadcasting.
    """

    def __init__(self, client: Redis):
        """
        Initialize pub/sub wrapper.

        Args:
            client: Redis client instance
        """
        self.client = client
        self.pubsub = None

    async def connect(self, channel: str) -> None:
        """
        Connect to pub/sub channel.

        Args:
            channel: Channel name to subscribe to
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
            logger.debug(f"Subscribed to channels: {', '.join(channels)}")

    async def unsubscribe(self, *channels: str) -> None:
        """
        Unsubscribe from channels.

        Args:
            *channels: Channel names
        """
        if self.pubsub:
            await self.pubsub.unsubscribe(*channels)

    async def publish(self, channel: str, message: Any) -> int:
        """
        Publish message to channel.

        Args:
            channel: Channel name
            message: Message to publish

        Returns:
            Number of subscribers who received the message
        """
        if self.pubsub:
            return await self.pubsub.publish(channel, message)
        return 0

    async def publish_raw(self, channel: str, message: Any) -> int:
        """
        Publish raw message to channel using Redis client directly.

        Args:
            channel: Channel name
            message: Message to publish

        Returns:
            Number of subscribers who received the message
        """
        if self.pubsub:
            await self.pubsub.subscribe(channel)
            return await self.pubsub.publish(channel, message)
        return 0

    async def on_message(self, channel: str, callback):
        """
        Register message callback.

        Args:
            channel: Channel pattern prefix
            callback: Async callback function for messages
        """
        if self.pubsub:
            await self.pubsub.psubscribe(
                f"{channel}:*",
                callback=self._on_message,
                callback_pattern=lambda msg: callback(msg.decode())
            )

    def _on_message(self, payload: bytes, pattern: str, channel: str, data: bytes):
        """Internal message handler."""
        if self.pubsub:
            self.pubsub.publish(self.pubsub.channels[0], data.decode())

    async def disconnect(self) -> None:
        """Disconnect from pub/sub."""
        if self.pubsub:
            await self.pubsub.unsubscribe()
            self.pubsub = None

    async def close(self) -> None:
        """Close pub/sub wrapper."""
        await self.disconnect()