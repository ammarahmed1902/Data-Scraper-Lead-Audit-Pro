# Lead Audit Pro — API Reference

Base URL: `/api/v1`

Authentication: `Authorization: Bearer <access_token>` (except auth endpoints)

---

## Authentication — `/auth`

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/auth/register` | None | Create new account |
| POST | `/auth/login` | None | Obtain JWT tokens |
| POST | `/auth/refresh` | None | Refresh access token |
| POST | `/auth/logout` | Required | Invalidate session |
| GET | `/auth/me` | Required | Current user profile |

### POST `/auth/register`

```json
// Request
{
  "email": "user@company.com",
  "password": "securepassword",
  "full_name": "Jane Smith"
}

// Response 201
{
  "user": { "id": "uuid", "email": "...", "role": "viewer", ... },
  "tokens": { "access_token": "...", "refresh_token": "...", "token_type": "bearer" }
}
```

### POST `/auth/login`

```json
// Request
{ "email": "user@company.com", "password": "securepassword" }

// Response 200
{ "user": { ... }, "tokens": { ... } }
```

---

## Users — `/users`

| Method | Endpoint | Role | Description |
|--------|----------|------|-------------|
| GET | `/users` | admin | List all users (paginated) |
| GET | `/users/{id}` | manager | Get user by ID |
| POST | `/users` | admin | Create user |
| PUT | `/users/{id}` | admin | Update user |
| DELETE | `/users/{id}` | admin | Deactivate user |

Query params (GET list): `page`, `page_size`, `sort_by`, `sort_order`

---

## Websites — `/websites`

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/websites` | Required | List user's websites |
| GET | `/websites/{id}` | Required | Get website details |
| POST | `/websites` | Required | Add single website |
| POST | `/websites/bulk` | Required | Bulk import (max 500) |
| PUT | `/websites/{id}` | Required | Update website |
| DELETE | `/websites/{id}` | Required | Delete website |

Query params (GET list): `page`, `page_size`, `status`, `search`

### POST `/websites`

```json
{
  "url": "https://example.com",
  "company_name": "Example Corp",
  "contact_name": "John Doe",
  "contact_email": "john@example.com",
  "industry": "Technology",
  "tags": ["prospect", "enterprise"]
}
```

---

## Audits — `/audits`

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/audits` | Required | List audits (paginated) |
| GET | `/audits/{id}` | Required | Get audit with sub-reports |
| POST | `/audits` | Required | Queue audit for website |
| POST | `/audits/bulk` | Required | Bulk audit (max 100) |
| DELETE | `/audits/{id}` | Required | Cancel pending audit |
| GET | `/audits/{id}/status` | Required | Poll audit progress |

Query params (GET list): `page`, `page_size`, `website_id`, `status`

### POST `/audits`

```json
{ "website_id": "uuid" }
// Response 202 — audit queued
```

---

## Reports — `/reports`

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/reports` | Required | List generated reports |
| GET | `/reports/{id}` | Required | Get report metadata |
| POST | `/reports` | Required | Generate report from audit |
| GET | `/reports/{id}/download` | Required | Download report file |
| DELETE | `/reports/{id}` | Required | Delete report |

### POST `/reports`

```json
{
  "audit_report_id": "uuid",
  "title": "SEO Audit — example.com",
  "format": "pdf"
}
```

---

## Analytics — `/analytics`

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/analytics/overview` | Required | Dashboard summary |
| GET | `/analytics/trends` | Required | Audit trends over time |
| GET | `/analytics/scores` | Required | Score distribution |
| GET | `/analytics/issues` | Required | Top recurring issues |

Query params: `date_from`, `date_to`, `period` (7d|30d|90d|1y), `limit`

---

## Exports — `/exports`

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/exports` | Required | List export history |
| GET | `/exports/{id}` | Required | Get export status |
| POST | `/exports` | Required | Create export job |
| GET | `/exports/{id}/download` | Required | Download export file |
| DELETE | `/exports/{id}` | Required | Delete export |

### POST `/exports`

```json
{
  "export_type": "websites",
  "format": "csv",
  "filters": { "status": "completed", "date_from": "2026-01-01" }
}
```

---

## Common Response Patterns

### Paginated List

```json
{
  "items": [...],
  "total": 150,
  "page": 1,
  "page_size": 20,
  "total_pages": 8
}
```

### Error Response

```json
{
  "detail": "Error message"
}
```

### HTTP Status Codes

| Code | Usage |
|------|-------|
| 200 | Success |
| 201 | Created |
| 202 | Accepted (async job queued) |
| 204 | No content (delete) |
| 400 | Validation error |
| 401 | Unauthorized |
| 403 | Forbidden (RBAC) |
| 404 | Not found |
| 429 | Rate limited |
| 501 | Not yet implemented (Phase 01) |

---

## Rate Limits

| Endpoint Group | Limit |
|----------------|-------|
| `/auth/register` | 5/minute |
| `/auth/login` | 10/minute |
| All other endpoints | 60/minute (configurable) |
| Nginx gateway | 30 req/s (API), 60 req/s (frontend) |
