import logging

from sqlalchemy import inspect, text
from sqlalchemy.ext.asyncio import AsyncConnection

logger = logging.getLogger("schema_migrations")

RECOMMENDATION_HISTORY_SCORE_COLUMNS = {
    "price_score": "NUMERIC(5, 2)",
    "waiting_time_score": "NUMERIC(5, 2)",
    "distance_score": "NUMERIC(5, 2)",
    "facilities_score": "NUMERIC(5, 2)",
}


async def apply_runtime_schema_migrations(conn: AsyncConnection) -> None:
    await _add_missing_columns(
        conn,
        table_name="recommendation_history",
        columns=RECOMMENDATION_HISTORY_SCORE_COLUMNS,
    )


async def _add_missing_columns(
    conn: AsyncConnection,
    *,
    table_name: str,
    columns: dict[str, str],
) -> None:
    existing_columns = await conn.run_sync(_get_existing_columns, table_name)
    if existing_columns is None:
        return

    for column_name, column_type in columns.items():
        if column_name in existing_columns:
            continue

        await conn.execute(
            text(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}")
        )
        logger.info(
            "%s table migrated: added column %s",
            table_name,
            column_name,
        )


def _get_existing_columns(sync_conn, table_name: str) -> set[str] | None:
    inspector = inspect(sync_conn)
    if not inspector.has_table(table_name):
        return None
    return {column["name"] for column in inspector.get_columns(table_name)}
