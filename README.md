# FaceMortgage.com

A real-time lead generation platform featuring a "Hollywood Squares" style video grid where borrowers can browse, filter, and instantly connect with mortgage professionals via video call.

## Project Structure

```
facemortgage/
├── backend/          # FastAPI Python backend
├── frontend/         # Next.js 15 React frontend
├── shared/           # Shared types and contracts
└── docker-compose.yml
```

## Features

- **Video Grid**: Live/pre-recorded video thumbnails of mortgage professionals
- **Real-time Filtering**: By language, specialty, location, loan type
- **Instant Video Calls**: Click to connect via WebRTC
- **Pickup Time Tracking**: Incentivizes fast responses
- **Baseball Card Profiles**: Professional stats from external data API
- **Hybrid Billing**: Subscriptions + bidding for premium placement

## Tech Stack

### Backend
- Python 3.11+
- FastAPI
- PostgreSQL + TimescaleDB
- Redis
- SQLAlchemy + Alembic

### Frontend
- Next.js 15
- React 19
- TypeScript
- Tailwind CSS
- Zustand + TanStack Query
- LiveKit (WebRTC)

## Getting Started

### Prerequisites
- Python 3.11+
- Node.js 20+
- Docker & Docker Compose
- PostgreSQL 16
- Redis 7+

### Development Setup

1. Clone the repository
2. Start infrastructure:
   ```bash
   docker-compose up -d postgres redis
   ```

3. Backend setup:
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   alembic upgrade head
   uvicorn src.app.main:app --reload
   ```

4. Frontend setup:
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

## Environment Variables

See `.env.example` files in `backend/` and `frontend/` directories.

## License

Proprietary - All rights reserved
