from pathlib import Path
from uuid import UUID

import pytest

from tests.helpers import CollectingProductStore, InMemoryJobStore
from workflow_app.models import JobStatus
from workflow_app.tasks import process_import

FIXTURES = Path(__file__).parent / "fixtures"


def _read_fixture(name: str) -> bytes:
    return (FIXTURES / name).read_bytes()


@pytest.mark.parametrize(
    (
        "fixture_name",
        "job_filename",
        "expected_total_rows",
        "expected_processed_rows",
        "expected_failed_rows",
        "expected_skus",
    ),
    [
        pytest.param(
            "sample-inventory.csv",
            "sample-inventory.csv",
            5,
            5,
            0,
            ("SKU-001", "SKU-002", "SKU-003", "SKU-004", "SKU-005"),
            id="valid-inventory",
        ),
        pytest.param(
            "sample-inventory-with-errors.csv",
            "errors.csv",
            4,
            1,
            3,
            ("VALID-001",),
            id="invalid-rows",
        ),
    ],
)
def test_process_import_fixture(
    fixture_name: str,
    job_filename: str,
    expected_total_rows: int,
    expected_processed_rows: int,
    expected_failed_rows: int,
    expected_skus: tuple[str, ...],
) -> None:
    owner_id = UUID("11111111-1111-1111-1111-111111111111")
    content = _read_fixture(fixture_name)
    job_store = InMemoryJobStore(owner_id, job_filename, content)
    product_store = CollectingProductStore()

    process_import(
        job_id=UUID("00000000-0000-0000-0000-000000000042"),
        job_store=job_store,
        product_store=product_store,
    )

    final = job_store.get_job(UUID("00000000-0000-0000-0000-000000000042"))
    assert final is not None
    assert final.status == JobStatus.COMPLETED
    assert final.total_rows == expected_total_rows
    assert final.processed_rows == expected_processed_rows
    assert final.failed_rows == expected_failed_rows
    assert tuple(product.sku for product in product_store.saved) == expected_skus
