# PDF Report Generator — FlyRank A8

A complete implementation of the FlyRank Backend Track Week 4 A8 assignment using **Python + FastAPI + SQLite + Playwright**.

## Pipeline

`SQLite orders → SQL aggregation → HTML template → Playwright PDF → disk → API link`

The implementation covers Stages 0–6 and includes the optional Stage 7 AI review notes.

## Features

- `/health` health check
- 200 seeded shop orders across 6 products
- Four reporting aggregations: totals, top 5 products, and last-7-days grouped sales
- Multi-page A4 PDF with repeating table headers and `break-inside: avoid`
- `POST /reports` generates a report and returns a file link
- `GET /reports/{id}` returns report metadata
- `GET /reports/{id}/file` streams the PDF from disk
- Same-day idempotency: repeated requests reuse the existing report
- `{ "force": true }` creates a fresh report
- `GET /reports` lists generated reports

## Run

```bash
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium
python scripts/seed.py
uvicorn app.main:app --reload
```

If Playwright's bundled browser is unavailable on your machine, set `CHROMIUM_PATH` and adjust `app/reporting.py` to use that executable. This development environment uses `/usr/bin/chromium`.

## Checkpoints

```bash
curl -i http://localhost:8000/health
curl -i -X POST http://localhost:8000/reports
curl -o my-report.pdf http://localhost:8000/reports/1/file
```

The POST endpoint intentionally takes a few seconds because the assignment keeps PDF generation inside the request. For larger reports or many users, this work should move to a background job and the API should return `202` with a pending status.

## Idempotency

The same-day check protects against double-clicks, retries, or duplicate client requests creating multiple copies of the same report. A real-world equivalent is preventing a customer from receiving the same email twice. Use `{ "force": true }` when a fresh report is explicitly requested.

## SQL used by the report

```sql
SELECT COUNT(*) FROM orders;
SELECT COALESCE(SUM(amount), 0) FROM orders;
SELECT product, COUNT(*) AS order_count, ROUND(SUM(amount), 2) AS revenue
FROM orders GROUP BY product ORDER BY revenue DESC LIMIT 5;
SELECT substr(created_at, 1, 10) AS day, COUNT(*) AS orders, ROUND(SUM(amount), 2) AS revenue
FROM orders WHERE date(created_at) >= date('now', '-6 days')
GROUP BY day ORDER BY day;
```

## GitHub / submission

Generated database files and PDFs are ignored by Git. The code and README are the source of truth; generated artifacts stay on disk.

## AI vs me

The hand-built version defines the schema, seed behavior, SQL aggregations, PDF layout, API contract, and idempotency rule explicitly. An AI-generated implementation can be reviewed against those checkpoints instead of being accepted blindly.

### Example AI review differences

1. AI implementations often return PDF bytes directly; this project stores the artifact and returns a link.
2. AI implementations may omit repeated table headers or row-safe page breaks; this project includes both print-CSS rules.
3. AI implementations may regenerate on every POST; this project checks today's report first and supports an explicit `force` override.

### Improved prompt used for review

> Build a Python FastAPI report service backed by SQLite. Create an orders table and a deterministic seed script for 200 rows. Implement one report-data function with total orders, total revenue, top five products by revenue, orders per day for the last seven days, and all orders for the long PDF table. Render an A4 PDF from HTML with Playwright. The PDF must be at least two pages for the seeded dataset, repeat table headers, and never split table rows. Store PDFs on disk and keep only their path in the reports table. Implement POST /reports, GET /reports/{id}, GET /reports/{id}/file, and same-day idempotency with an optional force flag. JSON endpoints must never contain PDF bytes. Include a README with run commands and SQL.

## Evidence

The local submission package includes `docs/report-preview.png`, a screenshot of page 1 of a generated six-page report.
