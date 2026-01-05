"""
Pytest configuration and fixtures for the FaceMortgage backend.
"""
import asyncio
import uuid
from datetime import datetime
from decimal import Decimal
from typing import AsyncGenerator, Generator

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool

from src.app.main import app
from src.app.core.database import Base, get_db
from src.app.core.auth import get_current_user, create_access_token
from src.app.models.user import User, UserType
from src.app.models.professional import ProfessionalProfile, ProfessionalStatus, SubscriptionTier


# Use in-memory SQLite for tests
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def db_engine():
    """Create a test database engine."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        poolclass=NullPool,
        echo=False,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def db_session(db_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create a test database session."""
    async_session = async_sessionmaker(
        db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture(scope="function")
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create a test HTTP client."""

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        yield client

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def test_user(db_session: AsyncSession) -> User:
    """Create a test borrower user."""
    user = User(
        id=uuid.uuid4(),
        email="borrower@test.com",
        password_hash="$2b$12$test_hash",  # Not a real hash
        first_name="Test",
        last_name="Borrower",
        user_type=UserType.BORROWER,
        is_active=True,
        email_verified=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def test_professional_user(db_session: AsyncSession) -> User:
    """Create a test professional user."""
    user = User(
        id=uuid.uuid4(),
        email="pro@test.com",
        password_hash="$2b$12$test_hash",
        first_name="Test",
        last_name="Professional",
        user_type=UserType.LOAN_OFFICER,
        is_active=True,
        email_verified=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def test_professional(
    db_session: AsyncSession,
    test_professional_user: User,
) -> ProfessionalProfile:
    """Create a test professional profile."""
    profile = ProfessionalProfile(
        id=uuid.uuid4(),
        user_id=test_professional_user.id,
        company_name="Test Mortgage Co",
        job_title="Loan Officer",
        bio="Test bio",
        years_experience=5,
        nmls_id="123456",
        nmls_verified=True,
        timezone="America/New_York",
        status=ProfessionalStatus.ONLINE_AVAILABLE,
        subscription_tier=SubscriptionTier.PROFESSIONAL,
        current_bid_amount=Decimal("5.00"),
        avg_rating=Decimal("4.5"),
        total_reviews=10,
        total_calls_completed=50,
        profile_complete=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db_session.add(profile)
    await db_session.commit()
    await db_session.refresh(profile)
    return profile


@pytest.fixture
def auth_headers(test_user: User) -> dict:
    """Create authentication headers for test user."""
    token = create_access_token(data={"sub": str(test_user.id)})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def pro_auth_headers(test_professional_user: User) -> dict:
    """Create authentication headers for professional user."""
    token = create_access_token(data={"sub": str(test_professional_user.id)})
    return {"Authorization": f"Bearer {token}"}


def authenticated_client(client: AsyncClient, user: User):
    """Helper to create authenticated client."""

    async def override_get_current_user():
        return user

    app.dependency_overrides[get_current_user] = override_get_current_user
    return client
