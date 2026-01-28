"""Audit log model for tracking system events.

This module defines the AuditLog model for recording
security-relevant events and admin actions for compliance.
"""
import uuid
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import String, Text, DateTime, Enum as SQLEnum, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from src.app.core.database import Base

if TYPE_CHECKING:
    from src.app.models.user import User


class AuditEventType(str, Enum):
    """Types of auditable events."""
    # Authentication
    LOGIN = "login"
    LOGIN_FAILED = "login_failed"
    LOGOUT = "logout"
    PASSWORD_CHANGE = "password_change"
    
    # Account
    ACCOUNT_CREATED = "account_created"
    ACCOUNT_DISABLED = "account_disabled"
    ACCOUNT_ENABLED = "account_enabled"
    PROFILE_UPDATED = "profile_updated"
    
    # Admin actions
    ADMIN_USER_STATUS_CHANGE = "admin_user_status_change"
    ADMIN_VIDEO_APPROVED = "admin_video_approved"
    ADMIN_VIDEO_REJECTED = "admin_video_rejected"
    ADMIN_DISPUTE_RESOLVED = "admin_dispute_resolved"
    
    # Billing
    SUBSCRIPTION_CREATED = "subscription_created"
    SUBSCRIPTION_CANCELLED = "subscription_cancelled"
    
    # System
    API_KEY_CREATED = "api_key_created"
    DATA_EXPORT = "data_export"


class AuditLog(Base):
    """
    Audit log for tracking system events.
    
    Records user actions, admin operations, and system events
    for security monitoring and compliance purposes.
    """
    __tablename__ = "audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    event_type: Mapped[AuditEventType] = mapped_column(
        SQLEnum(AuditEventType), nullable=False, index=True
    )
    resource_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    resource_id: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(500), nullable=True)
    extra_data: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False, index=True
    )

    # Relationships
    user: Mapped["User"] = relationship("User")
