# Basic Celery

A small, independent Celery example retained from the project's original
arithmetic-task demo. It uses Redis for both the broker and result backend;
Celery Beat schedules addition, multiplication, and division tasks every ten
seconds.

## Run Locally

Install the example's dependencies with Python 3.13+ and start Redis:

```bash
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
redis-server
```

Start the worker and Beat in separate terminals:

```bash
celery --app celery_app.celery worker --pool eventlet --concurrency 4 --loglevel info
celery --app celery_app.celery beat --loglevel info
```

Optionally inspect task activity with Flower:

```bash
celery --broker=redis://127.0.0.1:6379/0 flower --port=5555
```

## Run With Docker

```bash
docker compose up --build
```

This starts Redis, a worker, Beat, and Flower. Open Flower at
`http://127.0.0.1:5555`.
