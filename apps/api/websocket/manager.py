"""
WebSocket connection manager.

Handles connection lifecycle, subscriptions, and event broadcasting.
"""

import asyncio
import json
import logging
import uuid
from datetime import datetime
from typing import Any, Dict, Optional, Set

from fastapi import WebSocket
from fastapi.websockets import WebSocketDisconnect

from apps.api.core.config import settings
from apps.api.schemas.websocket import EventData

logger = logging.getLogger(__name__)


# ===============================
# GLOBAL MANAGER INSTANCE
# ===============================


websocket_manager = None


# ===============================
# MANAGER CLASS
# ===============================


class ConnectionManager:
    """
    WebSocket connection manager.
    """

    def __init__(self):
        """
        Initialize connection manager.
        """
        # Active connections: client_id -> {websocket, subscriptions, last_heartbeat}
        self.active_connections: Dict[str, dict] = {}
        self.subscriptions: Dict[str, Set[str]] = {}  # workflow_id -> set of client_ids
        self.heartbeat_interval = settings.WEBSOCKET_HEARTBEAT_INTERVAL
        self._ping_task: Optional[asyncio.Task] = None
        self._running: bool = False

    async def connect(
        self,
        websocket: WebSocket,
        workflow_id: str,
    ) -> None:
        """
        Accept websocket connection.

        Args:
            websocket: WebSocket connection
            workflow_id: Workflow ID to subscribe to
        """
        await websocket.accept()

        # Generate client ID
        client_id = websocket.headers.get(
            "x-correlation-id",
            str(uuid.uuid4()),
        )

        # Track connection
        self.active_connections[client_id] = {
            "websocket": websocket,
            "workflow_id": workflow_id,
            "subscriptions": {workflow_id},
            "last_heartbeat": datetime.utcnow(),
            "connected_at": datetime.utcnow(),
        }

        # Register subscription
        if workflow_id not in self.subscriptions:
            self.subscriptions[workflow_id] = set()
        self.subscriptions[workflow_id].add(client_id)

        logger.info(
            "Websocket connected",
            client_id=client_id,
            workflow_id=workflow_id,
        )

    async def disconnect(
        self,
        websocket: WebSocket,
        workflow_id: str,
    ) -> None:
        """
        Handle disconnect.

        Args:
            websocket: WebSocket connection
            workflow_id: Workflow ID

        Returns:
            True if disconnected
        """
        # Find client by websocket or client_id
        client_id = None

        for id_, data in list(self.active_connections.items()):
            if (
                data["websocket"] == websocket
                or data["workflow_id"] == workflow_id
            ):
                client_id = id_
                break

        if client_id and client_id in self.active_connections:
            client_data = self.active_connections[client_id]

            # Unsubscribe from workflow
            if workflow_id in client_data["subscriptions"]:
                client_data["subscriptions"].discard(workflow_id)

            # Remove from workflow subscriptions
            if workflow_id in self.subscriptions:
                self.subscriptions[workflow_id].discard(client_id)

            # Remove from active connections if no subscriptions
            if not client_data["subscriptions"]:
                client_id = None
                self.active_connections.pop(client_id)
                self.subscriptions.pop(workflow_id, None)

            # Remove from active_connections if no more subscriptions
            if client_id:
                self.active_connections[client_id]["websocket"].close()
                self.active_connections.pop(client_id)
                self.subscriptions.pop(workflow_id, None)

            logger.info(
                "Websocket disconnected",
                client_id=client_id,
                workflow_id=workflow_id,
            )

    async def send_to_client(
        self,
        client_id: str,
        message: dict,
    ) -> bool:
        """
        Send message to specific client.

        Args:
            client_id: Client connection ID
            message: Message to send

        Returns:
            True if sent
        """
        if client_id not in self.active_connections:
            return False

        try:
            await self.active_connections[client_id]["websocket"].send_json(
                message,
            )
            return True
        except Exception as e:
            logger.error(
                "Failed to send message",
                client_id=client_id,
                error=str(e),
            )
            return False

    async def broadcast(
        self,
        workflow_id: str,
        message: dict,
    ) -> int:
        """
        Broadcast message to all clients subscribed to workflow.

        Args:
            workflow_id: Workflow ID
            message: Message to broadcast

        Returns:
            Number of subscribers
        """
        if workflow_id not in self.subscriptions:
            return 0

        subscribers = self.subscriptions[workflow_id]
        if not subscribers:
            return 0

        # Send to all subscribers
        sent_count = 0
        for client_id in list(subscribers):
            if client_id in self.active_connections:
                if await self.send_to_client(client_id, message):
                    sent_count += 1

        return sent_count

    async def send_ping(self) -> None:
        """
        Send ping to all active connections.
        """
        for client_id, data in list(self.active_connections.items()):
            try:
                await data["websocket"].send_json(
                    {
                        "type": "ping",
                        "timestamp": datetime.utcnow().isoformat(),
                    },
                )
            except Exception:
                continue

    async def send_pong(
        self,
        client_id: str,
        message: dict,
    ) -> None:
        """
        Send pong to specific client.

        Args:
            client_id: Client connection ID
            message: Pong message
        """
        if client_id in self.active_connections:
            try:
                await self.active_connections[client_id]["websocket"].send_json(
                    message,
                )
            except Exception:
                pass

    async def _ping_loop(self) -> None:
        """
        Heartbeat ping loop.
        """
        while self._running:
            try:
                await asyncio.sleep(self.heartbeat_interval)

                # Send ping
                await self.send_ping()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(
                    "Ping loop error",
                    error=str(e),
                )

    async def start(self) -> None:
        """
        Start connection manager.
        """
        self._running = True

        # Start ping loop
        self._ping_task = asyncio.create_task(self._ping_loop())

        logger.info("Websocket manager started")

    async def shutdown(self) -> None:
        """
        Shutdown connection manager.
        """
        self._running = False

        if self._ping_task:
            self._ping_task.cancel()

            try:
                await self._ping_task
            except asyncio.CancelledError:
                pass

        # Close all connections
        for client_data in self.active_connections.values():
            try:
                client_data["websocket"].close()
            except Exception:
                pass

        self.active_connections.clear()

        logger.info("Websocket manager shutdown")


# ===============================
# GLOBAL MANAGER INSTANCE INITIALIZATION
# ===============================

websocket_manager = ConnectionManager()


# ===============================
# START MANAGER
# ===============================


async def start() -> None:
    """
    Start websocket manager.
    """
    global websocket_manager

    if websocket_manager is None:
        websocket_manager = ConnectionManager()

    await websocket_manager.start()


# ===============================
# SHUTDOWN
# ===============================


async def shutdown() -> None:
    """
    Shutdown websocket manager.
    """
    global websocket_manager

    if websocket_manager:
        await websocket_manager.shutdown()


# ===============================
# GET MANAGER
# ===============================


def get_manager() -> ConnectionManager:
    """
    Get websocket manager instance.

    Returns:
        ConnectionManager instance
    """
    global websocket_manager

    if websocket_manager is None:
        websocket_manager = ConnectionManager()

    return websocket_manager
