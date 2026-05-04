from __future__ import annotations

from pathlib import Path
import logging

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncEngine

logger = logging.getLogger(__name__)


def _split_sql_statements(sql_text: str) -> list[str]:
    statements: list[str] = []
    for chunk in sql_text.split(";"):
        line_joined = "\n".join(
            line for line in chunk.splitlines() if not line.strip().startswith("--")
        ).strip()
        if line_joined:
            statements.append(line_joined)
    return statements


def _normalize_sql_for_sqlite(statement: str) -> str:
    normalized = statement
    normalized = normalized.replace("start_hour", "start_time")
    normalized = normalized.replace("end_hour", "end_time")
    return normalized


async def run_startup_sql(engine: AsyncEngine, sql_dir: str = "sql") -> None:
    base_path = Path(sql_dir)
    if not base_path.exists():
        return

    files = sorted([p for p in base_path.iterdir() if p.is_file()])
    ddl_files = [p for p in files if p.name.lower().endswith("ddl.sql")]
    dml_files = [p for p in files if p.name.lower().endswith("dml.sql")]
    run_files = dml_files if engine.dialect.name == "sqlite" else ddl_files + dml_files

    async with engine.begin() as conn:
        await conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS _sql_bootstrap_runs (
                    file_name TEXT PRIMARY KEY,
                    executed_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
        )

        for sql_file in run_files:
            already_run = await conn.execute(
                text(
                    "SELECT 1 FROM _sql_bootstrap_runs WHERE file_name = :file_name LIMIT 1"
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
                        "Skipping startup SQL statement from %s due to error: %s",
                        sql_file.name,
                        exc,
                    )

            await conn.execute(
                text(
                    "INSERT INTO _sql_bootstrap_runs (file_name) VALUES (:file_name)"
                ),
                {"file_name": sql_file.name},
            )
