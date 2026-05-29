"""
WebSocket Manager for Real-time Updates.

Provides:
- Connection management
- Room-based broadcasting
- Presence updates
- Grid refresh events
- Call notifications
"""

import logging
from datetime import datetime
from typing import Dict, Set, Optional

from fastapi import WebSocket
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class WebSocketMessage(BaseModel):
    """Standard WebSocket message format."""
    type: str
    data: dict
    timestamp: str = None
    
    def __init__(self, **data):
        if 'timestamp' not in data:
            data['timestamp'] = datetime.utcnow().isoformat()
        super().__init__(**data)


class ConnectionManager:
    """
    Manages WebSocket connections for real-time updates.
    
    Features:
    - User-to-connection mapping
    - Room-based broadcasting (e.g., by state)
    - Automatic cleanup on disconnect
    """
    
    def __init__(self):
        # user_id -> WebSocket connection
        self._connections: Dict[str, WebSocket] = {}
        # room_id -> set of user_ids
        self._rooms: Dict[str, Set[str]] = {}
        # user_id -> set of room_ids
        self._user_rooms: Dict[str, Set[str]] = {}
    
    async def connect(self, websocket: WebSocket, user_id: str) -> None:
        """Accept a WebSocket connection for a user."""
        await websocket.accept()
        self._connections[user_id] = websocket
        self._user_rooms[user_id] = set()
        logger.info(f"WebSocket connected: user={user_id}")
    
    def disconnect(self, user_id: str) -> None:
        """Handle user disconnection and cleanup."""
        if user_id in self._connections:
            del self._connections[user_id]
        
        # Remove from all rooms
        if user_id in self._user_rooms:
            for room_id in self._user_rooms[user_id]:
                if room_id in self._rooms:
                    self._rooms[room_id].discard(user_id)
            del self._user_rooms[user_id]
        
        logger.info(f"WebSocket disconnected: user={user_id}")
    
    async def join_room(self, user_id: str, room_id: str) -> None:
        """Add user to a room for targeted broadcasts."""
        if room_id not in self._rooms:
            self._rooms[room_id] = set()
        self._rooms[room_id].add(user_id)
        
        if user_id in self._user_rooms:
            self._user_rooms[user_id].add(room_id)
        
        logger.debug(f"User {user_id} joined room {room_id}")
    
    async def leave_room(self, user_id: str, room_id: str) -> None:
        """Remove user from a room."""
        if room_id in self._rooms:
            self._rooms[room_id].discard(user_id)
        if user_id in self._user_rooms:
            self._user_rooms[user_id].discard(room_id)
    
    async def send_personal(self, user_id: str, message: WebSocketMessage) -> bool:
        """Send message to a specific user."""
        if user_id in self._connections:
            try:
                await self._connections[user_id].send_json(message.model_dump())
                return True
            except Exception as e:
                logger.error(f"Failed to send to {user_id}: {e}")
                self.disconnect(user_id)
        return False
    
    async def broadcast_room(self, room_id: str, message: WebSocketMessage) -> int:
        """Broadcast message to all users in a room."""
        if room_id not in self._rooms:
            return 0
        
        sent = 0
        for user_id in self._rooms[room_id].copy():
            if await self.send_personal(user_id, message):
                sent += 1
        
        return sent
    
    async def broadcast_all(self, message: WebSocketMessage) -> int:
        """Broadcast message to all connected users."""
        sent = 0
        for user_id in list(self._connections.keys()):
            if await self.send_personal(user_id, message):
                sent += 1
        return sent
    
    @property
    def connection_count(self) -> int:
        """Get total number of active connections."""
        return len(self._connections)
    
    def get_room_members(self, room_id: str) -> Set[str]:
        """Get set of user IDs in a room."""
        return self._rooms.get(room_id, set()).copy()


# ==================== Message Types ====================

class PresenceMessage(WebSocketMessage):
    """Presence update message."""
    def __init__(self, professional_id: str, status: str, name: str = None):
        super().__init__(
            type="presence_update",
            data={
                "professional_id": professional_id,
                "status": status,
                "name": name,
            }
        )


class GridRefreshMessage(WebSocketMessage):
    """Grid refresh signal."""
    def __init__(self, reason: str = "data_changed"):
        super().__init__(
            type="grid_refresh",
            data={"reason": reason}
        )


class CallNotificationMessage(WebSocketMessage):
    """Incoming call notification."""
    def __init__(
        self,
        call_id: str,
        caller_name: str,
        caller_type: str = "borrower",
    ):
        super().__init__(
            type="incoming_call",
            data={
                "call_id": call_id,
                "caller_name": caller_name,
                "caller_type": caller_type,
            }
        )


class LeadNotificationMessage(WebSocketMessage):
    """New lead notification."""
    def __init__(
        self,
        lead_id: str,
        borrower_name: str,
        loan_purpose: str,
    ):
        super().__init__(
            type="new_lead",
            data={
                "lead_id": lead_id,
                "borrower_name": borrower_name,
                "loan_purpose": loan_purpose,
            }
        )


# ==================== Singleton ====================

_manager: Optional[ConnectionManager] = None


def get_connection_manager() -> ConnectionManager:
    """Get WebSocket connection manager singleton."""
    global _manager
    if _manager is None:
        _manager = ConnectionManager()
    return _manager


# ==================== Event Emitters ====================

async def emit_presence_change(
    professional_id: str,
    status: str,
    name: str = None,
) -> None:
    """Emit presence change to all grid viewers."""
    manager = get_connection_manager()
    message = PresenceMessage(professional_id, status, name)
    await manager.broadcast_room("grid_viewers", message)


async def emit_grid_refresh(reason: str = "data_changed") -> None:
    """Signal grid viewers to refresh their data."""
    manager = get_connection_manager()
    message = GridRefreshMessage(reason)
    await manager.broadcast_room("grid_viewers", message)


async def emit_incoming_call(
    professional_id: str,
    call_id: str,
    caller_name: str,
) -> None:
    """Notify professional of incoming call."""
    manager = get_connection_manager()
    message = CallNotificationMessage(call_id, caller_name)
    await manager.send_personal(professional_id, message)


async def emit_new_lead(
    professional_id: str,
    lead_id: str,
    borrower_name: str,
    loan_purpose: str,
) -> None:
    """Notify professional of new lead."""
    manager = get_connection_manager()
    message = LeadNotificationMessage(lead_id, borrower_name, loan_purpose)
    await manager.send_personal(professional_id, message)
