# TaxTrace Staging Deployment Guide

## Overview

This document describes the CI/CD pipeline and staging deployment process for TaxTrace.

## Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   GitHub    │────▶│  CI/CD      │────▶│  Staging    │
│   Actions   │     │  Pipeline   │     │  Environment│
└─────────────┘     └─────────────┘     └─────────────┘
                           │
                    ┌──────┴──────┐
                    ▼           ▼
              ┌─────────┐ ┌──────────┐
              │ Backend │ │ Frontend │
              │ Image   │ │ Image    │
              └─────────┘ └──────────┘
```

## CI/CD Pipeline

### Trigger
- **Push to `main`**: Full CI + Docker build + Deploy to staging
- **Push to `develop`**: Full CI + Docker build (no deploy)
- **Pull Request**: Full CI only
- **Manual Dispatch**: Full CI + Docker build + optional staging deploy

### Pipeline Stages

| Stage | Job | Timeout | Required |
|-------|-----|---------|----------|
| Test | `backend-tests` | 15 min | ✅ |
| Test | `frontend-tests` | 15 min | ✅ |
| Build | `docker-build` | 20 min | ✅ (on push) |
| Deploy | `deploy-staging` | 15 min | ✅ (on main) |

### Backend Tests
- Unit/integration tests (`pytest tests/`)
- Reconciliation benchmark gates (`python -m evaluations.benchmark_reconciliation`)
- Security audit (`python -m scripts.security_audit`)

### Frontend Tests
- Unit tests (`npx vitest run`)
- TypeScript type check (`npx tsc --noEmit`)
- ESLint (`npm run lint`)
- Production build (`npm run build`)

### Docker Build
- Multi-platform builds via Buildx
- Caches via GitHub Actions cache
- Tags: `branch-name`, `sha`, `latest` (main only)
- Pushes to `ghcr.io/<org>/<repo>/backend` and `/frontend`

## Staging Environment

### Infrastructure Requirements

| Component | Specification |
|-----------|---------------|
| Host | Ubuntu 22.04+ (x86_64 or ARM64) |
| Docker | 24+ with Compose v2 |
| RAM | 4 GB minimum (8 GB recommended) |
| Disk | 20 GB free space |
| Ports | 8000 (API), 3000 (Frontend) |

### Required GitHub Secrets

| Secret | Description | Example |
|----------|-------------|---------|
| `STAGING_HOST` | Staging server hostname/IP | `staging.taxtrace.example` |
| `STAGING_USER` | SSH username | `ubuntu` |
| `STAGING_SSH_KEY` | Private SSH key (PEM format) | `-----BEGIN OPENSSH PRIVATE KEY-----...` |
| `STAGING_PORT` | SSH port (default 22) | `22` |
| `DB_PASSWORD` | PostgreSQL password | `secure-random-password` |
| `JWT_SECRET_KEY` | 32+ char secret for JWT | `openssl rand -base64 32` |
| `ALLOWED_ORIGINS` | Comma-separated domains | `https://staging.example.com` |
| `SLACK_WEBHOOK_URL` | Optional Slack notifications | `https://hooks.slack.com/...` |

### Staging Server Setup

```bash
# 1. Create deployment directory
sudo mkdir -p /opt/taxtrace-staging
sudo chown $USER:$USER /opt/taxtrace-staging
cd /opt/taxtrace-staging

# 2. Clone repository (or use deploy key)
git clone https://github.com/eklakhdewan/TaxTrace.git .

# 3. Create environment file
cp .env.staging.example .env.staging
# Edit .env.staging with actual values
# Required: DB_PASSWORD, JWT_SECRET_KEY, ALLOWED_ORIGINS

# 4. Install Docker & Compose
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker $USER
# Log out and back in

# 5. Install Docker Compose v2 (if not included)
DOCKER_CONFIG=${DOCKER_CONFIG:-$HOME/.docker}
mkdir -p $DOCKER_CONFIG/cli-plugins
curl -SL https://github.com/docker/compose/releases/download/v2.24.0/docker-compose-linux-x86_64 -o $DOCKER_CONFIG/cli-plugins/docker-compose
chmod +x $DOCKER_CONFIG/cli-plugins/docker-compose

# 6. Configure GitHub SSH access
# Add deploy key to GitHub repo settings
# Or use token-based auth in workflow

# 7. Test deployment
docker compose -f docker-compose.staging.yml --env-file .env.staging pull
docker compose -f docker-compose.staging.yml --env-file .env.staging run --rm backend poetry run alembic upgrade head
docker compose -f docker-compose.staging.yml --env-file .env.staging up -d

# 8. Verify health
curl -f http://localhost:8000/health
curl -f http://localhost:3000
```

### Environment File (`.env.staging`)

```bash
# Database
DB_USER=taxtrace
DB_PASSWORD=<from-secret>
DB_NAME=taxtrace_staging

# Security
JWT_SECRET_KEY=<from-secret>
ALLOWED_ORIGINS=https://staging.example.com

# API
NEXT_PUBLIC_API_URL=https://api.staging.example.com/api/v1

# Docker
STAGING_TAG=latest
```

### Deployment Process

The CI/CD pipeline automates this:

1. **Build** - Docker images built and pushed to GHCR
2. **SSH** - Pipeline connects to staging server
3. **Pull** - `docker compose pull` gets latest images
4. **Migrate** - Runs `alembic upgrade head` in backend container
5. **Restart** - `docker compose up -d` with zero-downtime
6. **Health Check** - Verifies `/health` and frontend

### Manual Deployment (Emergency)

```bash
cd /opt/taxtrace-staging

# Pull specific tag
STAGING_TAG=v0.1.0-rc1 docker compose -f docker-compose.staging.yml --env-file .env.staging pull

# Run migrations
docker compose -f docker-compose.staging.yml --env-file .env.staging run --rm backend poetry run alembic upgrade head

# Deploy
docker compose -f docker-compose.staging.yml --env-file .env.staging up -d

# Verify
curl -f http://localhost:8000/health && echo "Backend OK"
curl -f http://localhost:3000 && echo "Frontend OK"
```

### Rollback

```bash
# Rollback to previous version
STAGING_TAG=previous-working-tag docker compose -f docker-compose.staging.yml --env-file .env.staging pull
docker compose -f docker-compose.staging.yml --env-file .env.staging up -d
```

## Monitoring & Health Checks

### Health Endpoints
- Backend: `GET /health` → `{ "status": "ok" }`
- Frontend: `GET /` → 200 OK
- Database: `pg_isready` (Docker healthcheck)

### Logs
```bash
# View all logs
docker compose -f docker-compose.staging.yml logs -f

# Specific service
docker compose -f docker-compose.staging.yml logs -f backend
docker compose -f docker-compose.staging.yml logs -f frontend
```

### Metrics (Prometheus)
- Backend: `http://staging-api.example.com:8000/metrics`
- Scrape interval: 30s

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `alembic` fails | Check DB connectivity, run manually: `docker compose run --rm backend poetry run alembic upgrade head` |
| Frontend 404 | Verify `NEXT_PUBLIC_API_URL` matches backend URL |
| SSL/TLS errors | Use reverse proxy (nginx/Caddy) for TLS termination |
| Out of memory | Increase swap or instance size |
| Permission denied | Ensure user in `docker` group |

## Pipeline Status Badges

Add to README:

```markdown
![CI](https://github.com/eklakhdewan/TaxTrace/actions/workflows/ci-cd.yml/badge.svg)
![Staging](https://img.shields.io/badge/staging-deployed-brightgreen)
```

## Related Files

| File | Purpose |
|------|---------|
| `.github/workflows/ci-cd.yml` | Main CI/CD pipeline |
| `docker-compose.staging.yml` | Staging compose file |
| `.env.staging.example` | Environment template |
| `backend/Dockerfile` | Backend image |
| `frontend/Dockerfile` | Frontend image |