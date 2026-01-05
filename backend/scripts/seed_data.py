"""
Seed script to populate the database with test data.
Run with: python -m scripts.seed_data
"""
import asyncio
import random
import uuid
from datetime import datetime, date, timedelta
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from src.app.config import settings
from src.app.core.security import get_password_hash
from src.app.models.user import User, UserType
from src.app.models.professional import (
    ProfessionalProfile,
    ProfessionalStatus,
    SubscriptionTier,
    Specialty,
    Language,
    County,
    ProfessionalSpecialty,
    ProfessionalLanguage,
    ProfessionalServiceArea,
)
from src.app.models.borrower import BorrowerProfile
from src.app.models.analytics import GridImpression, GridClick


# Seed data
SPECIALTIES = [
    {"name": "Conventional Loans", "category": "loan_type"},
    {"name": "FHA Loans", "category": "loan_type"},
    {"name": "VA Loans", "category": "loan_type"},
    {"name": "USDA Loans", "category": "loan_type"},
    {"name": "Jumbo Loans", "category": "loan_type"},
    {"name": "Non-QM Loans", "category": "loan_type"},
    {"name": "Hard Money Loans", "category": "loan_type"},
    {"name": "Commercial Loans", "category": "loan_type"},
    {"name": "Construction Loans", "category": "loan_type"},
    {"name": "Reverse Mortgages", "category": "loan_type"},
    {"name": "Down Payment Assistance", "category": "program"},
    {"name": "First-Time Homebuyers", "category": "client_type"},
    {"name": "Investment Properties", "category": "property_type"},
    {"name": "Refinancing", "category": "loan_type"},
    {"name": "Cash-Out Refinance", "category": "loan_type"},
]

LANGUAGES = [
    {"code": "en", "name": "English"},
    {"code": "es", "name": "Spanish"},
    {"code": "zh", "name": "Chinese (Mandarin)"},
    {"code": "tl", "name": "Tagalog"},
    {"code": "vi", "name": "Vietnamese"},
    {"code": "ko", "name": "Korean"},
    {"code": "ru", "name": "Russian"},
    {"code": "ar", "name": "Arabic"},
    {"code": "hi", "name": "Hindi"},
    {"code": "pt", "name": "Portuguese"},
    {"code": "fr", "name": "French"},
    {"code": "de", "name": "German"},
    {"code": "it", "name": "Italian"},
    {"code": "pl", "name": "Polish"},
    {"code": "hu", "name": "Hungarian"},
    {"code": "ja", "name": "Japanese"},
]

COUNTIES = [
    {"state_code": "CA", "county_name": "Los Angeles", "fips_code": "06037"},
    {"state_code": "CA", "county_name": "San Diego", "fips_code": "06073"},
    {"state_code": "CA", "county_name": "Orange", "fips_code": "06059"},
    {"state_code": "CA", "county_name": "Santa Clara", "fips_code": "06085"},
    {"state_code": "TX", "county_name": "Harris", "fips_code": "48201"},
    {"state_code": "TX", "county_name": "Dallas", "fips_code": "48113"},
    {"state_code": "TX", "county_name": "Travis", "fips_code": "48453"},
    {"state_code": "FL", "county_name": "Miami-Dade", "fips_code": "12086"},
    {"state_code": "FL", "county_name": "Broward", "fips_code": "12011"},
    {"state_code": "AZ", "county_name": "Maricopa", "fips_code": "04013"},
    {"state_code": "NV", "county_name": "Clark", "fips_code": "32003"},
    {"state_code": "OH", "county_name": "Cuyahoga", "fips_code": "39035"},
    {"state_code": "NY", "county_name": "New York", "fips_code": "36061"},
    {"state_code": "IL", "county_name": "Cook", "fips_code": "17031"},
    {"state_code": "WA", "county_name": "King", "fips_code": "53033"},
]

# Test professionals
PROFESSIONALS = [
    {
        "email": "sarah.johnson@example.com",
        "first_name": "Sarah",
        "last_name": "Johnson",
        "user_type": UserType.LOAN_OFFICER,
        "company_name": "First National Mortgage",
        "job_title": "Senior Loan Officer",
        "bio": "15+ years helping families achieve their homeownership dreams. Specializing in first-time homebuyers and VA loans.",
        "years_experience": 15,
        "nmls_id": "123456",
        "subscription_tier": SubscriptionTier.PROFESSIONAL,
        "avg_rating": Decimal("4.8"),
        "total_reviews": 127,
        "avg_pickup_time_seconds": Decimal("8.5"),
        "total_calls_completed": 342,
        "status": ProfessionalStatus.ONLINE_AVAILABLE,
        "specialties": ["Conventional Loans", "VA Loans", "First-Time Homebuyers"],
        "languages": ["en", "es"],
        "service_areas": ["Los Angeles", "Orange", "San Diego"],
    },
    {
        "email": "michael.chen@example.com",
        "first_name": "Michael",
        "last_name": "Chen",
        "user_type": UserType.LOAN_OFFICER,
        "company_name": "Pacific Coast Lending",
        "job_title": "Mortgage Consultant",
        "bio": "Fluent in Mandarin and English. Helping Asian-American families navigate the mortgage process with cultural understanding.",
        "years_experience": 8,
        "nmls_id": "234567",
        "subscription_tier": SubscriptionTier.PREMIUM,
        "avg_rating": Decimal("4.9"),
        "total_reviews": 89,
        "avg_pickup_time_seconds": Decimal("5.2"),
        "total_calls_completed": 215,
        "status": ProfessionalStatus.ONLINE_AVAILABLE,
        "current_bid_amount": Decimal("25.00"),
        "specialties": ["Conventional Loans", "Jumbo Loans", "Investment Properties"],
        "languages": ["en", "zh"],
        "service_areas": ["Santa Clara", "Los Angeles"],
    },
    {
        "email": "maria.garcia@example.com",
        "first_name": "Maria",
        "last_name": "Garcia",
        "user_type": UserType.LOAN_OFFICER,
        "company_name": "Unity Home Loans",
        "job_title": "Bilingual Loan Officer",
        "bio": "Especialista en préstamos hipotecarios. Helping Spanish-speaking families understand their mortgage options.",
        "years_experience": 12,
        "nmls_id": "345678",
        "subscription_tier": SubscriptionTier.PROFESSIONAL,
        "avg_rating": Decimal("4.7"),
        "total_reviews": 156,
        "avg_pickup_time_seconds": Decimal("12.3"),
        "total_calls_completed": 428,
        "status": ProfessionalStatus.ONLINE_BUSY,
        "specialties": ["FHA Loans", "Down Payment Assistance", "First-Time Homebuyers"],
        "languages": ["en", "es"],
        "service_areas": ["Miami-Dade", "Broward"],
    },
    {
        "email": "james.wilson@example.com",
        "first_name": "James",
        "last_name": "Wilson",
        "user_type": UserType.LOAN_OFFICER,
        "company_name": "Veterans First Mortgage",
        "job_title": "VA Loan Specialist",
        "bio": "Army veteran dedicated to serving fellow veterans. Expert in VA loans and military benefits.",
        "years_experience": 10,
        "nmls_id": "456789",
        "subscription_tier": SubscriptionTier.BASIC,
        "avg_rating": Decimal("4.9"),
        "total_reviews": 203,
        "avg_pickup_time_seconds": Decimal("6.8"),
        "total_calls_completed": 567,
        "status": ProfessionalStatus.ONLINE_AVAILABLE,
        "specialties": ["VA Loans", "Conventional Loans", "Refinancing"],
        "languages": ["en"],
        "service_areas": ["Harris", "Dallas", "Travis"],
    },
    {
        "email": "anna.kovacs@example.com",
        "first_name": "Anna",
        "last_name": "Kovács",
        "user_type": UserType.LOAN_OFFICER,
        "company_name": "Central European Mortgage",
        "job_title": "International Loan Specialist",
        "bio": "Native Hungarian speaker helping Eastern European immigrants achieve homeownership in America.",
        "years_experience": 7,
        "nmls_id": "567890",
        "subscription_tier": SubscriptionTier.PROFESSIONAL,
        "avg_rating": Decimal("4.6"),
        "total_reviews": 45,
        "avg_pickup_time_seconds": Decimal("9.1"),
        "total_calls_completed": 98,
        "status": ProfessionalStatus.ONLINE_AVAILABLE,
        "specialties": ["FHA Loans", "Down Payment Assistance", "First-Time Homebuyers"],
        "languages": ["en", "hu", "de"],
        "service_areas": ["New York", "Cook"],
    },
    {
        "email": "robert.kim@example.com",
        "first_name": "Robert",
        "last_name": "Kim",
        "user_type": UserType.LOAN_OFFICER,
        "company_name": "Kim Financial Group",
        "job_title": "Commercial Loan Officer",
        "bio": "Specializing in commercial real estate and investment property financing. Korean and English speaker.",
        "years_experience": 18,
        "nmls_id": "678901",
        "subscription_tier": SubscriptionTier.PREMIUM,
        "avg_rating": Decimal("4.8"),
        "total_reviews": 67,
        "avg_pickup_time_seconds": Decimal("7.4"),
        "total_calls_completed": 189,
        "status": ProfessionalStatus.OFFLINE,
        "current_bid_amount": Decimal("50.00"),
        "specialties": ["Commercial Loans", "Investment Properties", "Hard Money Loans"],
        "languages": ["en", "ko"],
        "service_areas": ["Los Angeles", "Orange"],
    },
    {
        "email": "lisa.thompson@example.com",
        "first_name": "Lisa",
        "last_name": "Thompson",
        "user_type": UserType.REALTOR,
        "company_name": "Thompson Realty Group",
        "job_title": "Senior Real Estate Agent",
        "bio": "Top-producing agent in Southern California. Specializing in luxury homes and first-time buyers.",
        "years_experience": 20,
        "subscription_tier": SubscriptionTier.PROFESSIONAL,
        "avg_rating": Decimal("4.9"),
        "total_reviews": 312,
        "avg_pickup_time_seconds": Decimal("4.5"),
        "total_calls_completed": 892,
        "status": ProfessionalStatus.ONLINE_AVAILABLE,
        "specialties": ["Investment Properties", "First-Time Homebuyers"],
        "languages": ["en"],
        "service_areas": ["Los Angeles", "Orange", "San Diego"],
    },
    {
        "email": "david.nguyen@example.com",
        "first_name": "David",
        "last_name": "Nguyen",
        "user_type": UserType.LOAN_OFFICER,
        "company_name": "Community First Lending",
        "job_title": "Loan Officer",
        "bio": "Vietnamese-American loan officer passionate about helping immigrant families. Fluent in Vietnamese and English.",
        "years_experience": 5,
        "nmls_id": "789012",
        "subscription_tier": SubscriptionTier.BASIC,
        "avg_rating": Decimal("4.5"),
        "total_reviews": 34,
        "avg_pickup_time_seconds": Decimal("15.2"),
        "total_calls_completed": 78,
        "status": ProfessionalStatus.ONLINE_AVAILABLE,
        "specialties": ["FHA Loans", "Down Payment Assistance"],
        "languages": ["en", "vi"],
        "service_areas": ["Santa Clara", "King"],
    },
    {
        "email": "jennifer.martinez@example.com",
        "first_name": "Jennifer",
        "last_name": "Martinez",
        "user_type": UserType.TITLE_REP,
        "company_name": "Secure Title Services",
        "job_title": "Title Officer",
        "bio": "Ensuring smooth closings for over 10 years. Expert in complex title issues and clearing encumbrances.",
        "years_experience": 11,
        "subscription_tier": SubscriptionTier.BASIC,
        "avg_rating": Decimal("4.7"),
        "total_reviews": 89,
        "avg_pickup_time_seconds": Decimal("11.3"),
        "total_calls_completed": 234,
        "status": ProfessionalStatus.ONLINE_AVAILABLE,
        "languages": ["en", "es"],
        "service_areas": ["Maricopa", "Clark"],
    },
    {
        "email": "william.anderson@example.com",
        "first_name": "William",
        "last_name": "Anderson",
        "user_type": UserType.ATTORNEY,
        "company_name": "Anderson Law Group",
        "job_title": "Real Estate Attorney",
        "bio": "Experienced real estate attorney handling closings, contracts, and property disputes.",
        "years_experience": 15,
        "subscription_tier": SubscriptionTier.PROFESSIONAL,
        "avg_rating": Decimal("4.8"),
        "total_reviews": 56,
        "avg_pickup_time_seconds": Decimal("18.5"),
        "total_calls_completed": 145,
        "status": ProfessionalStatus.AWAY,
        "languages": ["en"],
        "service_areas": ["New York", "Cuyahoga"],
    },
]

# Test borrower
BORROWER = {
    "email": "test.borrower@example.com",
    "first_name": "Test",
    "last_name": "Borrower",
    "user_type": UserType.BORROWER,
}


async def seed_database():
    """Seed the database with test data."""
    engine = create_async_engine(settings.database_url, echo=True)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        # Seed specialties
        print("Seeding specialties...")
        specialty_map = {}
        for spec_data in SPECIALTIES:
            result = await session.execute(
                select(Specialty).where(Specialty.name == spec_data["name"])
            )
            existing = result.scalar_one_or_none()
            if not existing:
                specialty = Specialty(**spec_data)
                session.add(specialty)
                await session.flush()
                specialty_map[spec_data["name"]] = specialty.id
            else:
                specialty_map[spec_data["name"]] = existing.id

        # Seed languages
        print("Seeding languages...")
        language_map = {}
        for lang_data in LANGUAGES:
            result = await session.execute(
                select(Language).where(Language.code == lang_data["code"])
            )
            existing = result.scalar_one_or_none()
            if not existing:
                language = Language(**lang_data)
                session.add(language)
                await session.flush()
                language_map[lang_data["code"]] = language.id
            else:
                language_map[lang_data["code"]] = existing.id

        # Seed counties
        print("Seeding counties...")
        county_map = {}
        for county_data in COUNTIES:
            result = await session.execute(
                select(County).where(
                    County.state_code == county_data["state_code"],
                    County.county_name == county_data["county_name"]
                )
            )
            existing = result.scalar_one_or_none()
            if not existing:
                county = County(**county_data)
                session.add(county)
                await session.flush()
                county_map[county_data["county_name"]] = county.id
            else:
                county_map[county_data["county_name"]] = existing.id

        await session.commit()

        # Seed professionals
        print("Seeding professionals...")
        for prof_data in PROFESSIONALS:
            # Check if user already exists
            result = await session.execute(
                select(User).where(User.email == prof_data["email"])
            )
            if result.scalar_one_or_none():
                print(f"  Skipping {prof_data['email']} (already exists)")
                continue

            specialties = prof_data.pop("specialties", [])
            languages = prof_data.pop("languages", [])
            service_areas = prof_data.pop("service_areas", [])

            # Create user
            user = User(
                id=uuid.uuid4(),
                email=prof_data["email"],
                password_hash=get_password_hash("password123"),
                user_type=prof_data["user_type"],
                first_name=prof_data["first_name"],
                last_name=prof_data["last_name"],
                is_active=True,
                email_verified=True,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            session.add(user)
            await session.flush()

            # Create professional profile
            profile = ProfessionalProfile(
                id=uuid.uuid4(),
                user_id=user.id,
                company_name=prof_data.get("company_name"),
                job_title=prof_data.get("job_title"),
                bio=prof_data.get("bio"),
                years_experience=prof_data.get("years_experience"),
                nmls_id=prof_data.get("nmls_id"),
                nmls_verified=bool(prof_data.get("nmls_id")),
                subscription_tier=prof_data.get("subscription_tier", SubscriptionTier.FREE),
                avg_rating=prof_data.get("avg_rating", Decimal("0")),
                total_reviews=prof_data.get("total_reviews", 0),
                avg_pickup_time_seconds=prof_data.get("avg_pickup_time_seconds"),
                total_calls_completed=prof_data.get("total_calls_completed", 0),
                status=prof_data.get("status", ProfessionalStatus.OFFLINE),
                current_bid_amount=prof_data.get("current_bid_amount", Decimal("0")),
                profile_complete=True,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            session.add(profile)
            await session.flush()

            # Add specialties
            for spec_name in specialties:
                if spec_name in specialty_map:
                    ps = ProfessionalSpecialty(
                        professional_id=profile.id,
                        specialty_id=specialty_map[spec_name]
                    )
                    session.add(ps)

            # Add languages
            for lang_code in languages:
                if lang_code in language_map:
                    pl = ProfessionalLanguage(
                        professional_id=profile.id,
                        language_id=language_map[lang_code],
                        proficiency="fluent" if lang_code == "en" else "native"
                    )
                    session.add(pl)

            # Add service areas
            for county_name in service_areas:
                if county_name in county_map:
                    psa = ProfessionalServiceArea(
                        professional_id=profile.id,
                        county_id=county_map[county_name]
                    )
                    session.add(psa)

            print(f"  Created {prof_data['first_name']} {prof_data['last_name']}")

        # Seed test borrower
        print("Seeding test borrower...")
        result = await session.execute(
            select(User).where(User.email == BORROWER["email"])
        )
        if not result.scalar_one_or_none():
            borrower_user = User(
                id=uuid.uuid4(),
                email=BORROWER["email"],
                password_hash=get_password_hash("password123"),
                user_type=BORROWER["user_type"],
                first_name=BORROWER["first_name"],
                last_name=BORROWER["last_name"],
                is_active=True,
                email_verified=True,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            session.add(borrower_user)
            await session.flush()

            borrower_profile = BorrowerProfile(
                id=uuid.uuid4(),
                user_id=borrower_user.id,
                preferred_languages=["en"],
                loan_purpose="purchase",
                contact_preference="video",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            session.add(borrower_profile)
            print(f"  Created test borrower")

        await session.commit()

        # Seed grid analytics data
        await seed_grid_analytics(session)

        print("\nSeed data complete!")
        print("\nTest credentials:")
        print("  Professionals: password123")
        print("  Borrower: test.borrower@example.com / password123")


async def seed_grid_analytics(session: AsyncSession):
    """Seed grid impressions and clicks for the last 30 days."""
    print("\nSeeding grid analytics...")

    # Get all professional profiles
    result = await session.execute(select(ProfessionalProfile))
    professionals = result.scalars().all()

    if not professionals:
        print("  No professionals found, skipping grid analytics")
        return

    today = date.today()

    # Create impressions for the last 30 days
    for days_ago in range(30):
        current_date = today - timedelta(days=days_ago)

        for i, professional in enumerate(professionals):
            # Check if impression already exists for this date
            existing = await session.execute(
                select(GridImpression).where(
                    GridImpression.professional_id == professional.id,
                    GridImpression.date == current_date
                )
            )
            if existing.scalar_one_or_none():
                continue

            # Generate realistic metrics based on subscription tier and position
            base_impressions = random.randint(50, 200)
            tier_multiplier = {
                SubscriptionTier.FREE: 0.5,
                SubscriptionTier.BASIC: 1.0,
                SubscriptionTier.PROFESSIONAL: 1.5,
                SubscriptionTier.PREMIUM: 2.0,
            }.get(professional.subscription_tier, 1.0)

            impressions = int(base_impressions * tier_multiplier)

            # Click-through rate varies by tier (1-5%)
            ctr = random.uniform(0.01, 0.05) * tier_multiplier
            clicks = int(impressions * ctr)

            # Calls initiated is a subset of clicks (20-50% of clicks)
            calls = int(clicks * random.uniform(0.2, 0.5))

            # Average position based on subscription tier
            base_position = {
                SubscriptionTier.FREE: random.randint(20, 40),
                SubscriptionTier.BASIC: random.randint(10, 25),
                SubscriptionTier.PROFESSIONAL: random.randint(5, 15),
                SubscriptionTier.PREMIUM: random.randint(1, 8),
            }.get(professional.subscription_tier, random.randint(15, 30))

            impression = GridImpression(
                id=uuid.uuid4(),
                professional_id=professional.id,
                date=current_date,
                impressions_count=impressions,
                clicks_count=clicks,
                calls_initiated=calls,
                avg_position=base_position,
                created_at=datetime.combine(current_date, datetime.min.time()),
                updated_at=datetime.combine(current_date, datetime.min.time()),
            )
            session.add(impression)

        # Add some individual click records for the most recent 7 days
        if days_ago < 7:
            for professional in random.sample(professionals, min(5, len(professionals))):
                click_types = ['profile_view', 'call_initiated', 'video_preview']
                for _ in range(random.randint(1, 5)):
                    click = GridClick(
                        id=uuid.uuid4(),
                        professional_id=professional.id,
                        session_id=f"seed_session_{uuid.uuid4().hex[:8]}",
                        click_type=random.choice(click_types),
                        grid_position=random.randint(1, 20),
                        filter_context={"language": random.choice(["en", "es", "zh"])},
                        created_at=datetime.combine(
                            current_date,
                            datetime.min.time()
                        ) + timedelta(hours=random.randint(9, 17)),
                    )
                    session.add(click)

    await session.commit()
    print(f"  Created grid analytics for {len(professionals)} professionals over 30 days")


if __name__ == "__main__":
    asyncio.run(seed_database())
