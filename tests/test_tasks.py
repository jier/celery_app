from decimal import Decimal
from uuid import UUID

from workflow_app.models import ImportJob, JobStatus
from workflow_app.tasks import process_import
from workflow_app.validation import ProductRow


class FakeJobStore:
    def __init__(self) -> None:
        self.jobs: dict[UUID, ImportJob] = {
            UUID("00000000-0000-0000-0000-000000000001"): ImportJob(
                id=UUID("00000000-0000-0000-0000-000000000001"),
                owner_id=UUID("11111111-1111-1111-1111-111111111111"),
                filename="inventory.csv",
                status=JobStatus.QUEUED,
                total_rows=0,
                processed_rows=0,
                failed_rows=0,
            ),
        }
        self.job_contents: dict[UUID, bytes] = {
            UUID("00000000-0000-0000-0000-000000000001"): (
                b"sku,name,price,quantity\nSKU-001,Blue Widget,12.50,3\nSKU-002,Red Widget,7.25,5\n"
            ),
        }

    def get_job(self, job_id: UUID) -> ImportJob | None:
        return self.jobs.get(job_id)

    def get_content(self, job_id: UUID) -> bytes:
        return self.job_contents.get(job_id, b"")

    def update_job(self, job: ImportJob) -> None:
        self.jobs[job.id] = job


class FakeProductStore:
    def __init__(self) -> None:
        self.upserted: list[ProductRow] = []
        self.failures: list[tuple[ProductRow, str | None]] = []

    async def upsert(self, owner_id: UUID, product: ProductRow) -> None:
        del owner_id
        self.upserted.append(product)


def test_process_import_persists_valid_csv_rows_and_final_status() -> None:
    job_store = FakeJobStore()
    product_store = FakeProductStore()

    process_import(
        job_id=UUID("00000000-0000-0000-0000-000000000001"),
        job_store=job_store,
        product_store=product_store,
    )

    final_job = job_store.jobs[UUID("00000000-0000-0000-0000-000000000001")]
    assert final_job.status == JobStatus.COMPLETED
    assert final_job.total_rows == 2
    assert final_job.processed_rows == 2
    assert final_job.failed_rows == 0
    assert product_store.upserted == [
        ProductRow(sku="SKU-001", name="Blue Widget", price=Decimal("12.50"), quantity=3),
        ProductRow(sku="SKU-002", name="Red Widget", price=Decimal("7.25"), quantity=5),
    ]
