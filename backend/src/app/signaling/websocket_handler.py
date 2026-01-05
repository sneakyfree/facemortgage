"""
WebSocket handler for WebRTC signaling.

Manages real-time signaling messages between call participants:
- SDP offer/answer exchange
- ICE candidate exchange
- Call state notifications
"""
import json
import asyncio
import logging
from typing import Dict, Optional, Set
from fastapi import WebSocket, WebSocketDisconnect
from starlette.websockets import WebSocketState

from src.app.signaling.service import (
    SignalingService,
    get_signaling_service,
    CallState,
)
from src.app.presence import get_presence_service

logger = logging.getLogger(__name__)


class SignalingConnectionManager:
    """Manages WebSocket connections for signaling."""

    def __init__(self):
        # room_id -> {user_id: WebSocket}
        self.rooms: Dict[str, Dict[str, WebSocket]] = {}
        # user_id -> room_id (for quick lookup)
        self.user_rooms: Dict[str, str] = {}
        self._lock = asyncio.Lock()

    async def join_room(
        self,
        websocket: WebSocket,
        room_id: str,
        user_id: str,
    ) -> None:
        """Add a user to a signaling room."""
        async with self._lock:
            if room_id not in self.rooms:
                self.rooms[room_id] = {}

            self.rooms[room_id][user_id] = websocket
            self.user_rooms[user_id] = room_id

    async def leave_room(self, user_id: str) -> Optional[str]:
        """Remove a user from their room. Returns room_id if found."""
        async with self._lock:
            room_id = self.user_rooms.pop(user_id, None)
            if room_id and room_id in self.rooms:
                self.rooms[room_id].pop(user_id, None)
                # Clean up empty rooms
                if not self.rooms[room_id]:
                    del self.rooms[room_id]
            return room_id

    async def send_to_peer(
        self,
        room_id: str,
        sender_id: str,
        message: dict,
    ) -> bool:
        """Send a message to the other participant in the room."""
        if room_id not in self.rooms:
            return False

        for user_id, websocket in self.rooms[room_id].items():
            if user_id != sender_id:
                try:
                    if websocket.client_state == WebSocketState.CONNECTED:
                        await websocket.send_json(message)
                        return True
                except Exception as e:
                    logger.warning(f"Failed to send message to room {room_id}: {e}")
        return False

    async def send_to_user(
        self,
        room_id: str,
        target_user_id: str,
        message: dict,
    ) -> bool:
        """Send a message to a specific user in the room."""
        if room_id not in self.rooms:
            return False

        websocket = self.rooms[room_id].get(target_user_id)
        if websocket and websocket.client_state == WebSocketState.CONNECTED:
            try:
                await websocket.send_json(message)
                return True
            except Exception as e:
                logger.warning(f"Failed to send message to user {target_user_id} in room {room_id}: {e}")
        return False

    async def broadcast_to_room(
        self,
        room_id: str,
        message: dict,
        exclude_user: str = None,
    ) -> None:
        """Broadcast a message to all users in a room."""
        if room_id not in self.rooms:
            return

        for user_id, websocket in self.rooms[room_id].items():
            if user_id != exclude_user:
                try:
                    if websocket.client_state == WebSocketState.CONNECTED:
                        await websocket.send_json(message)
                except Exception as e:
                    logger.warning(f"Failed to broadcast to user {user_id} in room {room_id}: {e}")

    def get_room_participants(self, room_id: str) -> Set[str]:
        """Get user IDs of participants in a room."""
        return set(self.rooms.get(room_id, {}).keys())


# Global connection manager
signaling_manager = SignalingConnectionManager()


async def signaling_handler(
    websocket: WebSocket,
    room_id: str,
    user_id: str,
):
    """
    WebSocket handler for WebRTC signaling.

    Expected message format:
    {
        "type": "offer" | "answer" | "ice_candidate" | "call_action",
        "payload": { ... }
    }

    Actions:
    - offer: SDP offer from caller
    - answer: SDP answer from callee
    - ice_candidate: ICE candidate
    - call_action: answer, decline, end, mute, camera_off
    """
    await websocket.accept()

    signaling = get_signaling_service()
    presence = get_presence_service()

    # Verify room exists and user is a participant
    room = await signaling.get_room(room_id)
    if not room:
        await websocket.send_json({
            "type": "error",
            "payload": {"message": "Room not found"},
        })
        await websocket.close()
        return

    if user_id not in (room.borrower_id, room.professional_id):
        await websocket.send_json({
            "type": "error",
            "payload": {"message": "Not authorized for this room"},
        })
        await websocket.close()
        return

    # Join the signaling room
    await signaling_manager.join_room(websocket, room_id, user_id)

    # Send room info and ICE servers
    ice_servers = await signaling.get_ice_servers()
    await websocket.send_json({
        "type": "room_joined",
        "payload": {
            "room_id": room_id,
            "room": room.to_dict(),
            "ice_servers": ice_servers,
            "is_caller": user_id == room.borrower_id,
        },
    })

    # Notify peer that user joined
    await signaling_manager.send_to_peer(room_id, user_id, {
        "type": "peer_joined",
        "payload": {"user_id": user_id},
    })

    try:
        while True:
            try:
                data = await websocket.receive_json()
                msg_type = data.get("type")
                payload = data.get("payload", {})

                if msg_type == "offer":
                    # Forward SDP offer to peer
                    await signaling_manager.send_to_peer(room_id, user_id, {
                        "type": "offer",
                        "payload": payload,
                    })

                elif msg_type == "answer":
                    # Forward SDP answer to peer
                    await signaling_manager.send_to_peer(room_id, user_id, {
                        "type": "answer",
                        "payload": payload,
                    })

                elif msg_type == "ice_candidate":
                    # Forward ICE candidate to peer
                    await signaling_manager.send_to_peer(room_id, user_id, {
                        "type": "ice_candidate",
                        "payload": payload,
                    })

                elif msg_type == "call_action":
                    action = payload.get("action")

                    if action == "answer":
                        # Professional answered the call
                        await signaling.update_room_state(room_id, CallState.ACTIVE)
                        await signaling_manager.broadcast_to_room(room_id, {
                            "type": "call_state",
                            "payload": {"state": CallState.ACTIVE.value},
                        })
                        # Update presence to in_call
                        await presence.set_in_call(room.professional_id, room_id)

                    elif action == "decline":
                        # Professional declined the call
                        await signaling.update_room_state(
                            room_id, CallState.DECLINED, "declined_by_professional"
                        )
                        await signaling_manager.broadcast_to_room(room_id, {
                            "type": "call_state",
                            "payload": {
                                "state": CallState.DECLINED.value,
                                "reason": "declined",
                            },
                        })
                        # Professional back to available
                        await presence.set_available(room.professional_id)

                    elif action == "end":
                        # Either party ended the call
                        room = await signaling.update_room_state(
                            room_id, CallState.ENDED, f"ended_by_{user_id}"
                        )
                        await signaling_manager.broadcast_to_room(room_id, {
                            "type": "call_state",
                            "payload": {
                                "state": CallState.ENDED.value,
                                "reason": "call_ended",
                                "pickup_time_seconds": signaling.calculate_pickup_time(room),
                            },
                        })
                        # Professional back to available
                        await presence.set_available(room.professional_id)

                    elif action == "mute":
                        # Toggle mute state
                        muted = payload.get("muted", True)
                        await signaling_manager.send_to_peer(room_id, user_id, {
                            "type": "peer_muted",
                            "payload": {"muted": muted},
                        })

                    elif action == "camera_off":
                        # Toggle camera state
                        camera_off = payload.get("camera_off", True)
                        await signaling_manager.send_to_peer(room_id, user_id, {
                            "type": "peer_camera",
                            "payload": {"camera_off": camera_off},
                        })

                elif msg_type == "ping":
                    await websocket.send_json({"type": "pong"})

            except WebSocketDisconnect:
                break
            except json.JSONDecodeError:
                await websocket.send_json({
                    "type": "error",
                    "payload": {"message": "Invalid JSON"},
                })

    except WebSocketDisconnect:
        pass
    finally:
        # Clean up
        left_room_id = await signaling_manager.leave_room(user_id)

        if left_room_id:
            # Notify peer that user left
            await signaling_manager.broadcast_to_room(left_room_id, {
                "type": "peer_left",
                "payload": {"user_id": user_id},
            })

            # Check if room should be ended
            room = await signaling.get_room(left_room_id)
            if room and room.state in (CallState.INITIATING, CallState.RINGING, CallState.CONNECTING, CallState.ACTIVE):
                await signaling.update_room_state(
                    left_room_id,
                    CallState.ENDED,
                    f"disconnected_{user_id}",
                )
                # Professional back to available
                if room.professional_id:
                    await presence.set_available(room.professional_id)
