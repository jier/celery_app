from uuid import UUID

from workflow_app.models import ImportJob, JobStatus, ProductRow


class InMemoryJobStore:
    def __init__(self, owner_id: UUID, filename: str, content: bytes) -> None:
        self._job = ImportJob(
            id=UUID("00000000-0000-0000-0000-000000000042"),
            owner_id=owner_id,
            filename=filename,
            status=JobStatus.QUEUED,
        )
        self._content = content

    def get_job(self, job_id: UUID) -> ImportJob | None:
        del job_id
        return self._job

    def get_content(self, job_id: UUID) -> bytes:
        del job_id
        return self._content

    def update_job(self, job: ImportJob) -> None:
        self._job = job


class CollectingProductStore:
    def __init__(self) -> None:
        self.saved: list[ProductRow] = []

    async def upsert(self, owner_id: UUID, product: ProductRow) -> None:
        del owner_id
        self.saved.append(product)
