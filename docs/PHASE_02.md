# Phase 02 — Database & Authentication

## Deliverables

### Database Layer
- Alembic initial migration (`001_initial_schema.py`) — all 8 tables
- SQLAlchemy models (from Phase 01, unchanged)
- PostgreSQL extensions via `docker/postgres/init.sql`

### Authentication APIs
| Endpoint | Status |
|----------|--------|
| `POST /auth/register` | Implemented |
| `POST /auth/login` | Implemented |
| `POST /auth/refresh` | Implemented with token rotation |
| `POST /auth/logout` | Implemented with Redis revocation |
| `GET /auth/me` | Implemented |

### User Management APIs
| Endpoint | Role Required |
|----------|---------------|
| `GET /users` | admin |
| `GET /users/{id}` | manager (own profile for non-admins) |
| `POST /users` | admin |
| `PUT /users/{id}` | admin |
| `DELETE /users/{id}` | admin (soft deactivate) |

### Security Implementation
- JWT access tokens (30 min) with `jti` claim
- Refresh tokens (7 days) stored in Redis with rotation
- Access token blacklist on logout (Redis)
- bcrypt password hashing
- RBAC with 5 roles and permission matrix
- Rate limiting on auth endpoints

## Setup Commands

```bash
# Start infrastructure
docker compose up -d postgres redis

# Run migrations
cd backend
alembic upgrade head

# Seed super admin
python -m scripts.seed_admin

# Default credentials (change in production!)
# Email: admin@leadaudit.pro
# Password: Admin123!ChangeMe
```

## Running Tests

```bash
cd backend
pytest tests/test_auth_service.py tests/test_permissions.py tests/test_health.py -v
```

## Frontend Auth Flow

1. User submits login/register form
2. Tokens stored in Zustand (persisted to localStorage)
3. Auth cookie set for middleware route protection
4. API client auto-refreshes on 401
5. Logout revokes tokens server-side and clears client state

## Permission Matrix

See `backend/app/core/permissions.py` for the full `ROLE_PERMISSIONS` mapping.

| Role | Level | Can Manage Users |
|------|-------|-----------------|
| super_admin | 100 | All roles |
| admin | 80 | manager, analyst, viewer |
| manager | 60 | — |
| analyst | 40 | — |
| viewer | 20 | — |
