# Phase 03 — Website Audit Engine

## Overview

Full website audit pipeline covering **SEO**, **Performance** (Lighthouse / Core Web Vitals), and **Technical** (SSL, security headers, mobile, accessibility, indexability). Results are stored in PostgreSQL and processed asynchronously via Celery.

## Audit Categories

### SEO Audit
| Check | Storage |
|-------|---------|
| Meta Title | `seo_reports.title_tag` |
| Meta Description | `seo_reports.meta_description` |
| H1 Tags | `seo_reports.h1_count` + `issues.meta.h1_tags` |
| H2 Tags | `seo_reports.h2_count` + `issues.meta.h2_tags` |
| Canonical Tags | `seo_reports.canonical_url` |
| Robots.txt | `seo_reports.has_robots_txt` |
| Sitemap.xml | `seo_reports.has_sitemap` |
| Internal Links | `seo_reports.internal_links` |
| Broken Links | `seo_reports.broken_links` (sampled, max 15) |

### Performance Audit
| Metric | Storage |
|--------|---------|
| Lighthouse Score | `performance_reports.score` (via PageSpeed API) |
| LCP | `performance_reports.largest_contentful_paint` |
| FCP | `performance_reports.first_contentful_paint` |
| CLS | `performance_reports.cumulative_layout_shift` |
| TTFB | `performance_reports.metrics.ttfb` |
| Issues | `performance_reports.issues` |

### Technical Audit
| Check | Storage |
|-------|---------|
| SSL | `technical_reports.ssl_valid`, `ssl_expiry` |
| HTTPS | `issues.meta.uses_https` |
| Security Headers | `technical_reports.security_headers` |
| Mobile Friendliness | `technical_reports.mobile_friendly` |
| Accessibility | `technical_reports.accessibility_score` |
| Indexability | `technical_reports.indexable` |

## Scoring

| Score | Calculation |
|-------|-------------|
| SEO Score | 100 − weighted issue deductions |
| Performance Score | Lighthouse × 100, or HTTP fallback heuristic |
| Technical Score | 65% security/SSL + 35% accessibility (blended) |
| **Overall Score** | Average of SEO + Performance + Technical |

## Database Tables

- `audit_reports` — job status, overall score, summary, celery task
- `seo_reports` — SEO metrics (1:1 with audit)
- `performance_reports` — CWV metrics + issues (1:1)
- `technical_reports` — SSL, headers, accessibility (1:1)

Migration `004_audit_enhancements` adds: `h2_count`, `canonical_url`, `performance_reports.issues`, `accessibility_score`, `mobile_friendly`, `indexable`.

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/audits` | Audit a website (202) |
| POST | `/api/v1/audits/bulk` | Bulk audit up to 100 websites |
| POST | `/api/v1/audits/leads/{lead_id}` | Import lead (optional) + audit |
| GET | `/api/v1/audits` | List audits (paginated) |
| GET | `/api/v1/audits/{id}` | Full audit with sub-reports |
| GET | `/api/v1/audits/{id}/status` | Poll status |
| DELETE | `/api/v1/audits/{id}` | Cancel pending/running |

## Architecture

```
POST /audits or /audits/leads/{id}
  → AuditService (commit before queue)
  → Celery run_audit
  → AuditRunner
      → PageFetcher (single fetch)
      → SEOAnalyzer
      → PerformanceAnalyzer (+ PageSpeed Lighthouse)
      → TechnicalAnalyzer (+ AccessibilityAnalyzer)
      → AIReportService (executive summary)
  → seo_reports + performance_reports + technical_reports
```

## Configuration

```env
PAGESPEED_API_KEY=your_google_api_key   # Enables real Lighthouse + CWV
CELERY_TASK_ALWAYS_EAGER=true           # Dev inline execution
AUDIT_MAX_RETRIES=3
```

## Frontend

- `/audits` — audit history list
- `/audits/[id]` — detail view with SEO / Performance / Technical tabs
- **Websites** page — run audit, redirects to detail
- **Discovery** page — audit discovered lead (auto-imports to websites)

## Running

```powershell
cd backend
python -m alembic upgrade head
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
celery -A app.workers.celery_worker worker -Q audits -l info
```

```powershell
cd frontend
npm run dev
```

## Tests

```powershell
cd backend
python -m pytest tests/test_seo_service.py tests/test_accessibility.py -v
```
