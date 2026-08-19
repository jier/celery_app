from celery import Celery

from workflow_app.settings import Settings  # type: ignore[import-untyped]

settings = Settings()

app = Celery(
    "observable-imports",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)
app.conf.task_serializer = "json"
app.conf.accept_content = ["json"]
app.conf.result_serializer = "json"
app.conf.timezone = "UTC"
app.conf.enable_utc = True
