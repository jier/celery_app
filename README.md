# Observable Product Inventory Imports

Import product inventory from CSV files with live progress, powered by Celery and Supabase.

## Architecture

```
Browser → FastAPI → Supabase (Postgres + Storage + Auth + Realtime)
                ↘
              Redis → Celery Worker → Supabase Postgres
```

- **API** (`workflow_app/main.py`) receives CSV uploads, stores the file in Supabase Storage, creates a job record, and enqueues processing.
- **Worker** (`workflow_app/celery_app.py`) picks up jobs from Redis, validates each CSV row, upserts valid products into Postgres, and updates job progress.
- **Auth** verifies the caller's Supabase JWT token.
- **RLS** scopes every job and product to its owner.
- **Retries** transient failures (network, DB) retry with exponential backoff (max 3). Permanent failures mark the job as `failed`.
- **Idempotency** re-importing the same SKU updates quantity and price, never duplicates.
- **Observability** OpenTelemetry traces across API → Redis → Worker → Supabase, plus structured logs with trace context.

## Examples

The original arithmetic-task Celery demo is available separately at
[`examples/basic-celery/`](examples/basic-celery/). It is a standalone Redis,
Celery Beat, and Flower example and is not part of the import application.

## Quick Start

### Prerequisites

- [uv](https://docs.astral.sh/uv/) and Python 3.13+
- [Docker](https://docs.docker.com/) — the `supabase` CLI runs Postgres, Auth, Storage, and
  Realtime as Docker containers. The `supabase` Homebrew package is the orchestrator,
  not the database itself. No Docker means no local Supabase.
- [Redis](https://redis.io/) running locally on port 6379
- [Node.js](https://nodejs.org/) (for TypeScript compilation)

### 1. Start Services

```bash
supabase start          # Postgres, Auth, Storage, Realtime
redis-server            # or: brew services start redis
```

### 2. Install Dependencies

```bash
uv sync
```

### 3. Compile Dashboard

```bash
npx --package typescript tsc
# or in watch mode:
npx --package typescript tsc --watch
```

### 4. Start API

```bash
uv run uvicorn workflow_app.main:app --reload --host 127.0.0.1 --port 8000
```

### 5. Start Worker

```bash
uv run celery -A workflow_app.celery_app worker --pool solo --loglevel info
```

### 6. Open Dashboard

Visit `http://127.0.0.1:8000` in your browser. Login, upload a CSV from `tests/fixtures/`, and watch the import progress live via Supabase Realtime.

### 7. Or: CLI Alternative

The dashboard at `http://127.0.0.1:8000` handles login, upload, and progress. Use these
curl commands only if you prefer the terminal:

The `SUPABASE_ANON_KEY` is in your `.env` file or the `supabase start` output.

```bash
# Create an account through Supabase's local auth endpoint
curl -X POST http://127.0.0.1:54321/auth/v1/signup \
  -H "apikey: $SUPABASE_ANON_KEY" \
  -H "Content-Type: application/json" \
  -d '{"email": "demo@example.com", "password": "demodemo123"}'

# Extract the access_token from the response, then:
TOKEN="<access_token>"

# Upload a CSV
curl -i -X POST http://127.0.0.1:8000/imports \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@tests/fixtures/sample-inventory.csv"

# Check status (use the job id from the upload response)
curl -H "Authorization: Bearer $TOKEN" \
  http://127.0.0.1:8000/imports/<job-id>
```

## Docker Compose

For a self-contained environment with an OTLP collector for traces:

```bash
docker compose up
```

This starts: API, Celery worker, Redis, Flower, and an OTLP Collector.
Traces from both API and worker are sent to `http://localhost:4318/v1/traces`
and printed to the console for local development.

## API

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/imports` | Upload a CSV file. Returns 202 with job details. |
| `GET` | `/imports` | List all import jobs. |
| `GET` | `/imports/{job_id}` | Get job status and row counts. |
| `GET` | `/products` | List imported products. |

All endpoints require `Authorization: Bearer <access_token>`.

## CSV Format

Column headers must match exactly:

```csv
sku,name,price,quantity
SKU-001,Blue Widget,12.50,150
```

- `sku` and `name` are required strings.
- `price` must be zero or greater.
- `quantity` must be zero or greater (integer).
- SKUs are case-insensitive and whitespace-trimmed. Duplicate SKUs within the same owner are upserted.

## Project Structure

```
celery_app/
├── workflow_app/
│   ├── api.py            # FastAPI routes and pluggable protocols
│   ├── celery_app.py     # Celery app, worker task, and job store
│   ├── dispatcher.py     # Enqueues tasks via Celery
│   ├── main.py           # Wired entrypoint (auth + stores + dispatcher)
│   ├── models.py         # Pydantic models: User, ImportJob, JobStatus
│   ├── settings.py       # Env-var configuration (pydantic-settings)
│   ├── supabase_auth.py  # JWT token verification adapter
│   ├── supabase_store.py # Postgres + Storage adapters
│   ├── tasks.py          # CSV parsing, validation, and upsert logic
│   └── validation.py     # Product-row normalization and validation
├── tests/
│   ├── fixtures/         # Sample CSV files for testing
│   ├── test_api.py       # Import creation and status endpoints
│   ├── test_fixtures.py  # CSV fixture integration tests
│   ├── test_tasks.py     # Task contract test
│   └── test_validation.py
├── supabase/
│   └── migrations/       # SQL schema and RLS policies
├── pyproject.toml
└── .env.example
```

## Development

```bash
uv sync                     # install all dependencies
uv run pre-commit install   # enable git hooks
uv run pytest               # run tests
uv run pre-commit run -a    # run all checks
```

Pre-commit hooks: ruff (check + format), mypy, pytest, duplicate code detection.
