# Phase 03 — Website Management

**Status:** Complete  
**Completed:** June 2026

## Overview

Phase 03 delivers full website lifecycle management: CRUD operations, bulk import, validation, search, filtering, and pagination — on both backend APIs and frontend management pages.

## Backend Deliverables

### API Endpoints (`/api/v1/websites`)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/websites` | Paginated list with `status` and `search` filters |
| GET | `/websites/{id}` | Single website details |
| POST | `/websites` | Create website with URL validation |
| POST | `/websites/bulk` | Bulk import up to 500 URLs |
| PUT | `/websites/{id}` | Update website fields and status |
| DELETE | `/websites/{id}` | Delete website |

### Architecture

- **Service:** `app/services/website_service.py` — business logic, deduplication, validation
- **Repository:** `app/repositories/website_repository.py` — owner-scoped queries with search
- **Schemas:** `app/schemas/website.py` — Pydantic models with URL validators
- **Utils:** `app/utils/helpers.py` — `normalize_url`, `is_valid_url`, `extract_domain`

### Features

- URL normalization (adds `https://` if missing)
- Per-owner domain deduplication on create/update
- Bulk import skips duplicates within batch and existing domains
- Search across URL, domain, company name, and contact fields
- Status filter for website lifecycle states

### Tests

- `backend/tests/test_website_service.py` — unit tests for CRUD, validation, bulk import

## Frontend Deliverables

### Pages

- `/websites` — full management UI with table, search, filters, pagination

### Components

- `components/tables/website-table.tsx` — data table with actions
- `components/forms/website-form.tsx` — add/edit modal
- `components/forms/bulk-import-form.tsx` — CSV/line-based bulk import
- `components/ui/dialog.tsx`, `select.tsx`, `badge.tsx`, `label.tsx`, `textarea.tsx`

### Hooks & Services

- `hooks/use-websites.ts` — React Query hooks (list, create, update, delete, bulk)
- `services/website-service.ts` — API client methods

## Usage

### Add a website

1. Navigate to **Websites** in the sidebar
2. Click **Add Website**
3. Enter URL and optional lead details
4. Submit — domain is extracted and validated automatically

### Bulk import

1. Click **Bulk Import**
2. Paste one URL per line, or CSV: `url, company, contact, email`
3. Review import results (created, skipped, errors)

### Search & filter

- Use the search box to filter by URL, domain, company, or contact
- Use the status dropdown to filter by lifecycle state
- Pagination controls appear when results exceed 20 items

## Deferred to Phase 04

- Website detail view with audit results
- Trigger audit from website list
- Real-time audit status polling

## Running Tests

```bash
cd backend
python -m pytest tests/test_website_service.py -v
```

```bash
cd frontend
npm run type-check
```
