from uuid import UUID

from fastapi.testclient import TestClient

from workflow_app.api import create_app
from workflow_app.models import ImportJob, JobStatus, User


class FakeAuth:
    def authenticate(self, access_token: str) -> User:
        assert access_token == "test-token"
        return User(id=UUID("11111111-1111-1111-1111-111111111111"), email="user@example.com")


class FakeImports:
    def __init__(self) -> None:
        self.created: tuple[UUID, str, bytes] | None = None

    def create(self, owner_id: UUID, filename: str, content: bytes) -> ImportJob:
        self.created = (owner_id, filename, content)
        return ImportJob(
            id=UUID("22222222-2222-2222-2222-222222222222"),
            owner_id=owner_id,
            filename=filename,
            status=JobStatus.QUEUED,
        )

    def get(self, owner_id: UUID, job_id: UUID) -> ImportJob | None:
        del owner_id, job_id
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
