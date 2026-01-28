#!/usr/bin/env python3
"""
Seed Data Script for FaceMortgage Demo

Creates demo accounts for testing:
- Admin user
- Multiple loan officers with varying stats
- Sample borrowers
- Sample leads and calls

Run with: PYTHONPATH=. python scripts/seed_demo.py
"""

import asyncio
import uuid
from datetime import datetime, timedelta
from decimal import Decimal
import random

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from passlib.context import CryptContext

from src.app.models.user import User, UserType
from src.app.models.professional import (
    ProfessionalProfile, 
    ProfessionalStatus,
    Specialty,
    Language,
    ProfessionalSpecialty,
    ProfessionalLanguage,
)
from src.app.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# Demo Data
DEMO_USERS = [
    {
        "email": "admin@facemortgage.com",
        "password": "admin123",
        "first_name": "Admin",
        "last_name": "User",
        "user_type": UserType.ADMIN,
        "is_admin": True,
    },
    {
        "email": "john@loanpro.com",
        "password": "demo123",
        "first_name": "John",
        "last_name": "Smith",
        "user_type": UserType.LOAN_OFFICER,
        "pro_data": {
            "company_name": "LoanPro Mortgage",
            "nmls_id": "123456",
            "nmls_verified": True,
            "years_experience": 12,
            "avg_rating": Decimal("4.9"),
            "total_reviews": 156,
            "avg_pickup_time_seconds": Decimal("8"),
            "status": ProfessionalStatus.ONLINE_AVAILABLE,
            "specialties": ["FHA", "VA", "First-Time Buyer"],
            "languages": ["en", "es"],
        },
    },
    {
        "email": "maria@quickloans.com",
        "password": "demo123",
        "first_name": "Maria",
        "last_name": "Garcia",
        "user_type": UserType.LOAN_OFFICER,
        "pro_data": {
            "company_name": "QuickLoans Inc",
            "nmls_id": "789012",
            "nmls_verified": True,
            "years_experience": 8,
            "avg_rating": Decimal("4.7"),
            "total_reviews": 89,
            "avg_pickup_time_seconds": Decimal("15"),
            "status": ProfessionalStatus.ONLINE_AVAILABLE,
            "specialties": ["Conventional", "Jumbo", "Self-Employed"],
            "languages": ["en", "es"],
        },
    },
    {
        "email": "david@mortgageplus.com",
        "password": "demo123",
        "first_name": "David",
        "last_name": "Chen",
        "user_type": UserType.LOAN_OFFICER,
        "pro_data": {
            "company_name": "MortgagePlus",
            "nmls_id": "345678",
            "nmls_verified": True,
            "years_experience": 15,
            "avg_rating": Decimal("4.8"),
            "total_reviews": 234,
            "avg_pickup_time_seconds": Decimal("25"),
            "status": ProfessionalStatus.ONLINE_BUSY,
            "specialties": ["Jumbo", "Investment Property"],
            "languages": ["en", "zh"],
        },
    },
    {
        "email": "sarah@homelenders.com",
        "password": "demo123",
        "first_name": "Sarah",
        "last_name": "Johnson",
        "user_type": UserType.LOAN_OFFICER,
        "pro_data": {
            "company_name": "Home Lenders LLC",
            "nmls_id": "567890",
            "nmls_verified": False,  # Not yet verified
            "years_experience": 3,
            "avg_rating": Decimal("4.5"),
            "total_reviews": 24,
            "avg_pickup_time_seconds": Decimal("45"),
            "status": ProfessionalStatus.OFFLINE,
            "specialties": ["FHA", "Low Down Payment"],
            "languages": ["en"],
        },
    },
    {
        "email": "borrower@test.com",
        "password": "test123",
        "first_name": "Test",
        "last_name": "Borrower",
        "user_type": UserType.BORROWER,
    },
]


async def create_specialties_and_languages(session: AsyncSession):
    """Create lookup tables for specialties and languages."""
    specialties_data = [
        "FHA", "VA", "Conventional", "Jumbo", "First-Time Buyer",
        "Self-Employed", "Investment Property", "Low Down Payment",
        "USDA", "Refinance", "HELOC",
    ]
    
    languages_data = [
        ("en", "English"),
        ("es", "Spanish"),
        ("zh", "Chinese"),
        ("vi", "Vietnamese"),
        ("ko", "Korean"),
    ]
    
    specialty_map = {}
    for name in specialties_data:
        specialty = Specialty(id=uuid.uuid4(), name=name)
        session.add(specialty)
        specialty_map[name] = specialty
    
    language_map = {}
    for code, name in languages_data:
        lang = Language(id=uuid.uuid4(), code=code, name=name)
        session.add(lang)
        language_map[code] = lang
    
    await session.flush()
    return specialty_map, language_map


async def create_demo_users(session: AsyncSession, specialty_map: dict, language_map: dict):
    """Create demo users and professionals."""
    for user_data in DEMO_USERS:
        # Create user
        user = User(
            id=uuid.uuid4(),
            email=user_data["email"],
            hashed_password=pwd_context.hash(user_data["password"]),
            first_name=user_data["first_name"],
            last_name=user_data["last_name"],
            user_type=user_data["user_type"],
            is_admin=user_data.get("is_admin", False),
            email_verified=True,
            is_active=True,
        )
        session.add(user)
        
        # Create professional profile if LO
        if "pro_data" in user_data:
            pro_data = user_data["pro_data"]
            profile = ProfessionalProfile(
                id=uuid.uuid4(),
                user_id=user.id,
                company_name=pro_data["company_name"],
                nmls_id=pro_data["nmls_id"],
                nmls_verified=pro_data["nmls_verified"],
                years_experience=pro_data["years_experience"],
                avg_rating=pro_data["avg_rating"],
                total_reviews=pro_data["total_reviews"],
                avg_pickup_time_seconds=pro_data["avg_pickup_time_seconds"],
                status=pro_data["status"],
                profile_complete=True,
            )
            session.add(profile)
            await session.flush()
            
            # Add specialties
            for specialty_name in pro_data.get("specialties", []):
                if specialty_name in specialty_map:
                    ps = ProfessionalSpecialty(
                        professional_id=profile.id,
                        specialty_id=specialty_map[specialty_name].id,
                    )
                    session.add(ps)
            
            # Add languages
            for lang_code in pro_data.get("languages", []):
                if lang_code in language_map:
                    pl = ProfessionalLanguage(
                        professional_id=profile.id,
                        language_id=language_map[lang_code].id,
                    )
                    session.add(pl)
    
    await session.commit()
    print(f"✅ Created {len(DEMO_USERS)} demo users")


async def main():
    """Run the seed script."""
    print("🌱 Seeding FaceMortgage demo data...")
    
    # Create engine
    database_url = settings.database_url.replace("postgresql://", "postgresql+asyncpg://")
    if "sqlite" in database_url:
        database_url = database_url.replace("sqlite://", "sqlite+aiosqlite://")
    
    engine = create_async_engine(database_url, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        try:
            # Create lookups first
            specialty_map, language_map = await create_specialties_and_languages(session)
            
            # Create users and professionals
            await create_demo_users(session, specialty_map, language_map)
            
            print("\n✅ Demo data seeded successfully!")
            print("\nDemo Accounts:")
            print("-" * 40)
            for user in DEMO_USERS:
                print(f"  {user['email']} / {user['password']} ({user['user_type'].value})")
            print("-" * 40)
            
        except Exception as e:
            print(f"❌ Error: {e}")
            await session.rollback()
            raise


if __name__ == "__main__":
    asyncio.run(main())
