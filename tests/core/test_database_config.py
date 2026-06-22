import pytest
from sqlalchemy.engine import URL

from app.core import database


def test_normalize_database_url_converts_postgres_schemes(monkeypatch):
    monkeypatch.setenv("SUPABASE_DB_PASSWORD", "")
    monkeypatch.setenv("SUPABASE_DB_HOST", "")

    assert (
        database._normalize_database_url("postgres://user:pass@example.com/db")
        == "postgresql+asyncpg://user:pass@example.com/db"
    )
    assert (
        database._normalize_database_url("postgresql://user:pass@example.com/db")
        == "postgresql+asyncpg://user:pass@example.com/db"
    )
    assert (
        database._normalize_database_url("sqlite+aiosqlite:///./local.db")
        == "sqlite+aiosqlite:///./local.db"
    )


def test_database_url_from_split_supabase_parts_uses_url_object(monkeypatch):
    monkeypatch.setenv("SUPABASE_DB_HOST", "db.example.supabase.co")
    monkeypatch.setenv("SUPABASE_DB_PASSWORD", "raw:password/with@chars")
    monkeypatch.setenv("SUPABASE_DB_USER", "postgres")
    monkeypatch.setenv("SUPABASE_DB_PORT", "6543")
    monkeypatch.setenv("SUPABASE_DB_NAME", "postgres")
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("SUPABASE_DB_URL", raising=False)

    url = database._database_url()

    assert isinstance(url, URL)
    assert url.drivername == "postgresql+asyncpg"
    assert url.username == "postgres"
    assert url.password == "raw:password/with@chars"
    assert url.host == "db.example.supabase.co"
    assert url.port == 6543
    assert url.database == "postgres"


def test_database_url_repairs_raw_password_in_postgres_url(monkeypatch):
    monkeypatch.delenv("SUPABASE_DB_HOST", raising=False)
    monkeypatch.delenv("SUPABASE_DB_PASSWORD", raising=False)
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql://postgres:raw:password/with@chars@db.example.com:5432/postgres",
    )

    url = database._database_url()

    assert isinstance(url, URL)
    assert url.drivername == "postgresql+asyncpg"
    assert url.password == "raw:password/with@chars"
    assert url.host == "db.example.com"


def test_database_url_replaces_documented_placeholders(monkeypatch):
    monkeypatch.setenv("SUPABASE_DB_PASSWORD", "secret")
    monkeypatch.setenv("SUPABASE_DB_HOST", "db.example.com")

    resolved = database._resolve_database_url_placeholders(
        "postgresql://postgres:[PASSWORD]@[HOST]:5432/postgres"
    )

    assert resolved == "postgresql://postgres:secret@db.example.com:5432/postgres"


def test_validate_no_placeholder_rejects_angle_bracket_values():
    with pytest.raises(ValueError, match="placeholder"):
        database._validate_no_placeholder("SUPABASE_DB_HOST", "<project-ref>")


def test_with_asyncpg_pooler_options_adds_prepared_statement_cache_size():
    url = database._with_asyncpg_pooler_options(
        "postgresql+asyncpg://user:pass@example.com/db"
    )

    assert url.endswith("?prepared_statement_cache_size=0")


def test_with_asyncpg_pooler_options_preserves_existing_query_separator():
    url = database._with_asyncpg_pooler_options(
        "postgresql+asyncpg://user:pass@example.com/db?ssl=require"
    )

    assert url.endswith("?ssl=require&prepared_statement_cache_size=0")


def test_with_asyncpg_pooler_options_updates_url_object_query():
    url = URL.create(
        "postgresql+asyncpg",
        username="user",
        password="pass",
        host="example.com",
        database="db",
    )

    updated = database._with_asyncpg_pooler_options(url)

    assert isinstance(updated, URL)
    assert updated.query["prepared_statement_cache_size"] == "0"
