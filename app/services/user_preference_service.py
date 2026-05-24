from decimal import Decimal, ROUND_HALF_UP

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories import recommendation_history_repo, user_preference_repo
from app.schemas.recommendation_schema import SubScores
from app.schemas.user_preference_schema import (
    UserCreate,
    UserPreferenceLearningRequest,
    UserPreferenceUpdate,
    UserPreferenceResponse,
    UserResponse,
)

PREFERENCE_LEARNING_RATE = Decimal("0.10")
DEFAULT_WEIGHT_TOTAL = Decimal("4.00")
MIN_WEIGHT = Decimal("0.00")
MAX_WEIGHT = Decimal("3.00")
WEIGHT_PRECISION = Decimal("0.01")


class UserPreferenceService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_user(self, payload: UserCreate) -> UserResponse:
        try:
            user = await user_preference_repo.create_user(self.db, payload)
        except IntegrityError:
            await self.db.rollback()
            raise HTTPException(
                status_code=409,
                detail="User email already exists",
            )

        await user_preference_repo.get_user_preferences(self.db, user.user_id)
        return await self.get_user(user.user_id)

    async def get_user_preferences(self, user_id: int) -> UserPreferenceResponse:
        pref = await user_preference_repo.get_user_preferences(self.db, user_id)
        if pref is None:
            raise HTTPException(
                status_code=404,
                detail=f"User with ID {user_id} not found",
            )
        return pref

    async def update_user_preferences(
        self,
        user_id: int,
        payload: UserPreferenceUpdate,
    ) -> UserPreferenceResponse:
        pref = await user_preference_repo.update_user_preferences(
            self.db,
            user_id,
            payload,
        )
        if pref is None:
            raise HTTPException(
                status_code=404,
                detail=f"User with ID {user_id} not found",
            )
        return pref

    async def learn_from_selected_recommendation(
        self,
        user_id: int,
        payload: UserPreferenceLearningRequest,
    ) -> UserPreferenceResponse:
        pref = await user_preference_repo.get_user_preferences(self.db, user_id)
        if pref is None:
            raise HTTPException(
                status_code=404,
                detail=f"User with ID {user_id} not found",
            )

        current_weights = {
            "weight_price": Decimal(str(pref.weight_price)),
            "weight_waiting_time": Decimal(str(pref.weight_waiting_time)),
            "weight_distance": Decimal(str(pref.weight_distance)),
            "weight_facilities": Decimal(str(pref.weight_facilities)),
        }
        observed_weights = _scores_to_observed_weights(
            payload.sub_scores,
            _current_weight_total(current_weights),
        )

        update_payload = UserPreferenceUpdate(
            weight_price=_blend_weight(
                current_weights["weight_price"],
                observed_weights["weight_price"],
            ),
            weight_waiting_time=_blend_weight(
                current_weights["weight_waiting_time"],
                observed_weights["weight_waiting_time"],
            ),
            weight_distance=_blend_weight(
                current_weights["weight_distance"],
                observed_weights["weight_distance"],
            ),
            weight_facilities=_blend_weight(
                current_weights["weight_facilities"],
                observed_weights["weight_facilities"],
            ),
            safety_margin=Decimal(str(pref.safety_margin)),
        )

        updated_pref = await user_preference_repo.update_user_preferences(
            self.db,
            user_id,
            update_payload,
        )
        await recommendation_history_repo.mark_latest_recommendation_selected(
            self.db,
            user_id=user_id,
            chrstn_mno=payload.chrstn_mno,
        )
        return updated_pref

    async def get_user(self, user_id: int) -> UserResponse:
        user = await user_preference_repo.get_user(self.db, user_id)
        if user is None:
            raise HTTPException(
                status_code=404,
                detail=f"User with ID {user_id} not found",
            )
        return user


def _current_weight_total(weights: dict[str, Decimal]) -> Decimal:
    total = sum(weights.values(), Decimal("0"))
    return total if total > 0 else DEFAULT_WEIGHT_TOTAL


def _scores_to_observed_weights(
    scores: SubScores,
    weight_total: Decimal,
) -> dict[str, Decimal]:
    score_values = {
        "weight_price": _non_negative_decimal(scores.price),
        "weight_waiting_time": _non_negative_decimal(scores.waiting_time),
        "weight_distance": _non_negative_decimal(scores.distance),
        "weight_facilities": _non_negative_decimal(scores.facilities),
    }
    score_total = sum(score_values.values(), Decimal("0"))
    if score_total <= 0:
        equal_weight = weight_total / Decimal(len(score_values))
        return {key: equal_weight for key in score_values}

    return {
        key: (score / score_total) * weight_total
        for key, score in score_values.items()
    }


def _non_negative_decimal(value: float) -> Decimal:
    decimal_value = Decimal(str(value))
    return decimal_value if decimal_value > 0 else Decimal("0")


def _blend_weight(current: Decimal, observed: Decimal) -> Decimal:
    learned = (
        current * (Decimal("1") - PREFERENCE_LEARNING_RATE)
        + observed * PREFERENCE_LEARNING_RATE
    )
    clamped = min(MAX_WEIGHT, max(MIN_WEIGHT, learned))
    return clamped.quantize(WEIGHT_PRECISION, rounding=ROUND_HALF_UP)
