from fastapi import FastAPI

from workflow_app.api import create_app
from workflow_app.dispatcher import CeleryDispatcher
from workflow_app.settings import Settings
from workflow_app.supabase_auth import SupabaseAuthenticator
from workflow_app.supabase_store import SupabaseImportStore

settings = Settings()

app: FastAPI = create_app(
    auth=SupabaseAuthenticator(
        url=settings.supabase_url,
        anon_key=settings.supabase_anon_key,
    ),
    imports=SupabaseImportStore(
        url=settings.supabase_url,
        key=settings.supabase_service_role_key,
    ),
    dispatcher=CeleryDispatcher(),
)
