"""Dispute Resolution models for user support.

This module defines the data models for dispute tickets,
enabling users to submit billing/service disputes and admins to resolve them.
"""
import uuid
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, List

from sqlalchemy import String, Text, DateTime, Enum as SQLEnum, ForeignKey, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from src.app.core.database import Base

if TYPE_CHECKING:
    from src.app.models.user import User


class DisputeType(str, Enum):
    """Type of dispute."""
    BILLING = "billing"
    SERVICE = "service"
    TECHNICAL = "technical"
    OTHER = "other"


class DisputeStatus(str, Enum):
    """Status of a dispute."""
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"


class DisputePriority(str, Enum):
    """Priority level of a dispute."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class Dispute(Base):
    """
    Dispute ticket for user support.
    
    Users can submit disputes for billing issues, service complaints,
    technical problems, or other concerns. Admins can assign, respond, and resolve.
    """
    __tablename__ = "disputes"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    dispute_type: Mapped[DisputeType] = mapped_column(
        SQLEnum(DisputeType), nullable=False
    )
    subject: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[DisputeStatus] = mapped_column(
        SQLEnum(DisputeStatus), nullable=False, default=DisputeStatus.OPEN, index=True
    )
    priority: Mapped[DisputePriority] = mapped_column(
        SQLEnum(DisputePriority), nullable=False, default=DisputePriority.MEDIUM
    )
    related_transaction_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    assigned_to: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=True,
        index=True
    )
    resolution_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    user: Mapped["User"] = relationship("User", foreign_keys=[user_id], back_populates="disputes")
    assignee: Mapped["User"] = relationship("User", foreign_keys=[assigned_to])
    messages: Mapped[List["DisputeMessage"]] = relationship(
        "DisputeMessage", back_populates="dispute", order_by="DisputeMessage.created_at",
        cascade="all, delete-orphan"
    )


class DisputeMessage(Base):
    """
    Message in a dispute thread.
    
    Allows back-and-forth communication between user and admin.
    Internal messages are only visible to admins.
    """
    __tablename__ = "dispute_messages"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    dispute_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("disputes.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    sender_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False
    )
    message: Mapped[str] = mapped_column(Text, nullable=False)
    is_internal: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )

    # Relationships
    dispute: Mapped["Dispute"] = relationship("Dispute", back_populates="messages")
    sender: Mapped["User"] = relationship("User")
