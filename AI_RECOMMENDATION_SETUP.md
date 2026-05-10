# AI Recommendation Setup

이 문서는 AI 수소충전소 추천 기능을 처음 보는 사람이 실행 흐름과 테스트 방법을 이해할 수 있도록 정리한 문서입니다.

## 오늘 작업한 내용

### 1. Pydantic 기본값 정리

스키마에서 `"hydrogen"` 같은 기본값을 직접 대입하던 방식을 Pydantic `Field(default=...)` 방식으로 정리했습니다.

예:

```python
fuel_type: str = Field(default="hydrogen")
```

이 방식은 기본값, 검증 조건, 설명 등을 한 곳에서 관리하기 좋습니다.

### 2. AI 추천 요청 스키마 분리

클라이언트가 보내는 원본 요청과 Gemini로 보내는 요청을 분리했습니다.

- `AiRecommendationRequest`: API가 받는 원본 요청
- `AiRecommendationGeminiRequest`: 개인정보를 제거한 Gemini 전송용 요청
- `AIRecommendationResponse`: Gemini 응답을 검증하고 API 응답으로 내려주는 스키마

Gemini 전송용 요청에서는 다음 값을 제거하거나 완화합니다.

- `user_id` 제거
- `vehicle_id` 제거
- 목적지 이름 제거
- 사용자가 직접 작성할 수 있는 `trigger.reason` 제거
- 현재 위치와 목적지 좌표를 소수점 3자리로 반올림

### 3. AI 추천 서비스 레이어 추가

`app/services/ai_recommendation_service.py`에 기본 서비스 흐름을 만들었습니다.

처리 순서:

1. API 요청을 받습니다.
2. 목적지 주변 수소충전소 후보를 DB에서 조회합니다.
3. 개인정보가 제거된 Gemini 요청 객체를 만듭니다.
4. Gemini 프롬프트를 생성합니다.
5. Gemini를 호출합니다.
6. Gemini 응답 JSON을 `AIRecommendationResponse`로 검증합니다.
7. 검증된 JSON 응답을 클라이언트에 반환합니다.

Gemini 호출은 SDK import 지연을 피하기 위해 REST API로 보냅니다. 요청 제한 시간은 `30초`입니다.

### 4. 목적지 주변 충전소 후보 조회

사용자가 찍은 목적지 좌표를 기준으로 주변 충전소를 조회합니다.

기본값:

- 반경: `20km`
- 최대 후보 수: `10개`

조회 방식:

1. 목적지 좌표 기준 bounding box로 1차 필터링
2. Python에서 Haversine 거리 계산
3. 반경 밖 충전소 제거
4. 가까운 순서로 정렬
5. 실시간 정보와 충전기 정보를 함께 포함

Gemini는 전체 DB가 아니라 이 후보 목록 안에서만 추천합니다.

### 5. AI 추천 API 추가

새 API가 추가되었습니다.

```http
POST /ai-recommendations
```

등록 파일:

- `app/api/ai_recommendation_api.py`
- `index.py`

기존 `optimized_station_recommendation_api`는 현재 존재하지 않는 클래스명을 import하고 있어 서버 시작을 막을 수 있습니다. 그래서 `index.py`에서는 깨진 optimized 라우터 등록을 제외하고 새 AI 추천 라우터를 등록했습니다.

### 6. Startup SQL / 더미 데이터 로딩 보수

서버 실행 시 아래와 같은 로그가 반복될 수 있었습니다.

```text
table hydrogen_station already exists
near "DATABASE": syntax error
near "USE": syntax error
```

원인은 서버 시작 과정에서 `Base.metadata.create_all()`로 이미 테이블을 만든 뒤, `sql/*.DDL.sql` 파일을 다시 실행했기 때문입니다. 또한 `users DDL.sql`에는 MySQL 전용 문법인 `CREATE DATABASE`, `USE`가 들어 있어 SQLite에서 오류가 났습니다.

보수 내용:

- SQLite에서는 `CREATE DATABASE`, `USE` 문을 실행하지 않습니다.
- 이미 존재하는 테이블의 `CREATE TABLE` 문은 실행하지 않습니다.
- 더미 DML은 기본적으로 서버 시작 시 로딩됩니다.
- 더미 DML은 기존 테이블에 데이터가 있으면 중복 삽입하지 않습니다.
- SQLite에서는 DML을 `INSERT OR IGNORE` 형태로 실행해 중복 제약 오류를 줄입니다.
- 부산역 테스트용 충전소 더미 데이터를 추가했습니다.

이제 같은 DB로 서버를 다시 실행해도 startup SQL 경고가 반복되지 않아야 합니다.

더미 데이터 로딩을 끄고 싶으면 서버 실행 전에 아래 환경변수를 설정합니다.

```bash
ENABLE_STARTUP_DUMMY_DATA=false uvicorn index:app --reload
```

## Gemini API Key 설정

API key는 직접 넣으면 됩니다.

`app/core/gemini.properties` 파일을 만들고 아래처럼 작성합니다.

```properties
GEMINI_API_KEY=여기에_직접_넣기
GEMINI_MODEL=gemini-1.5-flash
```

참고용 파일은 이미 있습니다.

```text
app/core/gemini.properties.example
```

주의:

- 실제 API key는 Git에 올리면 안 됩니다.
- API key가 없으면 `/ai-recommendations` 호출 시 `500` 응답이 납니다.
- 네트워크 또는 Gemini API 문제로 30초 안에 응답이 없으면 `500` 응답이 납니다.

## 서버 실행

프로젝트 루트에서 실행합니다.

```bash
uvicorn index:app --reload
```

기본 주소:

```text
http://127.0.0.1:8000
```

Swagger 문서:

```text
http://127.0.0.1:8000/docs
```

## Postman 테스트 방법

### 1. 새 요청 만들기

Postman에서 새 요청을 만들고 아래처럼 설정합니다.

```http
POST http://127.0.0.1:8000/ai-recommendations
```

### 2. Headers 설정

필수:

```http
Content-Type: application/json
```

만약 서버 실행 환경에 `APP_API_KEY`를 설정했다면 아래 헤더도 넣어야 합니다.

```http
x-api-key: 설정한_APP_API_KEY
```

`APP_API_KEY`를 설정하지 않았다면 `x-api-key` 헤더는 없어도 됩니다.

### 3. Body 설정

Postman의 `Body` 탭에서 `raw`와 `JSON`을 선택한 뒤 아래 예시를 넣습니다.

아래 요청은 현재 더미 데이터 기준으로 실제 후보 충전소가 잡히는 요청입니다. 목적지는 부산역이고, DB에는 부산역 주변 충전소 3개가 들어 있습니다.

```json
{
  "user_id": 1,
  "vehicle_id": 1,
  "location": {
    "latitude": 37.5665,
    "longitude": 126.978
  },
  "navigation": {
    "destination": {
      "name": "부산역",
      "latitude": 35.1151,
      "longitude": 129.0415
    },
    "remaining_route_distance_km": 390.5,
    "estimated_arrival_time": "2026-05-08T15:20:00Z",
    "estimated_remaining_range_at_arrival_km": 12
  },
  "trigger": {
    "trigger_type": "LOW_FUEL",
    "reason": "주행가능거리가 임계값 이하입니다.",
    "range_threshold_km": 120,
    "arrival_range_threshold_km": 50,
    "fuel_threshold_percent": 30
  },
  "preferences": {
    "preference_700bar": true,
    "max_detour_km": 15
  }
}
```

이 요청으로 서버가 Gemini에 보내는 후보 충전소는 현재 더미 데이터 기준으로 아래 3개입니다.

```json
[
  {
    "station_id": 6,
    "name": "부산항 수소충전소",
    "distance_from_destination_km": 0.69,
    "station_status": "OPEN",
    "charger_count": 2
  },
  {
    "station_id": 7,
    "name": "부산 감만 수소충전소",
    "distance_from_destination_km": 4.21,
    "station_status": "OPEN",
    "charger_count": 2
  },
  {
    "station_id": 8,
    "name": "부산 사상 수소충전소",
    "distance_from_destination_km": 7.39,
    "station_status": "OPEN",
    "charger_count": 2
  }
]
```

후보 충전소가 실제로 잡히는지 먼저 확인하고 싶으면 아래 명령으로 DB 상태를 볼 수 있습니다.

```bash
python - <<'PY'
import asyncio
from app.core.database import async_session
from app.services.ai_recommendation_service import AiRecommendationService

async def main():
    async with async_session() as db:
        rows = await AiRecommendationService(db).get_candidate_stations_near_destination(
            35.1151,
            129.0415,
        )
        print(len(rows))
        for row in rows:
            print(row["station_id"], row["name"], row["distance_from_destination_km"])

asyncio.run(main())
PY
```

정상이라면 아래처럼 나옵니다.

```text
3
6 부산항 수소충전소 0.69
7 부산 감만 수소충전소 4.21
8 부산 사상 수소충전소 7.39
```

같은 요청을 터미널에서 보내려면 아래처럼 실행할 수 있습니다.

```bash
curl -X POST http://127.0.0.1:8000/ai-recommendations \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 1,
    "vehicle_id": 1,
    "location": {
      "latitude": 37.5665,
      "longitude": 126.978
    },
    "navigation": {
      "destination": {
        "name": "부산역",
        "latitude": 35.1151,
        "longitude": 129.0415
      },
      "remaining_route_distance_km": 390.5,
      "estimated_arrival_time": "2026-05-08T15:20:00Z",
      "estimated_remaining_range_at_arrival_km": 12
    },
    "trigger": {
      "trigger_type": "LOW_FUEL",
      "reason": "주행가능거리가 임계값 이하입니다.",
      "range_threshold_km": 120,
      "arrival_range_threshold_km": 50,
      "fuel_threshold_percent": 30
    },
    "preferences": {
      "preference_700bar": true,
      "max_detour_km": 15
    }
  }'
```

만약 `APP_API_KEY`를 설정했다면 curl에도 헤더를 추가해야 합니다.

```bash
-H "x-api-key: 설정한_APP_API_KEY"
```

### 4. 성공 응답 예시

Gemini가 정상적으로 JSON을 반환하고 스키마 검증에 통과하면 이런 형태로 응답합니다.

```json
{
  "recommendations": [
    {
      "rank": 1,
      "station_id": 101,
      "name": "추천 충전소",
      "address": "주소",
      "latitude": 35.1,
      "longitude": 129.0,
      "selected_charger_id": 1001,
      "score": 92,
      "reason": "목적지와 가깝고 대기 시간이 짧습니다.",
      "highlight": "목적지 주변 최적 후보",
      "decision_factor": {
        "reachable": true,
        "estimated_arrival_range_km": 40,
        "detour_distance_km": 2.5,
        "estimated_wait_time_min": 10,
        "price": 0,
        "supports_700bar": true,
        "station_status": "OPEN"
      }
    }
  ],
  "message": "목적지 주변 후보 중 가장 적합한 충전소를 추천했습니다.",
  "created_at": "2026-05-10T00:00:00Z"
}
```

## 자주 나는 오류

### 500: Gemini API key is not configured.

`app/core/gemini.properties`에 `GEMINI_API_KEY`가 없거나 값이 비어 있습니다.

### 500: Gemini request failed.

Gemini API 서버로 요청을 보내지 못한 상태입니다.

확인할 것:

- 인터넷 연결
- `GEMINI_API_KEY` 값
- `GEMINI_MODEL` 값
- 회사/학교 네트워크의 외부 API 차단 여부

아래 오류가 나오면 로컬 Python이 HTTPS 인증서 검증에 필요한 CA 인증서 묶음을 못 찾는 상태입니다.

```text
[SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: unable to get local issuer certificate
```

서비스 코드는 `certifi`가 설치되어 있으면 `certifi`의 CA bundle을 사용하도록 되어 있습니다. 그래도 같은 오류가 나면 아래를 확인합니다.

```bash
python - <<'PY'
import certifi
print(certifi.where())
PY
```

`ModuleNotFoundError: No module named 'certifi'`가 나오면 설치합니다.

```bash
pip install certifi
```

### 404 또는 502: No hydrogen station candidates found near destination.

목적지 반경 `20km` 안에 DB에 등록된 충전소가 없습니다.

해결 방법:

- 목적지 좌표를 DB에 있는 충전소 주변으로 바꿔서 테스트합니다.
- 서비스의 `radius_km` 기본값을 늘립니다.
- 충전소 더미 데이터를 추가합니다.

### 502: Gemini response does not match AIRecommendationResponse.

Gemini 응답 JSON이 `AIRecommendationResponse` 스키마와 맞지 않습니다.

확인할 필드:

- `recommendations`
- `station_id`
- `score`
- `decision_factor`
- `station_status`
- `message`

### 401: Unauthorized

환경변수 `APP_API_KEY`가 설정되어 있는데 Postman 요청에 `x-api-key` 헤더가 없거나 값이 다릅니다.

## 전체 흐름 요약

```text
Postman
  -> POST /ai-recommendations
  -> AiRecommendationRequest 검증
  -> 목적지 주변 충전소 후보 DB 조회
  -> 개인정보 제거
  -> Gemini 프롬프트 생성
  -> Gemini 호출
  -> AIRecommendationResponse 검증
  -> JSON 응답 반환
```
