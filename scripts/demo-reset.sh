#!/bin/bash
# FaceMortgage Demo Reset Script
# Resets environment to clean demo state in ~30 seconds

set -e
echo "🔄 FaceMortgage Demo Reset"
echo "=========================="

# Kill existing servers
echo "1️⃣  Stopping servers..."
lsof -ti:5846,5847 | xargs kill -9 2>/dev/null || true
sleep 1

# Reset database
echo "2️⃣  Resetting database..."
cd "$(dirname "$0")/../backend"
rm -f facemortgage_demo.db

# Create tables and seed
echo "3️⃣  Seeding demo data..."
export DATABASE_URL="sqlite+aiosqlite:///./facemortgage_demo.db"
export REDIS_URL="redis://localhost:6379/0"
export SECRET_KEY="demo-secret-key-32-chars-long!!"
export PYTHONPATH=.

python -c "
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
engine = create_async_engine('sqlite+aiosqlite:///./facemortgage_demo.db')
async def init():
    async with engine.begin() as conn:
        # Import all models to register them
        from src.app.models import user, professional, lead, call, billing
        from src.app.db import Base
        await conn.run_sync(Base.metadata.create_all)
asyncio.run(init())
print('  Tables created')
"

python scripts/seed_demo.py

# Start backend
echo "4️⃣  Starting backend (port 5846)..."
uvicorn src.app.main:app --host 0.0.0.0 --port 5846 &
sleep 2

# Start frontend
echo "5️⃣  Starting frontend (port 5847)..."
cd ../frontend
NEXT_PUBLIC_API_URL=http://localhost:5846 npm run dev -- --port 5847 &
sleep 3

echo ""
echo "✅ Demo reset complete!"
echo ""
echo "📱 Preview URL: http://localhost:5847"
echo "📚 API Docs:    http://localhost:5846/docs"
echo ""
echo "Demo Accounts:"
echo "  admin@facemortgage.com / admin123 (Admin)"
echo "  john@loanpro.com / demo123 (LO)"
echo "  borrower@test.com / test123 (Borrower)"
echo ""
