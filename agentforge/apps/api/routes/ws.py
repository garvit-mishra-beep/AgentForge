from __future__ import annotations

import json
import uuid
import asyncio
import logging
from typing import Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query

from apps.api.core.config import settings
from apps.api.services import AgentService, ExecutionService
from apps.api.core.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/ws", tags=["WebSocket"])


class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, list[WebSocket]] = {}

    async def connect(self, execution_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.setdefault(execution_id, []).append(websocket)

    def disconnect(self, execution_id: str, websocket: WebSocket):
        conns = self.active_connections.get(execution_id, [])
        if websocket in conns:
            conns.remove(websocket)
        if not conns:
            self.active_connections.pop(execution_id, None)

    async def broadcast(self, execution_id: str, message: dict):
        for ws in self.active_connections.get(execution_id, []):
            try:
                await ws.send_json(message)
            except Exception:
                pass

    async def send_to(self, execution_id: str, websocket: WebSocket, message: dict):
        try:
            await websocket.send_json(message)
        except Exception:
            pass


manager = ConnectionManager()


@router.websocket("/executions/{execution_id}")
async def execution_ws(
    websocket: WebSocket,
    execution_id: str,
    token: str = Query(...),
):
    from apps.api.dependencies.auth import verify_token
    payload = verify_token(token)
    if payload is None:
        await websocket.close(code=4001)
        return

    await manager.connect(execution_id, websocket)
    try:
        while True:
            data = await websocket.receive_text()
            msg = json.loads(data)
            msg_type = msg.get("type", "")

            if msg_type == "ping":
                await manager.send_to(execution_id, websocket, {"type": "pong"})
            elif msg_type == "cancel":
                await manager.broadcast(execution_id, {"type": "cancelled", "execution_id": execution_id})
                break
    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.error(f"WebSocket error for {execution_id}: {e}")
    finally:
        manager.disconnect(execution_id, websocket)


@router.websocket("/events")
async def events_ws(
    websocket: WebSocket,
    token: str = Query(...),
):
    from apps.api.dependencies.auth import verify_token
    payload = verify_token(token)
    if payload is None:
        await websocket.close(code=4001)
        return

    await websocket.accept()
    tenant_id = payload.get("sub", "unknown")
    try:
        while True:
            data = await websocket.receive_text()
            msg = json.loads(data)
            if msg.get("type") == "ping":
                await websocket.send_json({"type": "pong"})
    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.error(f"Events WebSocket error: {e}")
