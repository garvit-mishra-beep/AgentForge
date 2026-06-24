"""
WebSocket service.

Handles websocket connections, subscriptions, and event broadcasting.
"""

import asyncio
import json
import logging
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Set

from apps.api.core.config import settings
from apps.api.schemas.websocket import (
    EventData,
    WorkflowEvent,
)

logger = logging.getLogger(__name__)


# ===============================
# EVENT BROADCASTER
# ===============================


class EventBroadcaster:
    """
    Event broadcaster for websocket connections.
    """

    def __init__(self):
        """
        Initialize event broadcaster.
        """
        self._subscribers: Dict[str, Set[str]] = {}  # workflow_id -> set of client ids
        self._client_subscriptions: Dict[str, Set[str]] = {}  # client_id -> set of workflow_ids
        self._client_connections: Set[str] = set()  # All connected client ids
        self._running: bool = False
        self._event_loop: asyncio.AbstractEventLoop = None

    async def connect(self, client_id: str, workflow_id: str) -> bool:
        """
        Connect client to workflow.

        Args:
            client_id: Client connection ID
            workflow_id: Workflow ID to subscribe to

        Returns:
            True if connected
        """
        if not self._running:
            logger.error("Event broadcaster not running")
            return False

        # Register client
        self._client_connections.add(client_id)

        # Subscribe to workflow
        if workflow_id not in self._subscribers:
            self._subscribers[workflow_id] = set()

        self._subscribers[workflow_id].add(client_id)

        # Register workflow in client subscriptions
        if client_id not in self._client_subscriptions:
            self._client_subscriptions[client_id] = set()

        self._client_subscriptions[client_id].add(workflow_id)

        logger.info(
            "Client connected",
            client_id=client_id,
            workflow_id=workflow_id,
        )

        return True

    async def disconnect(self, client_id: str, workflow_id: str) -> bool:
        """
        Disconnect client from workflow.

        Args:
            client_id: Client connection ID
            workflow_id: Workflow ID

        Returns:
            True if disconnected
        """
        if client_id not in self._client_connections:
            return False

        # Remove from workflow subscribers
        if workflow_id in self._subscribers:
            self._subscribers[workflow_id].discard(client_id)

            # Clean up empty workflow
            if not self._subscribers[workflow_id]:
                del self._subscribers[workflow_id]

        # Remove from client subscriptions
        if client_id in self._client_subscriptions:
            self._client_subscriptions[client_id].discard(workflow_id)

            # Clean up empty client subscriptions
            if not self._client_subscriptions[client_id]:
                del self._client_subscriptions[client_id]

        # Remove client
        self._client_connections.discard(client_id)

        logger.info(
            "Client disconnected",
            client_id=client_id,
            workflow_id=workflow_id,
        )

        return True

    async def disconnect_all(self, client_id: str) -> int:
        """
        Disconnect all subscriptions for client.

        Args:
            client_id: Client connection ID

        Returns:
            Number of disconnected subscriptions
        """
        disconnected = 0

        # Disconnect from all workflows
        if client_id in self._client_subscriptions:
            for workflow_id in list(self._client_subscriptions[client_id]):
                await self.disconnect(client_id, workflow_id)
                disconnected += 1

        return disconnected

    async def broadcast(
        self,
        workflow_id: str,
        event: Dict[str, Any],
        exclude_client: str = None,
    ) -> int:
        """
        Broadcast event to all subscribers of workflow.

        Args:
            workflow_id: Workflow ID
            event: Event data
            exclude_client: Client ID to exclude from receiving

        Returns:
            Number of subscribers
        """
        if workflow_id not in self._subscribers:
            return 0

        subscribers = self._subscribers[workflow_id]

        if not subscribers:
            return 0

        # Send to subscribers (excluding exclude_client)
        for subscriber in subscribers:
            if subscriber != exclude_client:
                try:
                    # In production, send actual websocket message
                    # await self._send_message(subscriber, event)
                    pass
                except Exception as e:
                    logger.error(
                        "Failed to broadcast event",
                        workflow_id=workflow_id,
                        subscriber=subscriber,
                        error=str(e),
                    )

        return len(subscribers)

    async def send_event(
        self,
        client_id: str,
        event: EventData,
    ) -> bool:
        """
        Send event to specific client.

        Args:
            client_id: Client ID
            event: Event data

        Returns:
            True if sent
        """
        try:
            # In production, send actual websocket message
            # message = json.dumps(event.dict())
            # await self._send_message(client_id, message)
            pass
            return True
        except Exception as e:
            logger.error(
                "Failed to send event",
                client_id=client_id,
                error=str(e),
            )
            return False


# ===============================
# WEBSOCKET MANAGER
# ===============================


class WebSocketManager:
    """
    WebSocket manager for connection management and event broadcasting.
    """

    def __init__(self):
        """
        Initialize websocket manager.
        """
        self.broadcaster = EventBroadcaster()
        self.active_connections: Set[str] = set()
        self._running: bool = False
        self._ping_task: asyncio.Task = None

    async def start(self) -> None:
        """
        Start websocket manager.
        """
        self._running = True
        self._ping_task = asyncio.create_task(self._ping_loop())

        logger.info("Websocket manager started")

    async def shutdown(self) -> None:
        """
        Shutdown websocket manager.
        """
        self._running = False

        if self._ping_task:
            self._ping_task.cancel()

        await self.disconnect_all()

        logger.info("Websocket manager shutdown")

    async def connect(
        self,
        websocket,
        workflow_id: str,
    ) -> None:
        """
        Handle websocket connection.

        Args:
            websocket: WebSocket connection
            workflow_id: Workflow ID
        """
        # Generate client ID
        client_id = websocket.headers.get(
            "x-correlation-id",
            f"ws-{time.time()}:{id(websocket)}",
        )

        # Track connection
        self.active_connections.add(client_id)

        # Connect to workflow
        await self.broadcaster.connect(client_id, workflow_id)

        logger.info(
            "Websocket connected",
            client_id=client_id,
            workflow_id=workflow_id,
        )

    async def disconnect(
        self,
        websocket,
        workflow_id: str,
    ) -> None:
        """
        Handle websocket disconnect.

        Args:
            websocket: WebSocket connection
            workflow_id: Workflow ID
        """
        client_id = websocket.headers.get(
            "x-correlation-id",
            f"ws-{time.time()}:{id(websocket)}",
        )

        # Disconnect from workflow
        await self.broadcaster.disconnect(client_id, workflow_id)

        # Remove from active connections
        self.active_connections.discard(client_id)

        logger.info(
            "Websocket disconnected",
            client_id=client_id,
            workflow_id=workflow_id,
        )

    async def disconnect_all(self) -> None:
        """
        Disconnect all connections.
        """
        for client_id in list(self.active_connections):
            await self.disconnect(None, None)

        self.active_connections.clear()

    async def _ping_loop(self) -> None:
        """
        Ping loop for heartbeat.
        """
        while self._running:
            await asyncio.sleep(settings.WEBSOCKET_HEARTBEAT_INTERVAL)

            try:
                # Send ping to active connections
                for client_id in list(self.active_connections):
                    try:
                        # await websocket.ping()
                        pass
                    except Exception:
                        continue
            except Exception as e:
                logger.error(
                    "Ping loop error",
                    error=str(e),
                )
