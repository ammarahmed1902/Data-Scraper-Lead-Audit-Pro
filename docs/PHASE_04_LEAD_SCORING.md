# Phase 04 — Lead Scoring System

## Overview

Intelligent lead scoring engine that ranks discovered businesses by sales opportunity. Combines audit results, enrichment data, and homepage analysis to produce composite scores and hot/warm/cold classifications.

## Scores (0–100)

| Score | Meaning |
|-------|---------|
| **Website Quality** | Audit overall score (how good the site is) |
| **SEO Opportunity** | Inverted SEO score + issue severity bonus |
| **Technical Opportunity** | Inverted technical score + critical issue bonus |
| **Sales Potential** | Contact completeness + enrichment signals |
| **Composite** | 45% opportunity avg + 25% quality gap + 30% sales potential |

## Classification

| Class | Criteria |
|-------|----------|
| **Hot** | Composite ≥ 65, sales potential ≥ 45, audited or 2+ high opportunities |
| **Warm** | Composite ≥ 40, or sales potential ≥ 55 with high opportunities |
| **Cold** | Everything else |

## Auto-Detected Opportunities

- `missing_seo` — title, meta, H1, sitemap, canonical gaps
- `poor_performance` — low Lighthouse score, poor LCP/FCP/CLS
- `technical_problems` — HTTPS, SSL, security headers
- `missing_tracking_pixels` — no Facebook/GTM/pixel scripts
- `missing_analytics` — no Google Analytics or GTM
- `missing_conversion_elements` — no forms, CTAs, or contact paths

## Database

### `lead_scores` (1:1 with discovered_leads)
Stores all four sub-scores, composite, classification, opportunities JSON, ranking.

### `scoring_jobs`
Bulk/single scoring job tracking (Celery).

Migration: `005_lead_scoring`

## API

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/scoring/dashboard` | Hot/warm/cold stats + top hot leads |
| GET | `/api/v1/scoring/leads` | Ranked leads with filters |
| POST | `/api/v1/scoring/leads/{id}` | Score single lead (202) |
| POST | `/api/v1/scoring/searches/{id}` | Bulk score search (202) |
| GET | `/api/v1/scoring/leads/{id}` | Score breakdown |
| GET | `/api/v1/scoring/leads/{id}/opportunities` | Opportunity report |

## Auto-Scoring Triggers

Scores recalculate automatically when an audit or enrichment job completes.

## Frontend

- `/leads` — Priority dashboard with ranking, filters, opportunity reports
- `/dashboard` — Hot lead widget
- Discovery — Score All bulk action
