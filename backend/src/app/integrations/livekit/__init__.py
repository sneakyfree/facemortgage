"""
LiveKit integration for scalable video infrastructure.

LiveKit provides:
- SFU-based video routing (better for 2+ participants)
- Built-in recording capabilities
- Better scalability than peer-to-peer WebRTC
- Cloud-hosted or self-hosted options

This module provides a service that can be used as an alternative to
the built-in WebRTC signaling when scale requires it.
"""
from src.app.integrations.livekit.service import LiveKitService, get_livekit_service

__all__ = ["LiveKitService", "get_livekit_service"]
