from decimal import Decimal, ROUND_HALF_UP

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories import recommendation_history_repo, user_preference_repo
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
DEFAULT_USER_PREFERENCES = UserPreferenceUpdate(
    weight_price=Decimal("1.0"),
    weight_waiting_time=Decimal("1.0"),
    weight_distance=Decimal("1.0"),
    weight_facilities=Decimal("1.0"),
    safety_margin=Decimal("1.1"),
)


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

        await self._ensure_user_preferences(user.user_id)
        return await self.get_user(user.user_id)

    async def get_user_preferences(self, user_id: int) -> UserPreferenceResponse:
        return await self._ensure_user_preferences(user_id)

    async def update_user_preferences(
        self,
        user_id: int,
        payload: UserPreferenceUpdate,
    ) -> UserPreferenceResponse:
        pref = await self._ensure_user_preferences(user_id)
        return await user_preference_repo.update_user_preferences(
            self.db,
            pref,
            payload,
        )

    async def learn_from_selected_recommendation(
        self,
        user_id: int,
        payload: UserPreferenceLearningRequest,
    ) -> UserPreferenceResponse:
        pref = await self._ensure_user_preferences(user_id)
        selected_history = await recommendation_history_repo.get_latest_recommendation_history(
            self.db,
            user_id=user_id,
            chrstn_mno=payload.chrstn_mno,
        )
        if selected_history is None:
            raise HTTPException(
                status_code=404,
                detail="Selected recommendation history was not found",
            )

        score_values = _history_to_score_values(selected_history)
        if score_values is None:
            score_history = await recommendation_history_repo.get_latest_recommendation_history_with_score_snapshot(
                self.db,
                user_id=user_id,
                chrstn_mno=payload.chrstn_mno,
            )

            score_values = _score_values_from_payload(payload)
            if score_values is None and score_history is not None:
                score_values = _history_to_score_values(score_history)
            if score_values is None:
                raise HTTPException(
                    status_code=409,
                    detail="Selected recommendation history does not have score snapshot",
                )


        current_weights = {
            "weight_price": Decimal(str(pref.weight_price)),
            "weight_waiting_time": Decimal(str(pref.weight_waiting_time)),
            "weight_distance": Decimal(str(pref.weight_distance)),
            "weight_facilities": Decimal(str(pref.weight_facilities)),
        }
        observed_weights = _scores_to_observed_weights(
            score_values,
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
            pref,
            update_payload,
        )
        await recommendation_history_repo.mark_recommendation_selected(
            self.db,
            selected_history,
        )
        return updated_pref

    async def get_user(self, user_id: int) -> UserResponse:
        await self._get_user_or_404(user_id)
        await self._ensure_user_preferences(user_id)
        return await user_preference_repo.get_user(self.db, user_id)

    async def _ensure_user_preferences(self, user_id: int):
        await self._get_user_or_404(user_id)
        pref = await user_preference_repo.get_user_preferences(self.db, user_id)
        if pref is not None:
            return pref
        return await user_preference_repo.create_user_preferences(
            self.db,
            user_id,
            DEFAULT_USER_PREFERENCES,
        )

    async def _get_user_or_404(self, user_id: int):
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
    scores: dict[str, Decimal],
    weight_total: Decimal,
) -> dict[str, Decimal]:
    score_values = {
        key: _non_negative_decimal(value)
        for key, value in scores.items()
    }
    score_total = sum(score_values.values(), Decimal("0"))
    if score_total <= 0:
        equal_weight = weight_total / Decimal(len(score_values))
        return {key: equal_weight for key in score_values}

    return {
        key: (score / score_total) * weight_total
        for key, score in score_values.items()
    }


def _non_negative_decimal(value: Decimal) -> Decimal:
    decimal_value = Decimal(str(value))
    return decimal_value if decimal_value > 0 else Decimal("0")

def _history_has_score_snapshot(history) -> bool:
    return all(
        getattr(history, field) is not None
        for field in (
            "price_score",
            "waiting_time_score",
            "distance_score",
            "facilities_score",
        )
    )


def _history_to_score_values(history) -> dict[str, Decimal] | None:
    if not _history_has_score_snapshot(history):
        return None

    return {
        "weight_price": Decimal(str(history.price_score)),
        "weight_waiting_time": Decimal(str(history.waiting_time_score)),
        "weight_distance": Decimal(str(history.distance_score)),
        "weight_facilities": Decimal(str(history.facilities_score))
    }

def _score_values_from_payload(
        payload: UserPreferenceLearningRequest,
    )-> dict[str, Decimal] | None:
    score_values = {
        "weight_price": payload.price_score,
        "weight_waiting_time": payload.waiting_score,
        "weight_distance": payload.distance_score,
        "weight_facilities": payload.facilities_score
    }

    if all(value is None for value in score_values.values()):
        return None

    if any(value is None for value in score_values.values()):
        raise HTTPException(
            status_code=422,
            detail="All score fields are required when using client-side score fallback",
        )

    return {key: Decimal(str(value)) for key, value in score_values.items()}

def _blend_weight(current: Decimal, observed: Decimal) -> Decimal:
    learned = (
        current * (Decimal("1") - PREFERENCE_LEARNING_RATE)
        + observed * PREFERENCE_LEARNING_RATE
    )
    clamped = min(MAX_WEIGHT, max(MIN_WEIGHT, learned))
    return clamped.quantize(WEIGHT_PRECISION, rounding=ROUND_HALF_UP)
