from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel


class JobStatus(StrEnum):
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class User(BaseModel):
    id: UUID
    email: str


class ImportJob(BaseModel):
    id: UUID
    owner_id: UUID
    filename: str
    status: JobStatus
    total_rows: int = 0
    processed_rows: int = 0
    failed_rows: int = 0
    created_at: datetime | None = None

    @classmethod
    def from_supabase_row(cls, row: dict) -> "ImportJob":
        created_at_val = row.get("created_at")
        if isinstance(created_at_val, str):
            created_at_val = datetime.fromisoformat(created_at_val.replace("Z", "+00:00"))
        return cls(
            id=UUID(str(row["id"])),
            owner_id=UUID(str(row["owner_id"])),
            filename=str(row["filename"]),
            status=JobStatus(str(row["status"])),
            total_rows=int(row.get("total_rows", 0)),
            processed_rows=int(row.get("processed_rows", 0)),
            failed_rows=int(row.get("failed_rows", 0)),
            created_at=created_at_val,
        )
