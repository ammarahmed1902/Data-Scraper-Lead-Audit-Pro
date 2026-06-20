# Phase 02 — Business Data Enrichment

## Overview

Enriches discovered businesses by crawling their websites and extracting structured data: company info, contact details, services, team, technology stack, and CMS detection. Processing runs asynchronously via Celery on the `enrichment` queue.

## Database Schema

### `enrichment_jobs`
| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| user_id | UUID FK → users | Job owner |
| job_type | VARCHAR(50) | `single_lead` or `search_bulk` |
| lead_id | UUID FK | Target lead (single jobs) |
| search_id | UUID FK | Target search (bulk jobs) |
| status | VARCHAR(50) | pending, running, completed, failed |
| total_leads | INT | Leads to process |
| processed_leads | INT | Completed count |
| failed_leads | INT | Failed count |
| celery_task_id | VARCHAR | Background task ID |
| started_at / completed_at | TIMESTAMPTZ | Timing |

### `business_enrichments`
| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| lead_id | UUID FK → discovered_leads | 1:1 with lead |
| user_id | UUID FK | Owner |
| job_id | UUID FK | Parent job |
| status | VARCHAR(50) | pending, running, completed, failed |
| company_name | VARCHAR(500) | Extracted name |
| about_us_content | TEXT | About page text |
| services | JSONB | List of services |
| contact_page_data | JSONB | Address, hours, labeled fields |
| email_addresses | JSONB | Extracted emails |
| phone_numbers | JSONB | Extracted phones |
| team_members | JSONB | Name + title pairs |
| business_description | TEXT | Meta / summary description |
| technology_stack | JSONB | Detected technologies |
| cms_platform | VARCHAR(100) | Primary CMS |
| cms_detected | JSONB | WordPress, Shopify, Wix, etc. |
| pages_crawled | JSONB | URLs visited |
| raw_extraction | JSONB | Debug metadata |

**Unique constraint:** `lead_id` (one enrichment record per lead)

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/enrichment/leads/{lead_id}` | Enrich single lead (202, 10/min) |
| POST | `/api/v1/enrichment/searches/{search_id}` | Bulk enrich search (202, 5/min) |
| GET | `/api/v1/enrichment/jobs/{job_id}` | Job status & progress |
| GET | `/api/v1/enrichment/leads/{lead_id}` | Full enrichment data |
| GET | `/api/v1/enrichment/enrichments` | List enrichments (paginated) |

## Architecture

```
Frontend (/discovery)
  → POST /enrichment/leads/{id} or /enrichment/searches/{id}
  → EnrichmentService (commit before queue)
  → Celery run_enrichment_job
  → EnrichmentRunner
  → BusinessEnrichmentEngine
      → WebsiteCrawler (home, about, services, contact, team)
      → ContentExtractor (emails, phones, services, team)
      → TechStackDetector (CMS + stack)
  → business_enrichments table
```

## CMS Detection

Detects: WordPress, Shopify, Wix, Squarespace, Webflow, React, Next.js, Laravel, PHP

Signals: HTML markers, CDN URLs, meta tags, `X-Powered-By`, `Server` headers.

## Configuration

```env
ENRICHMENT_REQUEST_DELAY_SECONDS=0.75
ENRICHMENT_MAX_PAGES=6
ENRICHMENT_FETCH_TIMEOUT_SECONDS=20.0
CELERY_TASK_ALWAYS_EAGER=true  # dev — runs inline without Redis worker
```

## Permissions

- `enrichment:run` — ADMIN, MANAGER, ANALYST
- `enrichment:view` — all roles including VIEWER

## Frontend

Integrated into `/discovery`:
- **Enrich** button per lead with website
- **Enrich All** bulk action on completed searches
- **View** dialog showing full enrichment data
- Job polling for bulk enrichment progress

## Running

```powershell
# Apply migration
cd backend
alembic upgrade head

# Start API
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload

# Start Celery worker (production)
celery -A app.workers.celery_worker worker -Q enrichment,discovery,audits -l info
```
