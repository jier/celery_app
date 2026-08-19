from uuid import UUID

from fastapi import HTTPException

from supabase import create_client
from workflow_app.models import User


class SupabaseAuthenticator:
    def __init__(self, url: str, anon_key: str) -> None:
        self._url = url
        self._anon_key = anon_key

    async def authenticate(self, access_token: str) -> User:
        try:
            client = create_client(self._url, self._anon_key)
            client.postgrest.auth(access_token)
            supabase_user = await client.auth.get_user(access_token)
        except Exception as exc:
            raise HTTPException(status_code=401, detail="Invalid token") from exc
        if supabase_user is None or supabase_user.user is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return User(
            id=UUID(supabase_user.user.id),
            email=supabase_user.user.email or "",
        )
