"""
WebSocket routes.

Real-time event streaming endpoints.
"""

import logging
from datetime import datetime

from fastapi import APIRouter, WebSocket
from fastapi.websockets import WebSocketDisconnect

from apps.api.websocket.manager import websocket_manager
from apps.api.schemas.websocket import (
    SubscribeRequest,
    UnsubscribeRequest,
    EventData,
)

logger = logging.getLogger(__name__)

router = APIRouter()


# ===============================
# WEBSOCKET ROUTES
# ===============================


@router.websocket("/ws/subscribes")
async def websocket_subscribe(
    websocket: WebSocket,
    subscribe: SubscribeRequest,
):
    """
    Subscribe to workflow events.

    Args:
        websocket: WebSocket connection
        subscribe: Subscription request
    """
    await websocket.accept()

    await websocket_manager.connect(
        websocket,
        subscribe.workflow_id,
    )

    logger.info(
        "Subscribed to workflow events",
        workflow_id=subscribe.workflow_id,
        request_id=websocket.headers.get("x-correlation-id", "none"),
    )


@router.websocket("/ws/unsubscribe")
async def websocket_unsubscribe(
    websocket: WebSocket,
    unsubscribe: UnsubscribeRequest,
):
    """
    Unsubscribe from workflow events.

    Args:
        websocket: WebSocket connection
        unsubscribe: Unsubscription request
    """
    await websocket_manager.disconnect(
        websocket,
        unsubscribe.workflow_id,
    )

    logger.info(
        "Unsubscribed from workflow events",
        workflow_id=unsubscribe.workflow_id,
        request_id=websocket.headers.get("x-correlation-id", "none"),
    )


@router.websocket("/ws/workflows/{workflow_id}")
async def websocket_workflow_events(
    websocket: WebSocket,
    workflow_id: str,
):
    """
    Connect to workflow event stream.

    Args:
        websocket: WebSocket connection
        workflow_id: Workflow ID
    """
    await websocket.accept()

    await websocket_manager.connect(
        websocket,
        workflow_id,
    )

    logger.info(
        "Connected to workflow event stream",
        workflow_id=workflow_id,
        request_id=websocket.headers.get("x-correlation-id", "none"),
    )

    try:
        # Wait for disconnect
        await websocket.receive_text()

    except WebSocketDisconnect:
        logger.info(
            "Websocket disconnect",
            workflow_id=workflow_id,
            request_id=websocket.headers.get("x-correlation-id", "none"),
        )

    except Exception as e:
        logger.error(
            "Websocket error",
            workflow_id=workflow_id,
            error=str(e),
            request_id=websocket.headers.get("x-correlation-id", "none"),
        )

    finally:
        await websocket_manager.disconnect(
            websocket,
            workflow_id,
        )


# ===============================
# HELPER ROUTES
# ===============================


@router.post("/ws/ping")
async def websocket_ping():
    """
    Ping websocket server.

    Returns:
        Ping response
    """
    return {
        "status": "pong",
        "timestamp": datetime.utcnow().isoformat(),
    }
