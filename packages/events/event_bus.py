"""
Internal event bus for AgentOS.

Implements internal event routing and publishing.
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Set

from apps.api.core.config import settings

logger = logging.getLogger(__name__)


# ===============================
# EVENT TYPES
# ===============================


class EventType(str):
    """
    Event type constants.
    """

    # Workflow events
    WORKFLOW_CREATED = "workflow.created"
    WORKFLOW_STARTED = "workflow.started"
    WORKFLOW_COMPLETED = "workflow.completed"
    WORKFLOW_FAILED = "workflow.failed"
    WORKFLOW_CANCELLED = "workflow.cancelled"
    WORKFLOW_ESCALATED = "workflow.escalated"

    # Task events
    TASK_STARTED = "task.started"
    TASK_COMPLETED = "task.completed"
    TASK_FAILED = "task.failed"
    TASK_ESCALATED = "task.escalated"

    # Provider events
    PROVIDER_REQUEST = "provider.request"
    PROVIDER_RESPONSE = "provider.response"
    PROVIDER_ERROR = "provider.error"
    PROVIDER_TIMEOUT = "provider.timeout"

    # Retry events
    RETRY_STARTED = "retry.started"
    RETRY_COMPLETED = "retry.completed"
    RETRY_FAILED = "retry.failed"
    RETRY_EXHAUSTED = "retry.exhausted"

    # Escalation events
    ESCALATION_STARTED = "escalation.started"
    ESCALATION_COMPLETED = "escalation.completed"
    ESCALATION_FAILED = "escalation.failed"

    # System events
    HEARTBEAT = "heartbeat"
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    ERROR = "error"
    INFO = "info"
    WARNING = "warning"


# ===============================
# EVENT STRUCTURE
# ===============================


class Event:
    """
    Event structure.
    """

    def __init__(
        self,
        event_type: str,
        workflow_id: str,
        data: Optional[Dict[str, Any]] = None,
        source: Optional[str] = None,
    ):
        """
        Initialize event.

        Args:
            event_type: Event type string
            workflow_id: Workflow ID
            data: Event data
            source: Event source
        """
        self.event_type = event_type
        self.workflow_id = workflow_id
        self.data = data or {}
        self.source = source or "system"
        self.timestamp = datetime.utcnow().isoformat()
        self.id = f"evt-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"


# ===============================
# EVENT BUS
# ===============================


class EventBus:
    """
    Event bus for internal event routing.
    """

    def __init__(
        self,
        name: str = "default",
        queue_size: int = 1000,
    ):
        """
        Initialize event bus.

        Args:
            name: Bus name
            queue_size: Message queue size
        """
        self.name = name
        self.queue_size = queue_size

        # Event subscribers: event_type -> list of callbacks
        self._subscribers: Dict[str, List[Callable]] = {}

        # Event history: workflow_id -> list of events
        self._history: Dict[str, List[Dict]] = {}

        # Running flag
        self._running: bool = False

        # Metrics
        self._events_published: int = 0
        self._events_subscribed: int = 0
        self._errors: int = 0

    async def publish(
        self,
        event_type: str,
        workflow_id: str,
        data: Optional[Dict[str, Any]] = None,
        source: Optional[str] = None,
    ) -> bool:
        """
        Publish event to subscribers.

        Args:
            event_type: Event type
            workflow_id: Workflow ID
            data: Event data
            source: Event source

        Returns:
            True if published
        """
        # Create event
        event = Event(event_type, workflow_id, data, source)

        # Add to history
        if workflow_id not in self._history:
            self._history[workflow_id] = []

        self._history[workflow_id].append({
            "event": event,
            "timestamp": datetime.utcnow().isoformat(),
        })

        # Keep only last 1000 events
        if len(self._history.get(workflow_id, [])) > self.queue_size:
            self._history[workflow_id] = self._history[workflow_id][-self.queue_size:]

        # Notify subscribers
        subscribers = self._subscribers.get(event_type, [])

        if subscribers:
            for subscriber in subscribers:
                try:
                    await subscriber(event)
                except Exception as e:
                    logger.error(f"Event handler error: {e}")
                    self._errors += 1

        # Increment metrics
        self._events_published += 1

        return True

    def subscribe(
        self,
        event_type: str,
        callback: Callable,
    ) -> bool:
        """
        Subscribe to event type.

        Args:
            event_type: Event type to subscribe to
            callback: Async callback function

        Returns:
            True if subscribed
        """
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []

        if callback not in self._subscribers[event_type]:
            self._subscribers[event_type].append(callback)
            self._events_subscribed += 1

        logger.info(
            "Subscribed to event",
            event_type=event_type,
            callback_id=id(callback),
        )

        return True

    def unsubscribe(
        self,
        event_type: str,
        callback: Callable,
    ) -> bool:
        """
        Unsubscribe from event type.

        Args:
            event_type: Event type
            callback: Callback to remove

        Returns:
            True if unsubscribed
        """
        if event_type in self._subscribers:
            self._subscribers[event_type].remove(callback)
            logger.info(
                "Unsubscribed from event",
                event_type=event_type,
                callback_id=id(callback),
            )
            return True

        return False

    def get_history(
        self,
        workflow_id: str,
        limit: Optional[int] = None,
    ) -> List[Dict]:
        """
        Get event history.

        Args:
            workflow_id: Workflow ID
            limit: Limit number of events

        Returns:
            List of events
        """
        history = self._history.get(workflow_id, [])

        if limit:
            history = history[-limit:]

        return history

    def clear_history(
        self,
        workflow_id: Optional[str] = None,
    ) -> None:
        """
        Clear event history.

        Args:
            workflow_id: Workflow ID (None to clear all)
        """
        if workflow_id:
            self._history.pop(workflow_id, None)
        else:
            self._history.clear()

    def get_metrics(
        self,
    ) -> Dict[str, Any]:
        """
        Get bus metrics.

        Returns:
            Metrics dictionary
        """
        return {
            "name": self.name,
            "events_published": self._events_published,
            "events_subscribed": self._events_subscribed,
            "errors": self._errors,
            "subscribers_count": sum(
                len(s) for s in self._subscribers.values()
            ),
        }


# ===============================
# GLOBAL EVENT BUS
# ===============================


_event_bus: Optional[EventBus] = None


def get_event_bus(
    name: Optional[str] = None,
) -> EventBus:
    """
    Get or create global event bus.

    Args:
        name: Bus name

    Returns:
        EventBus instance
    """
    global _event_bus

    if _event_bus is None:
        _event_bus = EventBus(name or "default")

    return _event_bus


def publish_event(
    event_type: str,
    workflow_id: str,
    data: Optional[Dict[str, Any]] = None,
) -> bool:
    """
    Publish event using global event bus.

    Args:
        event_type: Event type
        workflow_id: Workflow ID
        data: Event data

    Returns:
        True if published
    """
    bus = get_event_bus()
    return bus.publish(event_type, workflow_id, data)


def subscribe_to_event(
    event_type: str,
    callback: Callable,
) -> bool:
    """
    Subscribe to event using global event bus.

    Args:
        event_type: Event type
        callback: Callback function

    Returns:
        True if subscribed
    """
    bus = get_event_bus()
    return bus.subscribe(event_type, callback)
