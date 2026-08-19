from typing import Annotated, Protocol
from uuid import UUID

from fastapi import FastAPI, File, Header, HTTPException, UploadFile
from fastapi.staticfiles import StaticFiles

from workflow_app.models import ImportJob, ProductRow, User


class Authenticator(Protocol):
    async def authenticate(self, access_token: str) -> User: ...


class ImportStore(Protocol):
    async def create(self, owner_id: UUID, filename: str, content: bytes) -> ImportJob: ...
    async def get(self, owner_id: UUID, job_id: UUID) -> ImportJob | None: ...
    async def list(self, owner_id: UUID) -> list[ImportJob]: ...


class ProductStore(Protocol):
    async def list(self, owner_id: UUID) -> list[ProductRow]: ...


class ImportDispatcher(Protocol):
    def enqueue(self, job_id: UUID) -> None: ...


def create_app(
    auth: Authenticator,
    imports: ImportStore,
    dispatcher: ImportDispatcher,
    products: ProductStore | None = None,
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

        user = await auth.authenticate(token)
        content = await file.read()
        job = await imports.create(
            owner_id=user.id,
            filename=file.filename or "unnamed.csv",
            content=content,
        )
        dispatcher.enqueue(job.id)
        return job

    @app.get("/imports/{job_id}", response_model_exclude_none=True)
    async def get_import(
        job_id: UUID,
        authorization: Annotated[str, Header(alias="Authorization")],
    ) -> ImportJob:
        if not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Missing Bearer token")
        token = authorization.removeprefix("Bearer ")

        user = await auth.authenticate(token)
        job = await imports.get(owner_id=user.id, job_id=job_id)
        if job is None:
            raise HTTPException(status_code=404, detail="Import job not found")
        return job

    @app.get("/imports/list", response_model_exclude_none=True)
    async def list_imports(
        authorization: Annotated[str, Header(alias="Authorization")],
    ) -> list[ImportJob]:
        if not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Missing Bearer token")
        token = authorization.removeprefix("Bearer ")

        user = await auth.authenticate(token)
        return await imports.list(owner_id=user.id)

    if products is not None:

        @app.get("/products", response_model_exclude_none=True)
        async def list_products(
            authorization: Annotated[str, Header(alias="Authorization")],
        ) -> list[ProductRow]:
            if not authorization.startswith("Bearer "):
                raise HTTPException(status_code=401, detail="Missing Bearer token")
            token = authorization.removeprefix("Bearer ")

            user = await auth.authenticate(token)
            return await products.list(owner_id=user.id)

    app.mount("/", StaticFiles(directory="static", html=True), name="static")

    return app
