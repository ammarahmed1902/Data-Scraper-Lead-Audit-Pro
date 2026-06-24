# QA Issue Register — Lead Audit Pro

Last updated: 2026-06-24

| ID | Issue | Scope | Priority | Status |
|----|-------|-------|----------|--------|
| QA-001 | Production build fails — login `useSearchParams` missing Suspense | Frontend | P0 | **Fixed** |
| QA-002 | Auth unit tests failing — `UserResponse` validation on register/login | Backend | P0 | **Fixed** |
| QA-003 | No website detail page (`/websites/[id]`) | Frontend | P1 | **Fixed** |
| QA-004 | Bulk audit not exposed in UI | Frontend | P1 | **Fixed** |
| QA-005 | RBAC not enforced in UI | Frontend | P1 | **Fixed** |
| QA-006 | Technical audit data not displayed (SSL, HTTPS, etc.) | Frontend | P1 | **Fixed** |
| QA-007 | Native `alert()` / `confirm()` for errors and delete | Frontend | P2 | **Fixed** |
| QA-008 | Settings notifications placeholder | Frontend + Backend | P2 | **Deferred** (copy updated) |
| QA-009 | Login redirect ignores protected route | Frontend | P2 | **Fixed** |
| QA-010 | ESLint unused `Clock` import on dashboard | Frontend | P3 | **Fixed** |
| QA-011 | Unused `TechnicalPanel` dead code | Frontend | P3 | **Fixed** (via QA-006) |
| QA-012 | Duplicate lockfiles — Next.js workspace root warning | Frontend | P3 | **Fixed** |
| QA-013 | Load testing at 10K+ scale not verified | Backend / Infra | P3 | **Smoke pass** (`scripts/load_test.py`; scale on staging) |
| QA-014 | README phase status outdated | Docs | P3 | **Fixed** |
| QA-015 | Reports list API returned 500 | Backend | P1 | **Fixed** |

## Verification commands

```bash
# Backend unit + integration tests
cd backend && python -m pytest tests/ -q

# API smoke test (requires running server)
cd backend && python -m scripts.smoke_test

# Load test smoke scenario (requires running server)
cd backend && python -m scripts.load_test --websites 25 --audits 10

# Frontend
cd frontend && npm run lint && npm run build
```

## QA sign-off checklist

- [x] Smoke: login page renders, auth redirect preserves `?redirect=`
- [x] Smoke: register page renders
- [x] API smoke: all core endpoints (incl. reports list)
- [ ] Manual: login with credentials in browser
- [ ] Websites: CRUD, bulk import, detail page, bulk audit
- [ ] Audits: trigger, tabs (SEO, Performance, Technical)
- [ ] Discovery: import, enrich, audit, score (toast errors)
- [ ] RBAC: Viewer read-only; Admin full access
- [x] Production build passes
- [x] Load test smoke scenario (25 websites, 10 audits)
