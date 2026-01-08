# FaceMortgage Production Deployment Checklist

## Pre-Deployment Verification

### Code Quality
- [ ] All tests passing (`pytest` for backend, `npm test` for frontend)
- [ ] No linting errors (`ruff check` for backend, `npm run lint` for frontend)
- [ ] Type checking passes (`mypy` for backend, `tsc --noEmit` for frontend)
- [ ] Code reviewed and approved

### Security
- [ ] No secrets committed to repository
- [ ] Environment variables documented
- [ ] HTTPS/TLS certificates ready
- [ ] CORS origins configured for production domain
- [ ] Rate limiting configured appropriately

---

## Environment Configuration

### Backend Environment Variables

```bash
# Database
DATABASE_URL=postgresql://user:password@host:5432/facemortgage
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=10

# Redis
REDIS_URL=redis://host:6379/0

# Security
SECRET_KEY=<generate-64-char-secure-key>
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
ALLOWED_ORIGINS=https://facemortgage.com,https://www.facemortgage.com
COOKIE_DOMAIN=.facemortgage.com

# Stripe
STRIPE_SECRET_KEY=sk_live_xxxx
STRIPE_WEBHOOK_SECRET=whsec_xxxx
STRIPE_PRICE_BASIC=price_xxxx
STRIPE_PRICE_PROFESSIONAL=price_xxxx
STRIPE_PRICE_PREMIUM=price_xxxx

# Email (SendGrid)
SENDGRID_API_KEY=SG.xxxx
FROM_EMAIL=noreply@facemortgage.com
FROM_NAME=FaceMortgage

# WebRTC/TURN Server
TURN_SERVER_URL=turn:turn.facemortgage.com:3478
TURN_USERNAME=user
TURN_CREDENTIAL=password

# Optional: Monitoring
SENTRY_DSN=https://xxxx@sentry.io/xxxx
```

### Frontend Environment Variables

```bash
NEXT_PUBLIC_API_URL=https://api.facemortgage.com
NEXT_PUBLIC_WS_URL=wss://api.facemortgage.com
NEXT_PUBLIC_STRIPE_PUBLIC_KEY=pk_live_xxxx
```

---

## Infrastructure Setup

### Database (PostgreSQL)
- [ ] PostgreSQL 16 instance provisioned
- [ ] Database created: `facemortgage`
- [ ] User with appropriate permissions created
- [ ] Connection pooling configured (PgBouncer recommended)
- [ ] Automated backups enabled
- [ ] Migrations run: `alembic upgrade head`

### Redis
- [ ] Redis 7 instance provisioned
- [ ] Memory limits configured
- [ ] Persistence enabled (AOF recommended)
- [ ] Connection URL configured

### SSL/TLS
- [ ] SSL certificate obtained (Let's Encrypt or commercial)
- [ ] Certificate auto-renewal configured
- [ ] HTTPS redirect enabled
- [ ] HSTS headers configured

### DNS
- [ ] A record for `facemortgage.com`
- [ ] A record for `api.facemortgage.com`
- [ ] CNAME for `www.facemortgage.com`

---

## Third-Party Services

### Stripe
- [ ] Live mode API keys obtained
- [ ] Webhook endpoint registered: `https://api.facemortgage.com/api/v1/billing/webhook`
- [ ] Subscription products created
- [ ] Price IDs configured

### SendGrid
- [ ] Account verified
- [ ] Domain authentication complete
- [ ] API key generated
- [ ] Templates configured (or using code templates)

### Twilio (for TURN server / optional)
- [ ] Account configured
- [ ] TURN credentials obtained

---

## Deployment Steps

### 1. Build Docker Images

```bash
# Backend
docker build -t facemortgage-backend:latest ./backend

# Frontend
docker build -t facemortgage-frontend:latest ./frontend
```

### 2. Push to Container Registry

```bash
# Tag and push to GitHub Container Registry (or your registry)
docker tag facemortgage-backend:latest ghcr.io/your-org/facemortgage-backend:latest
docker push ghcr.io/your-org/facemortgage-backend:latest

docker tag facemortgage-frontend:latest ghcr.io/your-org/facemortgage-frontend:latest
docker push ghcr.io/your-org/facemortgage-frontend:latest
```

### 3. Deploy to Staging

```bash
# Apply staging configuration
docker-compose -f docker-compose.staging.yml up -d
```

### 4. Staging Verification
- [ ] Application accessible
- [ ] Login/register flow working
- [ ] Professional grid loading
- [ ] Video calls functional (test with two browsers)
- [ ] Stripe checkout working (test mode)
- [ ] Email delivery working

### 5. Production Deployment

```bash
# Via GitHub Actions (recommended)
# Push to main branch with deployment approval

# Or manual deployment
docker-compose -f docker-compose.prod.yml up -d
```

---

## Post-Deployment Verification

### Smoke Tests
- [ ] Homepage loads
- [ ] Professional grid displays
- [ ] Filters work
- [ ] Login page accessible
- [ ] Registration flow works
- [ ] Video call initiates
- [ ] Stripe checkout redirects
- [ ] WebSocket connections established

### Monitoring Setup
- [ ] Application logs accessible
- [ ] Error tracking enabled
- [ ] Uptime monitoring configured
- [ ] Database monitoring enabled
- [ ] Alert thresholds configured

---

## Rollback Procedure

### If Issues Are Detected

1. **Immediate Rollback**
   ```bash
   docker-compose down
   docker-compose -f docker-compose.prod.yml up -d --tag previous-version
   ```

2. **Database Rollback (if needed)**
   ```bash
   alembic downgrade -1
   ```

3. **Notify Team**
   - Document the issue
   - Create incident report
   - Schedule post-mortem

---

## Maintenance Procedures

### Regular Tasks
- Weekly: Review error logs
- Weekly: Check disk usage
- Monthly: Review and rotate secrets
- Monthly: Update dependencies
- Quarterly: Security audit

### Database Maintenance
```bash
# Vacuum and analyze
psql -c "VACUUM ANALYZE;"

# Check table sizes
psql -c "SELECT relname, pg_size_pretty(pg_total_relation_size(relid))
         FROM pg_catalog.pg_statio_user_tables
         ORDER BY pg_total_relation_size(relid) DESC;"
```

### Log Rotation
- Configure Docker log rotation
- Set up log aggregation (optional but recommended)

---

## Support Contacts

| Service | Contact | Notes |
|---------|---------|-------|
| Hosting | your-provider@support | Include account ID |
| Stripe | stripe.com/support | Merchant ID |
| SendGrid | support@sendgrid.com | Account email |
| Database | db-provider@support | Cluster name |

---

## Version Information

**Current Release:** v1.0.0
**Deployment Date:** ___________
**Deployed By:** ___________

---

## Sign-Off

- [ ] Technical Lead Approval
- [ ] Security Review Approval
- [ ] Stakeholder Notification Sent
