"""
LiveKit video infrastructure service.

Provides integration with LiveKit for scalable video calls.
Can be used as an alternative to the built-in WebRTC signaling
when the platform needs to scale beyond peer-to-peer connections.

Requirements:
    pip install livekit livekit-api

Environment variables:
    LIVEKIT_URL: LiveKit server URL (e.g., wss://your-project.livekit.cloud)
    LIVEKIT_API_KEY: API key for authentication
    LIVEKIT_API_SECRET: API secret for token generation
"""
import logging
import time
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from enum import Enum

from src.app.config import settings

logger = logging.getLogger(__name__)


class ParticipantRole(str, Enum):
    """Roles for room participants."""
    BORROWER = "borrower"
    PROFESSIONAL = "professional"
    OBSERVER = "observer"  # For call recording/monitoring


@dataclass
class RoomToken:
    """Token for joining a LiveKit room."""
    token: str
    room_name: str
    participant_identity: str
    expires_at: datetime


@dataclass
class RoomInfo:
    """Information about a LiveKit room."""
    name: str
    sid: str
    num_participants: int
    created_at: datetime
    is_recording: bool


class LiveKitService:
    """
    Service for managing LiveKit video infrastructure.

    Provides room creation, token generation, and recording management
    for video calls that need to scale beyond peer-to-peer.
    """

    # Token expiry time
    TOKEN_TTL_SECONDS = 3600  # 1 hour

    # Room configuration
    MAX_PARTICIPANTS = 2  # Borrower + Professional
    EMPTY_ROOM_TIMEOUT = 300  # 5 minutes

    def __init__(
        self,
        livekit_url: Optional[str] = None,
        api_key: Optional[str] = None,
        api_secret: Optional[str] = None,
    ):
        self.livekit_url = livekit_url or getattr(settings, 'livekit_url', None)
        self.api_key = api_key or getattr(settings, 'livekit_api_key', None)
        self.api_secret = api_secret or getattr(settings, 'livekit_api_secret', None)

        self._api = None
        self._token_api = None

    @property
    def is_configured(self) -> bool:
        """Check if LiveKit is properly configured."""
        return all([self.livekit_url, self.api_key, self.api_secret])

    def _get_api(self):
        """Get or create the LiveKit API client."""
        if not self.is_configured:
            raise RuntimeError(
                "LiveKit is not configured. Set LIVEKIT_URL, LIVEKIT_API_KEY, "
                "and LIVEKIT_API_SECRET environment variables."
            )

        if self._api is None:
            try:
                from livekit import api
                self._api = api.LiveKitAPI(
                    self.livekit_url,
                    self.api_key,
                    self.api_secret,
                )
            except ImportError:
                raise RuntimeError(
                    "LiveKit SDK not installed. Install with: pip install livekit-api"
                )

        return self._api

    def _get_token_api(self):
        """Get the token generation API."""
        if self._token_api is None:
            try:
                from livekit import api
                self._token_api = api.AccessToken
            except ImportError:
                raise RuntimeError(
                    "LiveKit SDK not installed. Install with: pip install livekit-api"
                )

        return self._token_api

    def generate_room_name(self, borrower_id: str, professional_id: str) -> str:
        """Generate a unique room name for a call."""
        timestamp = int(time.time())
        return f"fm-call-{borrower_id[:8]}-{professional_id[:8]}-{timestamp}"

    def create_token(
        self,
        room_name: str,
        participant_identity: str,
        participant_name: str,
        role: ParticipantRole,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> RoomToken:
        """
        Create an access token for a participant to join a room.

        Args:
            room_name: Name of the room to join
            participant_identity: Unique identifier for the participant
            participant_name: Display name for the participant
            role: Role of the participant (borrower, professional, observer)
            metadata: Optional metadata to attach to the participant

        Returns:
            RoomToken with the JWT and expiry information
        """
        AccessToken = self._get_token_api()

        # Create token with grants
        token = AccessToken(
            api_key=self.api_key,
            api_secret=self.api_secret,
        )

        # Set identity and name
        token.identity = participant_identity
        token.name = participant_name

        # Set metadata
        if metadata:
            import json
            token.metadata = json.dumps(metadata)

        # Configure grants based on role
        grants = {
            "roomJoin": True,
            "room": room_name,
            "canPublish": role != ParticipantRole.OBSERVER,
            "canSubscribe": True,
            "canPublishData": True,
        }

        # Professionals can start recordings
        if role == ParticipantRole.PROFESSIONAL:
            grants["roomRecord"] = True

        token.add_grant(grants)

        # Set expiry
        expires_at = datetime.utcnow() + timedelta(seconds=self.TOKEN_TTL_SECONDS)
        token.ttl = timedelta(seconds=self.TOKEN_TTL_SECONDS)

        return RoomToken(
            token=token.to_jwt(),
            room_name=room_name,
            participant_identity=participant_identity,
            expires_at=expires_at,
        )

    async def create_room(
        self,
        room_name: str,
        empty_timeout: int = None,
        max_participants: int = None,
    ) -> RoomInfo:
        """
        Create a new LiveKit room.

        Args:
            room_name: Name of the room to create
            empty_timeout: Seconds to wait before closing empty room
            max_participants: Maximum number of participants

        Returns:
            RoomInfo with room details
        """
        lk_api = self._get_api()

        try:
            from livekit import api as lk

            room = await lk_api.room.create_room(
                lk.CreateRoomRequest(
                    name=room_name,
                    empty_timeout=empty_timeout or self.EMPTY_ROOM_TIMEOUT,
                    max_participants=max_participants or self.MAX_PARTICIPANTS,
                )
            )

            return RoomInfo(
                name=room.name,
                sid=room.sid,
                num_participants=room.num_participants,
                created_at=datetime.utcnow(),
                is_recording=False,
            )
        except Exception as e:
            logger.error(f"Failed to create LiveKit room: {e}")
            raise

    async def get_room(self, room_name: str) -> Optional[RoomInfo]:
        """Get information about a room."""
        lk_api = self._get_api()

        try:
            rooms = await lk_api.room.list_rooms(names=[room_name])
            if rooms.rooms:
                room = rooms.rooms[0]
                return RoomInfo(
                    name=room.name,
                    sid=room.sid,
                    num_participants=room.num_participants,
                    created_at=datetime.utcnow(),
                    is_recording=room.active_recording,
                )
            return None
        except Exception as e:
            logger.error(f"Failed to get room info: {e}")
            return None

    async def delete_room(self, room_name: str) -> bool:
        """Delete a room."""
        lk_api = self._get_api()

        try:
            from livekit import api as lk
            await lk_api.room.delete_room(
                lk.DeleteRoomRequest(room=room_name)
            )
            return True
        except Exception as e:
            logger.error(f"Failed to delete room: {e}")
            return False

    async def list_participants(self, room_name: str) -> List[Dict[str, Any]]:
        """List participants in a room."""
        lk_api = self._get_api()

        try:
            from livekit import api as lk
            response = await lk_api.room.list_participants(
                lk.ListParticipantsRequest(room=room_name)
            )

            return [
                {
                    "identity": p.identity,
                    "name": p.name,
                    "state": p.state,
                    "joined_at": p.joined_at,
                    "is_publisher": p.permission.can_publish,
                }
                for p in response.participants
            ]
        except Exception as e:
            logger.error(f"Failed to list participants: {e}")
            return []

    async def remove_participant(
        self,
        room_name: str,
        identity: str,
    ) -> bool:
        """Remove a participant from a room."""
        lk_api = self._get_api()

        try:
            from livekit import api as lk
            await lk_api.room.remove_participant(
                lk.RoomParticipantIdentity(
                    room=room_name,
                    identity=identity,
                )
            )
            return True
        except Exception as e:
            logger.error(f"Failed to remove participant: {e}")
            return False

    async def start_recording(
        self,
        room_name: str,
        output_path: Optional[str] = None,
    ) -> Optional[str]:
        """
        Start recording a room.

        Args:
            room_name: Name of the room to record
            output_path: S3 path for recording output (optional)

        Returns:
            Recording ID if successful, None otherwise
        """
        lk_api = self._get_api()

        try:
            from livekit import api as lk

            # Configure egress output
            if output_path:
                output = lk.EncodedFileOutput(
                    file_type=lk.EncodedFileType.MP4,
                    filepath=output_path,
                )
            else:
                # Use default S3 configuration from settings
                bucket = getattr(settings, 's3_bucket_name', 'facemortgage-recordings')
                output = lk.EncodedFileOutput(
                    file_type=lk.EncodedFileType.MP4,
                    s3=lk.S3Upload(
                        bucket=bucket,
                        region=getattr(settings, 'aws_region', 'us-east-1'),
                    ),
                )

            egress = await lk_api.egress.start_room_composite_egress(
                lk.RoomCompositeEgressRequest(
                    room_name=room_name,
                    file=output,
                )
            )

            logger.info(f"Started recording for room {room_name}: {egress.egress_id}")
            return egress.egress_id

        except Exception as e:
            logger.error(f"Failed to start recording: {e}")
            return None

    async def stop_recording(self, egress_id: str) -> bool:
        """Stop a recording."""
        lk_api = self._get_api()

        try:
            from livekit import api as lk
            await lk_api.egress.stop_egress(
                lk.StopEgressRequest(egress_id=egress_id)
            )
            logger.info(f"Stopped recording: {egress_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to stop recording: {e}")
            return False

    async def get_recording_status(self, egress_id: str) -> Optional[Dict[str, Any]]:
        """Get the status of a recording."""
        lk_api = self._get_api()

        try:
            from livekit import api as lk
            egress_list = await lk_api.egress.list_egress(
                lk.ListEgressRequest(egress_id=egress_id)
            )

            if egress_list.items:
                egress = egress_list.items[0]
                return {
                    "egress_id": egress.egress_id,
                    "room_name": egress.room_name,
                    "status": egress.status,
                    "started_at": egress.started_at,
                    "ended_at": egress.ended_at,
                }
            return None
        except Exception as e:
            logger.error(f"Failed to get recording status: {e}")
            return None


# Singleton instance
_livekit_service: Optional[LiveKitService] = None


def get_livekit_service() -> LiveKitService:
    """Get the LiveKit service singleton."""
    global _livekit_service
    if _livekit_service is None:
        _livekit_service = LiveKitService()
    return _livekit_service
