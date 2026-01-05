"""
Pytest configuration and fixtures for the FaceMortgage backend.

Provides comprehensive test fixtures for:
- Async database setup with in-memory SQLite
- User fixtures (borrower, professional, admin)
- Authentication header fixtures
- Database session fixtures
- Mock services for external dependencies
"""
import asyncio
import uuid
from datetime import datetime
from decimal import Decimal
from typing import AsyncGenerator, Generator, Optional
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool

from src.app.main import app
from src.app.core.database import Base, get_db
from src.app.core.auth import get_current_user, create_access_token
from src.app.core.dependencies import get_current_user_optional
from src.app.models.user import User, UserType
from src.app.models.professional import ProfessionalProfile, ProfessionalStatus, SubscriptionTier
from src.app.models.call import VideoCall, CallStatus
from src.app.models.lead import Lead, LeadStatus, LeadActivity
from src.app.models.billing import Subscription, BidWallet, SubscriptionStatus


# Use file-based SQLite for tests to avoid async session isolation issues
# with in-memory databases where each connection gets a fresh database
import tempfile
import os

TEST_DB_PATH = os.path.join(tempfile.gettempdir(), "facemortgage_test.db")
TEST_DATABASE_URL = f"sqlite+aiosqlite:///{TEST_DB_PATH}"


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def db_engine():
    """Create a test database engine."""
    # Remove old test database if exists
    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)

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

    # Clean up test database file
    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)


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


# ==================== User Fixtures ====================

@pytest_asyncio.fixture
async def test_user(db_session: AsyncSession) -> User:
    """Create a test borrower user."""
    user = User(
        id=uuid.uuid4(),
        email="borrower@test.com",
        password_hash="$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.rSe6o2J1G7GgjC",  # "testpass123"
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
        password_hash="$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.rSe6o2J1G7GgjC",
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
async def test_admin_user(db_session: AsyncSession) -> User:
    """Create a test admin user."""
    user = User(
        id=uuid.uuid4(),
        email="admin@test.com",
        password_hash="$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.rSe6o2J1G7GgjC",
        first_name="Admin",
        last_name="User",
        user_type=UserType.BORROWER,
        is_active=True,
        is_admin=True,
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


@pytest_asyncio.fixture
async def test_offline_professional(
    db_session: AsyncSession,
) -> tuple[User, ProfessionalProfile]:
    """Create a test professional who is offline."""
    user = User(
        id=uuid.uuid4(),
        email="offline_pro@test.com",
        password_hash="$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.rSe6o2J1G7GgjC",
        first_name="Offline",
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

    profile = ProfessionalProfile(
        id=uuid.uuid4(),
        user_id=user.id,
        company_name="Offline Mortgage Co",
        job_title="Loan Officer",
        bio="Offline test bio",
        years_experience=3,
        nmls_id="654321",
        nmls_verified=True,
        timezone="America/Los_Angeles",
        status=ProfessionalStatus.OFFLINE,
        subscription_tier=SubscriptionTier.BASIC,
        current_bid_amount=Decimal("3.00"),
        avg_rating=Decimal("4.0"),
        total_reviews=5,
        total_calls_completed=20,
        profile_complete=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db_session.add(profile)
    await db_session.commit()
    await db_session.refresh(profile)

    return user, profile


# ==================== Authentication Header Fixtures ====================

@pytest.fixture
def auth_headers(test_user: User) -> dict:
    """Create authentication headers for test user (borrower)."""
    token = create_access_token(subject=str(test_user.id))
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def pro_auth_headers(test_professional_user: User) -> dict:
    """Create authentication headers for professional user."""
    token = create_access_token(subject=str(test_professional_user.id))
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def admin_auth_headers(test_admin_user: User) -> dict:
    """Create authentication headers for admin user."""
    token = create_access_token(subject=str(test_admin_user.id))
    return {"Authorization": f"Bearer {token}"}


def create_auth_headers_for_user(user: User) -> dict:
    """Helper to create auth headers for any user."""
    token = create_access_token(subject=str(user.id))
    return {"Authorization": f"Bearer {token}"}


# ==================== Test Data Fixtures ====================

@pytest_asyncio.fixture
async def test_lead(
    db_session: AsyncSession,
    test_professional: ProfessionalProfile,
    test_user: User,
) -> Lead:
    """Create a test lead."""
    lead = Lead(
        id=uuid.uuid4(),
        professional_id=test_professional.id,
        borrower_id=test_user.id,
        lead_status=LeadStatus.NEW,
        contact_name="John Doe",
        contact_email="john.doe@example.com",
        contact_phone="555-123-4567",
        loan_purpose="purchase",
        estimated_loan_amount=Decimal("350000.00"),
        notes="Test lead notes",
        utm_source="test",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db_session.add(lead)
    await db_session.commit()
    await db_session.refresh(lead)
    return lead


@pytest_asyncio.fixture
async def test_video_call(
    db_session: AsyncSession,
    test_user: User,
    test_professional: ProfessionalProfile,
) -> VideoCall:
    """Create a test video call."""
    call = VideoCall(
        id=uuid.uuid4(),
        room_id=f"room_{uuid.uuid4().hex[:8]}",
        borrower_id=test_user.id,
        professional_id=test_professional.id,
        status=CallStatus.COMPLETED,
        initiated_at=datetime.utcnow(),
        answered_at=datetime.utcnow(),
        ended_at=datetime.utcnow(),
        duration_seconds=300,
        pickup_time_seconds=5,
    )
    db_session.add(call)
    await db_session.commit()
    await db_session.refresh(call)
    return call


@pytest_asyncio.fixture
async def test_anonymous_call(
    db_session: AsyncSession,
    test_professional: ProfessionalProfile,
) -> VideoCall:
    """Create a test anonymous video call (no borrower_id)."""
    call = VideoCall(
        id=uuid.uuid4(),
        room_id=f"room_{uuid.uuid4().hex[:8]}",
        borrower_id=None,
        professional_id=test_professional.id,
        anonymous_session_id=f"anon_{uuid.uuid4().hex[:16]}",
        anonymous_device_fingerprint="test_fingerprint",
        status=CallStatus.COMPLETED,
        initiated_at=datetime.utcnow(),
        answered_at=datetime.utcnow(),
        ended_at=datetime.utcnow(),
        duration_seconds=180,
        pickup_time_seconds=8,
    )
    db_session.add(call)
    await db_session.commit()
    await db_session.refresh(call)
    return call


@pytest_asyncio.fixture
async def test_subscription(
    db_session: AsyncSession,
    test_professional: ProfessionalProfile,
) -> Subscription:
    """Create a test subscription."""
    subscription = Subscription(
        id=uuid.uuid4(),
        professional_id=test_professional.id,
        stripe_subscription_id="sub_test123",
        tier=SubscriptionTier.PROFESSIONAL,
        status=SubscriptionStatus.ACTIVE,
        current_period_start=datetime.utcnow(),
        current_period_end=datetime.utcnow(),
    )
    db_session.add(subscription)
    await db_session.commit()
    await db_session.refresh(subscription)
    return subscription


@pytest_asyncio.fixture
async def test_bid_wallet(
    db_session: AsyncSession,
    test_professional: ProfessionalProfile,
) -> BidWallet:
    """Create a test bid wallet."""
    wallet = BidWallet(
        id=uuid.uuid4(),
        professional_id=test_professional.id,
        available_credits=Decimal("100.00"),
        reserved_credits=Decimal("10.00"),
        total_deposited=Decimal("200.00"),
        total_spent=Decimal("90.00"),
    )
    db_session.add(wallet)
    await db_session.commit()
    await db_session.refresh(wallet)
    return wallet


# ==================== Mock Service Fixtures ====================

@pytest.fixture
def mock_presence_service():
    """Mock the presence service for testing."""
    mock_service = MagicMock()
    mock_service.is_available = AsyncMock(return_value=True)
    mock_service.set_online = AsyncMock()
    mock_service.set_offline = AsyncMock()
    mock_service.set_busy = AsyncMock()
    mock_service.set_available = AsyncMock()
    mock_service.heartbeat = AsyncMock()
    return mock_service


@pytest.fixture
def mock_presence_service_offline():
    """Mock the presence service with professional offline."""
    mock_service = MagicMock()
    mock_service.is_available = AsyncMock(return_value=False)
    mock_service.set_online = AsyncMock()
    mock_service.set_offline = AsyncMock()
    mock_service.set_busy = AsyncMock()
    mock_service.set_available = AsyncMock()
    mock_service.heartbeat = AsyncMock()
    return mock_service


@pytest.fixture
def mock_signaling_service():
    """Mock the signaling service for testing."""
    mock_service = MagicMock()

    # Create a mock room
    mock_room = MagicMock()
    mock_room.room_id = f"room_{uuid.uuid4().hex[:8]}"
    mock_room.borrower_id = "test_borrower"
    mock_room.professional_id = "test_professional"

    mock_service.create_room = AsyncMock(return_value=mock_room)
    mock_service.get_room = AsyncMock(return_value=mock_room)
    mock_service.update_room_state = AsyncMock(return_value=mock_room)
    mock_service.get_ice_servers = AsyncMock(return_value=[
        {"urls": "stun:stun.l.google.com:19302"},
    ])
    mock_service.calculate_pickup_time = MagicMock(return_value=5.0)
    return mock_service


@pytest.fixture
def mock_stripe_service():
    """Mock the Stripe service for testing."""
    mock_service = MagicMock()
    mock_service.get_or_create_customer = AsyncMock(return_value="cus_test123")
    mock_service.create_subscription = AsyncMock(return_value={
        "subscription_id": "sub_test123",
        "status": "active",
        "client_secret": "pi_test_secret",
        "current_period_end": datetime.utcnow(),
    })
    mock_service.create_bid_deposit_session = AsyncMock(
        return_value="https://checkout.stripe.com/test"
    )
    mock_service.construct_webhook_event = MagicMock(return_value={
        "type": "checkout.session.completed",
        "data": {"object": {}},
    })
    mock_service.get_tier_pricing = MagicMock(return_value=[
        {"tier": "free", "name": "Free", "price": 0, "features": []},
        {"tier": "basic", "name": "Basic", "price": 49, "features": []},
    ])
    return mock_service


@pytest.fixture
def mock_push_notification_service():
    """Mock the push notification service for testing."""
    mock_service = MagicMock()
    mock_service.send_incoming_call = AsyncMock()
    mock_service.send_notification = AsyncMock()
    return mock_service


# ==================== Authenticated Client Helpers ====================

def authenticated_client(client: AsyncClient, user: User):
    """Helper to create authenticated client by overriding the dependency."""

    async def override_get_current_user():
        return user

    app.dependency_overrides[get_current_user] = override_get_current_user
    return client


@pytest_asyncio.fixture
async def authenticated_borrower_client(
    client: AsyncClient,
    test_user: User,
) -> AsyncClient:
    """Create an authenticated client for the borrower user."""
    # Override auth dependency
    async def override_get_current_user():
        return test_user

    app.dependency_overrides[get_current_user] = override_get_current_user
    yield client
    # Clean up is handled by the main client fixture


@pytest_asyncio.fixture
async def authenticated_professional_client(
    client: AsyncClient,
    test_professional_user: User,
    test_professional: ProfessionalProfile,  # Ensure profile exists
) -> AsyncClient:
    """Create an authenticated client for the professional user."""
    # Attach the professional profile to the user object for the dependency
    test_professional_user.professional_profile = test_professional

    async def override_get_current_user():
        return test_professional_user

    app.dependency_overrides[get_current_user] = override_get_current_user
    yield client
