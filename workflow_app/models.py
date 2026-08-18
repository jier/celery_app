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
