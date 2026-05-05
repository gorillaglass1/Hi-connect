from __future__ import annotations

import logging
import os
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncEngine

from app.core.sql_bootstrap import _normalize_sql_for_sqlite, _split_sql_statements

logger = logging.getLogger(__name__)

ENABLE_DUMMY_DATA_ENV = "ENABLE_STARTUP_DUMMY_DATA"


def _is_enabled() -> bool:
    value = os.getenv(ENABLE_DUMMY_DATA_ENV, "false").strip().lower()
    return value in {"1", "true", "yes", "on"}


async def load_dummy_data_from_dml(engine: AsyncEngine, sql_dir: str = "sql") -> None:
    if not _is_enabled():
        logger.info("%s is disabled. Skipping DML dummy data load.", ENABLE_DUMMY_DATA_ENV)
        return

    base_path = Path(sql_dir)
    if not base_path.exists():
        return

    dml_files = sorted(
        [p for p in base_path.iterdir() if p.is_file() and p.name.lower().endswith("dml.sql")]
    )
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
            for statement in statements:
                executable = statement
                if engine.dialect.name == "sqlite":
                    executable = _normalize_sql_for_sqlite(statement)
                try:
                    await conn.execute(text(executable))
                except SQLAlchemyError as exc:
                    logger.warning(
                        "Skipping dummy DML statement from %s due to error: %s",
                        sql_file.name,
                        exc,
                    )

            await conn.execute(
                text(
                    "INSERT INTO _dml_bootstrap_runs (file_name) VALUES (:file_name)"
                ),
                {"file_name": sql_file.name},
            )
