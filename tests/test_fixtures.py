from pathlib import Path
from uuid import UUID

from workflow_app.models import ImportJob, JobStatus, ProductRow
from workflow_app.tasks import process_import

FIXTURES = Path(__file__).parent / "fixtures"


def _read_fixture(name: str) -> bytes:
    return (FIXTURES / name).read_bytes()


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


def test_process_import_with_valid_csv_saves_all_rows() -> None:
    owner_id = UUID("11111111-1111-1111-1111-111111111111")
    content = _read_fixture("sample-inventory.csv")
    job_store = InMemoryJobStore(owner_id, "sample-inventory.csv", content)
    product_store = CollectingProductStore()

    process_import(
        job_id=UUID("00000000-0000-0000-0000-000000000042"),
        job_store=job_store,
        product_store=product_store,
    )

    final = job_store.get_job(UUID("00000000-0000-0000-0000-000000000042"))
    assert final is not None
    assert final.status == JobStatus.COMPLETED
    assert final.total_rows == 5
    assert final.processed_rows == 5
    assert final.failed_rows == 0
    assert product_store.saved[0].sku == "SKU-001"


def test_process_import_count_invalid_rows_as_failed() -> None:
    content = _read_fixture("sample-inventory-with-errors.csv")
    job_store = InMemoryJobStore(
        UUID("11111111-1111-1111-1111-111111111111"),
        "errors.csv",
        content,
    )
    product_store = CollectingProductStore()

    process_import(
        job_id=UUID("00000000-0000-0000-0000-000000000042"),
        job_store=job_store,
        product_store=product_store,
    )

    final = job_store.get_job(UUID("00000000-0000-0000-0000-000000000042"))
    assert final is not None
    assert final.total_rows == 4
    assert final.processed_rows == 1
    assert final.failed_rows == 3
