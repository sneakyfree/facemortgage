"""
Tests for the PresenceService.

Tests cover:
- Status management (online, offline, busy, available, away)
- Heartbeat functionality
- Stale connection detection
- Query methods
- Pub/Sub functionality
"""
import asyncio
import json
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.app.presence.service import PresenceService, get_presence_service
from src.app.models.professional import ProfessionalStatus


class TestPresenceService:
    """Tests for the PresenceService class."""

    @pytest.fixture
    def mock_redis(self):
        """Create a mock Redis client."""
        redis = AsyncMock()
        redis.zadd = AsyncMock()
        redis.zrem = AsyncMock()
        redis.hset = AsyncMock()
        redis.hgetall = AsyncMock(return_value={})
        redis.zrevrange = AsyncMock(return_value=[])
        redis.zrangebyscore = AsyncMock(return_value=[])
        redis.zcard = AsyncMock(return_value=0)
        redis.zscore = AsyncMock(return_value=None)
        redis.publish = AsyncMock()
        redis.close = AsyncMock()

        # Pipeline mock
        pipeline = AsyncMock()
        pipeline.zadd = MagicMock()
        pipeline.zrem = MagicMock()
        pipeline.hset = MagicMock()
        pipeline.execute = AsyncMock()
        redis.pipeline = MagicMock(return_value=pipeline)

        return redis

    @pytest.fixture
    def presence_service(self, mock_redis):
        """Create a PresenceService with mocked Redis."""
        service = PresenceService(redis_url="redis://localhost:6379")
        service.redis = mock_redis
        return service

    # ==================== Status Management Tests ====================

    @pytest.mark.asyncio
    async def test_set_online(self, presence_service, mock_redis):
        """Should mark professional as online and publish events."""
        professional_id = "test-prof-123"

        await presence_service.set_online(professional_id)

        # Verify pipeline operations were queued
        pipeline = mock_redis.pipeline()
        assert pipeline.zadd.called
        assert pipeline.hset.called
        pipeline.execute.assert_called()

        # Verify events were published
        assert mock_redis.publish.call_count == 2  # presence and grid_updates

    @pytest.mark.asyncio
    async def test_set_online_with_metadata(self, presence_service, mock_redis):
        """Should include metadata when setting online."""
        professional_id = "test-prof-123"
        metadata = {"custom_field": "value"}

        await presence_service.set_online(professional_id, metadata)

        pipeline = mock_redis.pipeline()
        assert pipeline.hset.called

    @pytest.mark.asyncio
    async def test_set_offline(self, presence_service, mock_redis):
        """Should mark professional as offline and remove from sets."""
        professional_id = "test-prof-123"

        await presence_service.set_offline(professional_id, reason="disconnect")

        pipeline = mock_redis.pipeline()
        assert pipeline.zrem.called
        assert pipeline.hset.called
        assert mock_redis.publish.call_count == 2

    @pytest.mark.asyncio
    async def test_set_busy(self, presence_service, mock_redis):
        """Should mark professional as busy."""
        professional_id = "test-prof-123"
        room_id = "room-456"

        await presence_service.set_busy(professional_id, room_id)

        pipeline = mock_redis.pipeline()
        # Should remove from available set but stay in online set
        assert pipeline.zrem.called
        assert pipeline.hset.called

    @pytest.mark.asyncio
    async def test_set_in_call(self, presence_service, mock_redis):
        """Should mark professional as in a call."""
        professional_id = "test-prof-123"
        room_id = "room-456"

        await presence_service.set_in_call(professional_id, room_id)

        pipeline = mock_redis.pipeline()
        assert pipeline.zrem.called
        assert pipeline.hset.called
        assert mock_redis.publish.called

    @pytest.mark.asyncio
    async def test_set_available(self, presence_service, mock_redis):
        """Should mark professional as available after call."""
        professional_id = "test-prof-123"

        await presence_service.set_available(professional_id)

        pipeline = mock_redis.pipeline()
        # Should add back to available set
        assert pipeline.zadd.called
        assert pipeline.hset.called

    @pytest.mark.asyncio
    async def test_set_away(self, presence_service, mock_redis):
        """Should mark professional as away."""
        professional_id = "test-prof-123"

        await presence_service.set_away(professional_id)

        pipeline = mock_redis.pipeline()
        assert pipeline.zrem.called
        assert pipeline.hset.called

    # ==================== Heartbeat Tests ====================

    @pytest.mark.asyncio
    async def test_heartbeat_updates_timestamp(self, presence_service, mock_redis):
        """Should update heartbeat timestamp."""
        professional_id = "test-prof-123"
        mock_redis.hgetall.return_value = {
            "status": ProfessionalStatus.ONLINE_AVAILABLE.value,
        }

        await presence_service.heartbeat(professional_id)

        pipeline = mock_redis.pipeline()
        assert pipeline.zadd.called
        assert pipeline.hset.called

    @pytest.mark.asyncio
    async def test_heartbeat_available_updates_both_sets(self, presence_service, mock_redis):
        """Available professional should update both online and available sets."""
        professional_id = "test-prof-123"
        mock_redis.hgetall.return_value = {
            "status": ProfessionalStatus.ONLINE_AVAILABLE.value,
        }

        await presence_service.heartbeat(professional_id)

        pipeline = mock_redis.pipeline()
        # Should call zadd for both sets
        assert pipeline.zadd.call_count >= 1

    @pytest.mark.asyncio
    async def test_check_stale_connections(self, presence_service, mock_redis):
        """Should detect and remove stale connections."""
        stale_ids = ["stale-1", "stale-2"]
        mock_redis.zrangebyscore.return_value = stale_ids

        result = await presence_service.check_stale_connections()

        assert len(result) == 2
        mock_redis.zrangebyscore.assert_called_once()
        # Each stale ID should trigger set_offline
        assert mock_redis.pipeline().execute.call_count >= 2

    @pytest.mark.asyncio
    async def test_check_stale_connections_empty(self, presence_service, mock_redis):
        """Should return empty list when no stale connections."""
        mock_redis.zrangebyscore.return_value = []

        result = await presence_service.check_stale_connections()

        assert result == []

    # ==================== Query Tests ====================

    @pytest.mark.asyncio
    async def test_get_online_professionals(self, presence_service, mock_redis):
        """Should return list of online professional IDs."""
        expected = ["prof-1", "prof-2", "prof-3"]
        mock_redis.zrevrange.return_value = expected

        result = await presence_service.get_online_professionals(limit=10)

        assert result == expected
        mock_redis.zrevrange.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_available_professionals(self, presence_service, mock_redis):
        """Should return list of available professional IDs."""
        expected = ["prof-1", "prof-2"]
        mock_redis.zrevrange.return_value = expected

        result = await presence_service.get_available_professionals(limit=10)

        assert result == expected

    @pytest.mark.asyncio
    async def test_get_professional_status(self, presence_service, mock_redis):
        """Should return detailed status for a professional."""
        expected = {
            "status": "online_available",
            "camera_on": "true",
            "last_heartbeat": "1234567890.0",
        }
        mock_redis.hgetall.return_value = expected

        result = await presence_service.get_professional_status("prof-123")

        assert result == expected

    @pytest.mark.asyncio
    async def test_get_professional_status_not_found(self, presence_service, mock_redis):
        """Should return None for non-existent professional."""
        mock_redis.hgetall.return_value = {}

        result = await presence_service.get_professional_status("unknown")

        assert result is None

    @pytest.mark.asyncio
    async def test_get_multiple_statuses(self, presence_service, mock_redis):
        """Should return statuses for multiple professionals."""
        professional_ids = ["prof-1", "prof-2", "prof-3"]
        statuses = [
            {"status": "online_available"},
            {"status": "online_busy"},
            {},  # Not found
        ]

        pipeline = mock_redis.pipeline()
        pipeline.execute.return_value = statuses

        result = await presence_service.get_multiple_statuses(professional_ids)

        assert "prof-1" in result
        assert "prof-2" in result
        assert "prof-3" not in result  # Empty status excluded

    @pytest.mark.asyncio
    async def test_get_online_count(self, presence_service, mock_redis):
        """Should return count of online professionals."""
        mock_redis.zcard.return_value = 42

        result = await presence_service.get_online_count()

        assert result == 42
        mock_redis.zcard.assert_called_with("online_professionals")

    @pytest.mark.asyncio
    async def test_get_available_count(self, presence_service, mock_redis):
        """Should return count of available professionals."""
        mock_redis.zcard.return_value = 30

        result = await presence_service.get_available_count()

        assert result == 30
        mock_redis.zcard.assert_called_with("available_professionals")

    @pytest.mark.asyncio
    async def test_is_online_true(self, presence_service, mock_redis):
        """Should return True for online professional."""
        mock_redis.zscore.return_value = 1234567890.0

        result = await presence_service.is_online("prof-123")

        assert result is True

    @pytest.mark.asyncio
    async def test_is_online_false(self, presence_service, mock_redis):
        """Should return False for offline professional."""
        mock_redis.zscore.return_value = None

        result = await presence_service.is_online("prof-123")

        assert result is False

    @pytest.mark.asyncio
    async def test_is_available_true(self, presence_service, mock_redis):
        """Should return True for available professional."""
        mock_redis.zscore.return_value = 1234567890.0

        result = await presence_service.is_available("prof-123")

        assert result is True

    @pytest.mark.asyncio
    async def test_is_available_false(self, presence_service, mock_redis):
        """Should return False for busy professional."""
        mock_redis.zscore.return_value = None

        result = await presence_service.is_available("prof-123")

        assert result is False

    # ==================== Pub/Sub Tests ====================

    @pytest.mark.asyncio
    async def test_publish_event(self, presence_service, mock_redis):
        """Should publish events to Redis channel."""
        event = {"event": "test", "data": "value"}

        await presence_service._publish_event("test_channel", event)

        mock_redis.publish.assert_called_once()
        call_args = mock_redis.publish.call_args
        assert call_args[0][0] == "test_channel"
        assert json.loads(call_args[0][1]) == event

    @pytest.mark.asyncio
    async def test_subscribe(self, presence_service, mock_redis):
        """Should subscribe to channels."""
        pubsub = AsyncMock()
        pubsub.subscribe = AsyncMock()
        mock_redis.pubsub = MagicMock(return_value=pubsub)

        result = await presence_service.subscribe("presence", "grid_updates")

        pubsub.subscribe.assert_called_once_with("presence", "grid_updates")
        assert result == pubsub

    @pytest.mark.asyncio
    async def test_get_message(self, presence_service, mock_redis):
        """Should get and parse messages from pubsub."""
        pubsub = AsyncMock()
        pubsub.get_message.return_value = {
            "type": "message",
            "data": '{"event": "test"}',
        }
        presence_service.pubsub = pubsub

        result = await presence_service.get_message()

        assert result == {"event": "test"}

    @pytest.mark.asyncio
    async def test_get_message_ignores_non_messages(self, presence_service, mock_redis):
        """Should ignore non-message types."""
        pubsub = AsyncMock()
        pubsub.get_message.return_value = {
            "type": "subscribe",
            "data": 1,
        }
        presence_service.pubsub = pubsub

        result = await presence_service.get_message()

        assert result is None

    @pytest.mark.asyncio
    async def test_get_message_no_pubsub(self, presence_service, mock_redis):
        """Should return None if not subscribed."""
        presence_service.pubsub = None

        result = await presence_service.get_message()

        assert result is None

    # ==================== Connection Management Tests ====================

    @pytest.mark.asyncio
    async def test_connect_creates_client(self, presence_service):
        """Should create Redis client on connect."""
        presence_service.redis = None

        with patch("redis.asyncio.from_url", new_callable=AsyncMock) as mock_from_url:
            mock_client = AsyncMock()
            mock_from_url.return_value = mock_client

            result = await presence_service.connect()

            mock_from_url.assert_called_once()
            assert result == mock_client

    @pytest.mark.asyncio
    async def test_connect_reuses_existing_client(self, presence_service, mock_redis):
        """Should reuse existing Redis client."""
        result = await presence_service.connect()

        assert result == mock_redis

    @pytest.mark.asyncio
    async def test_disconnect_closes_client(self, presence_service, mock_redis):
        """Should close Redis client on disconnect."""
        await presence_service.disconnect()

        mock_redis.close.assert_called_once()
        assert presence_service.redis is None

    def test_professional_key(self, presence_service):
        """Should build correct Redis key for professional."""
        key = presence_service._professional_key("prof-123")

        assert key == "professional:prof-123"


class TestGetPresenceService:
    """Tests for the get_presence_service factory function."""

    def test_returns_singleton(self):
        """Should return the same instance on multiple calls."""
        # Reset singleton
        import src.app.presence.service as service_module
        service_module._presence_service = None

        service1 = get_presence_service()
        service2 = get_presence_service()

        assert service1 is service2

        # Clean up
        service_module._presence_service = None
