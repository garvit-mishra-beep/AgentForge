"""
WebSocket events.

Event types and handlers for websocket broadcasting.
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Any, Dict, Optional

from fastapi import WebSocket

from apps.api.core.config import settings

logger = logging.getLogger(__name__)


# ===============================
# EVENT TYPES
# ===============================


class EventTypes:
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


# ===============================
# EVENT DATA STRUCTS
# ===============================


def create_workflow_created_event(
    workflow_id: str,
    data: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Create workflow created event.

    Args:
        workflow_id: Workflow ID
        data: Additional event data

    Returns:
        Event dictionary
    """
    return {
        "type": EventTypes.WORKFLOW_CREATED,
        "event_type": "workflow.created",
        "workflow_id": workflow_id,
        "timestamp": datetime.utcnow().isoformat(),
        "data": data or {},
    }


def create_workflow_started_event(
    workflow_id: str,
    execution_id: str,
    data: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Create workflow started event.

    Args:
        workflow_id: Workflow ID
        execution_id: Execution ID
        data: Additional event data

    Returns:
        Event dictionary
    """
    return {
        "type": EventTypes.WORKFLOW_STARTED,
        "event_type": "workflow.started",
        "workflow_id": workflow_id,
        "execution_id": execution_id,
        "timestamp": datetime.utcnow().isoformat(),
        "data": data or {},
    }


def create_workflow_completed_event(
    workflow_id: str,
    execution_id: str,
    result: Optional[Dict[str, Any]] = None,
    data: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Create workflow completed event.

    Args:
        workflow_id: Workflow ID
        execution_id: Execution ID
        result: Execution result
        data: Additional event data

    Returns:
        Event dictionary
    """
    return {
        "type": EventTypes.WORKFLOW_COMPLETED,
        "event_type": "workflow.completed",
        "workflow_id": workflow_id,
        "execution_id": execution_id,
        "timestamp": datetime.utcnow().isoformat(),
        "result": result,
        "data": data or {},
    }


def create_workflow_failed_event(
    workflow_id: str,
    execution_id: str,
    error: str,
    data: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Create workflow failed event.

    Args:
        workflow_id: Workflow ID
        execution_id: Execution ID
        error: Error message
        data: Additional event data

    Returns:
        Event dictionary
    """
    return {
        "type": EventTypes.WORKFLOW_FAILED,
        "event_type": "workflow.failed",
        "workflow_id": workflow_id,
        "execution_id": execution_id,
        "timestamp": datetime.utcnow().isoformat(),
        "error": error,
        "data": data or {},
    }


def create_heartbeat_event(
    workflow_id: str,
    data: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Create heartbeat event.

    Args:
        workflow_id: Workflow ID
        data: Additional event data

    Returns:
        Event dictionary
    """
    return {
        "type": EventTypes.HEARTBEAT,
        "event_type": "heartbeat",
        "workflow_id": workflow_id,
        "timestamp": datetime.utcnow().isoformat(),
        "data": data or {},
    }


def create_task_started_event(
    workflow_id: str,
    task_id: str,
    task_name: str,
    agent: str = "developer",
    data: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Create task started event.

    Args:
        workflow_id: Workflow ID
        task_id: Task ID
        task_name: Task name
        agent: Agent name
        data: Additional event data

    Returns:
        Event dictionary
    """
    return {
        "type": EventTypes.TASK_STARTED,
        "event_type": "task.started",
        "workflow_id": workflow_id,
        "task_id": task_id,
        "task_name": task_name,
        "agent": agent,
        "timestamp": datetime.utcnow().isoformat(),
        "data": data or {},
    }


def create_task_completed_event(
    workflow_id: str,
    task_id: str,
    task_name: str,
    result: Optional[Dict[str, Any]] = None,
    data: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Create task completed event.

    Args:
        workflow_id: Workflow ID
        task_id: Task ID
        task_name: Task name
        result: Task result
        data: Additional event data

    Returns:
        Event dictionary
    """
    return {
        "type": EventTypes.TASK_COMPLETED,
        "event_type": "task.completed",
        "workflow_id": workflow_id,
        "task_id": task_id,
        "task_name": task_name,
        "timestamp": datetime.utcnow().isoformat(),
        "result": result,
        "data": data or {},
    }


def create_provider_request_event(
    workflow_id: str,
    provider: str,
    model: Optional[str] = None,
    data: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Create provider request event.

    Args:
        workflow_id: Workflow ID
        provider: Provider name
        model: Model name
        data: Additional event data

    Returns:
        Event dictionary
    """
    return {
        "type": EventTypes.PROVIDER_REQUEST,
        "event_type": "provider.request",
        "workflow_id": workflow_id,
        "provider": provider,
        "model": model,
        "timestamp": datetime.utcnow().isoformat(),
        "data": data or {},
    }


def create_provider_response_event(
    workflow_id: str,
    provider: str,
    model: Optional[str] = None,
    status: str = "success",
    tokens: Optional[Dict[str, int]] = None,
    latency_ms: Optional[int] = None,
    data: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Create provider response event.

    Args:
        workflow_id: Workflow ID
        provider: Provider name
        model: Model name
        status: Response status
        tokens: Token usage
        latency_ms: Response latency
        data: Additional event data

    Returns:
        Event dictionary
    """
    return {
        "type": EventTypes.PROVIDER_RESPONSE,
        "event_type": "provider.response",
        "workflow_id": workflow_id,
        "provider": provider,
        "model": model,
        "status": status,
        "tokens": tokens,
        "latency_ms": latency_ms,
        "timestamp": datetime.utcnow().isoformat(),
        "data": data or {},
    }


def create_escalation_event(
    workflow_id: str,
    execution_id: str,
    event_type: str,
    recommendation: Optional[str] = None,
    data: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Create escalation event.

    Args:
        workflow_id: Workflow ID
        execution_id: Execution ID
        event_type: Escalation event type
        recommendation: Recommendation
        data: Additional event data

    Returns:
        Event dictionary
    """
    return {
        "type": EventTypes.ESCALATION_COMPLETED if event_type == "completed" else event_type,
        "event_type": event_type,
        "workflow_id": workflow_id,
        "execution_id": execution_id,
        "timestamp": datetime.utcnow().isoformat(),
        "recommendation": recommendation,
        "data": data or {},
    }


# ===============================
# EVENT PUBLISHER
# ===============================


class EventPublisher:
    """
    Event publisher for websocket broadcasting.
    """

    def __init__(self, broadcast_func):
        """
        Initialize event publisher.

        Args:
            broadcast_func: Function to broadcast messages
        """
        self.broadcast = broadcast_func

    async def publish(
        self,
        workflow_id: str,
        event: Dict[str, Any],
        exclude_client: str = None,
    ) -> int:
        """
        Publish event to subscribers.

        Args:
            workflow_id: Workflow ID
            event: Event data
            exclude_client: Client to exclude

        Returns:
            Number of subscribers
        """
        return await self.broadcast(workflow_id, event, exclude_client)

    async def publish_and_forget(
        self,
        workflow_id: str,
        event_type: str,
        **event_data,
    ) -> None:
        """
        Publish event without waiting for response.

        Args:
            workflow_id: Workflow ID
            event_type: Event type
            **event_data: Event data
        """
        event = {
            "event_type": event_type,
            "workflow_id": workflow_id,
            "timestamp": datetime.utcnow().isoformat(),
            **event_data,
        }

        await self.broadcast(workflow_id, event)


# ===============================
# EVENT HANDLER
# ===============================


class EventHandler:
    """
    Event handler for websocket events.
    """

    def __init__(
        self,
        publisher: EventPublisher,
        workflow_id: str,
        client_id: str,
    ):
        """
        Initialize event handler.

        Args:
            publisher: Event publisher
            workflow_id: Workflow ID
            client_id: Client ID
        """
        self.publisher = publisher
        self.workflow_id = workflow_id
        self.client_id = client_id

    async def handle_event(
        self,
        event_type: str,
        event_data: Dict[str, Any],
    ) -> None:
        """
        Handle incoming event.

        Args:
            event_type: Event type
            event_data: Event data
        """
        # Create event
        event = self._create_event(event_type, event_data)

        # Log event
        logger.info(
            "Event received",
            workflow_id=self.workflow_id,
            client_id=self.client_id,
            event_type=event_type,
            data=event.get("data", {}),
        )

    def _create_event(
        self,
        event_type: str,
        event_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Create event from data.

        Args:
            event_type: Event type
            event_data: Event data

        Returns:
            Event dictionary
        """
        # Simplified event creation
        return {
            "type": event_type,
            "event_type": event_type,
            "workflow_id": self.workflow_id,
            "timestamp": datetime.utcnow().isoformat(),
            "data": event_data,
        }


# ===============================
# EVENT ROUTER
# ===============================


class EventRouter:
    """
    Event router for routing events to handlers.
    """

    def __init__(
        self,
        publisher: EventPublisher,
        handler: Optional[EventHandler] = None,
    ):
        """
        Initialize event router.

        Args:
            publisher: Event publisher
            handler: Event handler
        """
        self.publisher = publisher
        self.handler = handler
        self._handlers: Dict[str, EventHandler] = {}

    async def route(
        self,
        event_type: str,
        event_data: Dict[str, Any],
    ) -> None:
        """
        Route event to handler.

        Args:
            event_type: Event type
            event_data: Event data
        """
        # Get handler for event type
        handler = self._handlers.get(event_type) or self.handler

        if handler:
            await handler.handle_event(event_type, event_data)

    async def register_handler(
        self,
        event_type: str,
        handler: EventHandler,
    ) -> None:
        """
        Register event handler.

        Args:
            event_type: Event type
            handler: Event handler
        """
        self._handlers[event_type] = handler
