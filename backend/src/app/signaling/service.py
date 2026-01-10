"""
WebRTC signaling service for managing video call connections.

Handles:
- Room creation and management
- SDP offer/answer exchange
- ICE candidate exchange
- Call state management
"""
import json
import asyncio
from datetime import datetime
from typing import Optional, Dict, Set, Any
from uuid import UUID, uuid4
from dataclasses import dataclass, field
from enum import Enum

import redis.asyncio as redis

from src.app.config import settings


class CallState(str, Enum):
    """States a call can be in."""
    INITIATING = "initiating"  # Borrower clicked call, waiting for professional
    RINGING = "ringing"  # Professional notified, waiting for answer
    CONNECTING = "connecting"  # Both parties connecting WebRTC
    ACTIVE = "active"  # Call in progress
    ENDED = "ended"  # Call finished
    MISSED = "missed"  # Professional didn't answer
    DECLINED = "declined"  # Professional declined
    FAILED = "failed"  # Technical failure


@dataclass
class CallRoom:
    """Represents a video call room."""
    room_id: str
    borrower_id: str
    professional_id: str
    state: CallState = CallState.INITIATING
    created_at: datetime = field(default_factory=datetime.utcnow)
    ring_started_at: Optional[datetime] = None
    answered_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    end_reason: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "room_id": self.room_id,
            "borrower_id": self.borrower_id,
            "professional_id": self.professional_id,
            "state": self.state.value,
            "created_at": self.created_at.isoformat(),
            "ring_started_at": self.ring_started_at.isoformat() if self.ring_started_at else None,
            "answered_at": self.answered_at.isoformat() if self.answered_at else None,
            "ended_at": self.ended_at.isoformat() if self.ended_at else None,
            "end_reason": self.end_reason,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "CallRoom":
        return cls(
            room_id=data["room_id"],
            borrower_id=data["borrower_id"],
            professional_id=data["professional_id"],
            state=CallState(data["state"]),
            created_at=datetime.fromisoformat(data["created_at"]),
            ring_started_at=datetime.fromisoformat(data["ring_started_at"]) if data.get("ring_started_at") else None,
            answered_at=datetime.fromisoformat(data["answered_at"]) if data.get("answered_at") else None,
            ended_at=datetime.fromisoformat(data["ended_at"]) if data.get("ended_at") else None,
            end_reason=data.get("end_reason"),
        )


class SignalingService:
    """
    Manages WebRTC signaling for video calls.

    Uses Redis for:
    - Room state storage
    - Pub/Sub for signaling messages between participants
    """

    ROOM_TTL = settings.room_ttl_seconds
    RING_TIMEOUT = settings.ring_timeout_seconds

    def __init__(self, redis_url: str = None):
        self.redis_url = redis_url or settings.redis_url
        self.redis: Optional[redis.Redis] = None

    async def connect(self):
        """Initialize Redis connection."""
        if self.redis is None:
            self.redis = await redis.from_url(self.redis_url, decode_responses=True)
        return self.redis

    async def disconnect(self):
        """Close Redis connection."""
        if self.redis:
            await self.redis.close()
            self.redis = None

    def _room_key(self, room_id: str) -> str:
        return f"call_room:{room_id}"

    def _user_room_key(self, user_id: str) -> str:
        return f"user_active_room:{user_id}"

    def _signaling_channel(self, room_id: str) -> str:
        return f"signaling:{room_id}"

    async def create_room(
        self,
        borrower_id: str,
        professional_id: str,
    ) -> CallRoom:
        """
        Create a new call room.

        Returns the room object with a unique room_id.
        """
        await self.connect()

        # Check if either party is already in a call
        borrower_room = await self.get_user_active_room(borrower_id)
        if borrower_room:
            raise ValueError("Borrower is already in a call")

        professional_room = await self.get_user_active_room(professional_id)
        if professional_room:
            raise ValueError("Professional is already in a call")

        # Create room
        room_id = str(uuid4())
        room = CallRoom(
            room_id=room_id,
            borrower_id=borrower_id,
            professional_id=professional_id,
            state=CallState.INITIATING,
        )

        # Store room in Redis
        await self.redis.setex(
            self._room_key(room_id),
            self.ROOM_TTL,
            json.dumps(room.to_dict()),
        )

        # Link users to room
        await self.redis.setex(self._user_room_key(borrower_id), self.ROOM_TTL, room_id)
        await self.redis.setex(self._user_room_key(professional_id), self.ROOM_TTL, room_id)

        return room

    async def get_room(self, room_id: str) -> Optional[CallRoom]:
        """Get a room by ID."""
        await self.connect()
        data = await self.redis.get(self._room_key(room_id))
        if data:
            return CallRoom.from_dict(json.loads(data))
        return None

    async def get_user_active_room(self, user_id: str) -> Optional[CallRoom]:
        """Get the active room for a user."""
        await self.connect()
        room_id = await self.redis.get(self._user_room_key(user_id))
        if room_id:
            return await self.get_room(room_id)
        return None

    async def update_room_state(
        self,
        room_id: str,
        new_state: CallState,
        end_reason: str = None,
    ) -> Optional[CallRoom]:
        """Update the state of a room."""
        await self.connect()

        room = await self.get_room(room_id)
        if not room:
            return None

        room.state = new_state
        now = datetime.utcnow()

        if new_state == CallState.RINGING:
            room.ring_started_at = now
        elif new_state == CallState.ACTIVE:
            room.answered_at = now
        elif new_state in (CallState.ENDED, CallState.MISSED, CallState.DECLINED, CallState.FAILED):
            room.ended_at = now
            room.end_reason = end_reason

        # Save updated room
        await self.redis.setex(
            self._room_key(room_id),
            self.ROOM_TTL,
            json.dumps(room.to_dict()),
        )

        # Clean up user room links if call ended
        if new_state in (CallState.ENDED, CallState.MISSED, CallState.DECLINED, CallState.FAILED):
            await self.redis.delete(self._user_room_key(room.borrower_id))
            await self.redis.delete(self._user_room_key(room.professional_id))

        return room

    async def send_signaling_message(
        self,
        room_id: str,
        sender_id: str,
        message_type: str,
        payload: dict,
    ) -> None:
        """
        Send a signaling message to the room.

        Message types: offer, answer, ice_candidate, call_state
        """
        await self.connect()

        message = {
            "type": message_type,
            "sender_id": sender_id,
            "room_id": room_id,
            "payload": payload,
            "timestamp": datetime.utcnow().isoformat(),
        }

        await self.redis.publish(
            self._signaling_channel(room_id),
            json.dumps(message),
        )

    async def subscribe_to_room(self, room_id: str):
        """Subscribe to signaling messages for a room."""
        await self.connect()
        pubsub = self.redis.pubsub()
        await pubsub.subscribe(self._signaling_channel(room_id))
        return pubsub

    async def get_ice_servers(self) -> list:
        """
        Get ICE server configuration for WebRTC.

        Returns STUN/TURN servers for NAT traversal.
        """
        servers = [
            {"urls": "stun:stun.l.google.com:19302"},
            {"urls": "stun:stun1.l.google.com:19302"},
        ]

        # Add configured TURN server if available
        if settings.turn_server_url:
            servers.append({
                "urls": settings.turn_server_url,
                "username": settings.turn_server_username,
                "credential": settings.turn_server_credential,
            })

        return servers

    def calculate_pickup_time(self, room: CallRoom) -> Optional[float]:
        """
        Calculate pickup time in seconds.

        Time from ring_started_at to answered_at.
        """
        if room.ring_started_at and room.answered_at:
            delta = room.answered_at - room.ring_started_at
            return delta.total_seconds()
        return None


# Singleton instance
_signaling_service: Optional[SignalingService] = None


def get_signaling_service() -> SignalingService:
    """Get the signaling service singleton."""
    global _signaling_service
    if _signaling_service is None:
        _signaling_service = SignalingService()
    return _signaling_service
