from typing import Annotated, Protocol
from uuid import UUID

from fastapi import FastAPI, File, Header, HTTPException, UploadFile

from workflow_app.models import ImportJob, User


class Authenticator(Protocol):
    def authenticate(self, access_token: str) -> User: ...


class ImportStore(Protocol):
    def create(self, owner_id: UUID, filename: str, content: bytes) -> ImportJob: ...
    def get(self, owner_id: UUID, job_id: UUID) -> ImportJob | None: ...


class ImportDispatcher(Protocol):
    def enqueue(self, job_id: UUID) -> None: ...


def create_app(
    auth: Authenticator,
    imports: ImportStore,
    dispatcher: ImportDispatcher,
) -> FastAPI:
    app = FastAPI()

    @app.post("/imports", status_code=202, response_model_exclude_none=True)
    async def create_import(
        authorization: Annotated[str, Header(alias="Authorization")],
        file: Annotated[UploadFile, File()],
    ) -> ImportJob:
        if not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Missing Bearer token")
        token = authorization.removeprefix("Bearer ")

        user = auth.authenticate(token)
        content = await file.read()
        job = imports.create(
            owner_id=user.id,
            filename=file.filename or "unnamed.csv",
            content=content,
        )
        dispatcher.enqueue(job.id)
        return job

    return app
