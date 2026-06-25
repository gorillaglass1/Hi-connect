"""nearest_recommendation 안내 문구 생성을 위한 시스템 프롬프트/스타일 관리 모듈.

권장 충전 시점(charge_timing)과 안내 문구(message)를 Gemini로 만들 때 사용하는
프롬프트를 한곳에서 관리한다. 매번 비슷한 문장이 나오지 않도록, 역할/규칙을 정의한
고정 system instruction 에 더해 호출마다 말투·표현 스타일을 바꿔 다양성을 높인다.

구성:
- SYSTEM_INSTRUCTION: 모델 역할 + 절대 규칙 + 출력(JSON) 형식 (변하지 않는 부분)
- MESSAGE_STYLES: 호출마다 무작위로 하나 선택해 표현만 바꾸는 스타일 가이드
- GENERATION_TEMPERATURE: 표현 다양성을 위한 샘플링 온도
- build_user_prompt(): 충전소 확정 데이터 + 선택된 스타일로 user 프롬프트 생성
"""
import json
import random

# 생성 다양성을 위한 샘플링 온도. 높일수록 표현이 다양해진다(0.0~2.0).
GENERATION_TEMPERATURE = 1.5

# 모델 역할과 절대 규칙, 출력 형식을 정의하는 고정 system instruction.
# 스타일이 바뀌어도 여기 규칙은 항상 지켜져야 한다.
SYSTEM_INSTRUCTION = """당신은 수소충전소 추천 서비스의 안내 문구 작성 도우미입니다.
규칙 엔진이 이미 선택한 추천 충전소의 확정 데이터만 보고, 사용자에게 보여줄
"권장 충전 시점(charge_timing)"과 "한 줄 안내 문구(message)"를 한국어로 작성합니다.
그리고 수소차 오너에게 도움이 되는 인사이트도 함께 제공해야합니다.
여기서 인사이트라 함은 관리팁, 충전팁 같은 수소차 오너에게 직접적으로 도움이 될 수 있는 자세한 깨알정보 등입니다.
내용이 서로 자연스럽게 어울어 지도록 답변을 준비하세요.

항상 지켜야 할 규칙:
- 제공된 사실 데이터에 근거해서만 작성하고, 없는 정보를 지어내지 마세요.
- 충전소를 새로 고르거나 다른 충전소를 언급하지 마세요. 주어진 충전소만 안내합니다.
- "연료_상태"(sufficient/recommend/urgent)에 맞는 긴급도와 톤으로 안내하세요.
- charge_timing: 언제 충전하면 좋은지 나타내는 짧은 표현(10자 이내, 한국어 존댓말).
- message: 80자 이내, 한국어 존댓말로 자연스럽게.
- 다른 설명·마크다운·코드블록 없이 아래 JSON 객체 하나만 출력하세요.
  {"charge_timing": "...", "message": "..."}
"""

# 호출마다 무작위로 하나를 골라 message 표현을 다양하게 만드는 스타일 가이드.
# 사실/길이/JSON 형식 규칙은 그대로 두고 "말투와 강조점"만 바꾼다.
MESSAGE_STYLES = [
    "가격 이점을 자연스럽게 강조하는 정보형 말투",
    "운전자를 가볍게 격려하는 따뜻한 말투",
    "핵심만 짚어 주는 간결하고 단정적인 말투",
    "거리·대기 등 편의를 부각하는 친근한 권유형 말투",
    "주행가능거리 같은 수치를 곁들인 데이터 강조형 말투",
    "다정하게 안부를 건네듯 부드러운 말투",
    "지금 행동을 가볍게 제안하는 코치 같은 말투",
]


def pick_message_style(rng: random.Random | None = None) -> str:
    """이번 호출에서 사용할 message 스타일 하나를 무작위로 고른다.

    테스트에서 결정적으로 만들고 싶으면 시드를 고정한 Random 을 넘기면 된다.
    """
    chooser = rng or random
    return chooser.choice(MESSAGE_STYLES)


def build_user_prompt(station_facts: dict, style: str | None = None) -> str:
    """충전소 확정 데이터와 이번 호출 스타일로 user 프롬프트를 만든다.

    style 을 생략하면 MESSAGE_STYLES 에서 무작위로 하나 선택한다.
    """
    if style is None:
        style = pick_message_style()

    return (
        "아래 추천 충전소 데이터를 바탕으로 안내 문구를 작성하세요.\n"
        f"이번 안내는 다음 스타일로 작성하세요: {style}\n"
        "스타일은 표현 방식만 바꾸는 것이며, system 규칙(사실 근거·길이·JSON 형식)은 "
        "그대로 지켜야 합니다.\n\n"
        "추천 충전소 데이터(JSON):\n"
        f"{json.dumps(station_facts, ensure_ascii=False)}"
    )
