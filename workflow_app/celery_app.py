from uuid import UUID

from celery import Celery

from workflow_app.models import ImportJob
from workflow_app.settings import Settings  # type: ignore[import-untyped]
from workflow_app.supabase_store import SupabaseProductStore, download_csv
from workflow_app.tasks import process_import

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


class SupabaseImportJobStore:
    def __init__(self, url: str, service_role_key: str) -> None:
        from supabase import create_client

        self._client = create_client(url, service_role_key)
        self._url = url
        self._service_role_key = service_role_key

    def get_job(self, job_id: UUID) -> ImportJob | None:
        result = self._client.table("import_jobs").select("*").eq("id", str(job_id)).execute()
        if not result.data:
            return None
        return ImportJob.from_supabase_row(result.data[0])  # type: ignore[arg-type]

    def get_content(self, job_id: UUID) -> bytes:
        job = self.get_job(job_id)
        if job is None:
            return b""
        return download_csv(self._url, self._service_role_key, job.owner_id, job_id)

    def update_job(self, job: ImportJob) -> None:
        self._client.table("import_jobs").update(
            {
                "status": str(job.status),
                "total_rows": job.total_rows,
                "processed_rows": job.processed_rows,
                "failed_rows": job.failed_rows,
            }
        ).eq("id", str(job.id)).execute()


@app.task(bind=True, name="process_import", max_retries=0)
def process_import_task(self, job_id: str) -> None:  # type: ignore[no-untyped-def]
    job_store = SupabaseImportJobStore(
        url=settings.supabase_url,
        service_role_key=settings.supabase_service_role_key,
    )
    product_store = SupabaseProductStore(
        url=settings.supabase_url,
        service_role_key=settings.supabase_service_role_key,
    )
    process_import(UUID(job_id), job_store=job_store, product_store=product_store)
