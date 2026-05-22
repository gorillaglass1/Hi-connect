import os
from urllib.parse import urlsplit

from sqlalchemy.pool import NullPool
from sqlalchemy.engine import URL
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase

from app.core.config import load_env


load_env()


def _normalize_database_url(url: str) -> str:
    url = _resolve_database_url_placeholders(url)
    _validate_database_url(url)
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+asyncpg://", 1)
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+asyncpg://", 1)
    return url


def _postgres_url_with_raw_password(url: str) -> URL | None:
    url = _resolve_database_url_placeholders(url)
    scheme, separator, remainder = url.partition("://")
    if separator == "" or scheme not in {"postgres", "postgresql", "postgresql+asyncpg"}:
        return None

    userinfo, at, hostinfo = remainder.rpartition("@")
    if at == "" or ":" not in userinfo:
        return None

    username, password = userinfo.split(":", 1)
    host_port, slash, database_and_query = hostinfo.partition("/")
    host, colon, port = host_port.rpartition(":")
    if colon == "":
        host = host_port
        port = None
    database, question_mark, query_string = database_and_query.partition("?")
    query = {}
    if question_mark:
        for item in query_string.split("&"):
            key, separator, value = item.partition("=")
            if separator:
                query[key] = value

    if not username or not password or not host:
        return None

    return URL.create(
        "postgresql+asyncpg",
        username=username,
        password=password,
        host=host,
        port=int(port) if port else None,
        database=database if slash else None,
        query=query,
    )


def _validate_database_url(url: str) -> None:
    try:
        parsed = urlsplit(url)
        _ = parsed.port
    except ValueError as exc:
        repaired_url = _postgres_url_with_raw_password(url)
        if repaired_url is not None:
            return
        raise ValueError(
            "Invalid DATABASE_URL/SUPABASE_DB_URL. If your DB password contains "
            "special characters, URL-encode the password or use the split "
            "SUPABASE_DB_* env vars instead."
        ) from exc


def _database_url_from_parts() -> URL | None:
    host = os.getenv("SUPABASE_DB_HOST")
    password = os.getenv("SUPABASE_DB_PASSWORD")
    if not host or not password:
        return None

    username = os.getenv("SUPABASE_DB_USER", "postgres")
    _validate_no_placeholder("SUPABASE_DB_HOST", host)
    _validate_no_placeholder("SUPABASE_DB_USER", username)

    return URL.create(
        "postgresql+asyncpg",
        username=username,
        password=password,
        host=host,
        port=int(os.getenv("SUPABASE_DB_PORT", "5432")),
        database=os.getenv("SUPABASE_DB_NAME", "postgres"),
    )


def _database_url() -> str | URL:
    split_url = _database_url_from_parts()
    if split_url is not None:
        return split_url

    raw_url = os.getenv("DATABASE_URL") or os.getenv("SUPABASE_DB_URL")
    if raw_url:
        repaired_url = _postgres_url_with_raw_password(raw_url)
        if repaired_url is not None:
            return repaired_url
        return _normalize_database_url(raw_url)

    return "sqlite+aiosqlite:///./test.db"


def _resolve_database_url_placeholders(url: str) -> str:
    password = os.getenv("SUPABASE_DB_PASSWORD", "")
    host = os.getenv("SUPABASE_DB_HOST", "")
    return (
        url.replace("[비밀번호]", password)
        .replace("[PASSWORD]", password)
        .replace("[password]", password)
        .replace("[호스트]", host)
        .replace("[HOST]", host)
        .replace("[host]", host)
    )


def _validate_no_placeholder(name: str, value: str) -> None:
    if "<" in value or ">" in value:
        raise ValueError(
            f"{name} still contains a placeholder: {value}. Replace it with the "
            "actual value from Supabase Database connection settings."
        )


def _with_asyncpg_pooler_options(database_url: str | URL) -> str | URL:
    if isinstance(database_url, URL):
        if database_url.drivername == "postgresql+asyncpg":
            return database_url.update_query_dict(
                {"prepared_statement_cache_size": "0"}
            )
        return database_url

    if database_url.startswith("postgresql+asyncpg") and (
        "prepared_statement_cache_size" not in database_url
    ):
        separator = "&" if "?" in database_url else "?"
        return f"{database_url}{separator}prepared_statement_cache_size=0"

    return database_url


DB_URL = _database_url()
DB_URL = _with_asyncpg_pooler_options(DB_URL)

if str(DB_URL).startswith("sqlite"):
    engine = create_async_engine(
        DB_URL,
        connect_args={"check_same_thread": False},
    )
else:
    engine = create_async_engine(
        DB_URL,
        connect_args={"statement_cache_size": 0},
        pool_pre_ping=True,
        pool_recycle=180,
        poolclass=NullPool,
    )


async_session = async_sessionmaker(autocommit=False, autoflush=False, bind=engine, class_=AsyncSession)

class Base(DeclarativeBase):
    pass

async def get_db():
    async with async_session() as session:
        yield session
