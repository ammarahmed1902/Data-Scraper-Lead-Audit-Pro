# Phase 01 — Lead Discovery Engine

## Overview

Automated lead discovery by **industry keyword**, **country**, **state**, and **city**.  
Searches public OpenStreetMap business data and supplemental web search results, enriches websites for email/social profiles, deduplicates results, and processes everything via Celery background workers.

## Database Schema

### `lead_discovery_searches`
| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| user_id | UUID FK → users | Search owner |
| industry_keyword | VARCHAR(255) | e.g. "Dentist" |
| country | VARCHAR(100) | e.g. "USA" |
| state | VARCHAR(100) | Optional |
| city | VARCHAR(100) | Optional |
| status | VARCHAR(50) | pending, running, completed, failed |
| total_found | INT | All records processed |
| total_new | INT | Non-duplicate leads |
| total_duplicates | INT | Skipped duplicates |
| pages_processed | INT | Pagination progress |
| celery_task_id | VARCHAR | Background task ID |
| started_at / completed_at | TIMESTAMPTZ | Timing |

### `discovered_leads`
| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| search_id | UUID FK | Parent search |
| user_id | UUID FK | Owner |
| business_name | VARCHAR(500) | Business name |
| website_url | VARCHAR(2048) | Website |
| domain | VARCHAR(255) | Normalized domain |
| business_category | VARCHAR(255) | Category |
| address, city, state, country | VARCHAR | Location |
| phone_number | VARCHAR(50) | Phone |
| email_address | VARCHAR(255) | Email (public) |
| social_profiles | JSONB | facebook, linkedin, etc. |
| source | VARCHAR(100) | openstreetmap, web_search |
| dedup_key | VARCHAR(255) | Duplicate detection key |
| is_duplicate | BOOL | Duplicate flag |
| imported_website_id | UUID FK | Linked website after import |

**Unique constraint:** `(search_id, dedup_key)`

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/discovery/searches` | Start search (202, rate limited 5/min) |
| GET | `/api/v1/discovery/searches` | Search history (paginated) |
| GET | `/api/v1/discovery/searches/{id}` | Search status |
| GET | `/api/v1/discovery/searches/{id}/leads` | Discovered leads (paginated) |
| POST | `/api/v1/discovery/leads/{id}/import` | Import lead → websites |

## Architecture

```
Frontend (/discovery)
  → POST /discovery/searches
  → LeadDiscoveryService.create_search()
  → DB commit
  → Celery run_discovery_search
  → LeadDiscoveryRunner
  → LeadDiscoveryEngine
      → OSMBusinessProvider (Nominatim + Overpass)
      → WebSearchProvider (DuckDuckGo HTML)
      → LeadEnrichmentService (email/social from websites)
      → Dedup by domain / phone / name+city
```

## Configuration

```env
DISCOVERY_USER_AGENT=LeadAuditPro/1.0 (contact@leadaudit.pro)
DISCOVERY_REQUEST_DELAY_SECONDS=1.0
DISCOVERY_MAX_RESULTS_PER_SEARCH=100
DISCOVERY_MAX_PAGES_PER_SEARCH=3
DISCOVERY_PAGE_SIZE=50
DISCOVERY_ENRICH_WEBSITES=true
CELERY_TASK_ALWAYS_EAGER=true  # dev without Redis worker
```

## Migration

```bash
cd backend
alembic upgrade head
```

## Frontend

- **Route:** `/discovery`
- **Sidebar:** Lead Discovery
- Search form, history panel, results table with import-to-websites

## Duplicate Detection

1. **Domain** (primary)
2. **Phone** (normalized digits)
3. **Name + city** hash (fallback)

Duplicates are flagged within the same search and across prior searches for the same user.
