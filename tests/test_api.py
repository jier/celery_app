from uuid import UUID

from fastapi.testclient import TestClient

from workflow_app.api import create_app
from workflow_app.models import ImportJob, JobStatus, User


class FakeAuth:
    async def authenticate(self, access_token: str) -> User:
        assert access_token == "test-token"
        return User(id=UUID("11111111-1111-1111-1111-111111111111"), email="user@example.com")


class FakeImports:
    def __init__(self) -> None:
        self.created: tuple[UUID, str, bytes] | None = None
        self._job: ImportJob | None = None

    async def create(self, owner_id: UUID, filename: str, content: bytes) -> ImportJob:
        self.created = (owner_id, filename, content)
        self._job = ImportJob(
            id=UUID("22222222-2222-2222-2222-222222222222"),
            owner_id=owner_id,
            filename=filename,
            status=JobStatus.QUEUED,
        )
        return self._job

    async def get(self, owner_id: UUID, job_id: UUID) -> ImportJob | None:
        del owner_id
        if self._job and job_id == self._job.id:
            return self._job
        return None


class FakeDispatcher:
    def __init__(self) -> None:
        self.job_ids: list[UUID] = []

    def enqueue(self, job_id: UUID) -> None:
        self.job_ids.append(job_id)


def test_authenticated_user_can_create_inventory_import() -> None:
    imports = FakeImports()
    dispatcher = FakeDispatcher()
    client = TestClient(create_app(auth=FakeAuth(), imports=imports, dispatcher=dispatcher))

    response = client.post(
        "/imports",
        headers={"Authorization": "Bearer test-token"},
        files={"file": ("inventory.csv", b"sku,name,price,quantity\nSKU-1,Widget,1.25,2\n")},
    )

    assert response.status_code == 202
    assert response.json() == {
        "id": "22222222-2222-2222-2222-222222222222",
        "owner_id": "11111111-1111-1111-1111-111111111111",
        "filename": "inventory.csv",
        "status": "queued",
        "total_rows": 0,
        "processed_rows": 0,
        "failed_rows": 0,
    }
    assert imports.created == (
        UUID("11111111-1111-1111-1111-111111111111"),
        "inventory.csv",
        b"sku,name,price,quantity\nSKU-1,Widget,1.25,2\n",
    )
    assert dispatcher.job_ids == [UUID("22222222-2222-2222-2222-222222222222")]


def test_owner_can_retrieve_their_import_job_status() -> None:
    imports = FakeImports()
    imports._job = ImportJob(
        id=UUID("00000000-0000-0000-0000-000000000099"),
        owner_id=UUID("11111111-1111-1111-1111-111111111111"),
        filename="big.csv",
        status=JobStatus.PROCESSING,
        total_rows=100,
        processed_rows=45,
        failed_rows=2,
    )
    client = TestClient(create_app(auth=FakeAuth(), imports=imports, dispatcher=FakeDispatcher()))

    response = client.get(
        "/imports/00000000-0000-0000-0000-000000000099",
        headers={"Authorization": "Bearer test-token"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "id": "00000000-0000-0000-0000-000000000099",
        "owner_id": "11111111-1111-1111-1111-111111111111",
        "filename": "big.csv",
        "status": "processing",
        "total_rows": 100,
        "processed_rows": 45,
        "failed_rows": 2,
    }
