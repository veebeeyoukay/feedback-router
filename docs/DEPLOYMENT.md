# Feedback Router: Deployment Guide

## Prerequisites

### System Requirements

**Python**:
- Python 3.11 or higher
- Recommended: 3.11.x or 3.12.x
- Virtual environment (venv or poetry)

**Node.js** (for website widget):
- Node 20 or higher
- npm or yarn

**Database**:
- PostgreSQL 15 or higher
- Database: feedback_router
- User with CREATE TABLE permissions

**Cache/Queue**:
- Redis 7 or higher
- For both caching and Celery queue

**Slack** (if using Slack integration):
- Slack Workspace (free or paid)
- Admin access to create bot app

**External APIs**:
- Anthropic API key (for Claude)
- Slack app tokens (if using Slack)
- Google Drive API credentials (if using company docs integration)

**Infrastructure**:
- Docker (recommended for production)
- Docker Compose (for local multi-service setup)
- Server with 2+ CPU cores, 4+ GB RAM minimum
- HTTPS certificate (self-signed for dev, real cert for production)

---

## Development Environment Setup

### Step 1: Clone Repository

```bash
git clone https://github.com/itjen/feedback-router.git
cd feedback-router
```

### Step 2: Create Virtual Environment

```bash
python3.11 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install --upgrade pip setuptools
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt  # For testing, linting, etc.
```

### Step 4: Database Setup

```bash
# Create PostgreSQL database
createdb feedback_router

# Run migrations
alembic upgrade head

# (Optional) Load sample data
python scripts/load_sample_data.py
```

### Step 5: Redis Setup

```bash
# Local Redis (macOS with Homebrew)
brew install redis
brew services start redis

# Or use Docker
docker run -d -p 6379:6379 redis:7-alpine
```

### Step 6: Environment Variables

```bash
# Copy template
cp config/env.example .env

# Edit .env with your values
# Required:
# - ANTHROPIC_API_KEY
# - SLACK_BOT_TOKEN (if using Slack)
# - SLACK_SIGNING_SECRET (if using Slack)
# - DATABASE_URL
# - REDIS_URL
```

See [Environment Variables](#environment-variables) section below.

### Step 7: Start Development Server

```bash
# Terminal 1: FastAPI backend
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2: Celery worker
celery -A src.celery_app worker --loglevel=info

# Terminal 3: Celery beat (scheduler)
celery -A src.celery_app beat --loglevel=info
```

The API will be available at `http://localhost:8000`.
API docs at `http://localhost:8000/docs`.

---

## Slack App Setup (Production)

### Step 1: Create Slack App

1. Go to https://api.slack.com/apps
2. Click "Create New App" → "From scratch"
3. **App name**: "ItsJen Feedback Router"
4. **Development Slack Workspace**: Select your workspace
5. Click "Create App"

### Step 2: Enable Event Subscriptions

1. In app settings, click "Event Subscriptions"
2. Toggle **Events** to ON
3. **Request URL**: `https://your-domain.com/api/feedback/slack`
   - Slack will verify with a challenge
   - Your server must respond with HTTP 200 within 3 seconds
   - Use `ngrok` for local testing: `ngrok http 8000`
4. **Subscribe to bot events**:
   - `message.channels` (messages in public channels)
   - `message.groups` (messages in private channels)
   - `message.im` (direct messages to bot)
   - `reaction_added` (reactions on messages)
5. Click "Save Changes"

### Step 3: Configure OAuth Scopes

1. Click "OAuth & Permissions"
2. Under **Bot Token Scopes**, add:
   - `chat:write` (post messages)
   - `channels:read` (list channels)
   - `groups:read` (list private channels)
   - `users:read` (get user info)
   - `reactions:write` (add reactions to messages)
   - `im:read` (read direct messages)
   - `team:read` (read workspace info)

### Step 4: Install Bot to Workspace

1. Click "Install to Workspace"
2. Review permissions
3. Click "Allow"
4. Copy **Bot User OAuth Token** (starts with `xoxb-`)
5. Store in secure secret management (Vault, AWS Secrets Manager, etc.)

### Step 5: Set Environment Variables

```bash
export SLACK_BOT_TOKEN=xoxb-xxxxx
export SLACK_SIGNING_SECRET=xxxxx
export SLACK_WORKSPACE_ID=Txxx
export FEEDBACK_CHANNEL_ID=C_xxx
```

### Step 6: Test Connection

```bash
python scripts/test_slack_connection.py
```

---

## Website Widget Deployment

### Step 1: Build Widget

```bash
cd src/widget
npm install
npm run build
# Output: dist/widget.js and dist/widget.css
```

### Step 2: Host Widget Files

Host on CDN (CloudFront, Cloudflare, etc.):
```
https://cdn.itjen.ai/widget.js
https://cdn.itjen.ai/widget.css
```

Or self-hosted:
```
https://api.itjen.ai/static/widget.js
https://api.itjen.ai/static/widget.css
```

### Step 3: Embed on Website

Add to your website's HTML (in `<head>` or before `</body>`):

```html
<script src="https://cdn.itjen.ai/widget.js"></script>
<script>
  ItsJenFeedback.init({
    apiKey: 'your_api_key_here',
    theme: 'light',
    position: 'bottom-right'
  });
</script>
```

### Step 4: Generate API Key

```bash
python scripts/generate_api_key.py --name "website-production"
# Output: sk_live_xxxxxxxxxxxxx
```

---

## Docker Deployment

### Local Development with Docker Compose

```bash
# Build images
docker-compose build

# Start all services
docker-compose up

# Services:
# - api (FastAPI): http://localhost:8000
# - worker (Celery): background jobs
# - postgres: database
# - redis: cache/queue
# - pgadmin: database admin (http://localhost:5050)
```

### Production Docker Image

```dockerfile
# Build
docker build -t feedback-router:latest .

# Run
docker run -d \
  --name feedback-router \
  -p 8000:8000 \
  --env-file .env.production \
  -e DATABASE_URL="postgresql://user:pass@postgres:5432/feedback_router" \
  -e REDIS_URL="redis://redis:6379/0" \
  feedback-router:latest

# Or use Kubernetes:
kubectl apply -f k8s/deployment.yaml
```

---

## Environment Variables

Copy `config/env.example` to `.env` and configure:

```bash
# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_ENV=production  # development|staging|production
DEBUG=false

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/feedback_router
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=10
DATABASE_ECHO=false  # Set to true to log SQL queries

# Redis/Cache
REDIS_URL=redis://localhost:6379/0
CACHE_TTL=3600  # seconds

# Slack Integration (optional)
SLACK_BOT_TOKEN=xoxb-xxxxx
SLACK_SIGNING_SECRET=xxxxx
SLACK_WORKSPACE_ID=Txxx
SLACK_FEEDBACK_CHANNEL=C_xxxxx

# Anthropic API
ANTHROPIC_API_KEY=sk-ant-xxxxx
ANTHROPIC_MODEL=claude-3-5-sonnet-20241022
ANTHROPIC_TEMPERATURE=0.7

# Google Drive Integration (optional)
GOOGLE_DRIVE_CREDENTIALS_JSON=/path/to/credentials.json
GOOGLE_DRIVE_FOLDER_ID=xxxxx

# Email/SMTP (optional)
SMTP_HOST=smtp.itjen.ai
SMTP_PORT=587
SMTP_USER=noreply@itjen.ai
SMTP_PASSWORD=xxxxx
SMTP_FROM_EMAIL=feedback@itjen.ai

# Feature Flags
ENABLE_SLACK_INTEGRATION=true
ENABLE_WEBSITE_WIDGET=true
ENABLE_EMAIL_CHANNEL=false  # Wave 2
ENABLE_AUTO_RESPOND=true
ENABLE_CHAT_HISTORY=false  # Future

# Security
SECRET_KEY=generate-with-secrets.token_hex(32)
JWT_EXPIRY_HOURS=24
RATE_LIMIT_REQUESTS_PER_MINUTE=100

# Logging
LOG_LEVEL=INFO  # DEBUG|INFO|WARNING|ERROR
LOG_FORMAT=json  # json|text
SENTRY_DSN=  # Optional: error tracking

# Monitoring
DATADOG_API_KEY=  # Optional: metrics
HEALTHCHECK_ENABLED=true
HEALTHCHECK_INTERVAL_SECONDS=30

# Celery
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
CELERY_TASK_TIME_LIMIT=600  # seconds
CELERY_WORKER_CONCURRENCY=4
```

### Generating Secret Key

```python
import secrets
print(secrets.token_hex(32))
# Use output for SECRET_KEY
```

---

## Database Migrations

The system uses Alembic for schema versioning:

```bash
# Create new migration (auto-detect schema changes)
alembic revision --autogenerate -m "Add feedback_items table"

# Apply migrations
alembic upgrade head

# Rollback last migration
alembic downgrade -1

# See migration history
alembic current  # Current revision
alembic history  # Full history
alembic show xxxxx  # View specific migration
```

Migrations run automatically on startup (can be disabled with `AUTO_MIGRATE=false`).

---

## Monitoring

### Health Check Endpoint

```bash
# Health check (no authentication required)
curl http://localhost:8000/api/health

# Response
{
  "status": "healthy",
  "timestamp": "2026-03-19T14:36:00Z",
  "services": {
    "database": {"status": "healthy", "response_time_ms": 12},
    "redis": {"status": "healthy", "response_time_ms": 5},
    "slack_api": {"status": "healthy", "response_time_ms": 234},
    "claude_api": {"status": "healthy", "response_time_ms": 1200}
  }
}
```

### Metrics & Logging

Structured logging to stdout (JSON format in production):

```json
{
  "timestamp": "2026-03-19T14:36:00Z",
  "level": "INFO",
  "message": "Feedback classified successfully",
  "feedback_id": "fb_1711014720_a1b2c3",
  "category": "bug",
  "confidence": 0.92,
  "processing_time_ms": 2100,
  "logger": "classifier_agent"
}
```

**Export to monitoring platform**:
- Datadog: `DATADOG_API_KEY=`
- New Relic: `NEW_RELIC_LICENSE_KEY=`
- CloudWatch: AWS SDK auto-detects credentials
- ELK Stack: Use Filebeat to ship logs

### Metrics Dashboard

Key metrics to track:

```
- Feedback ingestion rate (items/minute)
- Classification latency (p50, p95, p99)
- Routing decision latency
- Response generation latency
- Response rate (% of items receiving response)
- Success rate (% of operations completing)
- Error rate by component
- Queue depth (classification, routing, response)
- API endpoint latency
- Slack API failures
- Claude API cost/usage
```

### Alerting

Set up alerts for:

```yaml
alerts:
  - name: "Classification Queue Depth > 100"
    threshold: 100
    duration: 5m
    action: page

  - name: "Claude API Error Rate > 5%"
    threshold: 0.05
    duration: 5m
    action: page

  - name: "Database Connection Pool Exhausted"
    threshold: "pool_size_100%"
    duration: 1m
    action: page

  - name: "Response Rate < 95%"
    threshold: 0.95
    duration: 15m
    action: warning

  - name: "Slack Bot Token Expiring in 7 Days"
    action: email
```

---

## Scaling

### Horizontal Scaling

**Add more Celery workers**:
```bash
# Each worker processes tasks independently
# No state sharing required (stateless design)
celery -A src.celery_app worker --loglevel=info --concurrency=8
```

**Load balance API servers**:
```nginx
upstream api {
    server api1:8000;
    server api2:8000;
    server api3:8000;
}

server {
    listen 443 ssl;
    server_name api.itjen.ai;
    location / {
        proxy_pass http://api;
    }
}
```

**Database connection pooling**:
```python
# Via environment
DATABASE_POOL_SIZE=50
DATABASE_MAX_OVERFLOW=20

# Or config
engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=50,
    max_overflow=20,
    pool_pre_ping=True,  # Verify connection is alive
)
```

### Performance Tuning

```yaml
# Classification caching
# Cache results for identical message content (exact hash)
# TTL: 7 days (feedback patterns repeat)
CLASSIFICATION_CACHE_TTL=604800

# Routing rule caching
# Cache compiled rules in memory
# Reload when rules.yaml changes
ROUTING_RULES_CACHE=true

# Database connection pooling
DATABASE_POOL_SIZE=50
DATABASE_STATEMENT_CACHE_SIZE=200

# Celery task prefetching
CELERY_WORKER_PREFETCH_MULTIPLIER=4  # Process 4 tasks at a time

# Slack API rate limiting
SLACK_RATE_LIMIT_BACKOFF=true  # Auto-backoff on 429
```

---

## Rollback Procedure

### Rollback Steps

**1. Database**:
```bash
# If migrations failed, rollback last migration
alembic downgrade -1
# Or to specific revision
alembic downgrade abc123def456
```

**2. Application Code**:
```bash
# Using Docker
docker stop feedback-router
docker run -d --name feedback-router feedback-router:previous-version

# Using systemd
systemctl stop feedback-router
systemctl start feedback-router  # Should be pinned to previous version
```

**3. Verify**:
```bash
# Check health endpoint
curl http://localhost:8000/api/health

# Check logs
tail -f /var/log/feedback-router/error.log

# Verify recent feedback processed correctly
curl http://localhost:8000/api/feedback?limit=5
```

### Deployment Checklist

Before deploying to production:

- [ ] All tests pass locally
- [ ] Database migrations tested in staging
- [ ] Environment variables set correctly
- [ ] Slack app tokens valid
- [ ] API keys (Anthropic, etc.) valid
- [ ] SSL certificate valid
- [ ] Load balancer health checks configured
- [ ] Monitoring/alerting configured
- [ ] Logging aggregation working
- [ ] Rollback plan documented
- [ ] Feature flags correct
- [ ] Rate limiting configured
- [ ] Cache warm-up planned
- [ ] Database backups tested
- [ ] Team notified of deployment

---

## Troubleshooting

### Common Issues

**PostgreSQL Connection Refused**
```bash
# Check if service running
systemctl status postgresql

# Start if stopped
systemctl start postgresql

# Check connection string
psql -U user -h localhost -d feedback_router -c "SELECT 1"
```

**Redis Connection Refused**
```bash
# Check service
redis-cli ping
# Should return PONG

# Start Redis
redis-server /etc/redis/redis.conf
```

**Slack Events Not Received**
```bash
# Check Slack app logs
curl https://api.slack.com/apps/[APP_ID]/event-logs

# Verify webhook URL
curl -X GET https://api.itjen.ai/api/feedback/slack
# Should return 405 (wrong method) or error indicating endpoint exists

# Check ngrok tunnel (local testing)
ngrok http 8000
# Copy forwarding URL into Slack Request URL
```

**Claude API Timeout**
```bash
# Check API status
curl https://api.anthropic.com/health

# Check credentials
export ANTHROPIC_API_KEY=sk-ant-xxxxx
python -c "from anthropic import Anthropic; Anthropic().messages.create(model='claude-3-5-sonnet-20241022', max_tokens=100, messages=[{'role': 'user', 'content': 'test'}])"
```

**Database Lock/Deadlock**
```sql
-- Check active queries
SELECT pid, usename, query, query_start FROM pg_stat_activity WHERE state = 'active';

-- Kill stuck query
SELECT pg_terminate_backend(pid);

-- Check locks
SELECT * FROM pg_stat_activity WHERE state != 'idle';
```

---

## Security Checklist

- [ ] HTTPS only (no HTTP in production)
- [ ] API keys rotated regularly
- [ ] Database password meets complexity requirements
- [ ] Slack bot token stored in secure secret manager
- [ ] PII handling compliant with privacy policy
- [ ] Rate limiting configured
- [ ] CORS properly configured
- [ ] Request validation in place
- [ ] SQL injection protection (ORM + parameterized queries)
- [ ] XSS protection (input sanitization)
- [ ] CSRF tokens for state-changing operations
- [ ] Audit logs for sensitive operations
- [ ] Regular security updates (dependencies)
- [ ] WAF rules configured (if applicable)
- [ ] Backup encryption enabled
- [ ] Log retention policy set
