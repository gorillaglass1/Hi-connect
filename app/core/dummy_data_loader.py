from __future__ import annotations

import logging
import os
from pathlib import Path
import re

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncEngine

from app.core.sql_bootstrap import _normalize_sql_for_sqlite, _split_sql_statements

logger = logging.getLogger(__name__)

ENABLE_DUMMY_DATA_ENV = "ENABLE_STARTUP_DUMMY_DATA"


def _is_enabled() -> bool:
    value = os.getenv(ENABLE_DUMMY_DATA_ENV, "true").strip().lower()
    return value in {"1", "true", "yes", "on"}


async def load_dummy_data_from_dml(engine: AsyncEngine, sql_dir: str = "sql") -> None:
    if not _is_enabled():
        logger.info("%s is disabled. Skipping DML dummy data load.", ENABLE_DUMMY_DATA_ENV)
        return

    base_path = Path(sql_dir)
    if not base_path.exists():
        return

    dml_files = _ordered_dml_files(base_path)
    if not dml_files:
        return

    async with engine.begin() as conn:
        await conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS _dml_bootstrap_runs (
                    file_name TEXT PRIMARY KEY,
                    executed_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
        )

        for sql_file in dml_files:
            already_run = await conn.execute(
                text(
                    "SELECT 1 FROM _dml_bootstrap_runs WHERE file_name = :file_name LIMIT 1"
                ),
                {"file_name": sql_file.name},
            )
            if already_run.scalar_one_or_none():
                continue

            raw_sql = sql_file.read_text(encoding="utf-8")
            statements = _split_sql_statements(raw_sql)
            if engine.dialect.name == "sqlite":
                table_name = _extract_insert_table_name(statements[0]) if statements else None
                if table_name and await _sqlite_table_has_rows(conn, table_name):
                    await _mark_dml_file_as_run(conn, sql_file.name)
                    continue

            for statement in statements:
                executable = statement
                if engine.dialect.name == "sqlite":
                    executable = _normalize_sql_for_sqlite(statement)
                    executable = _normalize_insert_for_sqlite(executable)
                try:
                    await conn.execute(text(executable))
                except SQLAlchemyError as exc:
                    logger.warning(
                        "Skipping dummy DML statement from %s due to error: %s",
                        sql_file.name,
                        exc,
                    )

            await _mark_dml_file_as_run(conn, sql_file.name)


def _ordered_dml_files(base_path: Path) -> list[Path]:
    files = [
        p
        for p in base_path.iterdir()
        if p.is_file() and p.name.lower().endswith("dml.sql")
    ]
    order = {
        "users dml.sql": 0,
        "hydrogen_station dml.sql": 1,
        "vehicles dml.sql": 2,
        "hydrogen_charger dml.sql": 3,
        "hydrogen_station_realtime dml.sql": 4,
        "hydrogen_station_reservation dml.sql": 5,
        "charging_log dml.sql": 6,
        "recommendation_history dml.sql": 7,
    }
    return sorted(
        files,
        key=lambda path: (order.get(path.name.lower(), 100), path.name.lower()),
    )


def _extract_insert_table_name(statement: str) -> str | None:
    match = re.match(
        r"^\s*insert\s+into\s+[`\"]?([a-zA-Z_][\w]*)[`\"]?",
        statement,
        flags=re.IGNORECASE,
    )
    if match is None:
        return None
    return match.group(1)


def _normalize_insert_for_sqlite(statement: str) -> str:
    return re.sub(
        r"^\s*insert\s+into\s+",
        "INSERT OR IGNORE INTO ",
        statement,
        count=1,
        flags=re.IGNORECASE,
    )


async def _sqlite_table_has_rows(conn, table_name: str) -> bool:
    result = await conn.execute(
        text(f'SELECT 1 FROM "{table_name}" LIMIT 1')
    )
    return result.scalar_one_or_none() is not None


async def _mark_dml_file_as_run(conn, file_name: str) -> None:
    await conn.execute(
        text(
            "INSERT OR IGNORE INTO _dml_bootstrap_runs (file_name) VALUES (:file_name)"
        ),
        {"file_name": file_name},
    )
