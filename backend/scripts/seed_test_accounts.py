#!/usr/bin/env python3
"""
Seed script to create test accounts for development.

Run with: python scripts/seed_test_accounts.py
"""
import asyncio
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select
from src.app.core.database import async_session_maker, engine, Base
from src.app.models.user import User, UserType
from src.app.models.professional import ProfessionalProfile, SubscriptionTier
from src.app.core.security import get_password_hash


# Test accounts configuration
TEST_ACCOUNTS = [
    {
        "email": "superadmin@facemortgage.com",
        "password": "superadmin123",
        "first_name": "Super",
        "last_name": "Admin",
        "user_type": UserType.LOAN_OFFICER,
        "is_admin": True,
        "is_super_admin": True,
        "phone": "(555) 000-0001",
    },
    {
        "email": "admin@facemortgage.com",
        "password": "admin123",
        "first_name": "Platform",
        "last_name": "Admin",
        "user_type": UserType.LOAN_OFFICER,
        "is_admin": True,
        "is_super_admin": False,
        "phone": "(555) 000-0002",
    },
    {
        "email": "user@facemortgage.com",
        "password": "user123",
        "first_name": "John",
        "last_name": "Borrower",
        "user_type": UserType.BORROWER,
        "is_admin": False,
        "is_super_admin": False,
        "phone": "(555) 000-0003",
    },
    {
        "email": "sales@facemortgage.com",
        "password": "sales123",
        "first_name": "Sarah",
        "last_name": "Sales",
        "user_type": UserType.LOAN_OFFICER,
        "is_admin": False,
        "is_super_admin": False,
        "phone": "(555) 000-0004",
        "nmls_id": "123456",
        "company_name": "FaceMortgage Direct",
    },
]


async def create_tables():
    """Create all tables if they don't exist."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Database tables created/verified.")


async def seed_accounts():
    """Create test accounts."""
    async with async_session_maker() as session:
        created = 0
        skipped = 0

        for account in TEST_ACCOUNTS:
            # Check if account already exists
            result = await session.execute(
                select(User).where(User.email == account["email"])
            )
            existing = result.scalar_one_or_none()

            if existing:
                print(f"  Skipped: {account['email']} (already exists)")
                skipped += 1
                continue

            # Create user
            user = User(
                email=account["email"],
                password_hash=get_password_hash(account["password"]),
                first_name=account["first_name"],
                last_name=account["last_name"],
                user_type=account["user_type"],
                phone=account.get("phone"),
                is_admin=account.get("is_admin", False),
                is_super_admin=account.get("is_super_admin", False),
                email_verified=True,
                is_active=True,
            )
            session.add(user)
            await session.flush()  # Get the user ID

            # Create professional profile if applicable
            if account["user_type"] != UserType.BORROWER:
                profile = ProfessionalProfile(
                    user_id=user.id,
                    nmls_id=account.get("nmls_id", f"TEST{created + 1:05d}"),
                    company_name=account.get("company_name", "FaceMortgage Test"),
                    bio=f"Test account for {account['first_name']} {account['last_name']}",
                    subscription_tier=SubscriptionTier.PROFESSIONAL if account.get("is_admin") else SubscriptionTier.BASIC,
                    avg_rating=4.5,
                    total_reviews=10,
                    avg_pickup_time_seconds=8.0,
                )
                session.add(profile)

            print(f"  Created: {account['email']}")
            created += 1

        await session.commit()

        return created, skipped


async def main():
    print("\n" + "=" * 60)
    print("FaceMortgage Test Account Seeder")
    print("=" * 60 + "\n")

    print("Creating database tables...")
    await create_tables()

    print("\nSeeding test accounts...")
    created, skipped = await seed_accounts()

    print("\n" + "-" * 60)
    print(f"Results: {created} created, {skipped} skipped")
    print("-" * 60)

    print("\n Quick Login Credentials:")
    print("-" * 60)
    print(f"{'Role':<15} {'Email':<35} {'Password':<15}")
    print("-" * 60)
    for account in TEST_ACCOUNTS:
        role = "Super Admin" if account.get("is_super_admin") else \
               "Admin" if account.get("is_admin") else \
               "Sales Rep" if account.get("nmls_id") else "User"
        print(f"{role:<15} {account['email']:<35} {account['password']:<15}")
    print("-" * 60 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
