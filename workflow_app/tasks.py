import asyncio
import csv
from io import StringIO
from typing import Protocol
from uuid import UUID

from workflow_app.models import ImportJob, JobStatus, ProductRow
from workflow_app.validation import ProductRowValidationError, validate_product_row


class ImportJobStore(Protocol):
    def get_job(self, job_id: UUID) -> ImportJob | None: ...
    def get_content(self, job_id: UUID) -> bytes: ...
    def update_job(self, job: ImportJob) -> None: ...


class InventoryProductStore(Protocol):
    async def upsert(self, owner_id: UUID, product: ProductRow) -> None: ...


def process_import(
    job_id: UUID,
    job_store: ImportJobStore,
    product_store: InventoryProductStore,
) -> None:
    job = job_store.get_job(job_id)
    if job is None:
        return

    job.status = JobStatus.PROCESSING
    job_store.update_job(job)

    content = job_store.get_content(job_id)
    reader = csv.DictReader(StringIO(content.decode("utf-8")))
    rows = list(reader)

    job.total_rows = len(rows)
    processed = 0
    failed = 0

    for row in rows:
        try:
            product = validate_product_row(row)
        except ProductRowValidationError:
            failed += 1
            continue
        asyncio.run(product_store.upsert(job.owner_id, product))
        processed += 1

    job.processed_rows = processed
    job.failed_rows = failed
    job.status = JobStatus.COMPLETED
    job_store.update_job(job)
