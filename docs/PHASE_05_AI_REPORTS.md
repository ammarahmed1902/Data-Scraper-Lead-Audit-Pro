# Phase 05 — AI Report Generator

AI-powered client-ready reports for every completed website audit.

## Features

- **Executive Summary** — high-level audit overview
- **SEO / Performance / Technical Summaries** — section-specific analysis
- **Opportunity Summary** — sales-oriented gap analysis (uses lead scoring when available)
- **Client Recommendations** — prioritized, client-facing action items
- **Cold Calling Talking Points** — ready-to-use call scripts
- **Sales Pitch Summary** — concise outreach pitch
- **Outreach Recommendations** — channel, message, and timing guidance
- **PDF export** — branded downloadable report via ReportLab
- **Report history** — all reports stored in PostgreSQL with JSONB content
- **Auto-generation** — reports created automatically when audits complete

## Configuration

```env
OPENAI_API_KEY=sk-...          # Optional — uses OpenAI when set
OPENAI_MODEL=gpt-4o-mini       # Default model
AUTO_GENERATE_REPORTS=true     # Auto-create report after audit (default: true)
REPORT_STORAGE_PATH=storage/reports
REPORT_EXPIRY_DAYS=30
```

Without `OPENAI_API_KEY`, a deterministic template engine generates all sections from audit data.

## Database

Migration `006_ai_report_content` adds to `reports`:

| Column | Type | Description |
|--------|------|-------------|
| `user_id` | UUID | Report owner |
| `status` | string | pending / generating / completed / failed |
| `content` | JSONB | Full AI report sections |
| `error_message` | text | Failure details |
| `celery_task_id` | string | Background task reference |

Run migration:

```bash
cd backend && python -m alembic upgrade head
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/reports` | List report history (filter: `audit_id`) |
| GET | `/api/v1/reports/{id}` | Report metadata + status |
| GET | `/api/v1/reports/{id}/content` | Full AI report JSON |
| POST | `/api/v1/reports` | Generate report (custom title) |
| POST | `/api/v1/reports/audits/{audit_id}` | Generate report for audit |
| GET | `/api/v1/reports/{id}/download` | Download PDF/JSON file |
| DELETE | `/api/v1/reports/{id}` | Delete report + file |

## Architecture

```
Audit completes
    └── audit_runner.py → auto_generate_report_for_audit()
            └── Celery: generate_report task (reports queue)
                    └── ReportRunner.generate()
                            ├── AIReportService.generate_full_report()
                            ├── Store content in reports.content
                            └── PDFService.generate_audit_pdf()
```

Manual generation: **Audits → detail → Generate AI Report** or **Reports** page.

## Frontend

- `/reports` — report history with status badges, view + download
- `/reports/[id]` — full AI report viewer (all sections)
- `/audits/[id]` — Generate AI Report button + link to latest report

## Celery

Reports run on the `reports` queue:

```bash
celery -A app.workers.celery_worker worker -Q reports,default -l info
```

With `CELERY_TASK_ALWAYS_EAGER=true`, reports generate synchronously (dev/testing).

## Tests

```bash
cd backend && pytest tests/test_ai_report.py -v
```
