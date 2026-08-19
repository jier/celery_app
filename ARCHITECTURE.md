# Architecture

## Current (v0.1)

```
                         ┌──────────────────────┐
                         │      Supabase         │
                         │                      │
  Browser ──POST /imports─▶ FastAPI ──Storage──▶ import-files/
       │                 │  │                    │
       │                 │  └──Postgres──▶ import_jobs
       │                 │  │              products
       │                 │  └──Auth──────▶ JWT verification
       │                 │
       │                 │   Redis
       │                 └────▶ Celery Worker ──▶ import-files/ (download CSV)
       │                         │           │
       │                         │           └──▶ products (upsert)
       │                         │
       │                         └──▶ import_jobs (update status)
       │
       └── Realtime ◀── import_jobs changes ◀── Postgres
```

### Component Boundaries

Each external service is hidden behind a Protocol interface:

| Protocol | Real Adapter | Test Fake |
|----------|-------------|-----------|
| `Authenticator` | `SupabaseAuthenticator` (JWT) | `FakeAuth` |
| `ImportStore` | `SupabaseImportStore` (Postgres + Storage) | `FakeImports` |
| `ImportDispatcher` | `CeleryDispatcher` (Redis) | `FakeDispatcher` |
| `ImportJobStore` | `SupabaseImportJobStore` (Postgres + Storage) | `InMemoryJobStore` |
| `InventoryProductStore` | `SupabaseProductStore` (Postgres) | `CollectingProductStore` |

### Data Flow: CSV Import

1. User uploads CSV via `POST /imports` with Bearer token.
2. `SupabaseAuthenticator` calls `supabase.auth.get_user(token)` to verify identity.
3. `SupabaseImportStore.create()` inserts a `queued` row into `import_jobs` and uploads the CSV to Storage at `import-files/{owner_id}/{job_id}.csv`.
4. `CeleryDispatcher.enqueue()` calls `celery_app.send_task("process_import", args=[job_id])`.
5. Worker picks up the task from Redis.
6. `SupabaseImportJobStore.get_content()` downloads the CSV from Storage.
7. Rows are parsed and validated by `validate_product_row()`.
8. Valid rows are upserted into `products` via `SupabaseProductStore.upsert()`.
9. Job status, `total_rows`, `processed_rows`, and `failed_rows` are updated.
10. Frontend subscribes to `import_jobs` changes via Supabase Realtime for live progress.

### Security

- **Auth**: Supabase JWT tokens verified server-side on every request.
- **RLS**: Every `import_jobs` and `products` row is scoped to `auth.uid()`. One user cannot see another's data.
- **Storage RLS**: CSV files are stored under `import-files/{owner_id}/`; only the owning user can read their own files.
- **Worker**: Uses the `service_role` key which bypasses RLS; never exposed to the frontend.
- **Defense in depth**: The API's `ImportStore` requires user token; the worker's `ImportJobStore` requires `service_role`.

## Future (v0.2+)

```
                         ┌──────────────────────┐
                         │      Supabase         │
                         │                      │
  Browser ──▶ FastAPI ──▶ Storage  (CSV files)  │
       │                 │ Postgres (jobs,       │
       │                 │          products)    │
       │                 │ Auth    (users)       │
       │                 │ Realtime (progress)   │
       │                 │                      │
       │                 │   Redis               │
       │                 └──▶ Celery Worker      │
       │                      Celery Beat        │
       │                      Flower             │
       │                                       │
       │   Docker Compose                       │
       │   ┌──────────┬──────────┬───────────┐ │
       │   │ API       │ Worker    │ Redis     │ │
       │   │ (FastAPI) │ (Celery) │           │ │
       │   ├──────────┼──────────┼───────────┤ │
       │   │ Beat      │ Flower   │ Supabase  │ │
       │   │ (opt)     │ (opt)    │ (external)│ │
       │   └──────────┴──────────┴───────────┘ │
       │                                       │
       │   OpenTelemetry                        │
       │   ┌──────┬────────┬──────────────┐    │
       │   │ API  │ Worker │ Supabase     │    │
       │   │ span │ span   │ HTTP calls   │    │
       │   └──────┴────────┴──────────────┘    │
       │                                       │
       │   ┌──────────┐                        │
       │   │ Dashboard │ (Vue/Ionic PWA)       │
       │   │ - Login   │                       │
       │   │ - Upload  │                       │
       │   │ - Jobs    │                       │
       │   │ - Products│                       │
       │   └──────────┘                        │
       └───────────────────────────────────────┘
```

### Planned Additions

- **Dashboard**: Vue/Ionic PWA for login, CSV upload, live job progress, and product listing.
- **OpenTelemetry**: Traces across API → Redis → Worker → Supabase. Structured logs with trace context. RED metrics.
- **Containerization**: `docker compose` with FastAPI, Celery worker, Redis, optional Beat and Flower.
- **RabbitMQ comparison**: Optional broker profile for comparing delivery semantics and monitoring.
- **Retries & idempotency**: Automatic retry with backoff for transient failures. Idempotent product upserts via `(owner_id, sku)` unique constraint.
