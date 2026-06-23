"""검수된 수소 팁 풀 로딩 및 조회.

안전 원칙: 팁 본문(tip)은 LLM이 생성하지 않는다. LLM은 풀에 존재하는
tip_id만 선택하고, 본문은 이 검수 풀에서 꺼내 결합한다. 풀에 없는 ID가 오면
default 팁으로 폴백한다.
"""

import json
import logging
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

logger = logging.getLogger("hydrogen_tip_service")

_TIPS_PATH = Path(__file__).resolve().parents[1] / "data" / "hydrogen_tips.json"


@dataclass(frozen=True)
class HydrogenTip:
    tip_id: str
    tags: tuple[str, ...]
    title: str
    tip: str


class HydrogenTipPool:
    """tips.json을 메모리에 적재한 검수 팁 풀."""

    def __init__(self, tips: list[HydrogenTip], default_tip_id: str):
        self._by_id: dict[str, HydrogenTip] = {t.tip_id: t for t in tips}
        self._default_tip_id = default_tip_id
        if default_tip_id not in self._by_id and tips:
            # 설정된 기본 ID가 없으면 첫 팁을 기본으로 사용.
            self._default_tip_id = tips[0].tip_id

    @property
    def default_tip(self) -> HydrogenTip:
        return self._by_id[self._default_tip_id]

    def get(self, tip_id: str | None) -> HydrogenTip:
        """tip_id로 팁을 조회한다. 없으면 default 팁으로 폴백한다."""
        if tip_id and tip_id in self._by_id:
            return self._by_id[tip_id]
        if tip_id:
            logger.warning("풀에 없는 tip_id 요청, default로 폴백: %s", tip_id)
        return self.default_tip

    def has(self, tip_id: str | None) -> bool:
        return bool(tip_id) and tip_id in self._by_id

    def prompt_catalog(self) -> list[dict]:
        """LLM 프롬프트에 넣을 팁 카탈로그(본문 제외, 선택 근거용 메타데이터)."""
        return [
            {"tip_id": t.tip_id, "tags": list(t.tags), "title": t.title}
            for t in self._by_id.values()
        ]


@lru_cache(maxsize=1)
def get_tip_pool() -> HydrogenTipPool:
    """검수 팁 풀 싱글턴. 파일을 읽지 못하면 안전한 최소 기본 팁으로 폴백한다."""
    try:
        raw = json.loads(_TIPS_PATH.read_text(encoding="utf-8"))
        tips = [
            HydrogenTip(
                tip_id=item["tip_id"],
                tags=tuple(item.get("tags", [])),
                title=item.get("title", ""),
                tip=item["tip"],
            )
            for item in raw.get("tips", [])
        ]
        default_id = raw.get("default_tip_id", tips[0].tip_id if tips else "")
        if not tips:
            raise ValueError("tips.json에 팁이 비어 있습니다.")
        return HydrogenTipPool(tips, default_id)
    except Exception as exc:  # pragma: no cover - 방어적
        logger.error("수소 팁 풀 로딩 실패, 내장 기본 팁 사용: %s", exc)
        fallback = HydrogenTip(
            tip_id="tip_general_01",
            tags=("default",),
            title="안전한 충전 습관",
            tip="충전 중에는 시동을 끄고 노즐 체결 상태를 확인하세요.",
        )
        return HydrogenTipPool([fallback], fallback.tip_id)
