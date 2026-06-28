# FastAPI 서버 구현 프롬프트 (개인화 충전 추천)

> 아래 블록을 그대로 코딩 에이전트/LLM에 붙여넣어 사용한다.
> Android 클라이언트(`com.hyconnect.pleos`)의 기존 계약(`docs/personalized-charging-recommendation-api.md`,
> `SufficientDashboardDto.kt`)을 1:1로 만족하는 FastAPI 서버를 생성하기 위한 스펙이다.

---

## 프롬프트 (copy & paste)

너는 시니어 백엔드 엔지니어다. **FastAPI** 기반으로 수소차 커넥티드 앱(HyConnect)의
**개인화 충전 추천 API**를 구현한다. 이미 Android 클라이언트가 아래 계약대로 호출하고 있으므로,
**요청/응답 JSON 스키마를 한 글자도 바꾸지 말고** 정확히 맞춰라.

### 1. 목표

연료 충분(`battery_sufficient`) 대시보드용 엔드포인트 `POST /nearest-recommendation` 하나를 구현한다.
클라이언트는 차량 상태/위치와 함께 **로컬에서 집계한 운전습관(`driving_habit`)** 을 보낸다.
서버는 이 운전습관을 **Gemini API** 프롬프트에 합성해 **개인화된 충전 인사이트(`ai_insight`)** 와
**대표 추천 충전소(`recommended_station`)** 를 내려준다.

### 2. 기술 스택 / 제약

- Python 3.11+, FastAPI, Pydantic v2, uvicorn.
- Gemini 연동: `google-generativeai` (모델 예: `gemini-2.0-flash`). **API 키는 환경변수**(`GEMINI_API_KEY`)로만 읽고
  절대 코드/응답에 노출하지 않는다.
- 응답 인코딩: `application/json; charset=utf-8`. 한글 문자열 깨지지 않게 `ensure_ascii=False` 보장.
- CORS 허용(개발 단계, `*`).
- **JSON 키는 모두 snake_case**이며 아래 표기를 그대로 쓴다.
- ⚠️ **위도 키는 `lat`이 아니라 `let`이다.** (오타가 아니라 기존 계약. 요청·응답 모두 `let` 사용.)
- Pydantic 모델은 별칭(alias)으로 `let`을 받고, 응답도 `let`으로 직렬화한다
  (`model_config = ConfigDict(populate_by_name=True)`, 필드 `lat: float = Field(alias="let")`).

### 3. 엔드포인트

`POST /nearest-recommendation`

#### 3-1. Request body

```json
{
  "vehicle": { "fuel_percent": 83, "remaining_range": 500.0, "fuel_type": "hydrogen" },
  "location": { "let": 37.5791, "lon": 126.8895 },
  "context": { "radius_km": 10 },
  "driving_habit": {
    "total_sessions": 12, "total_driving_minutes": 372,
    "harsh_accel_count": 8, "harsh_brake_count": 5, "incautious_count": 3,
    "avg_score": 78, "style": "moderate", "events_per_hour": 2.58
  }
}
```

- `vehicle.fuel_percent`(int, 0~100), `vehicle.remaining_range`(float, km), `vehicle.fuel_type`(str, 현재 `"hydrogen"`) — 필수.
- `location.let`(float, **위도**), `location.lon`(float, 경도) — 필수.
- `context.radius_km`(int, 기본 10).
- `driving_habit`(object | **생략 가능**). 클라이언트에 누적 기록이 없으면 **키 자체가 빠진다.**
  - `total_sessions`, `total_driving_minutes`, `harsh_accel_count`, `harsh_brake_count`, `incautious_count`, `avg_score`(int)
  - `style`: `"calm" | "moderate" | "aggressive" | "unknown"`
  - `events_per_hour`(float, 주행 1시간당 위험 이벤트 빈도)

#### 3-2. Response body (200)

```json
{
  "screen": "battery_sufficient",
  "vehicle": { "fuel_type": "hydrogen", "fuel_percent": 83, "remaining_range": 500.0 },
  "ai_insight": {
    "status": "sufficient",
    "status_label": "수소 잔량 충분",
    "subtitle": "지금 충전이 급하지 않아요",
    "message": "급가속·급정거가 다소 잦은 편이라 평소보다 연료 소모가 빨라요. 다음 정차 때 상암 수소충전소에서 미리 채워두면 여유롭게 주행할 수 있어요.",
    "updated_at": "2026-06-27T14:30:00+09:00",
    "metrics": [
      { "label": "주행 가능 거리", "value": "500", "unit": "km", "tone": "neutral" },
      { "label": "권장 충전 시점", "value": "약 2시간 후", "unit": null, "tone": "neutral" },
      { "label": "예상 소모율", "value": "다소 높음", "unit": null, "tone": "warning" }
    ]
  },
  "recommended_station": {
    "chrstn_mno": "ST_SANGAM_001",
    "name": "상암 수소충전소",
    "road_nm_addr": "서울 마포구 상암동",
    "distance_km": 2.4,
    "ntsl_pc": 8250,
    "price_diff_from_avg": -430.0,
    "estimated_cost": 41200,
    "wait_vhcle_alge": 1,
    "is_open": true,
    "let": 37.5791,
    "lon": 126.8895
  }
}
```

응답 필드 규칙:
- `screen`: 항상 `"battery_sufficient"`.
- `vehicle`: 요청 차량값 echo(또는 서버 보정).
- `ai_insight.status`: `"sufficient" | "recommend" | "urgent"` (클라이언트 카드 강조색 분기).
- `ai_insight.updated_at`: ISO-8601(`+09:00`). null이면 클라이언트가 시각을 숨긴다.
- `ai_insight.metrics[].tone`: `"positive" | "warning" | "neutral"`. 누락 시 클라이언트는 `neutral`로 본다.
- `ai_insight.metrics[].unit`: 없으면 `null`.
- `recommended_station`: 추천소 없으면 **`null`**(클라이언트가 추천 카드/내비 버튼을 숨긴다).
  - `chrstn_mno`(식별자), `ntsl_pc`(수소 단가 원/kg, int), `price_diff_from_avg`(지역 평균 대비 단가차, 음수=저렴),
    `estimated_cost`(예상 비용 원, int), `wait_vhcle_alge`(대기 차량 수, int), `is_open`(bool), `let`/`lon`(좌표).
- 응답에 버튼(actions)은 넣지 않는다. 클라이언트가 추천소 유무로 액션을 구성한다.

### 4. 비즈니스 로직

1. 요청 위치/반경으로 **주변 충전소 후보**를 만든다.
   - 1차 구현은 **충전소 시드 데이터(메모리/JSON 파일)** 로 충분하다. (좌표·단가·대기차량·도로명주소 포함)
   - 거리 계산은 Haversine. `distance_km`은 소수 첫째 자리 반올림.
   - `estimated_cost`는 (남은 용량으로 채울 양 × `ntsl_pc`) 같은 단순 추정으로 계산해도 된다.
   - `price_diff_from_avg`는 후보 평균 단가 대비 차이.
2. 대표 추천소 1곳 선정(거리·단가·대기차량 가중). 후보가 없으면 `recommended_station = null`.
3. **Gemini로 `ai_insight` 생성**:
   - 입력: `driving_habit`(있을 때) + `vehicle` + 선정된 추천소 요약.
   - 출력은 **JSON만** 반환하도록 강제(아래 4-1). 파싱 실패 시 폴백(4-2).
   - 개인화 방향:
     - `style == "aggressive"` 또는 `events_per_hour` 높음 → 연료 소모 빠름 → **더 이른 충전 타이밍/여유** 강조,
       `metrics`에 "예상 소모율: 다소 높음(`warning`)".
     - `style == "calm"` → 가격/거리 효율 우선.
     - `driving_habit` 없음/`unknown` → **운전습관 언급 없이** 일반 인사이트.

#### 4-1. Gemini 출력 스키마(서버 내부 강제)

Gemini에는 다음 JSON만 생성하라고 지시한다(나머지 필드는 서버가 채운다):
```json
{ "status": "...", "status_label": "...", "subtitle": "...", "message": "...",
  "metrics": [ { "label": "...", "value": "...", "unit": null, "tone": "..." } ] }
```
- `message`는 **한국어 1~2문장**, 운전습관 신호를 자연스럽게 반영.
- 가능하면 `response_mime_type="application/json"`로 호출하고, 그래도 깨질 때를 대비해 JSON 추출/검증을 둔다.

#### 4-2. 폴백(중요)

- **Gemini 호출/파싱 실패라도 200을 반환**한다. 이때 운전습관을 뺀 **기본 인사이트**(템플릿 문구)로 채운다.
  클라이언트는 받은 값을 그대로 표시한다.
- 즉, 5xx로 떨어뜨리지 말 것(클라이언트는 네트워크 오류 시 자체 데모로 폴백하므로 서버는 항상 정상 페이로드를 주는 게 목표).
- `updated_at`은 인사이트 생성 시각(`Asia/Seoul`). 폴백이어도 채워도 되고, 비우려면 `null`.

### 5. Pydantic 모델 (이름 자유, 스키마는 고정)

- 요청: `NearestRecommendationRequest`(`vehicle`, `location`, `context`, `driving_habit | None`)
  - `RequestLocation`: `lat: float = Field(alias="let")`, `lon: float`
  - `DrivingHabit`: 위 8개 필드, 모두 Optional 아님(있을 땐 전부 존재).
- 응답: `SufficientDashboard`(`screen`, `vehicle`, `ai_insight`, `recommended_station | None`)
  - `RecommendedStation`: `lat: float = Field(alias="let")` + 직렬화 시 `let`로 나가게 `serialization_alias` 또는
    `by_alias=True` 응답.
- **응답을 `by_alias=True`로 직렬화**해 `let`/snake_case가 그대로 나가게 한다.
  (FastAPI에서는 `response_model` + `response_model_by_alias=True`, 또는 `JSONResponse`로 직접 직렬화.)

### 6. 프로젝트 구조(예시)

```
server/
  app/
    main.py            # FastAPI 앱, CORS, 라우터 등록
    schemas.py         # Pydantic 요청/응답 모델 (let alias 포함)
    routers/recommendation.py   # POST /nearest-recommendation
    services/stations.py        # 후보 충전소 + 거리/비용/대표 선정
    services/gemini.py          # Gemini 호출 + JSON 파싱 + 폴백
    data/stations.seed.json     # 시드 충전소
    core/config.py     # 환경변수(GEMINI_API_KEY 등)
  requirements.txt     # fastapi, uvicorn, pydantic, google-generativeai
  README.md            # 실행법(uvicorn app.main:app --reload), 환경변수
```

### 7. 검증(반드시 통과)

아래 cURL이 위 응답 스키마(특히 `let` 키, snake_case, 한글 비깨짐)대로 200을 반환해야 한다.
```bash
curl -X POST "http://localhost:8000/nearest-recommendation" \
  -H "Content-Type: application/json" \
  -d '{
    "vehicle": { "fuel_percent": 83, "remaining_range": 500.0, "fuel_type": "hydrogen" },
    "location": { "let": 37.5791, "lon": 126.8895 },
    "context": { "radius_km": 10 },
    "driving_habit": {
      "total_sessions": 12, "total_driving_minutes": 372,
      "harsh_accel_count": 8, "harsh_brake_count": 5, "incautious_count": 3,
      "avg_score": 78, "style": "moderate", "events_per_hour": 2.58
    }
  }'
```
추가로:
- `driving_habit` 키를 **생략**한 요청도 200(운전습관 언급 없는 일반 인사이트).
- `GEMINI_API_KEY` 미설정/오류 시에도 200(폴백 인사이트). 서버 로그에만 경고.
- 주변 후보가 없을 때 `recommended_station: null`.

### 8. 산출물

- 실행 가능한 FastAPI 서버 코드 일체 + `requirements.txt` + `README.md`(실행/환경변수/예시).
- pytest로 (a) 정상, (b) `driving_habit` 생략, (c) Gemini 실패 폴백 3케이스의 스키마 계약 테스트.
- 코드 주석은 한국어로, "왜"가 비자명한 부분에만.

---

## 참고: 향후 확장 엔드포인트(이번 범위 밖, 클라이언트에 이미 존재)

같은 서버에 점진 추가할 수 있는 클라이언트 의존 엔드포인트(필요 시 별도 프롬프트로 진행):

- `POST recommendations/personalized/delivery-payloads` — 자연어 질의 기반 충전소 목록(저연료 화면).
- 사용자 선호 학습(추천 카드 경로안내 선택 시) / 충전 로그 생성.

이번 프롬프트는 **개인화 충전 추천(`/nearest-recommendation`)** 한 기능에 집중한다.
