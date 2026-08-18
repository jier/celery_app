# Project Recommendations

Reviewed: 2026-08-19

## Decision

Develop this into an observable product-inventory CSV import pipeline. Use the
project to learn Celery with local Supabase Auth, Storage, Postgres, Realtime,
and row-level security.

## Value

- Demonstrates asynchronous workflow design, durable job state, retries,
  idempotency, progress reporting, and user isolation.
- Provides a real workload that can later become the sample application for
  `../observability-platform/`.

## First Version

- Small web dashboard for login, CSV upload, live progress, and row errors.
- Fixed product schema using SKU, name, price, and quantity.
- Supabase Auth for users and row-level security.
- Supabase Storage for uploaded CSV files.
- Supabase Postgres for jobs, products, and validation failures.
- Supabase Realtime for job-level progress.
- Redis database 0 as the Celery broker and database 1 as the temporary result backend.
- OpenTelemetry traces and metrics across API, queue, worker, and Supabase calls.

## Deferred Decisions

- Do not install RabbitMQ for the first version. Redis is already available
  locally and is sufficient to validate the workflow with fewer moving parts.
- Add RabbitMQ later as an optional broker-comparison profile if its delivery,
  routing, or operational behavior is specifically being studied.
- Do not containerize the whole system before the local workflow works.
- Keep local Supabase managed by `supabase start`; do not package Supabase into
  the application container.
- Later Compose packaging should use separate services for the API, Celery
  worker, Redis, and optional Flower/Beat. RabbitMQ remains optional.

## Implementation Order

1. Replace arithmetic tasks with a tested product-row validation function.
2. Clean dependencies and read Celery/Supabase configuration from environment variables.
3. Define Supabase tables, Storage bucket, Auth flow, and RLS policies.
4. Add the FastAPI job-creation and status endpoints.
5. Implement CSV upload and the Redis-backed Celery import workflow.
6. Add idempotent product upserts, retries, row errors, and durable job progress.
7. Build the small dashboard and subscribe to job progress through Realtime.
8. Add OpenTelemetry tracing, structured logs, metrics, and failure tests.
9. Containerize the API and worker, then add Redis and optional monitoring services to Compose.
10. Evaluate RabbitMQ only after the Redis-based version is complete and measured.

## Publication Position

Publish after the local workflow is reproducible, authenticated, tested, and
observable. It can then serve as the workload for the consolidated observability
platform.
