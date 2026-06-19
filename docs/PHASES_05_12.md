# Phases 05–12 — Audit Engines, Reports & Production

## Phase 05 — SEO Audit Engine ✅

**Service:** `app/services/seo_service.py`

Analyzes: meta title, meta description, H1/H2/H3, alt tags, sitemap, robots.txt, canonical, Open Graph, structured data (JSON-LD), internal/external links, broken links (sampled).

**Output:** SEO score (0–100), issues list, recommendations, stored in `seo_reports`.

## Phase 06 — Performance Audit Engine ✅

**Service:** `app/services/performance_service.py`

Integrations: Google PageSpeed Insights API (when `PAGESPEED_API_KEY` set), HTTP timing fallback.

Analyzes: LCP, FCP, CLS, TTFB, Speed Index, load time, page size.

**Output:** Performance score, metrics JSON, recommendations in `performance_reports`.

## Phase 07 — Technical Audit Engine ✅

**Service:** `app/services/technical_service.py`

Analyzes: SSL validity/expiry, HTTPS, security headers, mobile viewport, crawlability, indexability, technology detection, DNS.

**Output:** Technical score, issues, recommendations in `technical_reports`.

## Phase 08 — AI Report Generator ✅

**Service:** `app/services/ai_report_service.py`

Generates executive summary, sales opportunity summary. Uses OpenAI when `OPENAI_API_KEY` is set; falls back to rule-based templates.

Stored in `audit_reports.summary`.

## Phase 09 — PDF Report System ✅

**Services:** `app/services/pdf_service.py`, `app/services/report_service.py`

Features: multi-section PDF (executive summary, scores, SEO/perf/technical breakdown, recommendations).

**APIs:** `POST /reports`, `GET /reports/{id}/download`

## Phase 10 — Dashboard & Analytics ✅

**Backend:** `app/services/analytics_service.py` — overview stats, trends, score distribution, top issues.

**Frontend:** Dashboard widgets, Analytics charts (Recharts), live data from `/analytics/*`.

## Phase 11 — Export & Lead Management ✅

**Service:** `app/services/export_runner.py`

Exports websites + latest audit data in one file (CSV, XLSX, JSON). Lead priority scoring (high/medium/low/unaudited).

**APIs:** `POST /exports`, `GET /exports/{id}/download`

## Phase 12 — Production Deployment ✅

- Docker Compose (dev + prod)
- Nginx reverse proxy
- GitHub Actions CI (`.github/workflows/ci.yml`)
- Scalable architecture: Celery queues, connection pooling, indexed queries

See `docs/DEPLOYMENT.md` for VPS/AWS/DigitalOcean guides.

## Running Audits

```bash
# Dev mode (no Celery worker needed)
CELERY_TASK_ALWAYS_EAGER=true

# Start audit via API
POST /api/v1/audits
{ "website_id": "<uuid>" }
```

## Optional API Keys

| Variable | Purpose |
|----------|---------|
| `PAGESPEED_API_KEY` | Google PageSpeed / Lighthouse scores |
| `OPENAI_API_KEY` | AI-generated executive summaries |
