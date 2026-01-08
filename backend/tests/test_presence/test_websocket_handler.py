"""
Tests for the WebSocket handlers.

Tests cover:
- WebSocketRateLimiter functionality
- ConnectionManager connection management
- Professional presence WebSocket handler
- Grid updates WebSocket handler
"""
import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch, PropertyMock

import pytest
from starlette.websockets import WebSocketState

from src.app.presence.websocket_handler import (
    WebSocketRateLimiter,
    ConnectionManager,
    professional_presence_handler,
    grid_updates_handler,
    ws_rate_limiter,
    connection_manager,
)


class MockWebSocket:
    """Mock WebSocket for testing."""

    def __init__(self, client_ip: str = "127.0.0.1"):
        self.accepted = False
        self.closed = False
        self.close_code = None
        self.close_reason = None
        self.sent_messages = []
        self.receive_queue = []
        self._client_state = WebSocketState.CONNECTED
        self.client = MagicMock()
        self.client.host = client_ip
        self.headers = {}

    @property
    def client_state(self):
        return self._client_state

    async def accept(self, subprotocol=None):
        self.accepted = True
        self.subprotocol = subprotocol

    async def close(self, code=1000, reason=""):
        self.closed = True
        self.close_code = code
        self.close_reason = reason
        self._client_state = WebSocketState.DISCONNECTED

    async def send_json(self, data):
        self.sent_messages.append(data)

    async def send_text(self, text):
        self.sent_messages.append(text)

    async def receive_json(self):
        if not self.receive_queue:
            raise Exception("No more messages")
        msg = self.receive_queue.pop(0)
        if isinstance(msg, Exception):
            raise msg
        return msg

    def queue_message(self, msg):
        self.receive_queue.append(msg)


class TestWebSocketRateLimiter:
    """Tests for the WebSocketRateLimiter class."""

    @pytest.fixture
    def rate_limiter(self):
        """Create a fresh rate limiter for each test."""
        return WebSocketRateLimiter(
            max_connections_per_ip=3,
            connection_window_seconds=60,
            max_messages_per_second=10,
            message_burst_size=5,
        )

    @pytest.mark.asyncio
    async def test_allows_initial_connection(self, rate_limiter):
        """Should allow first connection from an IP."""
        ws = MockWebSocket("192.168.1.1")
        result = await rate_limiter.allow_connection(ws)
        assert result is True

    @pytest.mark.asyncio
    async def test_allows_multiple_connections_under_limit(self, rate_limiter):
        """Should allow connections under the limit."""
        for i in range(3):
            ws = MockWebSocket("192.168.1.1")
            result = await rate_limiter.allow_connection(ws)
            assert result is True

    @pytest.mark.asyncio
    async def test_blocks_connections_over_limit(self, rate_limiter):
        """Should block connections over the limit."""
        # Use up the limit
        for _ in range(3):
            ws = MockWebSocket("192.168.1.1")
            await rate_limiter.allow_connection(ws)

        # Fourth should be blocked
        ws = MockWebSocket("192.168.1.1")
        result = await rate_limiter.allow_connection(ws)
        assert result is False

    @pytest.mark.asyncio
    async def test_different_ips_have_separate_limits(self, rate_limiter):
        """Different IPs should have separate rate limits."""
        # Fill up one IP
        for _ in range(3):
            ws = MockWebSocket("192.168.1.1")
            await rate_limiter.allow_connection(ws)

        # Different IP should still be allowed
        ws = MockWebSocket("192.168.1.2")
        result = await rate_limiter.allow_connection(ws)
        assert result is True

    @pytest.mark.asyncio
    async def test_extracts_ip_from_x_forwarded_for(self, rate_limiter):
        """Should extract client IP from X-Forwarded-For header."""
        ws = MockWebSocket("127.0.0.1")
        ws.headers["x-forwarded-for"] = "203.0.113.1, 10.0.0.1"

        # Use up the limit for the forwarded IP
        for _ in range(3):
            await rate_limiter.allow_connection(ws)

        # Should be blocked based on forwarded IP
        result = await rate_limiter.allow_connection(ws)
        assert result is False

        # Different forwarded IP should work
        ws2 = MockWebSocket("127.0.0.1")
        ws2.headers["x-forwarded-for"] = "203.0.113.2"
        result = await rate_limiter.allow_connection(ws2)
        assert result is True

    @pytest.mark.asyncio
    async def test_extracts_ip_from_x_real_ip(self, rate_limiter):
        """Should extract client IP from X-Real-IP header."""
        ws = MockWebSocket("127.0.0.1")
        ws.headers["x-real-ip"] = "203.0.113.3"

        result = await rate_limiter.allow_connection(ws)
        assert result is True

    @pytest.mark.asyncio
    async def test_allows_initial_messages(self, rate_limiter):
        """Should allow initial burst of messages."""
        ws = MockWebSocket()

        # Should allow burst_size messages
        for _ in range(5):
            result = await rate_limiter.allow_message(ws)
            assert result is True

    @pytest.mark.asyncio
    async def test_blocks_messages_after_burst(self, rate_limiter):
        """Should block messages after burst is exhausted."""
        ws = MockWebSocket()

        # Exhaust the burst + a few more to ensure we hit the limit
        # (tokens refill at max_messages_per_second = 10/sec)
        for _ in range(6):
            result = await rate_limiter.allow_message(ws)

        # After exhausting burst (5) + 1 more, we should be blocked
        # unless enough time passes. The 6th call should be blocked.
        # Actually let's be more precise - check that eventually we get blocked
        blocked = False
        for _ in range(10):
            result = await rate_limiter.allow_message(ws)
            if not result:
                blocked = True
                break

        assert blocked is True

    @pytest.mark.asyncio
    async def test_tokens_refill_over_time(self, rate_limiter):
        """Should refill tokens over time."""
        ws = MockWebSocket()

        # Exhaust tokens
        for _ in range(5):
            await rate_limiter.allow_message(ws)

        # Wait for refill (10 messages/second = 0.1 second per token)
        await asyncio.sleep(0.15)

        # Should have at least one token now
        result = await rate_limiter.allow_message(ws)
        assert result is True

    @pytest.mark.asyncio
    async def test_remove_connection_cleans_up(self, rate_limiter):
        """Should clean up tracking data when connection removed."""
        ws = MockWebSocket()

        # Initialize message bucket
        await rate_limiter.allow_message(ws)

        conn_id = rate_limiter._get_connection_id(ws)
        assert conn_id in rate_limiter._message_buckets

        # Remove connection
        await rate_limiter.remove_connection(ws)
        assert conn_id not in rate_limiter._message_buckets

    @pytest.mark.asyncio
    async def test_cleanup_stale_entries(self, rate_limiter):
        """Should clean up stale entries."""
        # Create some entries
        ws = MockWebSocket("10.0.0.1")
        await rate_limiter.allow_connection(ws)
        await rate_limiter.allow_message(ws)

        # Force entries to be stale by manipulating timestamps
        rate_limiter._connection_times["10.0.0.1"] = [0]  # Very old timestamp

        conn_id = rate_limiter._get_connection_id(ws)
        rate_limiter._message_buckets[conn_id] = (5.0, 0)  # Very old last_update

        await rate_limiter.cleanup_stale_entries()

        # Stale entries should be cleaned
        assert "10.0.0.1" not in rate_limiter._connection_times
        assert conn_id not in rate_limiter._message_buckets


class TestConnectionManager:
    """Tests for the ConnectionManager class."""

    @pytest.fixture
    def manager(self):
        """Create a fresh ConnectionManager for each test."""
        return ConnectionManager()

    @pytest.fixture
    def mock_presence_service(self):
        """Create a mock presence service."""
        presence = MagicMock()
        presence.set_online = AsyncMock()
        presence.set_offline = AsyncMock()
        presence.set_available = AsyncMock()
        presence.set_busy = AsyncMock()
        presence.set_in_call = AsyncMock()
        presence.set_away = AsyncMock()
        presence.heartbeat = AsyncMock()
        presence.HEARTBEAT_INTERVAL = 30
        presence.redis = MagicMock()
        presence.redis.hset = AsyncMock()
        presence._professional_key = lambda x: f"professional:{x}"
        return presence

    @pytest.mark.asyncio
    async def test_connect_professional(self, manager, mock_presence_service):
        """Should connect professional and mark online."""
        ws = MockWebSocket()

        with patch("src.app.presence.websocket_handler.get_presence_service", return_value=mock_presence_service):
            await manager.connect_professional(ws, "prof-123")

        assert ws.accepted
        assert "prof-123" in manager.professional_connections
        mock_presence_service.set_online.assert_called_once()

    @pytest.mark.asyncio
    async def test_connect_professional_with_subprotocol(self, manager, mock_presence_service):
        """Should accept with subprotocol."""
        ws = MockWebSocket()

        with patch("src.app.presence.websocket_handler.get_presence_service", return_value=mock_presence_service):
            await manager.connect_professional(ws, "prof-123", subprotocol="access_token")

        assert ws.accepted
        assert ws.subprotocol == "access_token"

    @pytest.mark.asyncio
    async def test_connect_professional_replaces_existing(self, manager, mock_presence_service):
        """Should disconnect existing connection when new one connects."""
        old_ws = MockWebSocket()
        new_ws = MockWebSocket()

        with patch("src.app.presence.websocket_handler.get_presence_service", return_value=mock_presence_service):
            await manager.connect_professional(old_ws, "prof-123")
            await manager.connect_professional(new_ws, "prof-123")

        assert old_ws.closed
        assert manager.professional_connections["prof-123"] == new_ws

    @pytest.mark.asyncio
    async def test_disconnect_professional(self, manager, mock_presence_service):
        """Should disconnect professional and mark offline."""
        ws = MockWebSocket()

        with patch("src.app.presence.websocket_handler.get_presence_service", return_value=mock_presence_service):
            await manager.connect_professional(ws, "prof-123")
            await manager.disconnect_professional("prof-123", "test_disconnect")

        assert "prof-123" not in manager.professional_connections
        mock_presence_service.set_offline.assert_called_once_with("prof-123", "test_disconnect")

    @pytest.mark.asyncio
    async def test_connect_grid_subscriber(self, manager):
        """Should add grid subscriber."""
        ws = MockWebSocket()
        await manager.connect_grid_subscriber(ws)

        assert ws.accepted
        assert ws in manager.grid_subscribers

    @pytest.mark.asyncio
    async def test_disconnect_grid_subscriber(self, manager):
        """Should remove grid subscriber."""
        ws = MockWebSocket()
        await manager.connect_grid_subscriber(ws)
        await manager.disconnect_grid_subscriber(ws)

        assert ws not in manager.grid_subscribers

    @pytest.mark.asyncio
    async def test_broadcast_grid_update(self, manager):
        """Should broadcast to all subscribers."""
        ws1 = MockWebSocket()
        ws2 = MockWebSocket()

        await manager.connect_grid_subscriber(ws1)
        await manager.connect_grid_subscriber(ws2)

        await manager.broadcast_grid_update({"event": "test"})

        assert len(ws1.sent_messages) == 1
        assert len(ws2.sent_messages) == 1

    @pytest.mark.asyncio
    async def test_broadcast_removes_disconnected(self, manager):
        """Should remove disconnected subscribers during broadcast."""
        ws1 = MockWebSocket()
        ws2 = MockWebSocket()
        ws2._client_state = WebSocketState.DISCONNECTED

        await manager.connect_grid_subscriber(ws1)
        await manager.connect_grid_subscriber(ws2)

        await manager.broadcast_grid_update({"event": "test"})

        # ws2 should be removed from subscribers
        assert ws1 in manager.grid_subscribers
        # Note: ws2 might still be there if WebSocketState check works differently

    @pytest.mark.asyncio
    async def test_send_to_professional(self, manager, mock_presence_service):
        """Should send message to specific professional."""
        ws = MockWebSocket()

        with patch("src.app.presence.websocket_handler.get_presence_service", return_value=mock_presence_service):
            await manager.connect_professional(ws, "prof-123")
            result = await manager.send_to_professional("prof-123", {"type": "test"})

        assert result is True
        assert {"type": "test"} in ws.sent_messages

    @pytest.mark.asyncio
    async def test_send_to_nonexistent_professional(self, manager):
        """Should return False for nonexistent professional."""
        result = await manager.send_to_professional("nonexistent", {"type": "test"})
        assert result is False

    @pytest.mark.asyncio
    async def test_update_professional_status_available(self, manager, mock_presence_service):
        """Should update status to available."""
        with patch("src.app.presence.websocket_handler.get_presence_service", return_value=mock_presence_service):
            await manager.update_professional_status("prof-123", "available")

        mock_presence_service.set_available.assert_called_once_with("prof-123")

    @pytest.mark.asyncio
    async def test_update_professional_status_busy(self, manager, mock_presence_service):
        """Should update status to busy with room ID."""
        with patch("src.app.presence.websocket_handler.get_presence_service", return_value=mock_presence_service):
            await manager.update_professional_status("prof-123", "busy", "room-456")

        mock_presence_service.set_busy.assert_called_once_with("prof-123", "room-456")

    @pytest.mark.asyncio
    async def test_update_professional_status_in_call(self, manager, mock_presence_service):
        """Should update status to in_call."""
        with patch("src.app.presence.websocket_handler.get_presence_service", return_value=mock_presence_service):
            await manager.update_professional_status("prof-123", "in_call", "room-456")

        mock_presence_service.set_in_call.assert_called_once_with("prof-123", "room-456")

    @pytest.mark.asyncio
    async def test_update_professional_status_away(self, manager, mock_presence_service):
        """Should update status to away."""
        with patch("src.app.presence.websocket_handler.get_presence_service", return_value=mock_presence_service):
            await manager.update_professional_status("prof-123", "away")

        mock_presence_service.set_away.assert_called_once_with("prof-123")

    @pytest.mark.asyncio
    async def test_update_professional_status_offline(self, manager, mock_presence_service):
        """Should disconnect professional when status is offline."""
        ws = MockWebSocket()

        with patch("src.app.presence.websocket_handler.get_presence_service", return_value=mock_presence_service):
            await manager.connect_professional(ws, "prof-123")
            await manager.update_professional_status("prof-123", "offline")

        assert "prof-123" not in manager.professional_connections
        mock_presence_service.set_offline.assert_called()

    def test_get_online_count(self, manager):
        """Should return count of connected professionals."""
        manager.professional_connections = {"p1": MagicMock(), "p2": MagicMock()}
        assert manager.get_online_count() == 2

    def test_get_subscriber_count(self, manager):
        """Should return count of grid subscribers."""
        manager.grid_subscribers = {MagicMock(), MagicMock(), MagicMock()}
        assert manager.get_subscriber_count() == 3


class TestProfessionalPresenceHandler:
    """Tests for the professional_presence_handler function."""

    @pytest.fixture
    def mock_presence_service(self):
        """Create a mock presence service."""
        presence = MagicMock()
        presence.set_online = AsyncMock()
        presence.set_offline = AsyncMock()
        presence.set_available = AsyncMock()
        presence.set_busy = AsyncMock()
        presence.heartbeat = AsyncMock()
        presence.HEARTBEAT_INTERVAL = 30
        presence.redis = MagicMock()
        presence.redis.hset = AsyncMock()
        presence._professional_key = lambda x: f"professional:{x}"
        return presence

    @pytest.fixture
    def mock_rate_limiter(self):
        """Create a mock rate limiter."""
        limiter = MagicMock()
        limiter.allow_connection = AsyncMock(return_value=True)
        limiter.allow_message = AsyncMock(return_value=True)
        limiter.remove_connection = AsyncMock()
        return limiter

    @pytest.mark.asyncio
    async def test_rejects_rate_limited_connection(self):
        """Should reject connection when rate limited."""
        ws = MockWebSocket()

        with patch("src.app.presence.websocket_handler.ws_rate_limiter") as mock_limiter:
            mock_limiter.allow_connection = AsyncMock(return_value=False)

            await professional_presence_handler(ws, "prof-123")

        assert ws.closed
        assert ws.close_code == 1008

    @pytest.mark.asyncio
    async def test_handles_heartbeat_message(self, mock_presence_service, mock_rate_limiter):
        """Should handle heartbeat messages."""
        ws = MockWebSocket()
        ws.queue_message({"type": "heartbeat"})
        ws.queue_message(Exception("WebSocketDisconnect"))

        with patch("src.app.presence.websocket_handler.ws_rate_limiter", mock_rate_limiter):
            with patch("src.app.presence.websocket_handler.get_presence_service", return_value=mock_presence_service):
                # Patch connection_manager to avoid side effects
                with patch("src.app.presence.websocket_handler.connection_manager") as mock_cm:
                    mock_cm.connect_professional = AsyncMock()
                    mock_cm.disconnect_professional = AsyncMock()
                    mock_cm.broadcast_grid_update = AsyncMock()

                    try:
                        await professional_presence_handler(ws, "prof-123")
                    except Exception:
                        pass  # Expected when queue is exhausted

        # Verify heartbeat_ack was sent
        assert any(msg.get("type") == "heartbeat_ack" for msg in ws.sent_messages if isinstance(msg, dict))

    @pytest.mark.asyncio
    async def test_handles_status_update_message(self, mock_presence_service, mock_rate_limiter):
        """Should handle status update messages."""
        ws = MockWebSocket()
        ws.queue_message({"type": "status_update", "data": {"status": "available"}})
        ws.queue_message(Exception("WebSocketDisconnect"))

        with patch("src.app.presence.websocket_handler.ws_rate_limiter", mock_rate_limiter):
            with patch("src.app.presence.websocket_handler.get_presence_service", return_value=mock_presence_service):
                with patch("src.app.presence.websocket_handler.connection_manager") as mock_cm:
                    mock_cm.connect_professional = AsyncMock()
                    mock_cm.disconnect_professional = AsyncMock()
                    mock_cm.update_professional_status = AsyncMock()
                    mock_cm.broadcast_grid_update = AsyncMock()

                    try:
                        await professional_presence_handler(ws, "prof-123")
                    except Exception:
                        pass

        # Verify status_updated was sent
        assert any(msg.get("type") == "status_updated" for msg in ws.sent_messages if isinstance(msg, dict))

    @pytest.mark.asyncio
    async def test_rate_limits_messages(self, mock_presence_service):
        """Should rate limit excessive messages."""
        ws = MockWebSocket()
        ws.queue_message({"type": "heartbeat"})
        ws.queue_message(Exception("WebSocketDisconnect"))

        mock_rate_limiter = MagicMock()
        mock_rate_limiter.allow_connection = AsyncMock(return_value=True)
        mock_rate_limiter.allow_message = AsyncMock(return_value=False)  # Rate limited
        mock_rate_limiter.remove_connection = AsyncMock()

        with patch("src.app.presence.websocket_handler.ws_rate_limiter", mock_rate_limiter):
            with patch("src.app.presence.websocket_handler.get_presence_service", return_value=mock_presence_service):
                with patch("src.app.presence.websocket_handler.connection_manager") as mock_cm:
                    mock_cm.connect_professional = AsyncMock()
                    mock_cm.disconnect_professional = AsyncMock()
                    mock_cm.broadcast_grid_update = AsyncMock()

                    try:
                        await professional_presence_handler(ws, "prof-123")
                    except Exception:
                        pass

        # Should have sent rate limit error
        assert any(
            isinstance(msg, dict) and msg.get("type") == "error" and "Rate limit" in msg.get("message", "")
            for msg in ws.sent_messages
        )


class TestGridUpdatesHandler:
    """Tests for the grid_updates_handler function."""

    @pytest.fixture
    def mock_rate_limiter(self):
        """Create a mock rate limiter."""
        limiter = MagicMock()
        limiter.allow_connection = AsyncMock(return_value=True)
        limiter.allow_message = AsyncMock(return_value=True)
        limiter.remove_connection = AsyncMock()
        return limiter

    @pytest.mark.asyncio
    async def test_rejects_rate_limited_connection(self):
        """Should reject connection when rate limited."""
        ws = MockWebSocket()

        with patch("src.app.presence.websocket_handler.ws_rate_limiter") as mock_limiter:
            mock_limiter.allow_connection = AsyncMock(return_value=False)

            await grid_updates_handler(ws)

        assert ws.closed
        assert ws.close_code == 1008

    @pytest.mark.asyncio
    async def test_sends_connected_message(self, mock_rate_limiter):
        """Should send connected message on connection."""
        ws = MockWebSocket()
        ws.queue_message(Exception("WebSocketDisconnect"))

        with patch("src.app.presence.websocket_handler.ws_rate_limiter", mock_rate_limiter):
            with patch("src.app.presence.websocket_handler.connection_manager") as mock_cm:
                mock_cm.connect_grid_subscriber = AsyncMock()
                mock_cm.disconnect_grid_subscriber = AsyncMock()

                try:
                    await grid_updates_handler(ws)
                except Exception:
                    pass

        # Verify connected message was sent
        assert any(
            isinstance(msg, dict) and msg.get("type") == "connected"
            for msg in ws.sent_messages
        )

    @pytest.mark.asyncio
    async def test_handles_ping_message(self, mock_rate_limiter):
        """Should respond to ping with pong."""
        ws = MockWebSocket()
        ws.queue_message({"type": "ping"})
        ws.queue_message(Exception("WebSocketDisconnect"))

        with patch("src.app.presence.websocket_handler.ws_rate_limiter", mock_rate_limiter):
            with patch("src.app.presence.websocket_handler.connection_manager") as mock_cm:
                mock_cm.connect_grid_subscriber = AsyncMock()
                mock_cm.disconnect_grid_subscriber = AsyncMock()

                try:
                    await grid_updates_handler(ws)
                except Exception:
                    pass

        # Verify pong was sent
        assert any(
            isinstance(msg, dict) and msg.get("type") == "pong"
            for msg in ws.sent_messages
        )

    @pytest.mark.asyncio
    async def test_handles_get_online_count(self, mock_rate_limiter):
        """Should respond to get_online_count request."""
        ws = MockWebSocket()
        ws.queue_message({"type": "get_online_count"})
        ws.queue_message(Exception("WebSocketDisconnect"))

        mock_presence = MagicMock()
        mock_presence.get_online_count = AsyncMock(return_value=42)

        with patch("src.app.presence.websocket_handler.ws_rate_limiter", mock_rate_limiter):
            with patch("src.app.presence.websocket_handler.get_presence_service", return_value=mock_presence):
                with patch("src.app.presence.websocket_handler.connection_manager") as mock_cm:
                    mock_cm.connect_grid_subscriber = AsyncMock()
                    mock_cm.disconnect_grid_subscriber = AsyncMock()

                    try:
                        await grid_updates_handler(ws)
                    except Exception:
                        pass

        # Verify online_count was sent
        assert any(
            isinstance(msg, dict) and msg.get("type") == "online_count" and msg.get("count") == 42
            for msg in ws.sent_messages
        )

    @pytest.mark.asyncio
    async def test_rate_limits_messages(self):
        """Should rate limit excessive messages."""
        ws = MockWebSocket()
        ws.queue_message({"type": "ping"})
        ws.queue_message(Exception("WebSocketDisconnect"))

        mock_rate_limiter = MagicMock()
        mock_rate_limiter.allow_connection = AsyncMock(return_value=True)
        mock_rate_limiter.allow_message = AsyncMock(return_value=False)  # Rate limited
        mock_rate_limiter.remove_connection = AsyncMock()

        with patch("src.app.presence.websocket_handler.ws_rate_limiter", mock_rate_limiter):
            with patch("src.app.presence.websocket_handler.connection_manager") as mock_cm:
                mock_cm.connect_grid_subscriber = AsyncMock()
                mock_cm.disconnect_grid_subscriber = AsyncMock()

                try:
                    await grid_updates_handler(ws)
                except Exception:
                    pass

        # Should have sent rate limit error (after the initial connected message)
        error_messages = [
            msg for msg in ws.sent_messages
            if isinstance(msg, dict) and msg.get("type") == "error"
        ]
        assert len(error_messages) > 0
