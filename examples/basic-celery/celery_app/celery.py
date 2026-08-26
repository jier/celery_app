import os

from celery import Celery

app = Celery(
    "basic-celery",
    broker=os.environ.get("CELERY_BROKER_URL", "redis://127.0.0.1:6379/0"),
    backend=os.environ.get("CELERY_RESULT_BACKEND", "redis://127.0.0.1:6379/0"),
    include=["celery_app.tasks"],
)

app.conf.beat_schedule = {
    "add-every-10-seconds": {"task": "call_addition", "schedule": 10.0},
    "multiply-every-10-seconds": {"task": "call_multiplication", "schedule": 10.0},
    "divide-every-10-seconds": {"task": "call_division", "schedule": 10.0},
}
app.conf.update(
    result_expires=3600,
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Europe/Amsterdam",
    enable_utc=True,
)
