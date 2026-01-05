# GitHub Repository Secrets Configuration

This guide documents all the secrets required for the FaceMortgage CI/CD pipeline.

## Required Secrets for CI/CD

Navigate to your GitHub repository: **Settings > Secrets and variables > Actions**

### Core Application Secrets

| Secret Name | Description | Required For | Example |
|-------------|-------------|--------------|---------|
| `SECRET_KEY` | Application secret key for JWT/session signing | All environments | `python -c "import secrets; print(secrets.token_urlsafe(64))"` |
| `DATABASE_URL` | PostgreSQL connection string | Backend tests, deployments | `postgresql+asyncpg://user:pass@host:5432/dbname` |
| `REDIS_URL` | Redis connection string | Caching, sessions | `redis://localhost:6379/0` |

### Frontend Build Secrets

| Secret Name | Description | Required For | Example |
|-------------|-------------|--------------|---------|
| `API_URL` | Backend API URL for frontend build | Frontend build | `https://api.facemortgage.com` |
| `NEXT_PUBLIC_API_URL` | Public API URL (same as API_URL) | Frontend runtime | `https://api.facemortgage.com` |

### Stripe Integration

| Secret Name | Description | Required For | Example |
|-------------|-------------|--------------|---------|
| `STRIPE_SECRET_KEY` | Stripe API secret key | Billing features | `sk_live_...` or `sk_test_...` |
| `STRIPE_WEBHOOK_SECRET` | Stripe webhook signing secret | Webhook verification | `whsec_...` |
| `STRIPE_PUBLISHABLE_KEY` | Stripe public key (can be in code) | Frontend payments | `pk_live_...` or `pk_test_...` |

### Email Service (SendGrid)

| Secret Name | Description | Required For | Example |
|-------------|-------------|--------------|---------|
| `SENDGRID_API_KEY` | SendGrid API key | Email notifications | `SG.xxxxx...` |

### Video Infrastructure (LiveKit)

| Secret Name | Description | Required For | Example |
|-------------|-------------|--------------|---------|
| `LIVEKIT_URL` | LiveKit server URL | Video calls | `wss://your-app.livekit.cloud` |
| `LIVEKIT_API_KEY` | LiveKit API key | Video call authentication | `APIxxxxx` |
| `LIVEKIT_API_SECRET` | LiveKit API secret | Token generation | `xxxxx...` |

### Error Tracking (Sentry)

| Secret Name | Description | Required For | Example |
|-------------|-------------|--------------|---------|
| `SENTRY_DSN` | Sentry Data Source Name | Error tracking | `https://xxx@xxx.ingest.sentry.io/xxx` |

### Cloud Storage (Optional)

| Secret Name | Description | Required For | Example |
|-------------|-------------|--------------|---------|
| `AWS_ACCESS_KEY_ID` | AWS/R2 access key | File uploads | `AKIA...` |
| `AWS_SECRET_ACCESS_KEY` | AWS/R2 secret key | File uploads | `xxxxx...` |
| `S3_BUCKET_NAME` | S3/R2 bucket name | File uploads | `facemortgage-uploads` |
| `S3_ENDPOINT_URL` | Custom S3 endpoint (for R2) | Cloudflare R2 | `https://xxx.r2.cloudflarestorage.com` |

### SMS Notifications (Twilio - Optional)

| Secret Name | Description | Required For | Example |
|-------------|-------------|--------------|---------|
| `TWILIO_SID` | Twilio Account SID | SMS notifications | `AC...` |
| `TWILIO_AUTH_TOKEN` | Twilio Auth Token | SMS notifications | `xxxxx...` |
| `TWILIO_PHONE` | Twilio phone number | SMS sender | `+1234567890` |

## Environment-Specific Configuration

### Staging Environment
Create these as environment secrets under **Settings > Environments > staging**:
- All secrets above with staging/test credentials
- `API_URL=https://staging-api.facemortgage.com`

### Production Environment
Create these as environment secrets under **Settings > Environments > production**:
- All secrets above with production credentials
- `API_URL=https://api.facemortgage.com`
- Enable "Required reviewers" for deployment protection

## How to Add Secrets

1. Go to your GitHub repository
2. Navigate to **Settings > Secrets and variables > Actions**
3. Click **New repository secret**
4. Enter the secret name (exactly as shown above)
5. Enter the secret value
6. Click **Add secret**

## Minimum Required Secrets for CI to Pass

For the CI pipeline to run successfully, you need at minimum:
- `SECRET_KEY` - Generate with: `python -c "import secrets; print(secrets.token_urlsafe(64))"`
- `DATABASE_URL` - For backend tests (CI uses GitHub-provided PostgreSQL service)

The CI workflow automatically sets up PostgreSQL and Redis services for testing.

## Security Best Practices

1. **Never commit secrets** - Use `.env` files locally, GitHub secrets for CI/CD
2. **Rotate regularly** - Especially `SECRET_KEY` and API keys
3. **Use test keys** - For staging/development environments
4. **Limit access** - Only grant secret access to necessary team members
5. **Audit logs** - Review GitHub's audit log for secret access

## Verifying Secrets

After adding secrets, trigger a workflow run to verify they're working:

```bash
# Trigger a manual workflow run
gh workflow run ci.yml
```

Or push a commit to trigger the CI pipeline automatically.
