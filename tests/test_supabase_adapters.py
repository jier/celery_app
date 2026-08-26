import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID

from workflow_app.supabase_auth import SupabaseAuthenticator
from workflow_app.supabase_store import SupabaseImportStore, SupabaseProductStore


def _async_client_with_empty_list() -> tuple[MagicMock, AsyncMock]:
    client = MagicMock()
    query = client.table.return_value.select.return_value
    result = query.eq.return_value.order.return_value
    result.execute = AsyncMock(return_value=SimpleNamespace(data=[]))
    return client, AsyncMock(return_value=client)


def test_authenticator_uses_async_supabase_client() -> None:
    client = MagicMock()
    client.auth.get_user = AsyncMock(
        return_value=SimpleNamespace(
            user=SimpleNamespace(
                id="11111111-1111-1111-1111-111111111111", email="user@example.com"
            )
        )
    )
    create_client = AsyncMock(return_value=client)

    with patch("workflow_app.supabase_auth.acreate_client", create_client):
        authenticator = SupabaseAuthenticator("http://supabase.test", "anon")
        user = asyncio.run(authenticator.authenticate("token"))

    assert user.id == UUID("11111111-1111-1111-1111-111111111111")
    create_client.assert_awaited_once_with("http://supabase.test", "anon")
    client.postgrest.auth.assert_called_once_with("token")
    client.auth.get_user.assert_awaited_once_with("token")


def test_import_store_uses_async_client_for_list() -> None:
    _, create_client = _async_client_with_empty_list()
    owner_id = UUID("11111111-1111-1111-1111-111111111111")

    with patch("workflow_app.supabase_store.acreate_client", create_client):
        jobs = asyncio.run(SupabaseImportStore("http://supabase.test", "anon").list(owner_id))

    assert jobs == []
    create_client.assert_awaited_once_with("http://supabase.test", "anon")


def test_product_store_creates_an_async_client_per_operation() -> None:
    _, create_client = _async_client_with_empty_list()
    owner_id = UUID("11111111-1111-1111-1111-111111111111")
    store = SupabaseProductStore("http://supabase.test", "service-role")

    with patch("workflow_app.supabase_store.acreate_client", create_client):
        assert asyncio.run(store.list(owner_id)) == []
        assert asyncio.run(store.list(owner_id)) == []

    assert create_client.await_count == 2
