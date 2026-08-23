# Your First Background Job

FlyRank Backend Track Week 4, Assignment A7. A FastAPI service accepts a report request quickly with `202 Accepted`, then Inngest performs the slow 8-second work in the background. A status endpoint reports progress, and a cron function logs a heartbeat every minute.

## Stack

- Python 3.10+
- FastAPI
- Inngest Python SDK
- Uvicorn
- In-memory storage, as required by the assignment

## Run

Terminal 1:

```bash
python -m venv .venv
# Windows PowerShell: .\.venv\Scripts\Activate.ps1
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
# PowerShell: $env:INNGEST_DEV="1"
# macOS/Linux: export INNGEST_DEV=1
uvicorn main:app --reload --port 8000
```

Terminal 2:

```bash
npx inngest-cli@latest dev -u http://localhost:8000/api/inngest --no-discovery
```

Dashboard: `http://localhost:8288`

## Endpoints

| Endpoint/function | Purpose |
|---|---|
| `GET /health` | Returns HTTP 200 and `{ "status": "ok" }` |
| `POST /reports` | Validates `topic`, stores `pending`, sends `report/requested`, returns HTTP 202 |
| `GET /reports/:id` | Returns the saved report; unknown ID returns 404 |
| `say-hello` | Event `test/hello`, with a 5-second sleep |
| `make-report` | Event `report/requested`, 8-second sleep + build step, 2 retries |
| `heartbeat` | Cron `* * * * *`, logs pending/done/failed counts |

## Required proofs

### 202 then poll

```bash
curl -i -X POST http://localhost:8000/reports -H "Content-Type: application/json" -d '{"topic":"cats"}'
curl http://localhost:8000/reports/<id>
```

The first request returns 202 with an ID and `pending`. After roughly 8–10 seconds the status becomes `done` with a result.

### Retry proof

Send `{"topic":"fail"}`. The `make-report` function is configured with `retries=2`, so the dashboard should show three total attempts before failure.

### Validation

Missing or empty `topic` returns HTTP 400 and does not send a job. Invalid input should be rejected at the door instead of retried.

### Cron

- Every day at 08:00: `0 8 * * *`
- Every Sunday at 22:00: `0 22 * * 0`

## Idempotency

The report ID is also used as the event ID, and the worker checks the saved status before doing work. This prevents duplicate delivery of the same report event from building a completed report twice.

## AI vs me

The bonus rematch prompt is kept under `ai-version/PROMPT.md`. Three important review points are: explicit 400 validation, idempotent event IDs/status guard, and separate durable sleep/build steps.

## Submission checklist

- [x] FastAPI `/health`
- [x] Inngest connection
- [x] 202 report request
- [x] Background 8-second job
- [x] Status endpoint + 404
- [x] 400 validation
- [x] Retry demonstration
- [x] Every-minute cron
- [x] Idempotency guard
- [ ] Dashboard screenshot after local Dev Server run
