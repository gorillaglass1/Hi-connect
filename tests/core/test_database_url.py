import pytest
from sqlalchemy.engine import URL

from app.core import database


def test_normalize_database_url_converts_postgres_scheme(monkeypatch):
    monkeypatch.delenv("SUPABASE_DB_PASSWORD", raising=False)
    monkeypatch.delenv("SUPABASE_DB_HOST", raising=False)

    assert database._normalize_database_url(
        "postgres://user:pass@example.com:5432/postgres"
    ) == "postgresql+asyncpg://user:pass@example.com:5432/postgres"


def test_postgres_url_with_raw_password_accepts_special_characters():
    url = database._postgres_url_with_raw_password(
        "postgresql://postgres:p@ss:word@example.com:5432/postgres?sslmode=require"
    )

    assert isinstance(url, URL)
    assert url.drivername == "postgresql+asyncpg"
    assert url.username == "postgres"
    assert url.password == "p@ss:word"
    assert url.host == "example.com"
    assert url.port == 5432
    assert url.database == "postgres"
    assert url.query == {"sslmode": "require"}


def test_database_url_from_parts_rejects_placeholder_host(monkeypatch):
    monkeypatch.setenv("SUPABASE_DB_HOST", "<host>")
    monkeypatch.setenv("SUPABASE_DB_PASSWORD", "secret")

    with pytest.raises(ValueError, match="SUPABASE_DB_HOST still contains"):
        database._database_url_from_parts()


def test_with_asyncpg_pooler_options_adds_prepared_statement_cache_size():
    result = database._with_asyncpg_pooler_options(
        "postgresql+asyncpg://user:pass@example.com/postgres"
    )

    assert result.endswith("?prepared_statement_cache_size=0")


def test_with_asyncpg_pooler_options_does_not_duplicate_existing_option():
    original = (
        "postgresql+asyncpg://user:pass@example.com/postgres"
        "?prepared_statement_cache_size=0"
    )

    assert database._with_asyncpg_pooler_options(original) == original
