# Patient Navigator — Deployment Guide

## Prerequisites

- **Server:** Linux (Ubuntu 22.04+ recommended), minimum 2 GB RAM, 20 GB disk
- **Software:** Docker Engine 24+, Docker Compose v2+
- **DNS:** Domain name pointing to your server IP
- **SSL:** Let's Encrypt / Certbot for HTTPS

## Quick Start

### 1. Clone and configure

```bash
git clone <repo-url> /opt/patient-navigator
cd /opt/patient-navigator

# Create production environment file
cp .env.production.example .env.production
```

### 2. Generate secrets

```bash
# Generate a secure JWT secret
python3 -c "import secrets; print(secrets.token_urlsafe(32))"

# Generate a strong database password
python3 -c "import secrets; print(secrets.token_urlsafe(24))"
```

### 3. Edit `.env.production`

Fill in all required values:

| Variable | Required | Description |
|----------|----------|-------------|
| `POSTGRES_PASSWORD` | ✅ | Strong database password |
| `JWT_SECRET_KEY` | ✅ | Generated JWT secret (≥ 32 chars) |
| `CORS_ORIGINS` | ✅ | Your domain, e.g. `https://nav.example.com` |
| `ENVIRONMENT` | ✅ | Must be `production` |
| `DEBUG` | ✅ | Must be `false` |
| `OLLAMA_BASE_URL` | ❌ | Ollama endpoint (default: `http://ollama:11434`) |

### 4. Build and start

```bash
docker compose -f docker-compose.prod.yml up -d
```

This starts:
- **PostgreSQL** on the internal Docker network
- **Redis** with persistence
- **Backend** (FastAPI) with health checks
- **Frontend** (Nginx) on port 80

### 5. Run migrations & seed

```bash
# Migrations run automatically via the migrate service.
# To run manually:
docker compose -f docker-compose.prod.yml exec backend alembic upgrade head

# Seed initial data (admin user, roles, etc.)
docker compose -f docker-compose.prod.yml exec backend python scripts/seed_minimal.py
```

### 6. Verify

```bash
# Check all services are healthy
docker compose -f docker-compose.prod.yml ps

# Test the health endpoint
curl http://localhost/health
```

Expected response:
```json
{
  "status": "healthy",
  "version": "0.1.0",
  "checks": {
    "database": "ok",
    "redis": "ok",
    "ollama": "ok"
  }
}
```

## HTTPS with Let's Encrypt

### 1. Install Certbot

```bash
sudo apt install certbot python3-certbot-nginx
```

### 2. Obtain certificate

```bash
sudo certbot --nginx -d nav.example.com
```

### 3. Update Nginx config

The certbot will modify the Nginx config. Alternatively, update `nginx/nginx.conf`:

```nginx
server {
    listen 443 ssl http2;
    server_name nav.example.com;

    ssl_certificate /etc/letsencrypt/live/nav.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/nav.example.com/privkey.pem;

    # ... rest of config
}

server {
    listen 80;
    server_name nav.example.com;
    return 301 https://$host$request_uri;
}
```

### 4. Mount certificates in docker-compose

Add volume mounts to the frontend service in `docker-compose.prod.yml`:

```yaml
frontend:
  volumes:
    - /etc/letsencrypt:/etc/letsencrypt:ro
  ports:
    - "80:80"
    - "443:443"
```

### 5. Auto-renewal

Certbot installs a cron job automatically. Verify with:
```bash
sudo certbot renew --dry-run
```

## Database Backups

### Manual backup

```bash
./scripts/backup.sh
```

### Scheduled backups (cron)

```bash
# Edit crontab
crontab -e

# Add daily backup at 2 AM
0 2 * * * /opt/patient-navigator/scripts/backup.sh >> /var/log/patient-nav-backup.log 2>&1
```

Backups are retained for 30 days by default (configurable via `RETENTION_DAYS` env var).

### Restore from backup

```bash
./scripts/restore.sh backups/patient_nav_20260606_020000.sql.gz
```

## Updating

```bash
cd /opt/patient-navigator
git pull origin main

# Rebuild and restart (zero downtime with health checks)
docker compose -f docker-compose.prod.yml up -d --build

# Check health
docker compose -f docker-compose.prod.yml ps
curl http://localhost/health
```

## Rollback

If a deployment fails:

```bash
# 1. Revert to previous commit
git revert HEAD

# 2. Rebuild
docker compose -f docker-compose.prod.yml up -d --build

# 3. If database was migrated, roll back
docker compose -f docker-compose.prod.yml exec backend alembic downgrade -1

# 4. If needed, restore from backup
./scripts/restore.sh backups/patient_nav_<timestamp>.sql.gz
```

## Monitoring

- **Health check:** `GET /health` — returns status of database, Redis, Ollama
- **Metrics:** `GET /metrics` — uptime, request counts, memory usage, pool stats
- **Logs:** `docker compose -f docker-compose.prod.yml logs -f backend`

## Troubleshooting

| Symptom | Check |
|---------|-------|
| Backend won't start | Check `.env.production` values — all required vars set? |
| "Production validation failed" | `JWT_SECRET_KEY` must be changed from default |
| Database connection refused | Is `db` service healthy? Check `docker compose ps` |
| 502 Bad Gateway | Backend not ready yet — wait for health check |
| Upload fails | Check `UPLOAD_DIR` exists and is writable |
| AI features disabled | Ollama not reachable — non-critical, app works without it |
