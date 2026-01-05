# FaceMortgage Gap Remediation Plan

**Created**: January 1, 2026
**Status**: Ready for Implementation
**Estimated Completion**: 8-10 weeks of focused development

---

## Table of Contents

1. [Implementation Strategy](#implementation-strategy)
2. [Phase 1: Payment & Billing Completion](#phase-1-payment--billing-completion)
3. [Phase 2: Data Provider Integration](#phase-2-data-provider-integration)
4. [Phase 3: Video Infrastructure Upgrade](#phase-3-video-infrastructure-upgrade)
5. [Phase 4: Mobile & PWA](#phase-4-mobile--pwa)
6. [Phase 5: Analytics & Reporting](#phase-5-analytics--reporting)
7. [Phase 6: Testing & Quality Assurance](#phase-6-testing--quality-assurance)
8. [Phase 7: Production Readiness](#phase-7-production-readiness)
9. [Phase 8: Strategic Features](#phase-8-strategic-features)
10. [Task Checklist](#task-checklist)

---

## Implementation Strategy

### Parallel Workstreams

```
Week 1-2:  [Payment/Billing] + [Testing Infrastructure]
Week 3-4:  [Data Providers] + [Analytics Backend]
Week 5-6:  [Video Upgrade] + [Email Notifications]
Week 7-8:  [PWA/Mobile] + [Admin Dashboard]
Week 9-10: [Strategic Features] + [Production Hardening]
```

### Priority Matrix

| Priority | Category | Business Impact | Technical Risk |
|----------|----------|-----------------|----------------|
| P0 | Stripe Webhooks | Critical - No revenue without it | Low |
| P0 | Testing Suite | Critical - Can't deploy safely | Medium |
| P1 | Data Provider APIs | High - Core value prop | Medium |
| P1 | Email Notifications | High - User engagement | Low |
| P1 | Geo-Detection | High - UX improvement | Low |
| P2 | Analytics Dashboard | Medium - Professional retention | Medium |
| P2 | PWA + Push | Medium - Mobile experience | Medium |
| P2 | LiveKit Migration | Medium - Scale preparation | High |
| P3 | Embeddable Widget | Low - Growth channel | Low |
| P3 | Education Hub | Low - SEO play | Low |

---

## Phase 1: Payment & Billing Completion

### 1.1 Stripe Webhook Handler Implementation

**File**: `backend/src/app/api/v1/routes/billing.py`

#### Task 1.1.1: Create Webhook Endpoint
```python
# Add to billing.py

@router.post("/webhooks/stripe")
async def stripe_webhook(
    request: Request,
    db: DbSession,
):
    """Handle Stripe webhook events."""
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        raise HTTPException(400, "Invalid payload")
    except stripe.error.SignatureVerificationError:
        raise HTTPException(400, "Invalid signature")

    # Route to handlers
    handlers = {
        "customer.subscription.created": handle_subscription_created,
        "customer.subscription.updated": handle_subscription_updated,
        "customer.subscription.deleted": handle_subscription_deleted,
        "invoice.payment_succeeded": handle_invoice_paid,
        "invoice.payment_failed": handle_invoice_failed,
        "checkout.session.completed": handle_checkout_completed,
    }

    handler = handlers.get(event["type"])
    if handler:
        await handler(event["data"]["object"], db)

    return {"received": True}
```

#### Task 1.1.2: Implement Webhook Handlers
**File**: `backend/src/app/integrations/stripe/webhooks.py` (NEW)

```python
from datetime import datetime
from sqlalchemy import select
from src.app.models.billing import Subscription, SubscriptionTier, BillingTransaction
from src.app.models.user import User

async def handle_subscription_created(subscription_data: dict, db):
    """Handle new subscription creation."""
    customer_id = subscription_data["customer"]

    # Find user by Stripe customer ID
    user = await db.execute(
        select(User).where(User.stripe_customer_id == customer_id)
    )
    user = user.scalar_one_or_none()
    if not user:
        logger.error(f"User not found for customer {customer_id}")
        return

    # Map Stripe price to tier
    price_id = subscription_data["items"]["data"][0]["price"]["id"]
    tier = map_price_to_tier(price_id)

    # Create/update subscription record
    subscription = Subscription(
        professional_id=user.professional_profile.id,
        stripe_subscription_id=subscription_data["id"],
        stripe_customer_id=customer_id,
        tier=tier,
        status="active",
        current_period_start=datetime.fromtimestamp(subscription_data["current_period_start"]),
        current_period_end=datetime.fromtimestamp(subscription_data["current_period_end"]),
    )
    db.add(subscription)
    await db.commit()

async def handle_subscription_updated(subscription_data: dict, db):
    """Handle subscription changes (upgrade/downgrade/cancel)."""
    sub = await db.execute(
        select(Subscription).where(
            Subscription.stripe_subscription_id == subscription_data["id"]
        )
    )
    sub = sub.scalar_one_or_none()
    if not sub:
        return

    # Update tier if changed
    price_id = subscription_data["items"]["data"][0]["price"]["id"]
    sub.tier = map_price_to_tier(price_id)
    sub.status = subscription_data["status"]
    sub.current_period_end = datetime.fromtimestamp(subscription_data["current_period_end"])

    # Handle cancellation
    if subscription_data.get("cancel_at_period_end"):
        sub.cancel_at_period_end = True

    await db.commit()

async def handle_subscription_deleted(subscription_data: dict, db):
    """Handle subscription cancellation."""
    sub = await db.execute(
        select(Subscription).where(
            Subscription.stripe_subscription_id == subscription_data["id"]
        )
    )
    sub = sub.scalar_one_or_none()
    if sub:
        sub.status = "canceled"
        sub.canceled_at = datetime.utcnow()
        await db.commit()

async def handle_invoice_paid(invoice_data: dict, db):
    """Record successful payment."""
    transaction = BillingTransaction(
        stripe_invoice_id=invoice_data["id"],
        stripe_customer_id=invoice_data["customer"],
        amount_cents=invoice_data["amount_paid"],
        currency=invoice_data["currency"],
        status="succeeded",
        description=invoice_data.get("description", "Subscription payment"),
    )
    db.add(transaction)
    await db.commit()

async def handle_invoice_failed(invoice_data: dict, db):
    """Handle failed payment - pause bids, notify user."""
    customer_id = invoice_data["customer"]

    # Find professional
    user = await db.execute(
        select(User).where(User.stripe_customer_id == customer_id)
    )
    user = user.scalar_one_or_none()
    if not user or not user.professional_profile:
        return

    # Pause all active bids
    from src.app.models.billing import PlacementBid
    bids = await db.execute(
        select(PlacementBid).where(
            PlacementBid.professional_id == user.professional_profile.id,
            PlacementBid.status == "active"
        )
    )
    for bid in bids.scalars():
        bid.status = "paused"

    await db.commit()

    # Send notification
    send_payment_failed_email.delay(user.email, user.first_name)

def map_price_to_tier(price_id: str) -> SubscriptionTier:
    """Map Stripe price ID to subscription tier."""
    price_map = {
        settings.STRIPE_PRICE_BASIC: SubscriptionTier.BASIC,
        settings.STRIPE_PRICE_PROFESSIONAL: SubscriptionTier.PROFESSIONAL,
        settings.STRIPE_PRICE_PREMIUM: SubscriptionTier.PREMIUM,
    }
    return price_map.get(price_id, SubscriptionTier.FREE)
```

#### Task 1.1.3: Add Stripe Config to Settings
**File**: `backend/src/app/config.py`

```python
# Add to Settings class
STRIPE_SECRET_KEY: str
STRIPE_PUBLISHABLE_KEY: str
STRIPE_WEBHOOK_SECRET: str
STRIPE_PRICE_BASIC: str = "price_basic_monthly"
STRIPE_PRICE_PROFESSIONAL: str = "price_professional_monthly"
STRIPE_PRICE_PREMIUM: str = "price_premium_monthly"
```

#### Task 1.1.4: Create Checkout Session Endpoint
**File**: `backend/src/app/api/v1/routes/billing.py`

```python
@router.post("/create-checkout-session")
async def create_checkout_session(
    request: CreateCheckoutRequest,
    current_user: CurrentProfessional,
    db: DbSession,
):
    """Create Stripe checkout session for subscription."""

    # Get or create Stripe customer
    if not current_user.stripe_customer_id:
        customer = stripe.Customer.create(
            email=current_user.email,
            name=f"{current_user.first_name} {current_user.last_name}",
            metadata={"user_id": str(current_user.id)},
        )
        current_user.stripe_customer_id = customer.id
        await db.commit()

    # Create checkout session
    session = stripe.checkout.Session.create(
        customer=current_user.stripe_customer_id,
        payment_method_types=["card"],
        line_items=[{
            "price": request.price_id,
            "quantity": 1,
        }],
        mode="subscription",
        success_url=f"{settings.FRONTEND_URL}/dashboard/billing?success=true",
        cancel_url=f"{settings.FRONTEND_URL}/dashboard/billing?canceled=true",
        metadata={"user_id": str(current_user.id)},
    )

    return {"checkout_url": session.url, "session_id": session.id}
```

### 1.2 Bid Wallet Deposit Flow

#### Task 1.2.1: Create Wallet Deposit Endpoint
```python
@router.post("/wallet/deposit")
async def deposit_to_wallet(
    request: WalletDepositRequest,
    current_user: CurrentProfessional,
    db: DbSession,
):
    """Add credits to bid wallet via Stripe payment."""

    # Create payment intent
    intent = stripe.PaymentIntent.create(
        amount=request.amount_cents,
        currency="usd",
        customer=current_user.stripe_customer_id,
        metadata={
            "type": "wallet_deposit",
            "user_id": str(current_user.id),
        },
    )

    return {
        "client_secret": intent.client_secret,
        "amount": request.amount_cents,
    }

@router.post("/wallet/confirm-deposit")
async def confirm_wallet_deposit(
    request: ConfirmDepositRequest,
    current_user: CurrentProfessional,
    db: DbSession,
):
    """Confirm wallet deposit after successful payment."""

    # Verify payment intent
    intent = stripe.PaymentIntent.retrieve(request.payment_intent_id)
    if intent.status != "succeeded":
        raise HTTPException(400, "Payment not completed")

    # Add to wallet
    wallet = current_user.professional_profile.bid_wallet
    wallet.available_credits += intent.amount

    # Record transaction
    transaction = BillingTransaction(
        professional_id=current_user.professional_profile.id,
        type="wallet_deposit",
        amount_cents=intent.amount,
        status="completed",
        stripe_payment_intent_id=intent.id,
    )
    db.add(transaction)
    await db.commit()

    return {"new_balance": wallet.available_credits}
```

### 1.3 Frontend Billing Updates

#### Task 1.3.1: Update Billing Page
**File**: `frontend/src/app/dashboard/billing/page.tsx`

```typescript
// Add Stripe Elements integration
import { loadStripe } from '@stripe/stripe-js';
import { Elements, PaymentElement, useStripe, useElements } from '@stripe/react-stripe-js';

const stripePromise = loadStripe(process.env.NEXT_PUBLIC_STRIPE_KEY!);

// Add checkout flow
const handleSubscribe = async (priceId: string) => {
  const response = await billingApi.createCheckoutSession({ price_id: priceId });
  window.location.href = response.checkout_url;
};

// Add wallet deposit modal
const WalletDepositModal = ({ onClose }: { onClose: () => void }) => {
  const [amount, setAmount] = useState(50);
  const [clientSecret, setClientSecret] = useState<string | null>(null);

  const handleInitDeposit = async () => {
    const response = await billingApi.initiateDeposit({ amount_cents: amount * 100 });
    setClientSecret(response.client_secret);
  };

  return (
    <div className="modal">
      {!clientSecret ? (
        <div>
          <h3>Add Credits to Wallet</h3>
          <div className="amount-selector">
            {[25, 50, 100, 250, 500].map(amt => (
              <button
                key={amt}
                onClick={() => setAmount(amt)}
                className={amount === amt ? 'selected' : ''}
              >
                ${amt}
              </button>
            ))}
          </div>
          <button onClick={handleInitDeposit}>Continue to Payment</button>
        </div>
      ) : (
        <Elements stripe={stripePromise} options={{ clientSecret }}>
          <DepositForm amount={amount} onSuccess={onClose} />
        </Elements>
      )}
    </div>
  );
};
```

---

## Phase 2: Data Provider Integration

### 2.1 Complete Data Provider Factory

#### Task 2.1.1: Implement Datagod Provider
**File**: `backend/src/app/integrations/data_providers/datagod.py`

```python
from typing import Optional
from datetime import datetime, timedelta
import httpx
from .base import ProfessionalDataProvider, ProfessionalStats, LicenseInfo, ProductionHistory

class DatagodProvider(ProfessionalDataProvider):
    """Datagod API integration for professional data."""

    def __init__(self, api_key: str, base_url: str = "https://api.datagod.com/v1"):
        self.api_key = api_key
        self.base_url = base_url
        self.client = httpx.AsyncClient(
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=30.0,
        )

    async def get_professional_stats(self, nmls_id: str) -> ProfessionalStats:
        """Fetch production statistics from Datagod."""
        response = await self.client.get(
            f"{self.base_url}/loan-officers/{nmls_id}/stats"
        )
        response.raise_for_status()
        data = response.json()

        return ProfessionalStats(
            nmls_id=nmls_id,
            total_loans_closed=data.get("total_loans", 0),
            total_volume=data.get("total_volume", 0),
            avg_loan_size=data.get("avg_loan_size", 0),
            loans_last_12_months=data.get("loans_12m", 0),
            volume_last_12_months=data.get("volume_12m", 0),
            avg_days_to_close=data.get("avg_days_to_close"),
            purchase_percentage=data.get("purchase_pct", 0),
            refinance_percentage=data.get("refi_pct", 0),
            top_loan_types=data.get("top_loan_types", []),
            fetched_at=datetime.utcnow(),
        )

    async def get_license_info(self, nmls_id: str) -> LicenseInfo:
        """Fetch license information from Datagod."""
        response = await self.client.get(
            f"{self.base_url}/loan-officers/{nmls_id}/licenses"
        )
        response.raise_for_status()
        data = response.json()

        return LicenseInfo(
            nmls_id=nmls_id,
            name=data.get("name"),
            company=data.get("company"),
            licenses=[
                {
                    "state": lic["state"],
                    "license_number": lic["license_number"],
                    "status": lic["status"],
                    "expiration": lic.get("expiration"),
                }
                for lic in data.get("licenses", [])
            ],
            is_active=data.get("is_active", False),
            fetched_at=datetime.utcnow(),
        )

    async def get_production_history(
        self, nmls_id: str, months: int = 24
    ) -> ProductionHistory:
        """Fetch monthly production history."""
        response = await self.client.get(
            f"{self.base_url}/loan-officers/{nmls_id}/production",
            params={"months": months},
        )
        response.raise_for_status()
        data = response.json()

        return ProductionHistory(
            nmls_id=nmls_id,
            monthly_data=[
                {
                    "month": item["month"],
                    "loans": item["loan_count"],
                    "volume": item["volume"],
                }
                for item in data.get("monthly", [])
            ],
            fetched_at=datetime.utcnow(),
        )
```

#### Task 2.1.2: Implement CoreLogic Provider
**File**: `backend/src/app/integrations/data_providers/corelogic.py`

```python
class CoreLogicProvider(ProfessionalDataProvider):
    """CoreLogic API integration."""

    def __init__(self, api_key: str, api_secret: str):
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = "https://api.corelogic.com/property/v2"
        self._token = None
        self._token_expires = None

    async def _get_token(self) -> str:
        """Get OAuth token, refreshing if needed."""
        if self._token and self._token_expires > datetime.utcnow():
            return self._token

        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.corelogic.com/oauth/token",
                data={
                    "grant_type": "client_credentials",
                    "client_id": self.api_key,
                    "client_secret": self.api_secret,
                },
            )
            response.raise_for_status()
            data = response.json()
            self._token = data["access_token"]
            self._token_expires = datetime.utcnow() + timedelta(seconds=data["expires_in"] - 60)
            return self._token

    # ... implement same interface methods
```

#### Task 2.1.3: Update Factory with Caching
**File**: `backend/src/app/integrations/data_providers/factory.py`

```python
from typing import Optional
from datetime import datetime, timedelta
from sqlalchemy import select
from src.app.models.professional import ExternalProfessionalData
from src.app.config import settings

class DataProviderFactory:
    """Factory for creating and managing data providers with caching."""

    _providers = {}
    _cache_ttl = timedelta(hours=24)  # Default 24 hour cache

    @classmethod
    def get_provider(cls, provider_name: Optional[str] = None) -> ProfessionalDataProvider:
        """Get configured data provider instance."""
        provider_name = provider_name or settings.DEFAULT_DATA_PROVIDER

        if provider_name not in cls._providers:
            if provider_name == "datagod":
                cls._providers[provider_name] = DatagodProvider(
                    api_key=settings.DATAGOD_API_KEY
                )
            elif provider_name == "corelogic":
                cls._providers[provider_name] = CoreLogicProvider(
                    api_key=settings.CORELOGIC_API_KEY,
                    api_secret=settings.CORELOGIC_API_SECRET,
                )
            elif provider_name == "modex":
                cls._providers[provider_name] = ModexProvider(
                    api_key=settings.MODEX_API_KEY
                )
            elif provider_name == "redr":
                cls._providers[provider_name] = RedrProvider(
                    api_key=settings.REDR_API_KEY
                )
            else:
                raise ValueError(f"Unknown provider: {provider_name}")

        return cls._providers[provider_name]

    @classmethod
    async def get_professional_stats_cached(
        cls,
        nmls_id: str,
        db,
        provider_name: Optional[str] = None,
        force_refresh: bool = False,
    ) -> ProfessionalStats:
        """Get professional stats with database caching."""

        # Check cache first
        if not force_refresh:
            cached = await db.execute(
                select(ExternalProfessionalData).where(
                    ExternalProfessionalData.nmls_id == nmls_id,
                    ExternalProfessionalData.data_type == "stats",
                    ExternalProfessionalData.expires_at > datetime.utcnow(),
                )
            )
            cached = cached.scalar_one_or_none()
            if cached:
                return ProfessionalStats(**cached.data_json)

        # Fetch fresh data
        provider = cls.get_provider(provider_name)
        stats = await provider.get_professional_stats(nmls_id)

        # Cache result
        cache_entry = ExternalProfessionalData(
            nmls_id=nmls_id,
            provider=provider_name or settings.DEFAULT_DATA_PROVIDER,
            data_type="stats",
            data_json=stats.dict(),
            fetched_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + cls._cache_ttl,
        )
        db.add(cache_entry)
        await db.commit()

        return stats
```

#### Task 2.1.4: Create Baseball Card API Endpoint
**File**: `backend/src/app/api/v1/routes/professionals.py`

```python
@router.get("/{professional_id}/baseball-card")
async def get_baseball_card(
    professional_id: UUID,
    db: DbSession,
):
    """Get baseball card stats for a professional."""

    professional = await db.get(ProfessionalProfile, professional_id)
    if not professional:
        raise HTTPException(404, "Professional not found")

    if not professional.nmls_id:
        return {"error": "NMLS ID not configured", "data": None}

    try:
        # Get cached or fresh stats
        stats = await DataProviderFactory.get_professional_stats_cached(
            professional.nmls_id, db
        )
        license_info = await DataProviderFactory.get_license_info_cached(
            professional.nmls_id, db
        )

        return {
            "nmls_id": professional.nmls_id,
            "stats": stats.dict(),
            "licenses": license_info.dict(),
            "internal_stats": {
                "avg_rating": professional.avg_rating,
                "avg_pickup_time": professional.avg_pickup_time_seconds,
                "total_calls": professional.total_calls,
                "calls_this_month": professional.calls_this_month,
            },
        }
    except httpx.HTTPError as e:
        logger.error(f"Data provider error for {professional.nmls_id}: {e}")
        return {
            "error": "Unable to fetch external data",
            "internal_stats": {
                "avg_rating": professional.avg_rating,
                "avg_pickup_time": professional.avg_pickup_time_seconds,
            },
        }
```

### 2.2 Frontend Baseball Card Update

#### Task 2.2.1: Connect BaseballCard to Real Data
**File**: `frontend/src/components/grid/BaseballCard/BaseballCard.tsx`

```typescript
'use client';

import { useQuery } from '@tanstack/react-query';
import { professionalsApi } from '@/lib/api/endpoints';
import { TrendingUp, Award, Clock, Star, MapPin, Building } from 'lucide-react';

interface BaseballCardProps {
  professionalId: string;
  onClose: () => void;
}

export default function BaseballCard({ professionalId, onClose }: BaseballCardProps) {
  const { data, isLoading, error } = useQuery({
    queryKey: ['baseball-card', professionalId],
    queryFn: () => professionalsApi.getBaseballCard(professionalId),
  });

  if (isLoading) {
    return <BaseballCardSkeleton />;
  }

  if (error || !data) {
    return <BaseballCardError onClose={onClose} />;
  }

  const { stats, licenses, internal_stats } = data;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60" onClick={onClose}>
      <div
        className="bg-white rounded-2xl shadow-2xl max-w-md w-full mx-4 overflow-hidden"
        onClick={e => e.stopPropagation()}
      >
        {/* Header */}
        <div className="bg-gradient-to-r from-blue-600 to-indigo-600 p-6 text-white">
          <div className="flex items-center gap-4">
            <div className="w-20 h-20 bg-white/20 rounded-full flex items-center justify-center">
              <span className="text-3xl font-bold">
                {stats?.total_loans_closed ? Math.floor(stats.total_loans_closed / 100) : '?'}
              </span>
            </div>
            <div>
              <h2 className="text-xl font-bold">Production Stats</h2>
              <p className="text-blue-100">NMLS# {data.nmls_id}</p>
            </div>
          </div>
        </div>

        {/* Stats Grid */}
        <div className="p-6 grid grid-cols-2 gap-4">
          {/* Loans Closed */}
          <StatBox
            icon={TrendingUp}
            label="Loans Closed"
            value={stats?.loans_last_12_months || 'N/A'}
            subtitle="Last 12 months"
            color="blue"
          />

          {/* Volume */}
          <StatBox
            icon={Building}
            label="Total Volume"
            value={stats?.volume_last_12_months
              ? `$${(stats.volume_last_12_months / 1000000).toFixed(1)}M`
              : 'N/A'}
            subtitle="Last 12 months"
            color="green"
          />

          {/* Avg Loan Size */}
          <StatBox
            icon={Award}
            label="Avg Loan Size"
            value={stats?.avg_loan_size
              ? `$${(stats.avg_loan_size / 1000).toFixed(0)}K`
              : 'N/A'}
            subtitle="All time"
            color="purple"
          />

          {/* Days to Close */}
          <StatBox
            icon={Clock}
            label="Avg Days to Close"
            value={stats?.avg_days_to_close || 'N/A'}
            subtitle="Industry avg: 45"
            color="amber"
          />

          {/* Platform Stats */}
          <StatBox
            icon={Star}
            label="Rating"
            value={internal_stats?.avg_rating?.toFixed(1) || 'New'}
            subtitle={`${internal_stats?.total_calls || 0} calls`}
            color="yellow"
          />

          {/* Pickup Time */}
          <StatBox
            icon={Clock}
            label="Pickup Time"
            value={internal_stats?.avg_pickup_time
              ? `${internal_stats.avg_pickup_time}s`
              : 'N/A'}
            subtitle="Avg response"
            color="teal"
          />
        </div>

        {/* Licenses */}
        {licenses?.licenses?.length > 0 && (
          <div className="px-6 pb-6">
            <h3 className="text-sm font-medium text-gray-500 mb-2">Licensed In</h3>
            <div className="flex flex-wrap gap-2">
              {licenses.licenses.slice(0, 6).map((lic: any) => (
                <span
                  key={lic.state}
                  className={`px-2 py-1 rounded text-sm ${
                    lic.status === 'active'
                      ? 'bg-green-100 text-green-700'
                      : 'bg-gray-100 text-gray-600'
                  }`}
                >
                  <MapPin className="w-3 h-3 inline mr-1" />
                  {lic.state}
                </span>
              ))}
              {licenses.licenses.length > 6 && (
                <span className="px-2 py-1 rounded text-sm bg-gray-100 text-gray-600">
                  +{licenses.licenses.length - 6} more
                </span>
              )}
            </div>
          </div>
        )}

        {/* Loan Type Mix */}
        {stats?.top_loan_types?.length > 0 && (
          <div className="px-6 pb-6">
            <h3 className="text-sm font-medium text-gray-500 mb-2">Loan Mix</h3>
            <div className="flex gap-2">
              {stats.top_loan_types.map((type: any) => (
                <div key={type.name} className="flex-1 bg-gray-100 rounded-lg p-2 text-center">
                  <div className="text-lg font-bold text-gray-900">{type.percentage}%</div>
                  <div className="text-xs text-gray-600">{type.name}</div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Footer */}
        <div className="bg-gray-50 px-6 py-4 text-center">
          <p className="text-xs text-gray-500">
            Data provided by {data.provider || 'external sources'}. Updated {
              stats?.fetched_at
                ? new Date(stats.fetched_at).toLocaleDateString()
                : 'recently'
            }.
          </p>
        </div>
      </div>
    </div>
  );
}

function StatBox({ icon: Icon, label, value, subtitle, color }: {
  icon: any;
  label: string;
  value: string | number;
  subtitle: string;
  color: string;
}) {
  const colorClasses = {
    blue: 'bg-blue-50 text-blue-600',
    green: 'bg-green-50 text-green-600',
    purple: 'bg-purple-50 text-purple-600',
    amber: 'bg-amber-50 text-amber-600',
    yellow: 'bg-yellow-50 text-yellow-600',
    teal: 'bg-teal-50 text-teal-600',
  };

  return (
    <div className="bg-gray-50 rounded-lg p-3">
      <div className="flex items-center gap-2 mb-1">
        <div className={`p-1.5 rounded ${colorClasses[color]}`}>
          <Icon className="w-4 h-4" />
        </div>
        <span className="text-xs text-gray-500">{label}</span>
      </div>
      <div className="text-xl font-bold text-gray-900">{value}</div>
      <div className="text-xs text-gray-500">{subtitle}</div>
    </div>
  );
}
```

---

## Phase 3: Video Infrastructure Upgrade

### 3.1 LiveKit Integration (Optional but Recommended)

#### Task 3.1.1: Install LiveKit Server SDK
```bash
pip install livekit-server-sdk
```

#### Task 3.1.2: Create LiveKit Service
**File**: `backend/src/app/integrations/livekit/service.py` (NEW)

```python
from livekit import api
from src.app.config import settings

class LiveKitService:
    """LiveKit server integration for scalable video calls."""

    def __init__(self):
        self.api_key = settings.LIVEKIT_API_KEY
        self.api_secret = settings.LIVEKIT_API_SECRET
        self.host = settings.LIVEKIT_HOST

    def create_token(
        self,
        room_name: str,
        participant_name: str,
        participant_identity: str,
        can_publish: bool = True,
        can_subscribe: bool = True,
        ttl_seconds: int = 3600,
    ) -> str:
        """Generate access token for participant."""
        token = api.AccessToken(self.api_key, self.api_secret)
        token.with_identity(participant_identity)
        token.with_name(participant_name)
        token.with_grants(api.VideoGrants(
            room_join=True,
            room=room_name,
            can_publish=can_publish,
            can_subscribe=can_subscribe,
        ))
        token.ttl = ttl_seconds
        return token.to_jwt()

    async def create_room(self, room_name: str) -> dict:
        """Create a new room."""
        room_service = api.RoomServiceClient(self.host, self.api_key, self.api_secret)
        room = await room_service.create_room(api.CreateRoomRequest(
            name=room_name,
            empty_timeout=300,  # 5 min timeout when empty
            max_participants=2,  # 1:1 calls
        ))
        return {"room_name": room.name, "sid": room.sid}

    async def end_room(self, room_name: str):
        """Delete/end a room."""
        room_service = api.RoomServiceClient(self.host, self.api_key, self.api_secret)
        await room_service.delete_room(api.DeleteRoomRequest(room=room_name))

livekit_service = LiveKitService()
```

#### Task 3.1.3: Update Call Initiation for LiveKit
**File**: `backend/src/app/api/v1/routes/calls.py`

```python
@router.post("")
async def initiate_call(
    request: InitiateCallRequest,
    current_user: CurrentUserOptional,
    db: DbSession,
):
    # ... existing validation ...

    # Create room
    room_name = f"call_{uuid.uuid4().hex[:12]}"

    if settings.USE_LIVEKIT:
        from src.app.integrations.livekit.service import livekit_service
        await livekit_service.create_room(room_name)

        # Generate tokens for both participants
        borrower_identity = str(current_user.id) if current_user else f"anon:{anonymous_session_id}"
        borrower_token = livekit_service.create_token(
            room_name=room_name,
            participant_name=current_user.first_name if current_user else "Guest",
            participant_identity=borrower_identity,
        )

        return InitiateCallResponse(
            room_id=room_name,
            livekit_token=borrower_token,
            livekit_url=settings.LIVEKIT_HOST,
            call_id=video_call.id,
            is_anonymous=is_anonymous,
        )
    else:
        # Existing WebRTC signaling flow
        ...
```

### 3.2 Video Storage & Recording

#### Task 3.2.1: Implement S3 Video Upload
**File**: `backend/src/app/services/storage.py`

```python
import boto3
from botocore.config import Config
from src.app.config import settings

class StorageService:
    """Cloud storage service for videos and files."""

    def __init__(self):
        if settings.STORAGE_PROVIDER == "s3":
            self.client = boto3.client(
                's3',
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                region_name=settings.AWS_REGION,
            )
            self.bucket = settings.AWS_S3_BUCKET
        elif settings.STORAGE_PROVIDER == "r2":
            self.client = boto3.client(
                's3',
                endpoint_url=settings.R2_ENDPOINT,
                aws_access_key_id=settings.R2_ACCESS_KEY_ID,
                aws_secret_access_key=settings.R2_SECRET_ACCESS_KEY,
            )
            self.bucket = settings.R2_BUCKET

    async def upload_video(
        self,
        file_content: bytes,
        filename: str,
        content_type: str = "video/mp4",
        folder: str = "videos",
    ) -> str:
        """Upload video to cloud storage."""
        key = f"{folder}/{filename}"

        self.client.put_object(
            Bucket=self.bucket,
            Key=key,
            Body=file_content,
            ContentType=content_type,
        )

        # Return public URL
        if settings.STORAGE_PROVIDER == "r2":
            return f"{settings.R2_PUBLIC_URL}/{key}"
        else:
            return f"https://{self.bucket}.s3.{settings.AWS_REGION}.amazonaws.com/{key}"

    async def get_presigned_upload_url(
        self,
        filename: str,
        content_type: str,
        folder: str = "videos",
        expires_in: int = 3600,
    ) -> dict:
        """Generate presigned URL for direct browser upload."""
        key = f"{folder}/{filename}"

        url = self.client.generate_presigned_url(
            'put_object',
            Params={
                'Bucket': self.bucket,
                'Key': key,
                'ContentType': content_type,
            },
            ExpiresIn=expires_in,
        )

        return {"upload_url": url, "key": key}

    async def get_presigned_download_url(
        self,
        key: str,
        expires_in: int = 3600,
    ) -> str:
        """Generate presigned URL for private file download."""
        return self.client.generate_presigned_url(
            'get_object',
            Params={'Bucket': self.bucket, 'Key': key},
            ExpiresIn=expires_in,
        )

storage_service = StorageService()
```

#### Task 3.2.2: Video Upload Endpoint
**File**: `backend/src/app/api/v1/routes/videos.py`

```python
@router.post("/upload-url")
async def get_video_upload_url(
    request: VideoUploadRequest,
    current_user: CurrentProfessional,
    db: DbSession,
):
    """Get presigned URL for video upload."""

    filename = f"{current_user.professional_profile.id}/{uuid.uuid4()}.{request.extension}"

    result = await storage_service.get_presigned_upload_url(
        filename=filename,
        content_type=request.content_type,
        folder="professional-videos",
    )

    return {
        "upload_url": result["upload_url"],
        "video_key": result["key"],
    }

@router.post("/confirm-upload")
async def confirm_video_upload(
    request: ConfirmUploadRequest,
    current_user: CurrentProfessional,
    db: DbSession,
):
    """Confirm video upload and update profile."""

    # Verify the file exists
    # ... verification logic ...

    # Update professional profile
    if request.video_type == "intro":
        current_user.professional_profile.intro_video_url = request.video_key
    elif request.video_type == "prerecorded":
        current_user.professional_profile.prerecorded_video_url = request.video_key

    await db.commit()

    return {"success": True, "video_url": request.video_key}
```

---

## Phase 4: Mobile & PWA

### 4.1 Progressive Web App Setup

#### Task 4.1.1: Create Web App Manifest
**File**: `frontend/public/manifest.json`

```json
{
  "name": "FaceMortgage",
  "short_name": "FaceMortgage",
  "description": "Connect with mortgage professionals instantly via video",
  "start_url": "/",
  "display": "standalone",
  "background_color": "#ffffff",
  "theme_color": "#2563eb",
  "orientation": "portrait-primary",
  "icons": [
    {
      "src": "/icons/icon-72x72.png",
      "sizes": "72x72",
      "type": "image/png"
    },
    {
      "src": "/icons/icon-96x96.png",
      "sizes": "96x96",
      "type": "image/png"
    },
    {
      "src": "/icons/icon-128x128.png",
      "sizes": "128x128",
      "type": "image/png"
    },
    {
      "src": "/icons/icon-144x144.png",
      "sizes": "144x144",
      "type": "image/png"
    },
    {
      "src": "/icons/icon-152x152.png",
      "sizes": "152x152",
      "type": "image/png"
    },
    {
      "src": "/icons/icon-192x192.png",
      "sizes": "192x192",
      "type": "image/png"
    },
    {
      "src": "/icons/icon-384x384.png",
      "sizes": "384x384",
      "type": "image/png"
    },
    {
      "src": "/icons/icon-512x512.png",
      "sizes": "512x512",
      "type": "image/png"
    }
  ],
  "categories": ["finance", "business"],
  "screenshots": [
    {
      "src": "/screenshots/home.png",
      "sizes": "1280x720",
      "type": "image/png",
      "form_factor": "wide"
    },
    {
      "src": "/screenshots/mobile.png",
      "sizes": "750x1334",
      "type": "image/png",
      "form_factor": "narrow"
    }
  ]
}
```

#### Task 4.1.2: Create Service Worker
**File**: `frontend/public/sw.js`

```javascript
const CACHE_NAME = 'facemortgage-v1';
const OFFLINE_URL = '/offline.html';

// Assets to cache immediately
const PRECACHE_ASSETS = [
  '/',
  '/offline.html',
  '/manifest.json',
  '/icons/icon-192x192.png',
];

// Install event - cache critical assets
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(PRECACHE_ASSETS);
    })
  );
  self.skipWaiting();
});

// Activate event - clean old caches
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames
          .filter((name) => name !== CACHE_NAME)
          .map((name) => caches.delete(name))
      );
    })
  );
  self.clients.claim();
});

// Fetch event - network first, fallback to cache
self.addEventListener('fetch', (event) => {
  // Skip non-GET requests
  if (event.request.method !== 'GET') return;

  // Skip API requests
  if (event.request.url.includes('/api/')) return;

  event.respondWith(
    fetch(event.request)
      .then((response) => {
        // Clone and cache successful responses
        if (response.ok) {
          const responseClone = response.clone();
          caches.open(CACHE_NAME).then((cache) => {
            cache.put(event.request, responseClone);
          });
        }
        return response;
      })
      .catch(() => {
        // Return cached version or offline page
        return caches.match(event.request).then((cached) => {
          return cached || caches.match(OFFLINE_URL);
        });
      })
  );
});

// Push notification handler
self.addEventListener('push', (event) => {
  const data = event.data?.json() || {};

  const options = {
    body: data.body || 'You have a new notification',
    icon: '/icons/icon-192x192.png',
    badge: '/icons/badge-72x72.png',
    vibrate: [100, 50, 100],
    data: {
      url: data.url || '/',
    },
    actions: data.actions || [],
  };

  event.waitUntil(
    self.registration.showNotification(data.title || 'FaceMortgage', options)
  );
});

// Notification click handler
self.addEventListener('notificationclick', (event) => {
  event.notification.close();

  const url = event.notification.data?.url || '/';

  event.waitUntil(
    clients.matchAll({ type: 'window' }).then((windowClients) => {
      // Focus existing window if available
      for (const client of windowClients) {
        if (client.url === url && 'focus' in client) {
          return client.focus();
        }
      }
      // Open new window
      if (clients.openWindow) {
        return clients.openWindow(url);
      }
    })
  );
});
```

#### Task 4.1.3: Register Service Worker
**File**: `frontend/src/app/layout.tsx`

```typescript
// Add to layout.tsx
useEffect(() => {
  if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('/sw.js').then((registration) => {
      console.log('SW registered:', registration.scope);
    });
  }
}, []);
```

### 4.2 Push Notifications

#### Task 4.2.1: Create Push Notification Hook
**File**: `frontend/src/hooks/usePushNotifications.ts`

```typescript
import { useState, useEffect, useCallback } from 'react';
import { devicesApi } from '@/lib/api/endpoints';

export function usePushNotifications() {
  const [permission, setPermission] = useState<NotificationPermission>('default');
  const [subscription, setSubscription] = useState<PushSubscription | null>(null);
  const [isSupported, setIsSupported] = useState(false);

  useEffect(() => {
    setIsSupported('Notification' in window && 'serviceWorker' in navigator);
    if ('Notification' in window) {
      setPermission(Notification.permission);
    }
  }, []);

  const requestPermission = useCallback(async () => {
    if (!isSupported) return false;

    const result = await Notification.requestPermission();
    setPermission(result);

    if (result === 'granted') {
      await subscribeToNotifications();
      return true;
    }
    return false;
  }, [isSupported]);

  const subscribeToNotifications = async () => {
    try {
      const registration = await navigator.serviceWorker.ready;

      const sub = await registration.pushManager.subscribe({
        userVisibleOnly: true,
        applicationServerKey: process.env.NEXT_PUBLIC_VAPID_PUBLIC_KEY,
      });

      setSubscription(sub);

      // Send subscription to backend
      await devicesApi.registerPushToken({
        endpoint: sub.endpoint,
        keys: {
          p256dh: arrayBufferToBase64(sub.getKey('p256dh')!),
          auth: arrayBufferToBase64(sub.getKey('auth')!),
        },
      });

      return sub;
    } catch (error) {
      console.error('Failed to subscribe:', error);
      return null;
    }
  };

  const unsubscribe = async () => {
    if (subscription) {
      await subscription.unsubscribe();
      await devicesApi.unregisterPushToken({ endpoint: subscription.endpoint });
      setSubscription(null);
    }
  };

  return {
    isSupported,
    permission,
    subscription,
    requestPermission,
    unsubscribe,
  };
}

function arrayBufferToBase64(buffer: ArrayBuffer): string {
  const bytes = new Uint8Array(buffer);
  let binary = '';
  for (let i = 0; i < bytes.byteLength; i++) {
    binary += String.fromCharCode(bytes[i]);
  }
  return btoa(binary);
}
```

#### Task 4.2.2: Backend Push Notification Service
**File**: `backend/src/app/services/push_notification.py`

```python
from pywebpush import webpush, WebPushException
from src.app.config import settings

class PushNotificationService:
    """Web Push notification service."""

    def __init__(self):
        self.vapid_private_key = settings.VAPID_PRIVATE_KEY
        self.vapid_public_key = settings.VAPID_PUBLIC_KEY
        self.vapid_claims = {"sub": f"mailto:{settings.VAPID_EMAIL}"}

    async def send_notification(
        self,
        subscription_info: dict,
        title: str,
        body: str,
        url: str = "/",
        actions: list = None,
    ):
        """Send push notification to a single device."""
        data = {
            "title": title,
            "body": body,
            "url": url,
            "actions": actions or [],
        }

        try:
            webpush(
                subscription_info=subscription_info,
                data=json.dumps(data),
                vapid_private_key=self.vapid_private_key,
                vapid_claims=self.vapid_claims,
            )
            return True
        except WebPushException as e:
            logger.error(f"Push notification failed: {e}")
            if e.response and e.response.status_code == 410:
                # Subscription expired, should be removed
                return "expired"
            return False

    async def notify_incoming_call(
        self,
        professional_subscriptions: list,
        borrower_name: str,
        call_id: str,
    ):
        """Notify professional of incoming call."""
        for sub in professional_subscriptions:
            await self.send_notification(
                subscription_info=sub,
                title="Incoming Call",
                body=f"{borrower_name} is calling you",
                url=f"/call/{call_id}",
                actions=[
                    {"action": "answer", "title": "Answer"},
                    {"action": "decline", "title": "Decline"},
                ],
            )

    async def notify_new_lead(
        self,
        professional_subscriptions: list,
        lead_name: str,
        lead_id: str,
    ):
        """Notify professional of new lead."""
        for sub in professional_subscriptions:
            await self.send_notification(
                subscription_info=sub,
                title="New Lead",
                body=f"You have a new lead from {lead_name}",
                url=f"/dashboard/leads/{lead_id}",
            )

push_service = PushNotificationService()
```

---

## Phase 5: Analytics & Reporting

### 5.1 Backend Analytics Aggregation

#### Task 5.1.1: Create Analytics Service
**File**: `backend/src/app/services/analytics_service.py` (NEW)

```python
from datetime import datetime, timedelta
from sqlalchemy import select, func, and_
from src.app.models.call import VideoCall, CallStatus
from src.app.models.lead import Lead, LeadStatus
from src.app.models.analytics import GridImpression, GridClick

class AnalyticsService:
    """Analytics aggregation service."""

    async def get_professional_dashboard_stats(
        self,
        professional_id: str,
        db,
        days: int = 30,
    ) -> dict:
        """Get comprehensive dashboard stats for a professional."""

        start_date = datetime.utcnow() - timedelta(days=days)

        # Call stats
        calls_query = select(
            func.count(VideoCall.id).label("total_calls"),
            func.count(VideoCall.id).filter(VideoCall.status == CallStatus.COMPLETED).label("completed_calls"),
            func.avg(VideoCall.pickup_time_seconds).label("avg_pickup_time"),
            func.avg(VideoCall.duration_seconds).label("avg_duration"),
            func.sum(VideoCall.duration_seconds).label("total_talk_time"),
        ).where(
            VideoCall.professional_id == professional_id,
            VideoCall.initiated_at >= start_date,
        )
        call_stats = (await db.execute(calls_query)).one()

        # Lead stats
        leads_query = select(
            func.count(Lead.id).label("total_leads"),
            func.count(Lead.id).filter(Lead.lead_status == LeadStatus.WON).label("won_leads"),
            func.count(Lead.id).filter(Lead.lead_status == LeadStatus.NEW).label("new_leads"),
        ).where(
            Lead.professional_id == professional_id,
            Lead.created_at >= start_date,
        )
        lead_stats = (await db.execute(leads_query)).one()

        # Grid performance
        impressions_query = select(
            func.sum(GridImpression.impression_count).label("total_impressions"),
        ).where(
            GridImpression.professional_id == professional_id,
            GridImpression.date >= start_date.date(),
        )
        impression_stats = (await db.execute(impressions_query)).one()

        clicks_query = select(
            func.count(GridClick.id).label("total_clicks"),
        ).where(
            GridClick.professional_id == professional_id,
            GridClick.clicked_at >= start_date,
        )
        click_stats = (await db.execute(clicks_query)).one()

        # Calculate metrics
        impressions = impression_stats.total_impressions or 0
        clicks = click_stats.total_clicks or 0
        calls = call_stats.total_calls or 0
        completed = call_stats.completed_calls or 0

        return {
            "period_days": days,
            "calls": {
                "total": calls,
                "completed": completed,
                "missed": calls - completed,
                "answer_rate": round(completed / calls * 100, 1) if calls > 0 else 0,
                "avg_pickup_time_seconds": round(call_stats.avg_pickup_time or 0, 1),
                "avg_duration_seconds": round(call_stats.avg_duration or 0, 0),
                "total_talk_time_minutes": round((call_stats.total_talk_time or 0) / 60, 0),
            },
            "leads": {
                "total": lead_stats.total_leads or 0,
                "new": lead_stats.new_leads or 0,
                "won": lead_stats.won_leads or 0,
                "conversion_rate": round(
                    (lead_stats.won_leads or 0) / (lead_stats.total_leads or 1) * 100, 1
                ),
            },
            "grid": {
                "impressions": impressions,
                "clicks": clicks,
                "ctr": round(clicks / impressions * 100, 2) if impressions > 0 else 0,
                "click_to_call_rate": round(calls / clicks * 100, 1) if clicks > 0 else 0,
            },
        }

    async def get_daily_trends(
        self,
        professional_id: str,
        db,
        days: int = 30,
    ) -> list:
        """Get daily trend data for charts."""

        start_date = datetime.utcnow() - timedelta(days=days)

        # Daily calls
        daily_calls = await db.execute(
            select(
                func.date(VideoCall.initiated_at).label("date"),
                func.count(VideoCall.id).label("calls"),
                func.count(VideoCall.id).filter(VideoCall.status == CallStatus.COMPLETED).label("completed"),
            )
            .where(
                VideoCall.professional_id == professional_id,
                VideoCall.initiated_at >= start_date,
            )
            .group_by(func.date(VideoCall.initiated_at))
            .order_by(func.date(VideoCall.initiated_at))
        )

        return [
            {
                "date": row.date.isoformat(),
                "calls": row.calls,
                "completed": row.completed,
            }
            for row in daily_calls
        ]

analytics_service = AnalyticsService()
```

#### Task 5.1.2: Create Analytics Endpoints
**File**: `backend/src/app/api/v1/routes/analytics.py`

```python
@router.get("/dashboard")
async def get_dashboard_analytics(
    days: int = Query(30, ge=7, le=365),
    current_user: CurrentProfessional = Depends(),
    db: DbSession = Depends(),
):
    """Get comprehensive dashboard analytics."""

    stats = await analytics_service.get_professional_dashboard_stats(
        professional_id=str(current_user.professional_profile.id),
        db=db,
        days=days,
    )

    trends = await analytics_service.get_daily_trends(
        professional_id=str(current_user.professional_profile.id),
        db=db,
        days=days,
    )

    return {
        "summary": stats,
        "trends": trends,
    }

@router.get("/roi")
async def get_roi_analytics(
    current_user: CurrentProfessional = Depends(),
    db: DbSession = Depends(),
):
    """Calculate ROI metrics for professional."""

    # Get subscription cost
    subscription = current_user.professional_profile.subscription
    monthly_cost = subscription.plan.monthly_price if subscription else 0

    # Get bid spend
    from src.app.models.billing import BillingTransaction
    bid_spend = await db.execute(
        select(func.sum(BillingTransaction.amount_cents))
        .where(
            BillingTransaction.professional_id == current_user.professional_profile.id,
            BillingTransaction.type == "bid_charge",
            BillingTransaction.created_at >= datetime.utcnow() - timedelta(days=30),
        )
    )
    monthly_bid_spend = (bid_spend.scalar() or 0) / 100

    # Get leads won
    leads_won = await db.execute(
        select(func.count(Lead.id), func.sum(Lead.estimated_loan_amount))
        .where(
            Lead.professional_id == current_user.professional_profile.id,
            Lead.lead_status == LeadStatus.WON,
            Lead.updated_at >= datetime.utcnow() - timedelta(days=30),
        )
    )
    won_count, total_volume = leads_won.one()

    # Calculate estimated commission (assume 1% avg)
    estimated_commission = (total_volume or 0) * 0.01

    total_cost = monthly_cost + monthly_bid_spend

    return {
        "monthly_cost": {
            "subscription": monthly_cost,
            "bid_spend": monthly_bid_spend,
            "total": total_cost,
        },
        "results": {
            "leads_won": won_count or 0,
            "total_volume": total_volume or 0,
            "estimated_commission": estimated_commission,
        },
        "roi": {
            "cost_per_lead": round(total_cost / (won_count or 1), 2),
            "return_on_investment": round(
                (estimated_commission - total_cost) / (total_cost or 1) * 100, 1
            ),
        },
    }
```

### 5.2 Frontend Analytics Dashboard

#### Task 5.2.1: Update Analytics Page
**File**: `frontend/src/app/dashboard/analytics/page.tsx`

```typescript
'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  Phone, TrendingUp, Users, DollarSign, Clock,
  Target, BarChart3, LineChart, PieChart
} from 'lucide-react';
import { analyticsApi } from '@/lib/api/endpoints';
import {
  LineChart as RechartsLine,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  BarChart,
  Bar,
} from 'recharts';

export default function AnalyticsPage() {
  const [period, setPeriod] = useState(30);

  const { data: analytics, isLoading } = useQuery({
    queryKey: ['analytics', period],
    queryFn: () => analyticsApi.getDashboard(period),
  });

  const { data: roi } = useQuery({
    queryKey: ['roi'],
    queryFn: () => analyticsApi.getROI(),
  });

  if (isLoading) return <AnalyticsSkeleton />;

  const { summary, trends } = analytics || {};

  return (
    <div className="p-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Analytics</h1>
          <p className="text-gray-600">Track your performance and ROI</p>
        </div>
        <select
          value={period}
          onChange={(e) => setPeriod(Number(e.target.value))}
          className="px-4 py-2 border rounded-lg"
        >
          <option value={7}>Last 7 days</option>
          <option value={30}>Last 30 days</option>
          <option value={90}>Last 90 days</option>
          <option value={365}>Last year</option>
        </select>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <KPICard
          icon={Phone}
          label="Total Calls"
          value={summary?.calls.total || 0}
          change={`${summary?.calls.answer_rate || 0}% answered`}
          color="blue"
        />
        <KPICard
          icon={Users}
          label="New Leads"
          value={summary?.leads.total || 0}
          change={`${summary?.leads.conversion_rate || 0}% converted`}
          color="green"
        />
        <KPICard
          icon={Target}
          label="Grid CTR"
          value={`${summary?.grid.ctr || 0}%`}
          change={`${summary?.grid.impressions?.toLocaleString() || 0} impressions`}
          color="purple"
        />
        <KPICard
          icon={Clock}
          label="Avg Pickup"
          value={`${summary?.calls.avg_pickup_time_seconds || 0}s`}
          change={summary?.calls.avg_pickup_time_seconds < 10 ? 'Excellent' : 'Room to improve'}
          color="amber"
        />
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        {/* Calls Trend */}
        <div className="bg-white rounded-xl shadow-sm p-6">
          <h3 className="text-lg font-semibold mb-4">Calls Over Time</h3>
          <ResponsiveContainer width="100%" height={250}>
            <RechartsLine data={trends}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" />
              <YAxis />
              <Tooltip />
              <Line
                type="monotone"
                dataKey="calls"
                stroke="#2563eb"
                strokeWidth={2}
                name="Total Calls"
              />
              <Line
                type="monotone"
                dataKey="completed"
                stroke="#10b981"
                strokeWidth={2}
                name="Completed"
              />
            </RechartsLine>
          </ResponsiveContainer>
        </div>

        {/* Funnel */}
        <div className="bg-white rounded-xl shadow-sm p-6">
          <h3 className="text-lg font-semibold mb-4">Conversion Funnel</h3>
          <div className="space-y-4">
            <FunnelStep
              label="Impressions"
              value={summary?.grid.impressions || 0}
              percent={100}
            />
            <FunnelStep
              label="Clicks"
              value={summary?.grid.clicks || 0}
              percent={summary?.grid.ctr || 0}
            />
            <FunnelStep
              label="Calls"
              value={summary?.calls.total || 0}
              percent={summary?.grid.click_to_call_rate || 0}
            />
            <FunnelStep
              label="Leads"
              value={summary?.leads.total || 0}
              percent={
                summary?.calls.total
                  ? (summary.leads.total / summary.calls.total * 100)
                  : 0
              }
            />
            <FunnelStep
              label="Closed"
              value={summary?.leads.won || 0}
              percent={summary?.leads.conversion_rate || 0}
            />
          </div>
        </div>
      </div>

      {/* ROI Section */}
      {roi && (
        <div className="bg-gradient-to-r from-blue-600 to-indigo-600 rounded-xl p-6 text-white">
          <h3 className="text-xl font-semibold mb-6">Return on Investment</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div>
              <p className="text-blue-100 text-sm">Monthly Cost</p>
              <p className="text-3xl font-bold">${roi.monthly_cost.total.toFixed(0)}</p>
              <p className="text-blue-200 text-sm">
                ${roi.monthly_cost.subscription} subscription + ${roi.monthly_cost.bid_spend.toFixed(0)} bids
              </p>
            </div>
            <div>
              <p className="text-blue-100 text-sm">Estimated Commission</p>
              <p className="text-3xl font-bold">${roi.results.estimated_commission.toLocaleString()}</p>
              <p className="text-blue-200 text-sm">
                {roi.results.leads_won} closed deals
              </p>
            </div>
            <div>
              <p className="text-blue-100 text-sm">ROI</p>
              <p className={`text-3xl font-bold ${roi.roi.return_on_investment > 0 ? 'text-green-300' : 'text-red-300'}`}>
                {roi.roi.return_on_investment > 0 ? '+' : ''}{roi.roi.return_on_investment}%
              </p>
              <p className="text-blue-200 text-sm">
                ${roi.roi.cost_per_lead.toFixed(0)} per lead
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
```

---

## Phase 6: Testing & Quality Assurance

### 6.1 Backend Testing Setup

#### Task 6.1.1: Create Test Fixtures
**File**: `backend/tests/conftest.py`

```python
import pytest
import asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from src.app.main import app
from src.app.core.database import Base, get_db
from src.app.models.user import User, UserType
from src.app.models.professional import ProfessionalProfile
from src.app.core.security import hash_password

# Test database URL
TEST_DATABASE_URL = "postgresql+asyncpg://test:test@localhost:5432/facemortgage_test"

@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
async def engine():
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()

@pytest.fixture
async def db_session(engine):
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        yield session
        await session.rollback()

@pytest.fixture
async def client(db_session):
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as ac:
        yield ac

    app.dependency_overrides.clear()

@pytest.fixture
async def test_user(db_session):
    """Create a test borrower user."""
    user = User(
        email="borrower@test.com",
        password_hash=hash_password("testpass123"),
        first_name="Test",
        last_name="Borrower",
        user_type=UserType.BORROWER,
        is_verified=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user

@pytest.fixture
async def test_professional(db_session):
    """Create a test loan officer with profile."""
    user = User(
        email="loanofficer@test.com",
        password_hash=hash_password("testpass123"),
        first_name="Test",
        last_name="LoanOfficer",
        user_type=UserType.LOAN_OFFICER,
        is_verified=True,
    )
    db_session.add(user)
    await db_session.flush()

    profile = ProfessionalProfile(
        user_id=user.id,
        nmls_id="123456",
        company_name="Test Mortgage Co",
        bio="Test bio",
        status="online_available",
    )
    db_session.add(profile)
    await db_session.commit()
    await db_session.refresh(user)
    return user

@pytest.fixture
async def auth_headers(client, test_user):
    """Get auth headers for test user."""
    response = await client.post("/api/v1/auth/login", json={
        "email": "borrower@test.com",
        "password": "testpass123",
    })
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
async def professional_auth_headers(client, test_professional):
    """Get auth headers for test professional."""
    response = await client.post("/api/v1/auth/login", json={
        "email": "loanofficer@test.com",
        "password": "testpass123",
    })
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
```

#### Task 6.1.2: Create API Tests
**File**: `backend/tests/test_calls.py`

```python
import pytest
from uuid import uuid4

class TestCallsAPI:
    """Test video call endpoints."""

    @pytest.mark.asyncio
    async def test_initiate_call_authenticated(
        self, client, auth_headers, test_professional
    ):
        """Test initiating call as authenticated user."""
        response = await client.post(
            "/api/v1/calls",
            json={"professional_id": str(test_professional.professional_profile.id)},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "room_id" in data
        assert "call_id" in data
        assert data["is_anonymous"] == False

    @pytest.mark.asyncio
    async def test_initiate_call_anonymous(self, client, test_professional):
        """Test initiating call as anonymous user."""
        response = await client.post(
            "/api/v1/calls",
            json={
                "professional_id": str(test_professional.professional_profile.id),
                "anonymous_session_id": "test-session-123",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["is_anonymous"] == True
        assert data["session_id"] == "test-session-123"

    @pytest.mark.asyncio
    async def test_initiate_call_professional_offline(
        self, client, auth_headers, test_professional, db_session
    ):
        """Test call fails when professional is offline."""
        # Set professional offline
        test_professional.professional_profile.status = "offline"
        await db_session.commit()

        response = await client.post(
            "/api/v1/calls",
            json={"professional_id": str(test_professional.professional_profile.id)},
            headers=auth_headers,
        )
        assert response.status_code == 400
        assert "not available" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_capture_lead_after_anonymous_call(self, client, test_professional):
        """Test lead capture after anonymous call."""
        # First initiate anonymous call
        call_response = await client.post(
            "/api/v1/calls",
            json={
                "professional_id": str(test_professional.professional_profile.id),
                "anonymous_session_id": "test-session-456",
            },
        )
        call_id = call_response.json()["call_id"]

        # Capture lead
        response = await client.post(
            f"/api/v1/calls/{call_id}/capture-lead",
            json={
                "name": "John Doe",
                "email": "john@example.com",
                "phone": "555-1234",
                "loan_purpose": "purchase",
            },
        )
        assert response.status_code == 200
        assert response.json()["success"] == True
        assert "lead_id" in response.json()


class TestLeadsAPI:
    """Test lead management endpoints."""

    @pytest.mark.asyncio
    async def test_get_leads(self, client, professional_auth_headers):
        """Test getting leads for professional."""
        response = await client.get(
            "/api/v1/leads",
            headers=professional_auth_headers,
        )
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    @pytest.mark.asyncio
    async def test_update_lead_status(
        self, client, professional_auth_headers, db_session, test_professional
    ):
        """Test updating lead status."""
        # Create a lead first
        from src.app.models.lead import Lead
        lead = Lead(
            professional_id=test_professional.professional_profile.id,
            contact_name="Test Lead",
            contact_email="lead@test.com",
            lead_status="new",
        )
        db_session.add(lead)
        await db_session.commit()
        await db_session.refresh(lead)

        # Update status
        response = await client.patch(
            f"/api/v1/leads/{lead.id}",
            json={"lead_status": "contacted"},
            headers=professional_auth_headers,
        )
        assert response.status_code == 200
        assert response.json()["lead_status"] == "contacted"
```

#### Task 6.1.3: Create Integration Tests
**File**: `backend/tests/test_integration.py`

```python
import pytest

class TestCallToLeadFlow:
    """Integration tests for complete call-to-lead workflow."""

    @pytest.mark.asyncio
    async def test_full_anonymous_call_flow(
        self, client, test_professional, db_session
    ):
        """Test complete flow: browse -> call -> rate -> lead capture."""
        professional_id = str(test_professional.professional_profile.id)

        # 1. Browse grid
        grid_response = await client.get("/api/v1/professionals")
        assert grid_response.status_code == 200
        professionals = grid_response.json()
        assert len(professionals) > 0

        # 2. Track impression
        await client.post("/api/v1/grid/impressions", json={
            "professional_ids": [professional_id],
            "filters": {"languages": [], "specialties": []},
        })

        # 3. Track click
        await client.post("/api/v1/grid/clicks", json={
            "professional_id": professional_id,
            "action": "call_initiated",
            "position": 1,
        })

        # 4. Initiate anonymous call
        call_response = await client.post("/api/v1/calls", json={
            "professional_id": professional_id,
            "anonymous_session_id": "integration-test-session",
        })
        assert call_response.status_code == 200
        call_id = call_response.json()["call_id"]

        # 5. End call (simulated)
        # ... WebSocket interaction would happen here ...

        # 6. Capture lead
        lead_response = await client.post(
            f"/api/v1/calls/{call_id}/capture-lead",
            json={
                "name": "Integration Test User",
                "email": "integration@test.com",
                "phone": "555-0000",
                "loan_purpose": "purchase",
                "estimated_amount": 450000,
            },
        )
        assert lead_response.status_code == 200
        lead_id = lead_response.json()["lead_id"]

        # 7. Verify lead was created
        from src.app.models.lead import Lead
        lead = await db_session.get(Lead, lead_id)
        assert lead is not None
        assert lead.contact_name == "Integration Test User"
        assert lead.professional_id == test_professional.professional_profile.id
```

### 6.2 Frontend Testing

#### Task 6.2.1: Setup Jest/Vitest
**File**: `frontend/vitest.config.ts`

```typescript
import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig({
  plugins: [react()],
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: ['./tests/setup.ts'],
    include: ['**/*.test.{ts,tsx}'],
    coverage: {
      reporter: ['text', 'json', 'html'],
      exclude: ['node_modules/', 'tests/'],
    },
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
});
```

#### Task 6.2.2: Create Component Tests
**File**: `frontend/tests/components/ProfessionalCard.test.tsx`

```typescript
import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import ProfessionalCard from '@/components/grid/ProfessionalCard';

const mockProfessional = {
  id: '123',
  user: {
    first_name: 'John',
    last_name: 'Doe',
    avatar_url: null,
  },
  company_name: 'Test Mortgage',
  status: 'online_available',
  avg_rating: 4.5,
  avg_pickup_time_seconds: 8,
  specialties: ['VA', 'FHA'],
  languages: ['English', 'Spanish'],
};

describe('ProfessionalCard', () => {
  it('renders professional name and company', () => {
    render(<ProfessionalCard professional={mockProfessional} />);

    expect(screen.getByText('John Doe')).toBeInTheDocument();
    expect(screen.getByText('Test Mortgage')).toBeInTheDocument();
  });

  it('shows online status indicator', () => {
    render(<ProfessionalCard professional={mockProfessional} />);

    const statusIndicator = screen.getByTestId('status-indicator');
    expect(statusIndicator).toHaveClass('bg-green-500');
  });

  it('calls onCallInitiate when Call Now clicked', () => {
    const onCallInitiate = vi.fn();
    render(
      <ProfessionalCard
        professional={mockProfessional}
        onCallInitiate={onCallInitiate}
      />
    );

    fireEvent.click(screen.getByText('Call Now'));
    expect(onCallInitiate).toHaveBeenCalledWith('123');
  });

  it('displays rating when available', () => {
    render(<ProfessionalCard professional={mockProfessional} />);

    expect(screen.getByText('4.5')).toBeInTheDocument();
  });

  it('shows pickup time badge', () => {
    render(<ProfessionalCard professional={mockProfessional} />);

    expect(screen.getByText('8s avg')).toBeInTheDocument();
  });
});
```

---

## Phase 7: Production Readiness

### 7.1 Environment & Configuration

#### Task 7.1.1: Create Production Environment Files
**File**: `backend/.env.production.example`

```bash
# Database
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/facemortgage
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=10

# Redis
REDIS_URL=redis://host:6379/0
REDIS_PRESENCE_DB=1
REDIS_CACHE_DB=2

# Security
SECRET_KEY=your-production-secret-key-min-32-chars
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=60
CORS_ORIGINS=https://facemortgage.com,https://www.facemortgage.com

# Stripe
STRIPE_SECRET_KEY=sk_live_xxx
STRIPE_PUBLISHABLE_KEY=pk_live_xxx
STRIPE_WEBHOOK_SECRET=whsec_xxx
STRIPE_PRICE_BASIC=price_xxx
STRIPE_PRICE_PROFESSIONAL=price_xxx
STRIPE_PRICE_PREMIUM=price_xxx

# Data Providers
DEFAULT_DATA_PROVIDER=datagod
DATAGOD_API_KEY=xxx
CORELOGIC_API_KEY=xxx
CORELOGIC_API_SECRET=xxx

# Storage
STORAGE_PROVIDER=r2
R2_ENDPOINT=https://xxx.r2.cloudflarestorage.com
R2_ACCESS_KEY_ID=xxx
R2_SECRET_ACCESS_KEY=xxx
R2_BUCKET=facemortgage-prod
R2_PUBLIC_URL=https://cdn.facemortgage.com

# Email
SENDGRID_API_KEY=xxx
FROM_EMAIL=noreply@facemortgage.com

# Push Notifications
VAPID_PUBLIC_KEY=xxx
VAPID_PRIVATE_KEY=xxx
VAPID_EMAIL=admin@facemortgage.com

# LiveKit (optional)
USE_LIVEKIT=true
LIVEKIT_API_KEY=xxx
LIVEKIT_API_SECRET=xxx
LIVEKIT_HOST=wss://livekit.facemortgage.com

# Monitoring
SENTRY_DSN=https://xxx@sentry.io/xxx
LOG_LEVEL=INFO
```

### 7.2 Logging & Monitoring

#### Task 7.2.1: Setup Structured Logging
**File**: `backend/src/app/core/logging.py` (NEW)

```python
import logging
import json
import sys
from datetime import datetime
from src.app.config import settings

class JSONFormatter(logging.Formatter):
    """JSON log formatter for production."""

    def format(self, record):
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        if hasattr(record, "request_id"):
            log_data["request_id"] = record.request_id

        if hasattr(record, "user_id"):
            log_data["user_id"] = record.user_id

        return json.dumps(log_data)

def setup_logging():
    """Configure logging based on environment."""

    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.LOG_LEVEL, logging.INFO))

    # Remove existing handlers
    root_logger.handlers = []

    handler = logging.StreamHandler(sys.stdout)

    if settings.ENVIRONMENT == "production":
        handler.setFormatter(JSONFormatter())
    else:
        handler.setFormatter(logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        ))

    root_logger.addHandler(handler)

    # Reduce noise from third-party libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
```

#### Task 7.2.2: Add Sentry Integration
**File**: `backend/src/app/main.py`

```python
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

if settings.SENTRY_DSN:
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        environment=settings.ENVIRONMENT,
        integrations=[
            FastApiIntegration(),
            SqlalchemyIntegration(),
        ],
        traces_sample_rate=0.1,
        profiles_sample_rate=0.1,
    )
```

### 7.3 Health Checks & Monitoring

#### Task 7.3.1: Create Health Check Endpoints
**File**: `backend/src/app/api/v1/routes/health.py` (NEW)

```python
from fastapi import APIRouter, Depends
from sqlalchemy import text
from redis.asyncio import Redis

router = APIRouter(prefix="/health", tags=["health"])

@router.get("")
async def health_check():
    """Basic health check."""
    return {"status": "healthy"}

@router.get("/ready")
async def readiness_check(db: DbSession, redis: Redis = Depends(get_redis)):
    """Readiness check - verify all dependencies."""
    checks = {}

    # Database
    try:
        await db.execute(text("SELECT 1"))
        checks["database"] = "healthy"
    except Exception as e:
        checks["database"] = f"unhealthy: {str(e)}"

    # Redis
    try:
        await redis.ping()
        checks["redis"] = "healthy"
    except Exception as e:
        checks["redis"] = f"unhealthy: {str(e)}"

    # Overall status
    all_healthy = all(v == "healthy" for v in checks.values())

    return {
        "status": "ready" if all_healthy else "not_ready",
        "checks": checks,
    }

@router.get("/live")
async def liveness_check():
    """Liveness check - is the process alive."""
    return {"status": "alive"}
```

---

## Phase 8: Strategic Features

### 8.1 Geo-Auto-Detection

#### Task 8.1.1: Add Geo Detection Endpoint
**File**: `backend/src/app/api/v1/routes/lookups.py`

```python
@router.get("/geo/detect")
async def detect_location(request: Request):
    """Detect user location from IP."""

    # Get IP from headers (considering proxies)
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        ip = forwarded_for.split(",")[0].strip()
    else:
        ip = request.client.host

    # Use IP geolocation service
    try:
        import geoip2.database
        reader = geoip2.database.Reader('/path/to/GeoLite2-City.mmdb')
        response = reader.city(ip)

        return {
            "country": response.country.iso_code,
            "state": response.subdivisions.most_specific.iso_code,
            "city": response.city.name,
            "latitude": response.location.latitude,
            "longitude": response.location.longitude,
        }
    except Exception:
        return {"country": "US", "state": None, "city": None}
```

#### Task 8.1.2: Frontend Auto-Filter
**File**: `frontend/src/hooks/useGeoDetection.ts`

```typescript
import { useEffect } from 'react';
import { useFilterStore } from '@/stores/filterStore';
import { lookupsApi } from '@/lib/api/endpoints';

export function useGeoDetection() {
  const { setFilters } = useFilterStore();

  useEffect(() => {
    const detectAndFilter = async () => {
      try {
        const location = await lookupsApi.detectGeo();

        if (location.state) {
          // Auto-filter to user's state
          setFilters({ states: [location.state] });
        }
      } catch (error) {
        console.error('Geo detection failed:', error);
      }
    };

    detectAndFilter();
  }, [setFilters]);
}
```

### 8.2 Embeddable Widget

#### Task 8.2.1: Create Widget Script
**File**: `frontend/public/widget/fm-widget.js`

```javascript
(function() {
  'use strict';

  const FM_WIDGET_VERSION = '1.0.0';
  const FM_API_BASE = 'https://facemortgage.com';

  class FaceMortgageWidget {
    constructor(config) {
      this.config = {
        partnerId: config.partnerId,
        theme: config.theme || 'light',
        position: config.position || 'bottom-right',
        buttonText: config.buttonText || 'Get Financing',
        primaryColor: config.primaryColor || '#2563eb',
        ...config,
      };

      this.init();
    }

    init() {
      this.injectStyles();
      this.createButton();
      this.createModal();
    }

    injectStyles() {
      const style = document.createElement('style');
      style.textContent = `
        .fm-widget-button {
          position: fixed;
          ${this.config.position.includes('bottom') ? 'bottom: 20px;' : 'top: 20px;'}
          ${this.config.position.includes('right') ? 'right: 20px;' : 'left: 20px;'}
          background: ${this.config.primaryColor};
          color: white;
          border: none;
          padding: 12px 24px;
          border-radius: 8px;
          font-size: 16px;
          font-weight: 600;
          cursor: pointer;
          box-shadow: 0 4px 12px rgba(0,0,0,0.15);
          z-index: 9998;
          transition: transform 0.2s, box-shadow 0.2s;
        }
        .fm-widget-button:hover {
          transform: translateY(-2px);
          box-shadow: 0 6px 16px rgba(0,0,0,0.2);
        }
        .fm-widget-modal {
          position: fixed;
          inset: 0;
          background: rgba(0,0,0,0.5);
          display: none;
          align-items: center;
          justify-content: center;
          z-index: 9999;
        }
        .fm-widget-modal.active {
          display: flex;
        }
        .fm-widget-iframe {
          width: 90%;
          max-width: 500px;
          height: 80vh;
          max-height: 700px;
          border: none;
          border-radius: 12px;
          background: white;
        }
        .fm-widget-close {
          position: absolute;
          top: 20px;
          right: 20px;
          background: white;
          border: none;
          width: 40px;
          height: 40px;
          border-radius: 50%;
          cursor: pointer;
          font-size: 24px;
        }
      `;
      document.head.appendChild(style);
    }

    createButton() {
      this.button = document.createElement('button');
      this.button.className = 'fm-widget-button';
      this.button.textContent = this.config.buttonText;
      this.button.addEventListener('click', () => this.openModal());
      document.body.appendChild(this.button);
    }

    createModal() {
      this.modal = document.createElement('div');
      this.modal.className = 'fm-widget-modal';
      this.modal.innerHTML = `
        <button class="fm-widget-close">&times;</button>
        <iframe
          class="fm-widget-iframe"
          src="${FM_API_BASE}/embed/get-matched?partner=${this.config.partnerId}"
        ></iframe>
      `;

      this.modal.querySelector('.fm-widget-close').addEventListener('click', () => {
        this.closeModal();
      });

      this.modal.addEventListener('click', (e) => {
        if (e.target === this.modal) this.closeModal();
      });

      document.body.appendChild(this.modal);
    }

    openModal() {
      this.modal.classList.add('active');
      document.body.style.overflow = 'hidden';

      // Track widget open
      this.trackEvent('widget_opened');
    }

    closeModal() {
      this.modal.classList.remove('active');
      document.body.style.overflow = '';
    }

    trackEvent(eventName, data = {}) {
      fetch(`${FM_API_BASE}/api/v1/widget/track`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          partner_id: this.config.partnerId,
          event: eventName,
          url: window.location.href,
          ...data,
        }),
      }).catch(() => {}); // Silently fail
    }
  }

  // Expose to window
  window.FaceMortgageWidget = FaceMortgageWidget;

  // Auto-init if data attribute present
  document.addEventListener('DOMContentLoaded', () => {
    const autoInit = document.querySelector('[data-fm-widget]');
    if (autoInit) {
      new FaceMortgageWidget({
        partnerId: autoInit.dataset.fmPartner,
        theme: autoInit.dataset.fmTheme,
        buttonText: autoInit.dataset.fmButtonText,
      });
    }
  });
})();
```

### 8.3 Email Notification System

#### Task 8.3.1: Create Email Templates
**File**: `backend/src/app/services/email_templates.py` (NEW)

```python
from typing import Dict

EMAIL_TEMPLATES: Dict[str, Dict[str, str]] = {
    "welcome": {
        "subject": "Welcome to FaceMortgage!",
        "html": """
        <h1>Welcome, {{name}}!</h1>
        <p>Thank you for joining FaceMortgage. You're now ready to connect with borrowers instantly.</p>
        <p><a href="{{dashboard_url}}">Go to your dashboard</a></p>
        """,
    },
    "new_lead": {
        "subject": "New Lead: {{lead_name}}",
        "html": """
        <h2>You have a new lead!</h2>
        <p><strong>Name:</strong> {{lead_name}}</p>
        <p><strong>Email:</strong> {{lead_email}}</p>
        <p><strong>Phone:</strong> {{lead_phone}}</p>
        <p><strong>Purpose:</strong> {{loan_purpose}}</p>
        <p><a href="{{lead_url}}">View Lead Details</a></p>
        """,
    },
    "scheduled_call_reminder": {
        "subject": "Reminder: Call with {{borrower_name}} in 15 minutes",
        "html": """
        <h2>Upcoming Call Reminder</h2>
        <p>You have a scheduled call with <strong>{{borrower_name}}</strong> at {{scheduled_time}}.</p>
        <p><a href="{{call_url}}">Join Call</a></p>
        """,
    },
    "payment_failed": {
        "subject": "Payment Failed - Action Required",
        "html": """
        <h2>Payment Issue</h2>
        <p>Hi {{name}},</p>
        <p>We were unable to process your payment. Your placement bids have been paused.</p>
        <p><a href="{{billing_url}}">Update Payment Method</a></p>
        """,
    },
    "partnership_invitation": {
        "subject": "{{lo_name}} invited you to partner on FaceMortgage",
        "html": """
        <h2>Partnership Invitation</h2>
        <p>Hi {{realtor_name}},</p>
        <p><strong>{{lo_name}}</strong> from {{lo_company}} has invited you to partner with them on FaceMortgage.</p>
        <p>As partners, you can:</p>
        <ul>
          <li>Refer clients directly to {{lo_name}}</li>
          <li>Track referral status and outcomes</li>
          <li>Add a financing widget to your listings</li>
        </ul>
        <p><a href="{{accept_url}}">Accept Invitation</a></p>
        """,
    },
}
```

#### Task 8.3.2: Create Email Service
**File**: `backend/src/app/services/email_service.py` (NEW)

```python
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from jinja2 import Template
from src.app.config import settings
from .email_templates import EMAIL_TEMPLATES

class EmailService:
    """Email sending service using SendGrid."""

    def __init__(self):
        self.client = SendGridAPIClient(settings.SENDGRID_API_KEY)
        self.from_email = settings.FROM_EMAIL

    def render_template(self, template_name: str, context: dict) -> tuple[str, str]:
        """Render email template with context."""
        template = EMAIL_TEMPLATES.get(template_name)
        if not template:
            raise ValueError(f"Unknown template: {template_name}")

        subject = Template(template["subject"]).render(**context)
        html = Template(template["html"]).render(**context)

        return subject, html

    async def send_email(
        self,
        to_email: str,
        template_name: str,
        context: dict,
    ) -> bool:
        """Send templated email."""
        try:
            subject, html = self.render_template(template_name, context)

            message = Mail(
                from_email=self.from_email,
                to_emails=to_email,
                subject=subject,
                html_content=html,
            )

            response = self.client.send(message)
            return response.status_code in (200, 201, 202)
        except Exception as e:
            logger.error(f"Email send failed: {e}")
            return False

    async def send_welcome_email(self, user):
        """Send welcome email to new user."""
        return await self.send_email(
            to_email=user.email,
            template_name="welcome",
            context={
                "name": user.first_name,
                "dashboard_url": f"{settings.FRONTEND_URL}/dashboard",
            },
        )

    async def send_new_lead_notification(self, professional, lead):
        """Notify professional of new lead."""
        return await self.send_email(
            to_email=professional.user.email,
            template_name="new_lead",
            context={
                "lead_name": lead.contact_name,
                "lead_email": lead.contact_email,
                "lead_phone": lead.contact_phone or "Not provided",
                "loan_purpose": lead.loan_purpose or "Not specified",
                "lead_url": f"{settings.FRONTEND_URL}/dashboard/leads/{lead.id}",
            },
        )

email_service = EmailService()
```

#### Task 8.3.3: Wire Up Email Triggers
**File**: `backend/src/app/workers/tasks.py`

```python
from src.app.services.email_service import email_service

@celery_app.task
def send_welcome_email_task(user_id: str):
    """Background task to send welcome email."""
    async def _send():
        async with get_db_session() as db:
            user = await db.get(User, user_id)
            if user:
                await email_service.send_welcome_email(user)

    asyncio.run(_send())

@celery_app.task
def send_new_lead_notification_task(professional_id: str, lead_id: str):
    """Background task to notify professional of new lead."""
    async def _send():
        async with get_db_session() as db:
            professional = await db.get(ProfessionalProfile, professional_id)
            lead = await db.get(Lead, lead_id)
            if professional and lead:
                await email_service.send_new_lead_notification(professional, lead)

    asyncio.run(_send())

@celery_app.task
def send_scheduled_call_reminders():
    """Periodic task to send call reminders (run every 5 min)."""
    async def _send_reminders():
        async with get_db_session() as db:
            # Find calls starting in 15 minutes
            upcoming = await db.execute(
                select(ScheduledCall)
                .where(
                    ScheduledCall.scheduled_for.between(
                        datetime.utcnow() + timedelta(minutes=14),
                        datetime.utcnow() + timedelta(minutes=16),
                    ),
                    ScheduledCall.reminder_sent_at.is_(None),
                    ScheduledCall.status == "confirmed",
                )
            )

            for call in upcoming.scalars():
                # Send to professional
                await email_service.send_email(
                    to_email=call.professional.user.email,
                    template_name="scheduled_call_reminder",
                    context={
                        "borrower_name": call.contact_name,
                        "scheduled_time": call.scheduled_for.strftime("%I:%M %p"),
                        "call_url": f"{settings.FRONTEND_URL}/call/scheduled/{call.id}",
                    },
                )

                # Mark reminder as sent
                call.reminder_sent_at = datetime.utcnow()

            await db.commit()

    asyncio.run(_send_reminders())
```

---

## Task Checklist

### Phase 1: Payment & Billing
- [x] 1.1.1 Create Stripe webhook endpoint
- [x] 1.1.2 Implement webhook handlers (subscription events)
- [x] 1.1.3 Add Stripe config to settings
- [x] 1.1.4 Create checkout session endpoint
- [x] 1.2.1 Create wallet deposit endpoint
- [x] 1.3.1 Update frontend billing page with Stripe Elements

### Phase 2: Data Provider Integration
- [x] 2.1.1 Implement Datagod provider
- [x] 2.1.2 Implement CoreLogic provider
- [x] 2.1.3 Update factory with caching
- [x] 2.1.4 Create baseball card API endpoint
- [x] 2.2.1 Connect BaseballCard component to real data

### Phase 3: Video Infrastructure
- [x] 3.1.1 Install LiveKit SDK (optional)
- [x] 3.1.2 Create LiveKit service
- [x] 3.1.3 Update call initiation for LiveKit
- [x] 3.2.1 Implement S3 video upload
- [x] 3.2.2 Create video upload endpoint

### Phase 4: Mobile & PWA
- [x] 4.1.1 Create web app manifest
- [x] 4.1.2 Create service worker
- [x] 4.1.3 Register service worker
- [x] 4.2.1 Create push notification hook
- [x] 4.2.2 Backend push notification service

### Phase 5: Analytics & Reporting
- [x] 5.1.1 Create analytics service
- [x] 5.1.2 Create analytics endpoints
- [x] 5.2.1 Update analytics dashboard page

### Phase 6: Testing & QA
- [x] 6.1.1 Create test fixtures
- [x] 6.1.2 Create API tests
- [x] 6.1.3 Create integration tests
- [x] 6.2.1 Setup Vitest for frontend
- [x] 6.2.2 Create component tests

### Phase 7: Production Readiness
- [x] 7.1.1 Create production environment files
- [x] 7.2.1 Setup structured logging
- [x] 7.2.2 Add Sentry integration (backend complete; frontend pending @sentry/nextjs Next.js 16 support)
- [x] 7.3.1 Create health check endpoints

### Phase 8: Strategic Features
- [x] 8.1.1 Add geo detection endpoint
- [x] 8.1.2 Frontend auto-filter by location
- [x] 8.2.1 Create embeddable widget script
- [x] 8.3.1 Create email templates
- [x] 8.3.2 Create email service
- [x] 8.3.3 Wire up email triggers

---

## Autonomous Implementation Strategy

To work more autonomously on this plan, I can:

1. **Run parallel background agents** - Launch multiple agents to work on independent phases simultaneously
2. **Use task-based execution** - Break work into discrete tasks that can be completed without constant input
3. **Checkpoint progress** - Mark tasks complete and document blockers
4. **Test as I go** - Run tests after each implementation to verify correctness

When you're ready, say "start autonomous implementation" and I'll begin working through the phases, running multiple agents in parallel where possible, and only pausing for critical decisions or blockers.
