# Deployment Guide

## Quick Start (5 Minutes)

### Prerequisites

- Docker & Docker Compose (v2.x+)
- Python 3.11+ (for local development only)
- Node.js 18+ (for local development only)

### Deploy Locally

```bash
# 1. Clone repository
git clone https://github.com/jobgraph/jobgraph.git
cd jobgraph

# 2. Create environment file (NEVER commit this)
cp .env.example .env.local

# 3. Edit .env.local with YOUR credentials
vim .env.local
# Add:
# - GEMINI_API_KEY (from Google Cloud Console)
# - DB_PASSWORD (generate strong password)
# - MASTER_ENCRYPTION_KEY (generate: openssl rand -hex 32)

# 4. Start services
docker compose up -d

# 5. Initialize database
docker compose exec backend python -m app.infrastructure.bootstrap

# 6. Check status
docker compose ps
curl http://localhost:3000  # Frontend
curl http://localhost:8000/health  # API
```

### First Run Verification

```bash
# View logs
docker compose logs -f backend

# Test API
curl -X GET http://localhost:8000/api/v1/health \
  -H "X-API-Key: $API_KEY"

# Access dashboard
open http://localhost:3000
```

## Environment Configuration

### Required Variables

Create `.env.local` in project root (never commit):

```bash
# Database
DB_PASSWORD=<generate-strong-32-char-password>
DB_HOST=postgres
DB_PORT=5432
DB_NAME=jobgraph

# Encryption
MASTER_ENCRYPTION_KEY=<generate-hex-32-bytes>
# Generate with: openssl rand -hex 32

# LLM Provider
GEMINI_API_KEY=AIza...  # From Google Cloud Console
GEMINI_MODEL=gemini-1.5-pro

# MinIO Storage
MINIO_USER=minioadmin
MINIO_PASSWORD=<generate-strong-password>
MINIO_BUCKET=jobgraph

# Redis/Valkey
VALKEY_PASSWORD=<generate-strong-password>

# API
API_KEY=<generate-random-32-char-string>
API_BASE_URL=http://localhost:8000

# Optional: Telemetry (disabled by default)
TELEMETRY_ENABLED=false

# Optional: SSL (for production)
SSL_CERT_PATH=/path/to/cert.pem
SSL_KEY_PATH=/path/to/key.pem
```

### Optional Variables

```bash
# Logging
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR
STRUCTURED_LOGGING=true

# Feature Flags
FEATURE_BETA_MATCHING=false
FEATURE_ADVANCED_TAILORING=false

# Rate Limiting
RATE_LIMIT_PER_HOUR=100
RATE_LIMIT_PER_DAY=500

# Job Discovery
GREENHOUSE_SYNC_INTERVAL=3600  # seconds
LEVER_SYNC_INTERVAL=3600

# Browser Automation
PLAYWRIGHT_HEADLESS=true
PLAYWRIGHT_TIMEOUT_MS=30000
PLAYWRIGHT_RETRY_COUNT=3
```

## Docker Compose Setup

### Service Topology

```yaml
# docker-compose.yml

version: '3.9'

services:
  # Frontend (Next.js)
  frontend:
    image: node:18-alpine
    ports:
      - "3000:3000"
    environment:
      NEXT_PUBLIC_API_URL: http://localhost:8000
    volumes:
      - ./frontend:/app
    depends_on:
      - backend

  # Backend (FastAPI)
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      DB_HOST: postgres
      GEMINI_API_KEY: ${GEMINI_API_KEY}
      MASTER_ENCRYPTION_KEY: ${MASTER_ENCRYPTION_KEY}
    depends_on:
      - postgres
      - valkey
      - minio
    volumes:
      - ./backend/app:/app/app

  # PostgreSQL Database
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_PASSWORD: ${DB_PASSWORD}
      POSTGRES_DB: jobgraph
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]

  # Valkey (Redis)
  valkey:
    image: valkey/valkey:7-alpine
    environment:
      VALKEY_PASSWORD: ${VALKEY_PASSWORD}
    volumes:
      - valkey_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]

  # MinIO (S3-compatible storage)
  minio:
    image: minio/minio:latest
    environment:
      MINIO_ROOT_USER: ${MINIO_USER}
      MINIO_ROOT_PASSWORD: ${MINIO_PASSWORD}
    volumes:
      - minio_data:/data
    command: server /data
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9000/minio/health/live"]

volumes:
  postgres_data:
  valkey_data:
  minio_data:
```

### Service Health Checks

```bash
# Backend API
curl http://localhost:8000/health

# Database
docker compose exec postgres pg_isready

# Valkey
docker compose exec valkey redis-cli ping

# MinIO
curl http://localhost:9000/minio/health/live

# Frontend
curl http://localhost:3000

# All services
docker compose ps
```

## Production Deployment

### On VPS / Cloud VM

```bash
# 1. Clone and setup
git clone https://github.com/jobgraph/jobgraph.git
cd jobgraph

# 2. Create .env.local with secrets
# WARNING: Never expose this file
scp .env.local user@your-vps:/home/user/jobgraph/

# 3. Build and start
docker compose -f docker-compose.prod.yml up -d

# 4. Verify
docker compose logs -f backend
```

### With SSL/TLS

```yaml
# docker-compose.prod.yml

services:
  backend:
    # ... other config ...
    ports:
      - "443:443"
    environment:
      SSL_CERT_PATH: /etc/ssl/certs/jobgraph.pem
      SSL_KEY_PATH: /etc/ssl/private/jobgraph.key
    volumes:
      - /etc/ssl/certs:/etc/ssl/certs:ro
      - /etc/ssl/private:/etc/ssl/private:ro

  # Optional: Nginx reverse proxy
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - /etc/ssl:/etc/ssl:ro
    depends_on:
      - backend
```

### Kubernetes Deployment (Future)

```bash
# Coming in v1.0
# For now, use Docker Compose

# Helm chart available at: github.com/jobgraph/jobgraph-helm
# helm install jobgraph ./jobgraph-helm \
#   -f values.yaml \
#   --namespace production
```

## Backup & Recovery

### Automated Backups

```bash
#!/bin/bash
# backup.sh - Run daily via cron

BACKUP_DIR=/backups/jobgraph
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Database backup
docker compose exec postgres pg_dump -U postgres jobgraph \
  | gzip > $BACKUP_DIR/db_$TIMESTAMP.sql.gz

# MinIO backup (entire bucket)
docker compose exec minio mc cp -r \
  minio/jobgraph \
  $BACKUP_DIR/minio_$TIMESTAMP/

# Keep last 30 days
find $BACKUP_DIR -name "*.gz" -mtime +30 -delete

echo "Backup completed: $BACKUP_DIR"
```

### Restore from Backup

```bash
# Database restore
gunzip < /backups/jobgraph/db_20260619_120000.sql.gz | \
  docker compose exec -T postgres psql -U postgres -d jobgraph

# MinIO restore (if data lost)
docker compose exec minio mc cp -r \
  /backups/jobgraph/minio_20260619_120000 \
  minio/jobgraph
```

## Monitoring & Logging

### View Logs

```bash
# All services
docker compose logs

# Specific service
docker compose logs -f backend
docker compose logs -f postgres

# Last 100 lines
docker compose logs --tail=100 backend

# With timestamps
docker compose logs -f --timestamps backend
```

### Structured Logging

Logs are output as JSON for easy parsing:

```json
{
  "timestamp": "2026-06-19T14:30:00Z",
  "level": "INFO",
  "component": "TailoringAgent",
  "event": "resume_tailored",
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "duration_ms": 2340,
  "status": "success"
}
```

Parse with:

```bash
docker compose logs backend | jq '.[] | select(.level == "ERROR")'
```

### Performance Monitoring

```bash
# Database connections
docker compose exec postgres psql -U postgres -c \
  "SELECT datname, count(*) FROM pg_stat_activity GROUP BY datname;"

# Storage usage
docker compose exec postgres du -sh /var/lib/postgresql/data
docker compose exec minio du -sh /data

# Memory usage
docker stats

# API latency
curl -w "Response time: %{time_total}s\n" \
  http://localhost:8000/api/v1/health
```

## Troubleshooting

### Service Won't Start

```bash
# Check logs
docker compose logs backend

# Common issues:
# - Port already in use: lsof -i :8000
# - Insufficient disk space: df -h
# - Missing environment variables: grep GEMINI_API_KEY .env.local
# - Database connection refused: docker compose logs postgres
```

### Database Errors

```bash
# Test database connection
docker compose exec backend python -c \
  "from sqlalchemy import create_engine; engine = create_engine(os.getenv('DATABASE_URL')); print(engine.execute('SELECT 1'))"

# Repair database
docker compose exec postgres \
  vacuumdb -U postgres -d jobgraph -v -z

# Check table sizes
docker compose exec postgres psql -U postgres -d jobgraph -c \
  "SELECT schemaname, tablename, pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) FROM pg_tables ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;"
```

### Credential Issues

```bash
# Verify credentials are loaded
docker compose exec backend python -c \
  "from app.core.config import settings; print('Gemini key loaded:', bool(settings.gemini_api_key))"

# Check encryption key
docker compose exec backend python -c \
  "from app.core.config import settings; print('Encryption key length:', len(settings.master_encryption_key))"
```

### Storage Issues

```bash
# MinIO: List all buckets
docker compose exec minio mc ls minio/

# MinIO: Check bucket size
docker compose exec minio mc du minio/jobgraph

# PostgreSQL: Check disk usage
docker compose exec postgres pg_size_pretty(pg_database_size('jobgraph'))
```

## Upgrading

### Backup Before Upgrade

```bash
./backup.sh  # Create backup

git pull origin main

docker compose down

docker compose pull  # Get latest images

docker compose up -d

docker compose exec backend alembic upgrade head  # Database migrations
```

### Rollback if Issues

```bash
docker compose down

# Restore from backup
docker volume rm jobgraph_postgres_data  # Remove old data
docker volume create jobgraph_postgres_data

# Restore database
# (see Restore from Backup section above)

docker compose up -d
```

## Security Hardening

### Network Security

```yaml
# docker-compose.yml - Restrict ports

services:
  backend:
    # Only expose to host, not to network
    ports:
      - "127.0.0.1:8000:8000"  # Localhost only
    networks:
      - internal  # Private network

networks:
  internal:
    driver: bridge
```

### Disable Telemetry

```bash
# In .env.local
TELEMETRY_ENABLED=false
```

### Enable Audit Logging

```bash
# In .env.local
LOG_LEVEL=DEBUG
AUDIT_LOG_ENABLED=true
```

### Rotate Secrets

```bash
# Monthly credential rotation

# 1. Generate new API key
NEW_API_KEY=$(openssl rand -hex 16)

# 2. Update .env.local
sed -i "s/API_KEY=.*/API_KEY=$NEW_API_KEY/" .env.local

# 3. Restart service
docker compose restart backend

# 4. Old key no longer accepted
```

## Support

For issues, questions, or suggestions:

- **GitHub Issues**: https://github.com/jobgraph/jobgraph/issues
- **Documentation**: https://github.com/jobgraph/jobgraph/blob/main/docs/
- **Security**: security@jobgraph.dev
- **Community**: discord.gg/jobgraph (coming soon)

---

**Version**: 1.0  
**Last Updated**: 2026-06-19
