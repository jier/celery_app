from uuid import UUID

from workflow_app.celery_app import app as celery_app


class CeleryDispatcher:
    def enqueue(self, job_id: UUID) -> None:
        celery_app.send_task("process_import", args=[str(job_id)])
