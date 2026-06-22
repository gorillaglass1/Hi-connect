import pytest
from sqlalchemy import inspect, text
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.schema_migrations import apply_runtime_schema_migrations


@pytest.mark.asyncio
async def test_schema_migration_adds_recommendation_history_score_columns(tmp_path):
    engine = create_async_engine(
        f"sqlite+aiosqlite:///{tmp_path / 'legacy.db'}",
        connect_args={"check_same_thread": False},
    )

    async with engine.begin() as conn:
        await conn.execute(
            text(
                """
                CREATE TABLE recommendation_history (
                    recommendation_id INTEGER PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    chrstn_mno VARCHAR(30) NOT NULL,
                    recommendation_score NUMERIC(5, 2)
                )
                """
            )
        )
        await apply_runtime_schema_migrations(conn)

        columns = await conn.run_sync(
            lambda sync_conn: {
                column["name"]
                for column in inspect(sync_conn).get_columns(
                    "recommendation_history"
                )
            }
        )

    await engine.dispose()

    assert "price_score" in columns
    assert "waiting_time_score" in columns
    assert "distance_score" in columns
    assert "facilities_score" in columns
