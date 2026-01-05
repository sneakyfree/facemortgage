"""
WebSocket handlers for real-time presence updates.

Manages WebSocket connections for:
- Professional heartbeat and status updates
- Borrower grid subscriptions
- Real-time grid changes broadcasting
"""
import json
import asyncio
import logging
from typing import Dict, Set, Optional
from uuid import UUID
from fastapi import WebSocket, WebSocketDisconnect, HTTPException, status
from starlette.websockets import WebSocketState

from src.app.presence.service import get_presence_service, PresenceService
from src.app.core.dependencies import get_current_user_ws
from src.app.models.user import UserType

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections for different user types."""

    def __init__(self):
        # Professional connections: professional_id -> WebSocket
        self.professional_connections: Dict[str, WebSocket] = {}
        # Borrower connections: Set of WebSockets subscribed to grid updates
        self.grid_subscribers: Set[WebSocket] = set()
        # Heartbeat tasks for professionals
        self.heartbeat_tasks: Dict[str, asyncio.Task] = {}
        # Lock for thread-safe operations
        self._lock = asyncio.Lock()

    async def connect_professional(
        self, websocket: WebSocket, professional_id: str, metadata: dict = None
    ) -> None:
        """Connect a professional and mark them as online."""
        await websocket.accept()

        async with self._lock:
            # Disconnect existing connection if any
            if professional_id in self.professional_connections:
                old_ws = self.professional_connections[professional_id]
                try:
                    await old_ws.close(code=1000, reason="New connection established")
                except Exception as e:
                    logger.debug(f"Error closing old connection for {professional_id}: {e}")

            self.professional_connections[professional_id] = websocket

        # Mark as online in presence service
        presence = get_presence_service()
        await presence.set_online(professional_id, metadata)

        # Start heartbeat task
        await self._start_heartbeat(professional_id)

        # Notify grid subscribers
        await self.broadcast_grid_update({
            "event": "professional_online",
            "professional_id": professional_id,
        })

    async def disconnect_professional(
        self, professional_id: str, reason: str = "disconnect"
    ) -> None:
        """Disconnect a professional and mark them as offline."""
        async with self._lock:
            # Cancel heartbeat task
            if professional_id in self.heartbeat_tasks:
                self.heartbeat_tasks[professional_id].cancel()
                del self.heartbeat_tasks[professional_id]

            # Remove connection
            if professional_id in self.professional_connections:
                del self.professional_connections[professional_id]

        # Mark as offline in presence service
        presence = get_presence_service()
        await presence.set_offline(professional_id, reason)

        # Notify grid subscribers
        await self.broadcast_grid_update({
            "event": "professional_offline",
            "professional_id": professional_id,
        })

    async def connect_grid_subscriber(self, websocket: WebSocket) -> None:
        """Connect a borrower/viewer to receive grid updates."""
        await websocket.accept()
        async with self._lock:
            self.grid_subscribers.add(websocket)

    async def disconnect_grid_subscriber(self, websocket: WebSocket) -> None:
        """Disconnect a grid subscriber."""
        async with self._lock:
            self.grid_subscribers.discard(websocket)

    async def broadcast_grid_update(self, message: dict) -> None:
        """Broadcast a grid update to all subscribers."""
        if not self.grid_subscribers:
            return

        message_json = json.dumps(message)
        disconnected = set()

        for websocket in self.grid_subscribers:
            try:
                if websocket.client_state == WebSocketState.CONNECTED:
                    await websocket.send_text(message_json)
            except Exception as e:
                logger.debug(f"Failed to send grid update to subscriber: {e}")
                disconnected.add(websocket)

        # Clean up disconnected subscribers
        if disconnected:
            async with self._lock:
                self.grid_subscribers -= disconnected

    async def send_to_professional(
        self, professional_id: str, message: dict
    ) -> bool:
        """Send a message to a specific professional."""
        websocket = self.professional_connections.get(professional_id)
        if websocket and websocket.client_state == WebSocketState.CONNECTED:
            try:
                await websocket.send_json(message)
                return True
            except Exception as e:
                logger.warning(f"Failed to send message to professional {professional_id}: {e}")
                await self.disconnect_professional(professional_id, "send_error")
        return False

    async def _start_heartbeat(self, professional_id: str) -> None:
        """Start heartbeat monitoring for a professional."""
        if professional_id in self.heartbeat_tasks:
            self.heartbeat_tasks[professional_id].cancel()

        async def heartbeat_loop():
            presence = get_presence_service()
            while True:
                await asyncio.sleep(presence.HEARTBEAT_INTERVAL)
                try:
                    await presence.heartbeat(professional_id)
                except Exception as e:
                    logger.warning(f"Heartbeat failed for professional {professional_id}: {e}")
                    break

        self.heartbeat_tasks[professional_id] = asyncio.create_task(heartbeat_loop())

    async def update_professional_status(
        self, professional_id: str, new_status: str, room_id: str = None
    ) -> None:
        """Update a professional's status and notify subscribers."""
        presence = get_presence_service()

        if new_status == "available":
            await presence.set_available(professional_id)
        elif new_status == "busy":
            await presence.set_busy(professional_id, room_id)
        elif new_status == "in_call":
            await presence.set_in_call(professional_id, room_id)
        elif new_status == "away":
            await presence.set_away(professional_id)
        elif new_status == "offline":
            await self.disconnect_professional(professional_id, "status_change")
            return

        # Broadcast status change to grid
        await self.broadcast_grid_update({
            "event": f"professional_{new_status}",
            "professional_id": professional_id,
            "room_id": room_id,
        })

    def get_online_count(self) -> int:
        """Get count of connected professionals."""
        return len(self.professional_connections)

    def get_subscriber_count(self) -> int:
        """Get count of grid subscribers."""
        return len(self.grid_subscribers)


# Global connection manager instance
connection_manager = ConnectionManager()


async def professional_presence_handler(websocket: WebSocket, professional_id: str):
    """
    WebSocket handler for professional presence.

    Expected message format:
    {
        "type": "heartbeat" | "status_update" | "camera_toggle",
        "data": { ... }
    }
    """
    try:
        await connection_manager.connect_professional(websocket, professional_id)

        while True:
            try:
                data = await websocket.receive_json()
                msg_type = data.get("type")

                if msg_type == "heartbeat":
                    presence = get_presence_service()
                    await presence.heartbeat(professional_id)
                    await websocket.send_json({"type": "heartbeat_ack"})

                elif msg_type == "status_update":
                    new_status = data.get("data", {}).get("status")
                    room_id = data.get("data", {}).get("room_id")
                    if new_status:
                        await connection_manager.update_professional_status(
                            professional_id, new_status, room_id
                        )
                        await websocket.send_json({
                            "type": "status_updated",
                            "status": new_status
                        })

                elif msg_type == "camera_toggle":
                    camera_on = data.get("data", {}).get("camera_on", True)
                    presence = get_presence_service()
                    await presence.redis.hset(
                        presence._professional_key(professional_id),
                        "camera_on",
                        str(camera_on).lower()
                    )
                    await connection_manager.broadcast_grid_update({
                        "event": "camera_toggle",
                        "professional_id": professional_id,
                        "camera_on": camera_on,
                    })

            except WebSocketDisconnect:
                break
            except json.JSONDecodeError:
                await websocket.send_json({
                    "type": "error",
                    "message": "Invalid JSON format"
                })

    except WebSocketDisconnect:
        pass
    finally:
        await connection_manager.disconnect_professional(professional_id)


async def grid_updates_handler(websocket: WebSocket):
    """
    WebSocket handler for grid update subscriptions.

    Borrowers/viewers connect here to receive real-time grid updates:
    - Professional online/offline
    - Professional busy/available
    - Camera toggle events
    """
    try:
        await connection_manager.connect_grid_subscriber(websocket)

        # Send initial connection confirmation
        await websocket.send_json({
            "type": "connected",
            "message": "Subscribed to grid updates"
        })

        # Keep connection alive and handle any client messages
        while True:
            try:
                data = await websocket.receive_json()
                msg_type = data.get("type")

                if msg_type == "ping":
                    await websocket.send_json({"type": "pong"})

                elif msg_type == "get_online_count":
                    presence = get_presence_service()
                    count = await presence.get_online_count()
                    await websocket.send_json({
                        "type": "online_count",
                        "count": count
                    })

            except WebSocketDisconnect:
                break
            except json.JSONDecodeError:
                await websocket.send_json({
                    "type": "error",
                    "message": "Invalid JSON format"
                })

    except WebSocketDisconnect:
        pass
    finally:
        await connection_manager.disconnect_grid_subscriber(websocket)


async def redis_subscriber_task():
    """
    Background task that subscribes to Redis pub/sub channels
    and forwards events to WebSocket clients.
    """
    presence = get_presence_service()
    await presence.connect()

    pubsub = await presence.subscribe("presence", "grid_updates")

    while True:
        try:
            message = await presence.get_message(timeout=1.0)
            if message:
                # Forward to all grid subscribers
                await connection_manager.broadcast_grid_update(message)
        except Exception as e:
            print(f"Redis subscriber error: {e}")
            await asyncio.sleep(1)
