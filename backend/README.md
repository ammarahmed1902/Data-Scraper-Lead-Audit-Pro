# Backend

FastAPI application following clean architecture principles.

## Directory Guide

```
app/
├── api/v1/             # REST API route handlers (thin controllers)
│   ├── auth.py         # Authentication endpoints
│   ├── users.py        # User management
│   ├── websites.py     # Website CRUD
│   ├── audits.py       # Audit management
│   ├── reports.py      # Report generation
│   ├── analytics.py    # Dashboard analytics
│   └── exports.py      # Data exports
│
├── core/               # Infrastructure configuration
│   ├── config.py       # Pydantic Settings (env vars)
│   ├── database.py     # SQLAlchemy async engine + session
│   ├── security.py     # JWT, password hashing, RBAC
│   ├── rate_limit.py   # SlowAPI rate limiter
│   └── middleware.py   # Security headers middleware
│
├── models/             # SQLAlchemy ORM models (domain entities)
├── schemas/            # Pydantic request/response schemas
├── repositories/       # Data access layer (CRUD + queries)
├── services/           # Business logic layer
├── workers/            # Celery task definitions
└── utils/              # Shared helper functions
```

## Layer Rules

1. **Routes** validate input via schemas, call services, return responses
2. **Services** contain business logic, call repositories
3. **Repositories** handle database queries, return models
4. **Models** define table structure and relationships
5. **Workers** call services for background processing

## Commands

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload                    # Dev server
alembic revision --autogenerate -m "message"     # New migration
alembic upgrade head                             # Apply migrations
celery -A app.workers.celery_worker worker       # Start worker
pytest                                           # Run tests
ruff check app tests                             # Lint
```
