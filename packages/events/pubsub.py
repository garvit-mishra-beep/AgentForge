"""
Redis Pub/Sub abstraction for AgentOS.

Provides pub/sub abstraction over Redis for event broadcasting.
"""

import asyncio
import json
import logging
import uuid
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Set

import redis.asyncio as redis
from redis.asyncio.client import PubSub

from apps.api.core.config import settings
from apps.api.core.redis import get_redis
from apps.api.core.logging import get_structlog_logger

logger = get_structlog_logger(__name__)


# ===============================
# CHANNEL TYPES
# ===============================


class ChannelType(str):
    """
    Channel type constants.
    """

    WORKFLOW_EVENTS = "workflow_events"
    TASK_EVENTS = "task_events"
    PROVIDER_EVENTS = "provider_events"
    ESCALATION_EVENTS = "escalation_events"
    SYSTEM_EVENTS = "system_events"
    METRIC_EVENTS = "metric_events"


# ===============================
# EVENT DATA STRUCT
# ===============================


def create_event_data(
    event_type: str,
    workflow_id: str,
    data: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Create event data structure.

    Args:
        event_type: Event type
        workflow_id: Workflow ID
        data: Event data

    Returns:
        Event data dictionary
    """
    return {
        "event_type": event_type,
        "workflow_id": workflow_id,
        "timestamp": datetime.utcnow().isoformat(),
        "data": data or {},
    }


# ===============================
# PUB/SUB CHANNEL MANAGER
# ===============================


class PubSubChannelManager:
    """
    Redis Pub/Sub channel manager.
    """

    def __init__(
        self,
        redis_client: Optional[redis.Redis] = None,
    ):
        """
        Initialize channel manager.

        Args:
            redis_client: Redis client instance
        """
        self.client = redis_client or get_redis()
        self._pubsubs: Dict[str, PubSub] = {}
        self._subscribers: Dict[str, Set[str]] = {}
        self._callbacks: Dict[str, List[Callable]] = {}
        self._running: bool = False
        self._message_handlers: Dict[str, Callable] = {}

    async def start(self) -> None:
        """
        Start channel manager.
        """
        self._running = True
        logger.info("PubSub channel manager started")

    async def shutdown(self) -> None:
        """
        Shutdown channel manager.
        """
        self._running = False

        # Close all pubsubs
        for pubsub in self._pubsubs.values():
            await pubsub.close()

        self._pubsubs.clear()
        self._subscribers.clear()
        self._callbacks.clear()

        logger.info("PubSub channel manager shutdown")

    async def connect(
        self,
        channel_name: str,
        channel_type: Optional[str] = None,
    ) -> PubSub:
        """
        Connect to channel.

        Args:
            channel_name: Channel name
            channel_type: Channel type

        Returns:
            PubSub instance
        """
        # Create channel name
        if channel_type:
            full_channel = f"{channel_type}:{channel_name}"
        else:
            full_channel = channel_name

        # Connect
        pubsub = await self.client.publish_subscribe()
        await pubsub.psubscribe(full_channel)

        # Register pubsub
        self._pubsubs[full_channel] = pubsub
        self._subscribers[full_channel] = set()

        logger.info(
            "Connected to channel",
            channel=full_channel,
        )

        return pubsub

    async def disconnect(
        self,
        channel_name: str,
        channel_type: Optional[str] = None,
    ) -> None:
        """
        Disconnect from channel.

        Args:
            channel_name: Channel name
            channel_type: Channel type
        """
        if channel_type:
            full_channel = f"{channel_type}:{channel_name}"
        else:
            full_channel = channel_name

        if full_channel in self._pubsubs:
            await self._pubsubs[full_channel].unsubscribe(full_channel)
            await self._pubsubs[full_channel].close()
            del self._pubsubs[full_channel]
            self._subscribers.pop(full_channel, None)

        logger.info(
            "Disconnected from channel",
            channel=full_channel,
        )

    async def subscribe(
        self,
        channel_name: str,
        channel_type: Optional[str] = None,
        subscribers: Optional[Set[str]] = None,
    ) -> None:
        """
        Subscribe to channel.

        Args:
            channel_name: Channel name
            channel_type: Channel type
            subscribers: Set of subscriber IDs
        """
        if channel_type:
            full_channel = f"{channel_type}:{channel_name}"
        else:
            full_channel = channel_name

        if full_channel not in self._pubsubs:
            pubsub = await self.client.publish_subscribe()
            await pubsub.psubscribe(full_channel)
            self._pubsubs[full_channel] = pubsub

        if subscribers:
            self._subscribers[full_channel].update(subscribers)

        logger.info(
            "Subscribed to channel",
            channel=full_channel,
            subscribers=subscribers,
        )

    async def unsubscribe(
        self,
        channel_name: str,
        channel_type: Optional[str] = None,
    ) -> None:
        """
        Unsubscribe from channel.

        Args:
            channel_name: Channel name
            channel_type: Channel type
        """
        if channel_type:
            full_channel = f"{channel_type}:{channel_name}"
        else:
            full_channel = channel_name

        await self.disconnect(channel_name, channel_type)

    async def publish(
        self,
        channel_name: str,
        channel_type: Optional[str] = None,
        message: Optional[Dict[str, Any]] = None,
        exclude_client: Optional[str] = None,
    ) -> int:
        """
        Publish message to channel.

        Args:
            channel_name: Channel name
            channel_type: Channel type
            message: Message to publish
            exclude_client: Client to exclude

        Returns:
            Number of subscribers
        """
        if channel_type:
            full_channel = f"{channel_type}:{channel_name}"
        else:
            full_channel = channel_name

        # Check if we're subscribed
        if full_channel not in self._pubsubs:
            return 0

        # Publish using pubsub
        try:
            await self._pubsubs[full_channel].publish(json.dumps(message))
            return len(self._subscribers.get(full_channel, set()))
        except Exception as e:
            logger.error(f"Publish error: {e}")
            return 0

    def register_callback(
        self,
        channel_name: str,
        channel_type: Optional[str] = None,
        callback: Callable = lambda msg: None,
    ) -> None:
        """
        Register message callback.

        Args:
            channel_name: Channel name
            channel_type: Channel type
            callback: Callback function
        """
        if channel_type:
            full_channel = f"{channel_type}:{channel_name}"
        else:
            full_channel = channel_name

        if full_channel not in self._callbacks:
            self._callbacks[full_channel] = []

        self._callbacks[full_channel].append(callback)

        logger.info(
            "Registered callback",
            channel=full_channel,
            callback_id=id(callback),
        )

    async def handle_message(
        self,
        pubsub: PubSub,
        message: dict,
    ) -> None:
        """
        Handle received message.

        Args:
            pubsub: PubSub instance
            message: Received message
        """
        channel = pubsub.channels[0] if pubsub.channels else ""

        # Find callbacks for this channel
        callbacks = self._callbacks.get(channel, [])

        if callbacks:
            try:
                message_data = json.loads(message)

                for callback in callbacks:
                    try:
                        await callback(message_data)
                    except Exception as e:
                        logger.error(f"Callback error: {e}")
            except Exception as e:
                logger.error(f"Message handle error: {e}")

    async def on_message(self, callback: Callable) -> None:
        """
        Register message callback.

        Args:
            callback: Callback function
        """
        # Find all channels and subscribe
        for channel in list(self._pubsubs.keys()):
            await self._pubsubs[channel].psubscribe(channel)
            self._pubsubs[channel].pmessage(
                channel,
                lambda msg: asyncio.create_task(self.handle_message(self._pubsubs[channel], msg))
            )

    async def _message_handler(self, pubsub: PubSub, message: dict) -> None:
        """
        Internal message handler.
        """
        # Decode message
        try:
            message_data = json.loads(message)
        except Exception:
            return

        # Log message
        logger.debug(
            "Message received",
            channel=message_data.get("channel", ""),
            event_type=message_data.get("event_type", ""),
        )

        # Find callbacks for this channel
        channel = pubsub.channels[0] if pubsub.channels else ""
        callbacks = self._callbacks.get(channel, [])

        for callback in callbacks:
            try:
                await callback(message_data)
            except Exception as e:
                logger.error(f"Callback error: {e}")

    async def get_subscriber_count(
        self,
        channel_name: str,
        channel_type: Optional[str] = None,
    ) -> int:
        """
        Get subscriber count for channel.

        Args:
            channel_name: Channel name
            channel_type: Channel type

        Returns:
            Number of subscribers
        """
        if channel_type:
            full_channel = f"{channel_type}:{channel_name}"
        else:
            full_channel = channel_name

        return len(self._subscribers.get(full_channel, set()))

    async def list_channels(
        self,
    ) -> List[str]:
        """
        List all channels.

        Returns:
            List of channel names
        """
        return list(self._pubsubs.keys())

    async def list_subscribers(
        self,
        channel_name: str,
        channel_type: Optional[str] = None,
    ) -> Set[str]:
        """
        List subscribers for channel.

        Args:
            channel_name: Channel name
            channel_type: Channel type

        Returns:
            Set of subscriber IDs
        """
        if channel_type:
            full_channel = f"{channel_type}:{channel_name}"
        else:
            full_channel = channel_name

        return self._subscribers.get(full_channel, set())

    async def close(self) -> None:
        """
        Close channel manager.
        """
        await self.shutdown()


# ===============================
# GLOBAL PUB/SUB MANAGER
# ===============================


_pubsub_manager: Optional[PubSubChannelManager] = None


def get_pubsub_manager() -> PubSubChannelManager:
    """
    Get or create global pub/sub manager.

    Returns:
        PubSubChannelManager instance
    """
    global _pubsub_manager

    if _pubsub_manager is None:
        _pubsub_manager = PubSubChannelManager()

    return _pubsub_manager
