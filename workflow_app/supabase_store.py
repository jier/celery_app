from typing import Any
from uuid import UUID

from supabase import create_client
from workflow_app.models import ImportJob
from workflow_app.validation import ProductRow

BUCKET = "import-files"


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
        job = ImportJob.from_supabase_row(result.data[0])
        storage_path = f"{owner_id}/{job.id}.csv"
        await client.storage.from_(BUCKET).upload(
            storage_path,
            content,
            {"content-type": "text/csv"},
        )
        return job

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
        return ImportJob.from_supabase_row(result.data[0])


class SupabaseProductStore:
    def __init__(self, url: str, service_role_key: str) -> None:
        self._client = create_client(url, service_role_key)
        self._url = url
        self._service_role_key = service_role_key

    async def upsert(self, owner_id: UUID, product: ProductRow) -> None:
        await (
            self._client.table("products")
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


def download_csv(url: str, service_role_key: str, owner_id: UUID, job_id: UUID) -> bytes:
    client = create_client(url, service_role_key)
    storage_path = f"{owner_id}/{job_id}.csv"
    return client.storage.from_(BUCKET).download(storage_path)
