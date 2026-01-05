"""
Push notification service for mobile app support.

Handles sending push notifications via Firebase Cloud Messaging (FCM)
for incoming calls, new leads, and other real-time events.
"""
import logging
from typing import Optional, List, Dict, Any
from enum import Enum

from src.app.config import settings

logger = logging.getLogger(__name__)


class PushPlatform(str, Enum):
    IOS = "ios"
    ANDROID = "android"
    WEB = "web"


class PushNotificationType(str, Enum):
    INCOMING_CALL = "incoming_call"
    NEW_LEAD = "new_lead"
    NEW_REFERRAL = "new_referral"
    SCHEDULED_CALL_REMINDER = "scheduled_call_reminder"
    MESSAGE = "message"


class PushNotificationService:
    """
    Service for sending push notifications.

    Uses Firebase Cloud Messaging for iOS and Android,
    and Web Push for browser notifications.
    """

    def __init__(self):
        self._initialized = False
        self._app = None

    def _ensure_initialized(self):
        """
        Lazily initialize Firebase Admin SDK.

        Only initializes when first notification is sent,
        to avoid errors when Firebase credentials aren't configured.
        """
        if self._initialized:
            return

        try:
            import firebase_admin
            from firebase_admin import credentials

            if not firebase_admin._apps:
                # Check if credentials are available
                creds_path = getattr(settings, 'FIREBASE_CREDENTIALS_PATH', None)
                if creds_path:
                    cred = credentials.Certificate(creds_path)
                    self._app = firebase_admin.initialize_app(cred)
                    self._initialized = True
                    logger.info("Firebase Admin SDK initialized successfully")
                else:
                    logger.warning("Firebase credentials not configured - push notifications disabled")
            else:
                self._app = firebase_admin.get_app()
                self._initialized = True
        except ImportError:
            logger.warning("firebase-admin package not installed - push notifications disabled")
        except Exception as e:
            logger.error(f"Failed to initialize Firebase: {e}")

    async def send_to_device(
        self,
        token: str,
        title: str,
        body: str,
        data: Optional[Dict[str, str]] = None,
        platform: PushPlatform = PushPlatform.ANDROID,
        priority: str = "high",
    ) -> bool:
        """
        Send push notification to a single device.

        Args:
            token: FCM device token
            title: Notification title
            body: Notification body text
            data: Additional data payload
            platform: Target platform (ios/android/web)
            priority: Message priority (high/normal)

        Returns:
            True if sent successfully, False otherwise
        """
        self._ensure_initialized()

        if not self._initialized:
            logger.warning("Push notifications not available - skipping")
            return False

        try:
            from firebase_admin import messaging

            # Build notification
            notification = messaging.Notification(
                title=title,
                body=body,
            )

            # Platform-specific config
            android_config = None
            apns_config = None

            if platform == PushPlatform.ANDROID:
                android_config = messaging.AndroidConfig(
                    priority=priority,
                    notification=messaging.AndroidNotification(
                        sound="default",
                        click_action="OPEN_CALL" if data and data.get("type") == "incoming_call" else "OPEN_APP",
                    ),
                )
            elif platform == PushPlatform.IOS:
                apns_config = messaging.APNSConfig(
                    payload=messaging.APNSPayload(
                        aps=messaging.Aps(
                            sound="default",
                            badge=1,
                            content_available=True,
                        ),
                    ),
                )

            message = messaging.Message(
                notification=notification,
                data=data or {},
                token=token,
                android=android_config,
                apns=apns_config,
            )

            response = messaging.send(message)
            logger.info(f"Push notification sent: {response}")
            return True

        except Exception as e:
            logger.error(f"Failed to send push notification: {e}")
            return False

    async def send_to_user_devices(
        self,
        device_tokens: List[Dict[str, Any]],
        title: str,
        body: str,
        data: Optional[Dict[str, str]] = None,
        priority: str = "high",
    ) -> int:
        """
        Send push notification to all of a user's devices.

        Args:
            device_tokens: List of {"token": str, "platform": str} dicts
            title: Notification title
            body: Notification body text
            data: Additional data payload
            priority: Message priority

        Returns:
            Number of successful sends
        """
        success_count = 0

        for device in device_tokens:
            token = device.get("token")
            platform = PushPlatform(device.get("platform", "android"))

            if token:
                result = await self.send_to_device(
                    token=token,
                    title=title,
                    body=body,
                    data=data,
                    platform=platform,
                    priority=priority,
                )
                if result:
                    success_count += 1

        return success_count

    async def send_incoming_call_notification(
        self,
        device_tokens: List[Dict[str, Any]],
        caller_name: str,
        room_id: str,
        call_id: str,
        is_anonymous: bool = False,
    ) -> int:
        """
        Send high-priority incoming call notification.

        This should trigger a call-style notification on mobile devices.
        """
        return await self.send_to_user_devices(
            device_tokens=device_tokens,
            title="Incoming Call",
            body=f"{caller_name} is calling you",
            data={
                "type": PushNotificationType.INCOMING_CALL.value,
                "room_id": room_id,
                "call_id": call_id,
                "caller_name": caller_name,
                "is_anonymous": str(is_anonymous).lower(),
            },
            priority="high",
        )

    async def send_new_lead_notification(
        self,
        device_tokens: List[Dict[str, Any]],
        lead_name: str,
        lead_source: str,
        lead_id: str,
    ) -> int:
        """Send notification about a new lead."""
        return await self.send_to_user_devices(
            device_tokens=device_tokens,
            title="New Lead",
            body=f"New lead from {lead_source}: {lead_name}",
            data={
                "type": PushNotificationType.NEW_LEAD.value,
                "lead_id": lead_id,
                "lead_name": lead_name,
                "source": lead_source,
            },
            priority="high",
        )

    async def send_referral_notification(
        self,
        device_tokens: List[Dict[str, Any]],
        referrer_name: str,
        borrower_name: str,
        referral_id: str,
    ) -> int:
        """Send notification about a new partner referral."""
        return await self.send_to_user_devices(
            device_tokens=device_tokens,
            title="New Referral",
            body=f"{referrer_name} referred {borrower_name}",
            data={
                "type": PushNotificationType.NEW_REFERRAL.value,
                "referral_id": referral_id,
                "referrer_name": referrer_name,
                "borrower_name": borrower_name,
            },
            priority="high",
        )

    async def send_scheduled_call_reminder(
        self,
        device_tokens: List[Dict[str, Any]],
        caller_name: str,
        scheduled_time: str,
        scheduled_call_id: str,
    ) -> int:
        """Send reminder about an upcoming scheduled call."""
        return await self.send_to_user_devices(
            device_tokens=device_tokens,
            title="Upcoming Call",
            body=f"Call with {caller_name} in 15 minutes",
            data={
                "type": PushNotificationType.SCHEDULED_CALL_REMINDER.value,
                "scheduled_call_id": scheduled_call_id,
                "caller_name": caller_name,
                "scheduled_time": scheduled_time,
            },
            priority="high",
        )


    async def send_incoming_call(
        self,
        professional_user_id: str,
        caller_name: str,
        room_id: str,
        call_id: str,
        is_anonymous: bool = False,
    ) -> int:
        """
        Convenience method to send incoming call notification to a professional.

        Fetches the user's device tokens from the database and sends the notification.

        Args:
            professional_user_id: The user ID of the professional
            caller_name: Name of the caller
            room_id: The call room ID
            call_id: The call ID
            is_anonymous: Whether the caller is anonymous

        Returns:
            Number of successful notifications sent
        """
        from src.app.core.database import async_session_factory
        from src.app.models.user import User

        async with async_session_factory() as db:
            user = await db.get(User, professional_user_id)

            if not user or not user.device_tokens or not user.push_enabled:
                logger.debug(f"No push notifications for user {professional_user_id}: no tokens or disabled")
                return 0

            return await self.send_incoming_call_notification(
                device_tokens=user.device_tokens,
                caller_name=caller_name,
                room_id=room_id,
                call_id=call_id,
                is_anonymous=is_anonymous,
            )


# Singleton instance
push_service = PushNotificationService()


def get_push_service() -> PushNotificationService:
    """Get the push notification service instance."""
    return push_service
