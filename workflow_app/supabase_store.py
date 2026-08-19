from datetime import datetime
from typing import Any
from uuid import UUID

from supabase import create_client
from workflow_app.models import ImportJob, JobStatus
from workflow_app.validation import ProductRow


def _import_job_from_row(row: dict[str, Any]) -> ImportJob:
    created_at = row.get("created_at")
    if isinstance(created_at, str):
        created_at = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
    return ImportJob(
        id=UUID(str(row["id"])),
        owner_id=UUID(str(row["owner_id"])),
        filename=str(row["filename"]),
        status=JobStatus(str(row["status"])),
        total_rows=int(row.get("total_rows", 0)),
        processed_rows=int(row.get("processed_rows", 0)),
        failed_rows=int(row.get("failed_rows", 0)),
        created_at=created_at,
    )


class SupabaseImportStore:
    def __init__(self, url: str, key: str, access_token: str = "") -> None:
        self._url = url
        self._key = key
        self._access_token = access_token

    def _client(self) -> Any:
        client = create_client(self._url, self._key)
        if self._access_token:
            client.postgrest.auth(self._access_token)
        return client

    async def create(self, owner_id: UUID, filename: str, content: bytes) -> ImportJob:
        client = self._client()
        result = (
            await client.table("import_jobs")
            .insert(
                {
                    "owner_id": str(owner_id),
                    "filename": filename,
                    "status": "queued",
                }
            )
            .execute()
        )
        return _import_job_from_row(result.data[0])

    async def get(self, owner_id: UUID, job_id: UUID) -> ImportJob | None:
        client = self._client()
        result = (
            await client.table("import_jobs")
            .select("*")
            .eq(
                "id",
                str(job_id),
            )
            .eq("owner_id", str(owner_id))
            .execute()
        )
        if not result.data:
            return None
        return _import_job_from_row(result.data[0])


class SupabaseProductStore:
    def __init__(self, url: str, service_role_key: str) -> None:
        self._url = url
        self._service_role_key = service_role_key

    async def upsert(self, owner_id: UUID, product: ProductRow) -> None:
        client = create_client(self._url, self._service_role_key)
        await (
            client.table("products")
            .upsert(
                {
                    "owner_id": str(owner_id),
                    "sku": product.sku,
                    "name": product.name,
                    "price": float(product.price),
                    "quantity": product.quantity,
                },
                on_conflict="owner_id,sku",
            )
            .execute()
        )
