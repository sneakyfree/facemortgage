"""
Real-time presence service using Redis.

Manages professional availability status with:
- Sorted Set for online professionals (score = timestamp)
- Hash for detailed status per professional
- Pub/Sub for real-time updates
"""
import json
import asyncio
from datetime import datetime
from typing import Optional, List, Dict

import redis.asyncio as redis

from src.app.config import settings
from src.app.models.professional import ProfessionalStatus


class PresenceService:
    """
    Manages real-time presence/availability of professionals.

    Redis Data Structures:
    - Sorted Set 'online_professionals': members are professional_ids, scores are timestamps
    - Hash 'professional:{id}': status, last_heartbeat, camera_on, current_room
    - Pub/Sub 'presence': broadcasts status changes
    - Pub/Sub 'grid_updates': broadcasts grid-relevant changes
    """

    HEARTBEAT_TIMEOUT = settings.heartbeat_timeout_seconds
    HEARTBEAT_INTERVAL = settings.heartbeat_interval_seconds
    ONLINE_SET_KEY = "online_professionals"
    AVAILABLE_SET_KEY = "available_professionals"

    def __init__(self, redis_url: str = None):
        self.redis_url = redis_url or settings.redis_url
        self.redis: Optional[redis.Redis] = None
        self.pubsub: Optional[redis.client.PubSub] = None

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

    def _professional_key(self, professional_id: str) -> str:
        return f"professional:{professional_id}"

    # ==================== Status Management ====================

    async def set_online(self, professional_id: str, metadata: dict = None) -> None:
        """Mark a professional as online and available."""
        await self.connect()
        now = datetime.utcnow()
        timestamp = now.timestamp()

        pipe = self.redis.pipeline()

        # Add to online sorted set
        pipe.zadd(self.ONLINE_SET_KEY, {professional_id: timestamp})
        pipe.zadd(self.AVAILABLE_SET_KEY, {professional_id: timestamp})

        # Set detailed status
        status_data = {
            "status": ProfessionalStatus.ONLINE_AVAILABLE.value,
            "last_heartbeat": str(timestamp),
            "camera_on": "true",
            "online_since": str(timestamp),
            "current_room": "",
        }
        if metadata:
            status_data.update({k: str(v) for k, v in metadata.items()})

        pipe.hset(self._professional_key(professional_id), mapping=status_data)

        await pipe.execute()

        # Publish presence update
        await self._publish_event("presence", {
            "event": "online",
            "professional_id": professional_id,
            "timestamp": timestamp,
        })

        await self._publish_event("grid_updates", {
            "event": "professional_available",
            "professional_id": professional_id,
            "action": "add_to_grid",
        })

    async def set_offline(self, professional_id: str, reason: str = "disconnect") -> None:
        """Mark a professional as offline."""
        await self.connect()

        pipe = self.redis.pipeline()

        # Remove from sorted sets
        pipe.zrem(self.ONLINE_SET_KEY, professional_id)
        pipe.zrem(self.AVAILABLE_SET_KEY, professional_id)

        # Update status
        pipe.hset(self._professional_key(professional_id), mapping={
            "status": ProfessionalStatus.OFFLINE.value,
            "offline_reason": reason,
            "current_room": "",
        })

        await pipe.execute()

        # Publish updates
        await self._publish_event("presence", {
            "event": "offline",
            "professional_id": professional_id,
            "reason": reason,
        })

        await self._publish_event("grid_updates", {
            "event": "professional_offline",
            "professional_id": professional_id,
            "action": "remove_from_grid",
        })

    async def set_busy(self, professional_id: str, room_id: str = None) -> None:
        """Mark professional as busy (in call or occupied)."""
        await self.connect()
        now = datetime.utcnow().timestamp()

        pipe = self.redis.pipeline()

        # Remove from available set but keep in online set
        pipe.zrem(self.AVAILABLE_SET_KEY, professional_id)

        # Update status
        status_data = {
            "status": ProfessionalStatus.ONLINE_BUSY.value,
            "last_heartbeat": str(now),
        }
        if room_id:
            status_data["current_room"] = room_id

        pipe.hset(self._professional_key(professional_id), mapping=status_data)

        await pipe.execute()

        await self._publish_event("grid_updates", {
            "event": "professional_busy",
            "professional_id": professional_id,
            "action": "show_prerecorded",
        })

    async def set_in_call(self, professional_id: str, room_id: str) -> None:
        """Mark professional as in an active call."""
        await self.connect()
        now = datetime.utcnow().timestamp()

        pipe = self.redis.pipeline()

        pipe.zrem(self.AVAILABLE_SET_KEY, professional_id)
        pipe.hset(self._professional_key(professional_id), mapping={
            "status": ProfessionalStatus.IN_CALL.value,
            "current_room": room_id,
            "call_started": str(now),
            "last_heartbeat": str(now),
        })

        await pipe.execute()

        await self._publish_event("grid_updates", {
            "event": "professional_in_call",
            "professional_id": professional_id,
            "action": "show_prerecorded",
        })

    async def set_available(self, professional_id: str) -> None:
        """Mark professional as available again after a call."""
        await self.connect()
        now = datetime.utcnow().timestamp()

        pipe = self.redis.pipeline()

        # Add back to available set
        pipe.zadd(self.AVAILABLE_SET_KEY, {professional_id: now})

        # Update status
        pipe.hset(self._professional_key(professional_id), mapping={
            "status": ProfessionalStatus.ONLINE_AVAILABLE.value,
            "current_room": "",
            "last_heartbeat": str(now),
        })

        await pipe.execute()

        await self._publish_event("grid_updates", {
            "event": "professional_available",
            "professional_id": professional_id,
            "action": "show_live",
        })

    async def set_away(self, professional_id: str) -> None:
        """Mark professional as away (temporarily unavailable)."""
        await self.connect()

        pipe = self.redis.pipeline()

        pipe.zrem(self.AVAILABLE_SET_KEY, professional_id)
        pipe.hset(self._professional_key(professional_id), mapping={
            "status": ProfessionalStatus.AWAY.value,
        })

        await pipe.execute()

        await self._publish_event("grid_updates", {
            "event": "professional_away",
            "professional_id": professional_id,
            "action": "show_away",
        })

    # ==================== Heartbeat ====================

    async def heartbeat(self, professional_id: str) -> None:
        """Process heartbeat from a professional."""
        await self.connect()
        now = datetime.utcnow().timestamp()

        # Update timestamp in sorted set
        status = await self.get_professional_status(professional_id)

        pipe = self.redis.pipeline()

        # Always update online set
        pipe.zadd(self.ONLINE_SET_KEY, {professional_id: now})

        # Update available set only if status is available
        if status and status.get("status") == ProfessionalStatus.ONLINE_AVAILABLE.value:
            pipe.zadd(self.AVAILABLE_SET_KEY, {professional_id: now})

        pipe.hset(self._professional_key(professional_id), "last_heartbeat", str(now))

        await pipe.execute()

    async def check_stale_connections(self) -> List[str]:
        """Check and mark stale connections as offline. Returns list of removed IDs."""
        await self.connect()
        threshold = datetime.utcnow().timestamp() - self.HEARTBEAT_TIMEOUT

        # Find professionals with stale heartbeats
        stale_ids = await self.redis.zrangebyscore(
            self.ONLINE_SET_KEY,
            "-inf",
            threshold
        )

        for professional_id in stale_ids:
            await self.set_offline(professional_id, reason="heartbeat_timeout")

        return stale_ids

    # ==================== Queries ====================

    async def get_online_professionals(self, limit: int = 100, offset: int = 0) -> List[str]:
        """Get list of online professional IDs, ordered by most recent activity."""
        await self.connect()
        return await self.redis.zrevrange(
            self.ONLINE_SET_KEY,
            offset,
            offset + limit - 1
        )

    async def get_available_professionals(self, limit: int = 100, offset: int = 0) -> List[str]:
        """Get professionals who are online AND available (not in calls)."""
        await self.connect()
        return await self.redis.zrevrange(
            self.AVAILABLE_SET_KEY,
            offset,
            offset + limit - 1
        )

    async def get_professional_status(self, professional_id: str) -> Optional[Dict[str, str]]:
        """Get detailed status for a professional."""
        await self.connect()
        data = await self.redis.hgetall(self._professional_key(professional_id))
        return data if data else None

    async def get_multiple_statuses(self, professional_ids: List[str]) -> Dict[str, Dict[str, str]]:
        """Get statuses for multiple professionals efficiently."""
        await self.connect()
        pipe = self.redis.pipeline()

        for prof_id in professional_ids:
            pipe.hgetall(self._professional_key(prof_id))

        results = await pipe.execute()

        return {
            prof_id: status
            for prof_id, status in zip(professional_ids, results)
            if status
        }

    async def get_online_count(self) -> int:
        """Get count of online professionals."""
        await self.connect()
        return await self.redis.zcard(self.ONLINE_SET_KEY)

    async def get_available_count(self) -> int:
        """Get count of available (not busy) professionals."""
        await self.connect()
        return await self.redis.zcard(self.AVAILABLE_SET_KEY)

    async def is_online(self, professional_id: str) -> bool:
        """Check if a professional is online."""
        await self.connect()
        score = await self.redis.zscore(self.ONLINE_SET_KEY, professional_id)
        return score is not None

    async def is_available(self, professional_id: str) -> bool:
        """Check if a professional is available for calls."""
        await self.connect()
        score = await self.redis.zscore(self.AVAILABLE_SET_KEY, professional_id)
        return score is not None

    # ==================== Pub/Sub ====================

    async def _publish_event(self, channel: str, event: dict) -> None:
        """Publish an event to a channel."""
        await self.connect()
        await self.redis.publish(channel, json.dumps(event))

    async def subscribe(self, *channels: str):
        """Subscribe to channels for real-time updates."""
        await self.connect()
        if self.pubsub is None:
            self.pubsub = self.redis.pubsub()
        await self.pubsub.subscribe(*channels)
        return self.pubsub

    async def get_message(self, timeout: float = 1.0) -> Optional[dict]:
        """Get next message from subscribed channels."""
        if self.pubsub:
            message = await self.pubsub.get_message(
                ignore_subscribe_messages=True,
                timeout=timeout
            )
            if message and message.get("type") == "message":
                return json.loads(message["data"])
        return None


# Singleton instance
_presence_service: Optional[PresenceService] = None


def get_presence_service() -> PresenceService:
    """Get the presence service singleton."""
    global _presence_service
    if _presence_service is None:
        _presence_service = PresenceService()
    return _presence_service


# Background task for heartbeat checking
async def heartbeat_checker_task():
    """Background task to clean up stale connections. Run every 10 seconds."""
    service = get_presence_service()
    while True:
        try:
            stale = await service.check_stale_connections()
            if stale:
                print(f"Removed {len(stale)} stale connections: {stale}")
        except Exception as e:
            print(f"Error in heartbeat checker: {e}")
        await asyncio.sleep(10)
