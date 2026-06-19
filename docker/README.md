# Docker Configuration

Container definitions and orchestration for Lead Audit Pro.

## Structure

```
docker/
├── backend/
│   └── Dockerfile          # Multi-stage: development + production
├── frontend/
│   └── Dockerfile          # Multi-stage: deps → builder → production
├── nginx/
│   ├── Dockerfile
│   ├── nginx.conf          # Global Nginx config (gzip, rate limits)
│   └── conf.d/
│       └── default.conf    # Reverse proxy rules
└── postgres/
    └── init.sql            # Extensions (uuid-ossp, pg_trgm, citext)
```

## Compose Files

| File | Purpose |
|------|---------|
| `docker-compose.yml` | Development with hot reload and volume mounts |
| `docker-compose.prod.yml` | Production with Nginx, Gunicorn, no volume mounts |

## Development

```bash
docker compose up -d              # Start all services
docker compose logs -f backend    # Tail backend logs
docker compose exec backend bash  # Shell into backend
docker compose down -v            # Stop and remove volumes
```

## Production

```bash
docker compose -f docker-compose.prod.yml up -d --build
docker compose -f docker-compose.prod.yml exec backend alembic upgrade head
```

## Network Architecture (Production)

- `lap_internal` — Private network for service-to-service communication
- `lap_external` — Only Nginx exposed to the internet
- PostgreSQL and Redis are NOT exposed externally in production
