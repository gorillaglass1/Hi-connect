from sqlalchemy.ext.asyncio import AsyncSession
from google import genai

from app.schemas import ai_recommendation_schema
from app.schemas.ai_recommendation_schema import decision_factor_Response, ai_recommendation_post


class AIRecommendationService:
    client = genai.Client()

    def __init__(self, db: AsyncSession):
        self.db = db

    def create_ai_recommendation(self, ai_recommendation: ai_recommendation_post):
        pass
