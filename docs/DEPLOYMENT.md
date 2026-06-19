# Lead Audit Pro — Deployment Architecture

## Container Topology (Production)

```mermaid
flowchart TB
    Internet["Internet"] --> Nginx["Nginx :80/:443"]
    Nginx --> Frontend["Frontend :3000"]
    Nginx -->|"/api/*"| Backend["Backend :8000"]
    Backend --> Postgres["PostgreSQL :5432"]
    Backend --> Redis["Redis :6379"]
    Worker["Celery Worker"] --> Postgres
    Worker --> Redis
    Beat["Celery Beat"] --> Redis
```

## Docker Services

| Service | Image | Port (dev) | Purpose |
|---------|-------|------------|---------|
| `postgres` | postgres:16-alpine | 5432 | Primary database |
| `redis` | redis:7-alpine | 6379 | Cache + Celery broker |
| `backend` | Custom (Python 3.12) | 8000 | FastAPI API server |
| `celery_worker` | Custom (Python 3.12) | — | Background task processing |
| `celery_beat` | Custom (Python 3.12) | — | Scheduled tasks |
| `frontend` | Custom (Node 20) | 3000 | Next.js application |
| `nginx` | nginx:1.25-alpine | 80, 443 | Reverse proxy (prod only) |

## Commands

```bash
# Development
docker compose up -d
docker compose logs -f backend

# Production
docker compose -f docker-compose.prod.yml up -d --build
docker compose -f docker-compose.prod.yml exec backend alembic upgrade head

# Scale workers
docker compose -f docker-compose.prod.yml up -d --scale celery_worker=4
```

---

## VPS Deployment (Generic)

### Prerequisites

- Ubuntu 22.04+ or Debian 12+
- 4 GB RAM minimum (8 GB recommended)
- Docker Engine 24+ and Docker Compose v2
- Domain with DNS A record pointing to server IP

### Steps

```bash
# 1. Server setup
apt update && apt upgrade -y
curl -fsSL https://get.docker.com | sh
usermod -aG docker $USER

# 2. Clone and configure
git clone <repo-url> /opt/lead-audit-pro
cd /opt/lead-audit-pro
cp .env.example .env
# Edit .env with production secrets

# 3. SSL certificates (Let's Encrypt)
apt install certbot
certbot certonly --standalone -d yourdomain.com
cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem docker/nginx/ssl/
cp /etc/letsencrypt/live/yourdomain.com/privkey.pem docker/nginx/ssl/

# 4. Deploy
docker compose -f docker-compose.prod.yml up -d --build
docker compose -f docker-compose.prod.yml exec backend alembic upgrade head

# 5. Verify
curl https://yourdomain.com/health
```

### Recommended Specs

| Tier | CPU | RAM | Storage | Monthly Cost |
|------|-----|-----|---------|-------------|
| Starter | 2 vCPU | 4 GB | 80 GB SSD | $20–40 |
| Growth | 4 vCPU | 8 GB | 160 GB SSD | $40–80 |
| Scale | 8 vCPU | 16 GB | 320 GB SSD | $80–160 |

---

## DigitalOcean Deployment

### Droplet Setup

1. Create Droplet: **Ubuntu 24.04**, 4 GB RAM / 2 vCPU ($24/mo)
2. Enable monitoring and automated backups
3. Add firewall rules: allow 22, 80, 443

### Managed Database (Optional)

Replace self-hosted PostgreSQL with DigitalOcean Managed PostgreSQL:

```env
DATABASE_URL=postgresql+asyncpg://user:pass@db-host:25060/lead_audit_pro?sslmode=require
DATABASE_URL_SYNC=postgresql://user:pass@db-host:25060/lead_audit_pro?sslmode=require
```

Remove `postgres` service from `docker-compose.prod.yml` when using managed DB.

### Managed Redis (Optional)

```env
REDIS_URL=rediss://default:pass@redis-host:25061
CELERY_BROKER_URL=rediss://default:pass@redis-host:25061/1
CELERY_RESULT_BACKEND=rediss://default:pass@redis-host:25061/2
```

### Load Balancer

For multi-instance deployment:
1. Create DO Load Balancer ($12/mo)
2. Add 2+ Droplets as backend targets
3. Health check: `GET /health` on port 80

---

## AWS Deployment

### Architecture

```mermaid
flowchart TB
    Route53["Route 53"] --> ALB["Application Load Balancer"]
    ALB --> ECS["ECS Fargate Cluster"]
    ECS --> API["API Service"]
    ECS --> Worker["Worker Service"]
    ECS --> Frontend["Frontend Service"]
    API --> RDS["RDS PostgreSQL"]
    API --> ElastiCache["ElastiCache Redis"]
    Worker --> RDS
    Worker --> ElastiCache
    S3["S3 Bucket"] --> Reports["Report Storage"]
```

### Services Mapping

| Component | AWS Service | Notes |
|-----------|------------|-------|
| API + Workers | ECS Fargate | Use existing Dockerfiles |
| Frontend | ECS Fargate or Amplify | Standalone Next.js output |
| Database | RDS PostgreSQL 16 | db.t3.medium minimum |
| Cache/Queue | ElastiCache Redis 7 | cache.t3.micro for dev |
| File Storage | S3 | Audit reports and exports |
| DNS | Route 53 | |
| TLS | ACM | Free certificates |
| Secrets | Secrets Manager | JWT keys, DB credentials |

### Estimated Monthly Cost (Starter)

| Service | Cost |
|---------|------|
| ECS Fargate (3 tasks) | ~$45 |
| RDS db.t3.medium | ~$50 |
| ElastiCache t3.micro | ~$15 |
| ALB | ~$20 |
| S3 + data transfer | ~$5 |
| **Total** | **~$135/mo** |

---

## Hetzner Deployment

Hetzner offers the best price-to-performance ratio for European deployments.

### Server Selection

| Plan | Specs | Price | Use Case |
|------|-------|-------|----------|
| CX22 | 2 vCPU, 4 GB | €4.35/mo | Development/staging |
| CX32 | 4 vCPU, 8 GB | €7.59/mo | Production (recommended) |
| CX42 | 8 vCPU, 16 GB | €14.39/mo | High-volume audits |

### Setup

```bash
# Hetzner Cloud server (Ubuntu 24.04, Falkenstein or Nuremberg)
# Same VPS steps as above

# Hetzner Object Storage for reports (S3-compatible)
# Endpoint: https://fsn1.your-objectstorage.com
```

### Hetzner-Specific Tips

- Use Hetzner Cloud Firewall (free) instead of ufw
- Enable automatic snapshots (€0.012/GB/mo)
- Place server in same region as target audience
- Consider Hetzner Load Balancer (€5.39/mo) for HA

---

## Environment Variables (Production Checklist)

| Variable | Action |
|----------|--------|
| `APP_SECRET_KEY` | Generate 64-char random string |
| `JWT_SECRET_KEY` | Generate 32+ char random string |
| `CSRF_SECRET_KEY` | Generate 32+ char random string |
| `POSTGRES_PASSWORD` | Strong unique password |
| `APP_DEBUG` | Set to `false` |
| `APP_ENV` | Set to `production` |
| `CORS_ORIGINS` | Set to production domain only |
| `CELERY_TASK_ALWAYS_EAGER` | Set to `false` |

Generate secrets:

```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

---

## Backup Strategy

| Data | Method | Frequency | Retention |
|------|--------|-----------|-----------|
| PostgreSQL | `pg_dump` via cron | Daily | 30 days |
| Redis | AOF persistence | Continuous | 7 days |
| Report files | S3/Object Storage sync | Daily | 90 days |
| Docker volumes | Snapshot | Weekly | 4 weeks |

```bash
# PostgreSQL backup cron
0 2 * * * docker compose exec -T postgres pg_dump -U leadaudit lead_audit_pro | gzip > /backups/db_$(date +\%Y\%m\%d).sql.gz
```

---

## Monitoring (Phase 02+)

| Tool | Purpose |
|------|---------|
| Health endpoint (`/health`) | Uptime monitoring |
| Docker logs | Application debugging |
| Prometheus + Grafana | Metrics (future) |
| Sentry | Error tracking (future) |
