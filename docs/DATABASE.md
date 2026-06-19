# Lead Audit Pro — Database Architecture

## Entity Relationship Diagram

```mermaid
erDiagram
    users ||--o{ websites : owns
    users ||--o{ audit_reports : creates
    users ||--o{ export_history : requests

    websites ||--o{ audit_reports : has

    audit_reports ||--o| seo_reports : contains
    audit_reports ||--o| performance_reports : contains
    audit_reports ||--o| technical_reports : contains
    audit_reports ||--o{ reports : generates

    users {
        uuid id PK
        varchar email UK
        varchar hashed_password
        varchar full_name
        varchar role
        boolean is_active
        boolean is_verified
        varchar avatar_url
        varchar phone
        varchar timezone
        timestamptz last_login_at
        timestamptz created_at
        timestamptz updated_at
    }

    websites {
        uuid id PK
        uuid owner_id FK
        varchar url
        varchar domain
        varchar company_name
        varchar contact_name
        varchar contact_email
        varchar contact_phone
        varchar industry
        varchar status
        text notes
        text tags
        timestamptz last_audited_at
        timestamptz created_at
        timestamptz updated_at
    }

    audit_reports {
        uuid id PK
        uuid website_id FK
        uuid created_by FK
        varchar status
        float overall_score
        text summary
        jsonb raw_data
        text error_message
        varchar celery_task_id
        timestamptz started_at
        timestamptz completed_at
        timestamptz created_at
    }

    seo_reports {
        uuid id PK
        uuid audit_report_id FK UK
        float score
        varchar title_tag
        text meta_description
        int h1_count
        int internal_links
        int external_links
        int broken_links
        boolean has_sitemap
        boolean has_robots_txt
        boolean mobile_friendly
        jsonb issues
        jsonb recommendations
        timestamptz created_at
    }

    performance_reports {
        uuid id PK
        uuid audit_report_id FK UK
        float score
        float load_time_ms
        float first_contentful_paint
        float largest_contentful_paint
        float time_to_interactive
        float total_blocking_time
        float cumulative_layout_shift
        float page_size_kb
        int request_count
        jsonb metrics
        jsonb recommendations
        timestamptz created_at
    }

    technical_reports {
        uuid id PK
        uuid audit_report_id FK UK
        float score
        boolean ssl_valid
        timestamptz ssl_expiry
        int http_status_code
        varchar server_header
        jsonb technologies
        jsonb security_headers
        jsonb dns_records
        jsonb issues
        jsonb recommendations
        timestamptz created_at
    }

    reports {
        uuid id PK
        uuid audit_report_id FK
        varchar title
        varchar format
        varchar file_path
        int file_size_bytes
        timestamptz generated_at
        timestamptz expires_at
    }

    export_history {
        uuid id PK
        uuid user_id FK
        varchar export_type
        varchar format
        varchar status
        jsonb filters
        varchar file_path
        int file_size_bytes
        int record_count
        text error_message
        varchar celery_task_id
        timestamptz started_at
        timestamptz completed_at
        timestamptz created_at
    }
```

---

## Table Reference

### `users`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK, default uuid4 | Primary key |
| email | VARCHAR(255) | UNIQUE, NOT NULL | Login identifier |
| hashed_password | VARCHAR(255) | NOT NULL | bcrypt hash |
| full_name | VARCHAR(255) | NOT NULL | Display name |
| role | VARCHAR(50) | NOT NULL, default `viewer` | RBAC role |
| is_active | BOOLEAN | NOT NULL, default true | Account status |
| is_verified | BOOLEAN | NOT NULL, default false | Email verification |
| avatar_url | VARCHAR(500) | NULL | Profile image URL |
| phone | VARCHAR(50) | NULL | Contact phone |
| timezone | VARCHAR(50) | NOT NULL, default `UTC` | User timezone |
| last_login_at | TIMESTAMPTZ | NULL | Last successful login |
| created_at | TIMESTAMPTZ | NOT NULL | Record creation |
| updated_at | TIMESTAMPTZ | NOT NULL | Last modification |

**Indexes:** `email`, `role`, composite `(role, is_active)`

---

### `websites`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK | Primary key |
| owner_id | UUID | FK → users.id, CASCADE | Owning user |
| url | VARCHAR(2048) | NOT NULL | Full website URL |
| domain | VARCHAR(255) | NOT NULL | Extracted domain |
| company_name | VARCHAR(255) | NULL | Lead company |
| contact_name | VARCHAR(255) | NULL | Contact person |
| contact_email | VARCHAR(255) | NULL | Contact email |
| contact_phone | VARCHAR(50) | NULL | Contact phone |
| industry | VARCHAR(100) | NULL | Industry category |
| status | VARCHAR(50) | NOT NULL, default `pending` | Audit pipeline status |
| notes | TEXT | NULL | Free-form notes |
| tags | TEXT | NULL | JSON array of tags |
| last_audited_at | TIMESTAMPTZ | NULL | Most recent audit |
| created_at | TIMESTAMPTZ | NOT NULL | Record creation |
| updated_at | TIMESTAMPTZ | NOT NULL | Last modification |

**Indexes:** `owner_id`, `domain`, `status`, composite `(owner_id, status)`, `created_at`, `domain` (pg_trgm for fuzzy search)

---

### `audit_reports`

Parent record for each audit execution. One website can have many audit reports (historical).

**Indexes:** `website_id`, `created_by`, `status`, `celery_task_id`, composite `(website_id, status)`, `created_at`, `overall_score`

---

### Sub-Report Tables

`seo_reports`, `performance_reports`, and `technical_reports` each have a **1:1** relationship with `audit_reports` via `audit_report_id` (UNIQUE FK).

---

### `reports`

Generated output files (PDF, HTML, JSON, CSV) linked to audit reports.

**Indexes:** composite `(audit_report_id, format)`

---

### `export_history`

Tracks bulk data export jobs initiated by users.

**Indexes:** `user_id`, `export_type`, `status`, composite `(user_id, status)`, `created_at`

---

## Indexing Strategy

| Table | Index | Purpose |
|-------|-------|---------|
| users | `email` | Login lookup |
| users | `(role, is_active)` | Admin user listing |
| websites | `(owner_id, status)` | Dashboard filtered lists |
| websites | `domain` + pg_trgm | Fuzzy domain search at 10K+ scale |
| websites | `created_at` | Chronological sorting |
| audit_reports | `(website_id, status)` | Website audit history |
| audit_reports | `created_at` | Time-range analytics queries |
| audit_reports | `overall_score` | Score distribution charts |
| audit_reports | `celery_task_id` | Task status polling |
| export_history | `(user_id, status)` | User export dashboard |

---

## Migration Management

Migrations are managed via **Alembic**:

```bash
# Generate migration after model changes
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback one step
alembic downgrade -1
```

Migration files live in `backend/alembic/versions/`.

---

## Data Volume Projections

| Entity | Expected Volume | Retention |
|--------|----------------|-----------|
| users | 100–1,000 | Permanent |
| websites | 10,000+ | Permanent (archive status) |
| audit_reports | 100,000+ | 12 months active, then archive |
| sub-reports | 300,000+ (3 per audit) | Tied to audit retention |
| reports (files) | 50,000+ | 90-day expiry |
| export_history | 10,000+ | 30-day cleanup |
