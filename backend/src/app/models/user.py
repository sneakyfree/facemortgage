import uuid
from datetime import datetime
from enum import Enum
from sqlalchemy import String, Boolean, DateTime, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB

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

    # Push notification settings
    device_tokens: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    push_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    last_platform: Mapped[str | None] = mapped_column(String(20), nullable=True)

    # Relationships
    professional_profile: Mapped["ProfessionalProfile"] = relationship(
        "ProfessionalProfile", back_populates="user", uselist=False
    )
    borrower_profile: Mapped["BorrowerProfile"] = relationship(
        "BorrowerProfile", back_populates="user", uselist=False
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
