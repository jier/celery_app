from uuid import UUID

import pytest

from tests.helpers import CollectingProductStore, InMemoryJobStore
from workflow_app.models import ProductRow
from workflow_app.tasks import process_import


class FlakyProductStore:
    def __init__(self, fail_count: int = 0) -> None:
        self.saved: list[ProductRow] = []
        self._fail_count = fail_count
        self._call_count = 0

    async def upsert(self, owner_id: UUID, product: ProductRow) -> None:
        del owner_id
        self._call_count += 1
        if self._call_count <= self._fail_count:
            raise ConnectionError("Transient DB connection error")
        self.saved.append(product)


def test_task_retries_on_transient_failure() -> None:
    content = b"sku,name,price,quantity\nSKU-001,Widget,1.25,2\n"
    store = FlakyProductStore(fail_count=2)
    job_store = InMemoryJobStore(
        UUID("11111111-1111-1111-1111-111111111111"),
        "retry.csv",
        content,
    )

    with pytest.raises(ConnectionError):
        process_import(
            job_id=UUID("00000000-0000-0000-0000-000000000042"),
            job_store=job_store,
            product_store=store,
        )
    with pytest.raises(ConnectionError):
        process_import(
            job_id=UUID("00000000-0000-0000-0000-000000000042"),
            job_store=job_store,
            product_store=store,
        )
    process_import(
        job_id=UUID("00000000-0000-0000-0000-000000000042"),
        job_store=job_store,
        product_store=store,
    )

    assert store._call_count == 3
    assert len(store.saved) == 1
    assert store.saved[0].sku == "SKU-001"


def test_reimport_is_idempotent_no_duplicate_products() -> None:
    content = b"sku,name,price,quantity\nSKU-001,Blue Widget,12.50,3\nSKU-002,Red Widget,7.25,5\n"
    owner_id = UUID("11111111-1111-1111-1111-111111111111")
    job_store = InMemoryJobStore(owner_id, "idempotent.csv", content)
    product_store = CollectingProductStore()

    process_import(
        job_id=UUID("00000000-0000-0000-0000-000000000042"),
        job_store=job_store,
        product_store=product_store,
    )

    assert len(product_store.saved) == 2
    assert product_store.saved[0].sku == "SKU-001"
    assert product_store.saved[1].sku == "SKU-002"
