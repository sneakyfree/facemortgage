#!/usr/bin/env bash
# ============================================================
# FaceMortgage — Environment Configuration Validator
# Run this before starting the app to verify required env vars.
# Usage: bash scripts/check-env.sh
# ============================================================

set -euo pipefail

RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

ERRORS=0
WARNINGS=0

check_required() {
    local var_name="$1"
    local description="$2"
    if [ -z "${!var_name:-}" ]; then
        echo -e "${RED}✗ MISSING${NC} $var_name — $description"
        ERRORS=$((ERRORS + 1))
    else
        echo -e "${GREEN}✓${NC} $var_name"
    fi
}

check_recommended() {
    local var_name="$1"
    local description="$2"
    if [ -z "${!var_name:-}" ]; then
        echo -e "${YELLOW}⚠ NOT SET${NC} $var_name — $description"
        WARNINGS=$((WARNINGS + 1))
    else
        echo -e "${GREEN}✓${NC} $var_name"
    fi
}

# Load .env if it exists
if [ -f .env ]; then
    set -a
    source .env
    set +a
    echo "Loaded .env file"
elif [ -f backend/.env ]; then
    set -a
    source backend/.env
    set +a
    echo "Loaded backend/.env file"
fi

echo ""
echo "═══════════════════════════════════════════"
echo " FaceMortgage Environment Check"
echo "═══════════════════════════════════════════"

echo ""
echo "── Core (Required) ──"
check_required "DATABASE_URL" "PostgreSQL connection string"
check_required "REDIS_URL" "Redis connection string"
check_required "SECRET_KEY" "JWT signing key (production)"

echo ""
echo "── Stripe (Required for billing) ──"
check_recommended "STRIPE_SECRET_KEY" "Stripe API secret key"
check_recommended "STRIPE_WEBHOOK_SECRET" "Stripe webhook signature secret"
check_recommended "STRIPE_PRICE_ID_BASIC" "Basic tier price ID"
check_recommended "STRIPE_PRICE_ID_PROFESSIONAL" "Professional tier price ID"
check_recommended "STRIPE_PRICE_ID_PREMIUM" "Premium tier price ID"

echo ""
echo "── Email (Required for notifications) ──"
check_recommended "SENDGRID_API_KEY" "SendGrid API key for transactional emails"

echo ""
echo "── Video Calling ──"
check_recommended "TURN_SERVER_URL" "TURN server for NAT traversal (video calls)"
check_recommended "TURN_SERVER_USERNAME" "TURN server username"
check_recommended "TURN_SERVER_CREDENTIAL" "TURN server credential"

echo ""
echo "── SMS ──"
check_recommended "TWILIO_SID" "Twilio account SID"
check_recommended "TWILIO_AUTH_TOKEN" "Twilio auth token"
check_recommended "TWILIO_PHONE" "Twilio phone number"

echo ""
echo "── Error Tracking ──"
check_recommended "SENTRY_DSN" "Sentry DSN for error monitoring"

echo ""
echo "═══════════════════════════════════════════"
if [ $ERRORS -gt 0 ]; then
    echo -e "${RED}$ERRORS required variable(s) missing!${NC}"
    echo "Fix these before starting the application."
    exit 1
elif [ $WARNINGS -gt 0 ]; then
    echo -e "${YELLOW}$WARNINGS recommended variable(s) not set.${NC}"
    echo "The app will start but some features will be disabled."
    exit 0
else
    echo -e "${GREEN}All checks passed!${NC}"
    exit 0
fi
