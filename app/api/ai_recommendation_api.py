from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.ai_recommendation_schema import (
    AIRecommendationResponse,
    AiRecommendationRequest,
)
from app.services.ai_recommendation_service import AiRecommendationService

router = APIRouter(prefix="/ai-recommendations", tags=["ai-recommendations"])


@router.post(
    "",
    response_model=AIRecommendationResponse,
    status_code=status.HTTP_200_OK,
)
async def create_ai_recommendation(
    payload: AiRecommendationRequest,
    db: AsyncSession = Depends(get_db),
):
    try:
        return await AiRecommendationService(db).create_ai_response(payload)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc
