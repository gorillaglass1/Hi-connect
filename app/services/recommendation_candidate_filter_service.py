import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.text_to_sql_service import TextToSqlService


logger = logging.getLogger("recommendation_candidate_filter_service")


class RecommendationCandidateFilterService:
    """Builds an optional station candidate filter before recommendation scoring."""

    def __init__(self, db: AsyncSession):
        self.text_to_sql_service = TextToSqlService(db)

    async def filter_by_natural_language(
        self,
        nl_query: str | None,
    ) -> list[str] | None:
        if not nl_query or not nl_query.strip():
            return None

        logger.info("Running Text-to-SQL candidate filter: %s", nl_query)
        candidate_ids = await self.text_to_sql_service.execute_semantic_search(nl_query)
        if candidate_ids is None:
            logger.warning("Text-to-SQL candidate filter failed. Scoring all stations.")
            return None

        logger.info("Text-to-SQL candidate filter matched %s stations.", len(candidate_ids))
        return candidate_ids
