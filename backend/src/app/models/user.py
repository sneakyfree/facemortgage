import uuid
from datetime import datetime
from enum import Enum
from sqlalchemy import String, Boolean, DateTime, Enum as SQLEnum, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from src.app.core.database import Base


class UserType(str, Enum):
    BORROWER = "borrower"
    LOAN_OFFICER = "loan_officer"
    REALTOR = "realtor"
    TITLE_REP = "title_rep"
    ATTORNEY = "attorney"


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    user_type: Mapped[UserType] = mapped_column(SQLEnum(UserType), nullable=False)

    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    avatar_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    email_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    phone_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    is_super_admin: Mapped[bool] = mapped_column(Boolean, default=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Account lockout fields for brute force protection
    failed_login_attempts: Mapped[int] = mapped_column(default=0)
    locked_until: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Push notification settings
    # Using JSON instead of JSONB for SQLite test compatibility
    device_tokens: Mapped[list | None] = mapped_column(JSON, nullable=True)
    push_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    last_platform: Mapped[str | None] = mapped_column(String(20), nullable=True)

    # OAuth provider IDs
    google_id: Mapped[str | None] = mapped_column(String(100), nullable=True, unique=True, index=True)

    # Password reset
    password_reset_token: Mapped[str | None] = mapped_column(String(255), nullable=True)
    password_reset_expires: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Relationships
    professional_profile: Mapped["ProfessionalProfile"] = relationship(
        "ProfessionalProfile", back_populates="user", uselist=False
    )
    borrower_profile: Mapped["BorrowerProfile"] = relationship(
        "BorrowerProfile", back_populates="user", uselist=False
    )
    disputes: Mapped[list["Dispute"]] = relationship(
        "Dispute", foreign_keys="[Dispute.user_id]", back_populates="user"
    )

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    @property
    def is_professional(self) -> bool:
        return self.user_type in [
            UserType.LOAN_OFFICER,
            UserType.REALTOR,
            UserType.TITLE_REP,
            UserType.ATTORNEY,
        ]


# Import for type hints
from src.app.models.professional import ProfessionalProfile
from src.app.models.borrower import BorrowerProfile
from src.app.models.dispute import Dispute
