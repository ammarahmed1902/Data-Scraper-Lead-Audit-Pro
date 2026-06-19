# Lead Audit Pro — Complete Folder Hierarchy

```
lead-audit-pro/
│
├── .editorconfig                       # Editor formatting standards
├── .env.example                        # Environment variable template
├── .gitignore                          # Git ignore rules
├── .prettierrc                         # Prettier formatting config
├── docker-compose.yml                  # Development Docker Compose
├── docker-compose.prod.yml             # Production Docker Compose
├── Makefile                            # Common development commands
├── README.md                           # Project overview and quick start
│
├── docs/
│   ├── ARCHITECTURE.md                 # System design and module architecture
│   ├── API.md                          # REST endpoint reference
│   ├── DATABASE.md                     # ERD, tables, indexing strategy
│   ├── DEPLOYMENT.md                   # VPS, DO, AWS, Hetzner guides
│   └── ROADMAP.md                      # Development phases and milestones
│
├── docker/
│   ├── README.md
│   ├── backend/
│   │   └── Dockerfile                  # Python 3.12 multi-stage build
│   ├── frontend/
│   │   └── Dockerfile                  # Node 20 multi-stage build
│   ├── nginx/
│   │   ├── Dockerfile
│   │   ├── nginx.conf                  # Global config, gzip, rate limits
│   │   └── conf.d/
│   │       └── default.conf            # Reverse proxy routing
│   └── postgres/
│       └── init.sql                    # DB extensions (uuid-ossp, pg_trgm)
│
├── backend/
│   ├── README.md
│   ├── requirements.txt                # Python dependencies (pinned versions)
│   ├── pyproject.toml                  # Ruff, pytest, mypy configuration
│   ├── alembic.ini                     # Alembic migration config
│   ├── alembic/
│   │   ├── env.py                      # Migration environment
│   │   └── versions/                   # Migration scripts
│   ├── tests/
│   │   ├── conftest.py                 # Pytest fixtures
│   │   └── test_health.py              # Health endpoint test
│   └── app/
│       ├── __init__.py
│       ├── main.py                     # FastAPI app factory
│       ├── api/
│       │   ├── __init__.py
│       │   └── v1/
│       │       ├── __init__.py
│       │       ├── router.py           # Route aggregation
│       │       ├── auth.py             # /auth endpoints
│       │       ├── users.py            # /users endpoints
│       │       ├── websites.py         # /websites endpoints
│       │       ├── audits.py           # /audits endpoints
│       │       ├── reports.py          # /reports endpoints
│       │       ├── analytics.py        # /analytics endpoints
│       │       └── exports.py          # /exports endpoints
│       ├── core/
│       │   ├── __init__.py
│       │   ├── config.py               # Pydantic Settings
│       │   ├── database.py             # Async SQLAlchemy engine
│       │   ├── security.py             # JWT, RBAC, password hashing
│       │   ├── rate_limit.py           # SlowAPI limiter
│       │   └── middleware.py           # Security headers
│       ├── models/
│       │   ├── __init__.py
│       │   ├── user.py                 # users table
│       │   ├── website.py              # websites table
│       │   ├── audit.py                # audit_reports + sub-reports
│       │   ├── report.py               # reports table
│       │   └── export.py               # export_history table
│       ├── schemas/
│       │   ├── __init__.py
│       │   ├── common.py               # Pagination, shared types
│       │   ├── auth.py                 # Login, register, tokens
│       │   ├── user.py                 # User CRUD schemas
│       │   ├── website.py              # Website CRUD schemas
│       │   ├── audit.py                # Audit + sub-report schemas
│       │   ├── report.py               # Report + export schemas
│       │   └── analytics.py            # Dashboard analytics schemas
│       ├── repositories/
│       │   ├── __init__.py
│       │   ├── base.py                 # Generic CRUD repository
│       │   ├── user_repository.py
│       │   ├── website_repository.py
│       │   └── audit_repository.py
│       ├── services/
│       │   ├── __init__.py
│       │   ├── audit_service.py        # Audit orchestration
│       │   ├── seo_service.py          # SEO analysis
│       │   ├── performance_service.py  # Performance analysis
│       │   └── report_service.py       # Report generation
│       ├── workers/
│       │   ├── celery_worker.py        # Celery app configuration
│       │   └── tasks.py                # Background task definitions
│       └── utils/
│           └── helpers.py              # URL normalization, validation
│
└── frontend/
    ├── README.md
    ├── package.json                    # Node dependencies
    ├── tsconfig.json                   # TypeScript config (strict)
    ├── next.config.ts                  # Next.js config (standalone)
    ├── tailwind.config.ts              # Tailwind + design tokens
    ├── postcss.config.mjs
    ├── components.json                 # Shadcn UI config
    ├── eslint.config.mjs               # ESLint flat config
    ├── next-env.d.ts
    └── src/
        ├── app/                        # Next.js App Router
        │   ├── layout.tsx              # Root layout + providers
        │   ├── page.tsx                # Redirect to /dashboard
        │   ├── dashboard/
        │   │   └── page.tsx            # Dashboard overview
        │   ├── websites/
        │   │   └── page.tsx            # Website management
        │   ├── reports/
        │   │   └── page.tsx            # Report listing
        │   ├── analytics/
        │   │   └── page.tsx            # Analytics charts
        │   ├── settings/
        │   │   └── page.tsx            # User preferences
        │   └── auth/
        │       ├── login/
        │       │   └── page.tsx        # Login page
        │       └── register/
        │           └── page.tsx        # Registration page
        ├── components/
        │   ├── providers.tsx           # React Query provider
        │   ├── ui/
        │   │   ├── button.tsx          # Shadcn Button (+ glass variant)
        │   │   ├── card.tsx            # Shadcn Card
        │   │   └── input.tsx           # Shadcn Input
        │   ├── layout/
        │   │   ├── sidebar.tsx         # Navigation sidebar
        │   │   ├── header.tsx          # Top bar with search
        │   │   └── dashboard-shell.tsx # Dashboard layout wrapper
        │   ├── dashboard/
        │   │   ├── stat-card.tsx       # Metric stat cards
        │   │   └── page-header.tsx     # Page title + actions
        │   ├── tables/                 # Data tables (Phase 03)
        │   ├── charts/                 # Recharts wrappers (Phase 05)
        │   ├── forms/                  # Form components (Phase 03)
        │   └── animations/
        │       └── fade-in.tsx         # Framer Motion wrappers
        ├── hooks/
        │   ├── use-auth.ts             # Auth state hook
        │   ├── use-media-query.ts      # Responsive breakpoints
        │   └── use-require-auth.ts     # Route protection
        ├── lib/
        │   ├── utils.ts                # cn() class merger
        │   ├── api-client.ts           # HTTP client with auth
        │   ├── query-client.ts         # React Query config
        │   └── design-tokens.ts        # Programmatic design tokens
        ├── services/
        │   ├── auth-service.ts         # Auth API calls
        │   ├── website-service.ts      # Website API calls
        │   └── analytics-service.ts    # Analytics API calls
        ├── store/
        │   ├── auth-store.ts           # Zustand: authentication
        │   ├── dashboard-store.ts      # Zustand: dashboard UI
        │   └── ui-store.ts             # Zustand: theme, modals
        ├── styles/
        │   └── globals.css             # Design tokens + glassmorphism
        ├── types/
        │   └── index.ts                # TypeScript interfaces
        └── utils/
            └── format.ts               # Date, score formatting
```

## File Count Summary

| Area | Files | Status |
|------|-------|--------|
| Backend (Python) | 45+ | Scaffolded |
| Frontend (TypeScript) | 40+ | Scaffolded |
| Docker | 7 | Configured |
| Documentation | 6 | Complete |
| Config/Root | 8 | Complete |
