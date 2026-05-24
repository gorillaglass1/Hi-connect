# HY-Connect

수소차 운전자를 위한 개인화 수소충전 경유지 추천 플랫폼입니다.  
차량의 남은 주행가능거리, 충전소 실시간 상태, 대기 차량 수, 판매 가격, 편의시설, 사용자의 선호 가중치를 함께 계산해 실제로 도착하고 충전할 수 있는 충전소를 추천합니다.

이 저장소는 FastAPI 백엔드, SQLAlchemy ORM, Supabase/PostgreSQL 연동, Hying API 동기화, Gemini Text-to-SQL 조건 필터, 추천 테스트 대시보드, 홍보용 웹페이지를 함께 포함합니다.

---

## 1. 홍보용 소개

### 도착했는데 충전할 수 없다면, 추천이 아닙니다

기존 지도 검색은 가까운 충전소를 보여주는 데 집중합니다. 하지만 수소차 운전자에게 중요한 것은 단순한 거리보다 더 복합적입니다.

- 현재 주행가능거리로 안전하게 도착할 수 있는가
- 충전소가 실제 운영 중인가
- 대기 차량이 얼마나 있는가
- 목적지까지 우회가 과도하지 않은가
- 가격과 편의시설이 사용자의 성향에 맞는가

HY-Connect는 이 조건들을 한 번에 계산해 차량 안에서 바로 선택할 수 있는 경유지 추천 결과를 제공합니다.

### 현대차 홍보용 팜플렛 톤의 데모 화면

프로젝트에는 두 개의 웹 화면이 있습니다.

- `/`  
  홍보용 웹페이지입니다. 현대차/Pleos 계열 홍보 팜플렛 느낌에 맞춘 자동차 브로슈어형 랜딩 페이지입니다.

- `/dashboard`  
  테스트용 웹페이지입니다. 사용자 선택, 가중치 조정, 주행 시나리오 입력, 자연어 조건 필터, 추천 결과, 경로안내 선택 학습까지 직접 확인할 수 있습니다.

### 핵심 사용자 경험

1. 사용자가 현재 위치, 목적지, 차량 주행가능거리를 입력합니다.
2. 필요하면 "인천에 있고 가격이 낮고 대기 차량이 적은 충전소"처럼 자연어 조건을 넣습니다.
3. 서버가 조건에 맞는 충전소 후보를 찾고, 개인 가중치로 점수를 계산합니다.
4. 사용자는 추천 카드에서 `경로안내`를 누릅니다.
5. 프론트는 충전소 관리번호만 서버에 보내고, 서버가 추천 이력에 저장된 점수 스냅샷으로 선호 가중치를 조금 조정합니다.
6. 차량으로 보낼 JSON은 중복을 줄인 간단한 형식으로 만들어집니다.

---

## 2. 주요 기능

### 개인화 추천

추천 점수는 네 가지 세부 점수로 구성됩니다.

- 가격 점수
- 대기시간 점수
- 거리/우회 점수
- 편의시설 점수

사용자마다 네 항목의 중요도가 다릅니다. 예를 들어 어떤 사용자는 가격을 가장 중요하게 보고, 어떤 사용자는 대기시간과 우회거리를 더 중요하게 봅니다. HY-Connect는 `user_preferences` 테이블의 가중치를 이용해 같은 충전소라도 사용자별로 다른 순위를 만들 수 있습니다.

### 선택 기반 선호도 학습

사용자가 추천 목록에서 특정 충전소의 `경로안내` 버튼을 누르면, 서버는 그 선택을 하나의 신호로 봅니다.

예시로 선택한 충전소의 세부 점수가 아래와 같다고 가정합니다.

```text
가격 점수: 40
대기 점수: 90
거리 점수: 85
편의시설 점수: 25
```

이 사용자는 가격보다 대기와 거리가 높은 충전소를 선택했으므로, 서버는 대기/거리 가중치를 조금 올리고 가격/편의시설 가중치를 조금 낮춥니다.

프론트는 위 점수를 학습 요청에 담아 보내지 않습니다. 추천 생성 시 서버가 `recommendation_history`에 점수 스냅샷을 저장하고, 경로안내 선택 시에는 `chrstn_mno`만 받아 해당 이력을 찾아 학습합니다.

학습 공식은 다음과 같습니다.

```text
new_weight = old_weight * 0.9 + observed_preference * 0.1
```

학습률은 `0.1`입니다. 한 번의 선택으로 크게 바뀌지 않고, 여러 번의 선택이 쌓이며 천천히 사용자의 취향에 가까워집니다.

### 차량 전송용 JSON 간소화

추천 응답 전체에는 분석과 로그에 필요한 상세 데이터가 남아 있습니다.  
반면 차량으로 보내는 `delivery_payload`는 중복 필드를 제거하고 바로 쓰기 쉬운 flat 구조로 정리했습니다.

```json
{
  "chrstn_mno": "2820020121HS2019018",
  "chrstn_nm": "H인천수소충전소 에코스테이션",
  "road_nm_addr": "인천 남동구 청능대로468번길 1",
  "latitude": 37.39867905394416,
  "longitude": 126.71148794493556,
  "ntsl_pc": 11000,
  "distance_to_station": 175.82,
  "detour_distance": 0.36,
  "wait_vehicles": 0,
  "wait_time_minutes": 0,
  "facilities": ["대기실", "세차장", "편의점", "화장실"],
  "is_reachable": true,
  "final_score": 84.1,
  "recommendation_reason": "사용자 가중치 분석 결과 전반적 매칭도가 매우 높습니다."
}
```

### 실제 경로 범위 기반 충전소 후보 검색

출발지와 목적지의 직선거리만 보지 않고, 실제 경로 거리로 만들어지는 우회 가능 범위를 계산해 충전소 후보를 찾을 수 있습니다.

- 외접 박스 안에 있는 충전소를 1차 조회합니다.
- 내접 박스는 제외해 경로 주변 링 형태의 후보만 남깁니다.
- `POST /recommendations/path-range/stations`로 바로 호출할 수 있습니다.

### 상태 테이블 자동 최신화

서버가 실행되면 Hying API에서 충전소 기본 정보, 부대시설, 상태 정보를 한 번 동기화합니다.  
그 이후에는 `hydrogen_station_status` 계열 상태 데이터를 기본 5분마다 갱신합니다.

기본 주기:

```dotenv
HYING_STATUS_SYNC_INTERVAL_SECONDS=300
```

상태 sync가 실행되면 서버 터미널에 다음 형태의 로그가 찍힙니다.

```text
Hydrogen station status sync tick started
Starting hydrogen_station_status sync from Hying API: params={'pageNo': 1, 'numOfRows': 100}
hydrogen_station_status table updated: fetched=100 saved=96 skipped=4
Hydrogen station status sync tick finished: fetched=100 saved=96 skipped=4 next_run_in_seconds=300
```

---

## 3. 실행 방법

### 가상환경 생성

```bash
python -m venv .venv
source .venv/bin/activate
```

Windows에서는 다음 명령을 사용합니다.

```bash
.venv\Scripts\activate
```

### 의존성 설치

```bash
pip install fastapi aiosqlite sqlalchemy asyncpg pytest pytest-asyncio httpx email-validator greenlet google-genai
```

### 환경 변수 설정

루트에 `.env` 파일을 만들고 `.env.example`을 참고해 값을 채웁니다.

```dotenv
DATABASE_URL=
SUPABASE_DB_URL=postgresql://postgres:[비밀번호]@[호스트]:5432/postgres
SUPABASE_DB_PASSWORD=your_raw_password
SUPABASE_DB_HOST=db.example.supabase.co

HYING_API_BASE_URL=https://www.h2nbiz.or.kr
HYING_API_KEY=발급받은_API_KEY
HYING_STATIONS_ENDPOINT=/api/chrstnList/operationInfo
HYING_STATION_STATUS_ENDPOINT=/api/chrstnList/currentInfo
HYING_STATION_FACILITIES_ENDPOINT=/api/chrstnList/adiInfo

HYING_STATUS_SYNC_ENABLED=true
HYING_STATUS_SYNC_INTERVAL_SECONDS=300
HYING_STATUS_SYNC_PAGE_NO=1
HYING_STATUS_SYNC_NUM_OF_ROWS=100

GEMINI_API_KEY=your_gemini_api_key
GOOGLE_API_KEY=
```

Gemini 키가 없어도 기본 추천 기능은 동작합니다. 이 경우 자연어 Text-to-SQL 필터만 사용할 수 없습니다.

### 기존 DB 마이그레이션

기존 Supabase/PostgreSQL DB를 계속 사용한다면 추천 이력에 학습용 점수 스냅샷 컬럼을 한 번 추가해야 합니다.

`sql/recommendation_history_score_snapshot_migration.sql` 파일 내용을 Supabase SQL Editor에 그대로 붙여 넣어 실행하면 됩니다.

### 서버 실행

```bash
uvicorn index:app --reload
```

접속 URL:

- 홍보용 페이지: http://127.0.0.1:8000/
- 테스트 대시보드: http://127.0.0.1:8000/dashboard
- Swagger API 문서: http://127.0.0.1:8000/docs

### 테스트 실행

```bash
pytest -q
```

특정 기능만 확인하려면 다음처럼 실행할 수 있습니다.

```bash
pytest tests/api/test_user_api.py
pytest tests/api/test_personalized_recommendation_api.py
pytest tests/core/test_status_sync.py
```

---

## 4. 기술 구현 개요

### 전체 흐름

```text
브라우저
  |
  | POST /recommendations/personalized
  | 또는 POST /recommendations/personalized/delivery-payloads
  v
FastAPI Router
  |
  v
RecommendationService
  |
  |-- UserPreference 조회
  |-- Gemini Text-to-SQL 후보 필터
  |-- 충전소/상태/편의시설 DB 조회
  |-- 거리, 가격, 대기, 편의시설 점수 계산
  |-- 추천 결과 생성
  |-- 추천 이력 저장
  v
추천 응답 반환
  |
  | 사용자가 경로안내 클릭
  v
POST /users/{user_id}/preferences/learn
  |
  v
UserPreferenceService
  |
  |-- 최신 추천 이력에 저장된 세부 점수를 관측 선호도로 변환
  |-- 기존 가중치와 9:1로 혼합
  |-- user_preferences 업데이트
  |-- recommendation_history selected 처리
  v
업데이트된 사용자 가중치 반환
```

### 계층 구조

프로젝트는 초보자가 흐름을 따라가기 쉽도록 다음 계층으로 나뉩니다.

```text
app/api/          HTTP 엔드포인트
app/schemas/      요청/응답 JSON 모양
app/services/     비즈니스 로직
app/repositories/ DB 조회/저장
app/models/       DB 테이블 정의
app/core/         DB 연결, 시작 sync, 주기 sync
app/src/          HTML 테스트/홍보 화면
tests/            pytest 테스트
```

기본 원칙은 다음과 같습니다.

- Router는 HTTP 요청을 받고 Service를 호출합니다.
- Service는 계산, 검증, 예외 처리 같은 비즈니스 규칙을 담당합니다.
- Repository는 DB에 직접 접근합니다.
- Schema는 들어오고 나가는 JSON의 모양을 정의합니다.
- Model은 실제 테이블 구조를 정의합니다.

---

## 5. 주요 코드 설명

### `index.py`

앱의 시작점입니다.

역할:

- FastAPI 앱 생성
- 정적 asset 마운트: `/static`
- API router 등록
- 서버 시작 시 테이블 생성
- Hying 초기 동기화 실행
- 상태 sync 백그라운드 태스크 시작
- 앱 종료 시 백그라운드 태스크 정리

중요 코드:

```python
app.mount("/static", StaticFiles(directory="app/src/assets"), name="static")
```

홍보 페이지의 차량 이미지는 `app/src/assets/hyconnect-hero.png`에 있고 `/static/hyconnect-hero.png`로 접근합니다.

### `app/core/database.py`

DB 연결을 담당합니다.

지원 방식:

- `DATABASE_URL`
- `SUPABASE_DB_URL`
- Supabase host/password 조합
- 아무 값도 없을 때 로컬 SQLite 테스트 DB

SQLAlchemy 비동기 엔진과 `AsyncSession`을 만들고, API에서는 `Depends(get_db)`로 세션을 주입받습니다.

### `app/core/hying_startup_sync.py`

서버 시작 시 Hying API 데이터를 한 번 가져옵니다.

동기화 대상:

- 충전소 기본 정보
- 충전소 부대시설
- 충전소 실시간 상태

각 endpoint가 환경 변수에 설정되어 있을 때만 실행됩니다.

### `app/core/status_sync.py`

상태 테이블을 주기적으로 갱신하는 백그라운드 루프입니다.

핵심 값:

```python
DEFAULT_STATUS_SYNC_INTERVAL_SECONDS = 300
```

`HYING_STATUS_SYNC_INTERVAL_SECONDS`를 설정하면 주기를 바꿀 수 있습니다.

### `app/services/hydrogen_station_status_service.py`

Hying API에서 실시간 상태 데이터를 가져와 `hydrogen_station_status` 테이블에 upsert합니다.

반환값:

```json
{
  "fetched": 100,
  "saved": 96,
  "skipped": 4
}
```

`skipped`는 DB에 없는 충전소 관리번호가 들어와 저장하지 않은 경우입니다.

### `app/services/recommendation_service.py`

추천 엔진의 핵심입니다.

처리 순서:

1. 사용자 가중치 조회
2. 자연어 조건이 있으면 Text-to-SQL 후보 필터 실행
3. 운영 중이고 삭제되지 않은 충전소 조회
4. 현재 위치, 목적지, 충전소 위치로 거리 계산
5. 검색 반경 밖 후보 제외
6. 가격, 대기, 거리, 편의시설 점수 계산
7. 사용자 가중치로 최종 점수 계산
8. 도달 불가능 후보는 점수에 페널티 적용
9. 추천 사유 생성
10. 차량 전송용 `delivery_payload` 생성
11. 추천 이력 저장

### `app/services/recommendation_delivery_payload_service.py`

차량으로 보낼 수 있는 간단한 추천 JSON을 만듭니다.

이 서비스는 복잡한 계산을 하지 않습니다. 이미 계산된 추천 결과를 외부 전송에 적합한 모양으로 정리하는 역할만 합니다. 그래서 초보자는 이 파일을 보면 "최종 차량 payload가 어떻게 생겼는지"를 가장 쉽게 확인할 수 있습니다.

### `app/services/user_preference_service.py`

사용자 생성, 가중치 조회/수정, 선택 기반 선호도 학습을 담당합니다.

선택 학습 endpoint:

```http
POST /users/{user_id}/preferences/learn
```

요청 예시:

```json
{
  "chrstn_mno": "2820020121HS2019018"
}
```

프론트는 학습용 세부 점수를 보내지 않습니다. 서버가 최신 추천 이력에 저장한 점수 스냅샷으로 학습합니다. 응답은 업데이트된 사용자 가중치입니다.

```json
{
  "user_id": 1,
  "weight_price": "0.97",
  "weight_waiting_time": "1.05",
  "weight_distance": "1.04",
  "weight_facilities": "0.94",
  "safety_margin": "1.10",
  "created_at": "...",
  "updated_at": "..."
}
```

### `app/services/text_to_sql_service.py`

자연어 조건을 SQL로 바꾸는 역할을 합니다.

예:

```text
인천에 있고 가격이 9900원 이하인 세차장 있는 충전소
```

이런 문장을 Gemini에 보내고, 안전한 `SELECT` 쿼리로 제한해 후보 충전소 관리번호 목록을 가져옵니다.

---

## 6. API 사용 예시

### 개인화 추천 요청

```http
POST /recommendations/personalized
Content-Type: application/json
```

```json
{
  "user_id": 1,
  "current_latitude": 37.405,
  "current_longitude": 126.721,
  "destination_latitude": 37.46,
  "destination_longitude": 126.45,
  "remaining_range": 45,
  "nl_query": "인천에 있고 대기 차량이 적은 충전소"
}
```

추천 API 요청자는 alpha나 실제 경로거리를 보내지 않습니다. 서버가 내부 기준으로 `path_range_specification` 후보 검색을 먼저 시도하고, 적용 가능한 후보가 있으면 해당 후보만 점수화합니다. 후보가 없으면 서버가 직선거리의 일정 비율로 검색 반경 버퍼를 자동 계산해 기존 반경 방식으로 fallback합니다.

응답은 추천 충전소 배열입니다. 각 항목에는 화면 표시용 필드, 세부 점수, 차량 전송용 `delivery_payload`, 딥링크가 포함됩니다.

### 차량 전송용 추천 요청

대시보드 오른쪽 차량 적용 영역과 실제 차량 전송 시에는 아래 API를 사용합니다.

```http
POST /recommendations/personalized/delivery-payloads
Content-Type: application/json
```

요청 body는 `/recommendations/personalized`와 같습니다. 응답은 `delivery_payload` 배열만 반환하므로 `sub_scores`, 중첩 `delivery_payload`, 딥링크가 포함되지 않습니다.

### 경로 범위 충전소 후보 검색

```http
POST /recommendations/path-range/stations
Content-Type: application/json
```

```json
{
  "start_latitude": 37.0,
  "start_longitude": 126.0,
  "destination_latitude": 37.2,
  "destination_longitude": 126.2,
  "actual_distance_km": 40,
  "padding_km": 5
}
```

응답에는 외접/내접 박스, 네 방향 검색 박스, `candidate_stations` 배열이 포함됩니다.

### 선택 학습 요청

프론트에서 경로안내 버튼을 누르면 아래 요청을 보냅니다.

```http
POST /users/1/preferences/learn
Content-Type: application/json
```

```json
{
  "chrstn_mno": "2820020121HS2019018"
}
```

서버는 이 충전소의 최신 추천 이력을 찾아서, 그 이력에 저장된 가격/대기/거리/편의시설 점수로 사용자 가중치를 천천히 조정합니다.

---

## 7. 프론트엔드 화면 설명

### `/`

홍보용 페이지입니다.

구성:

- 첫 화면: 차량 브로슈어형 히어로
- 문제 제기: 도착했지만 충전 불가한 상황
- 해결 방식: 차량 데이터와 충전소 상태 연결
- 플랫폼 설명: Supabase, Gemini, Pleos Route UI
- 데모 이동 버튼

이미지는 `app/src/assets/hyconnect-hero.png`를 사용합니다.

### `/dashboard`

테스트용 대시보드입니다.

구성:

- 사용자 선택
- 사용자별 가중치 slider
- 주행 시나리오 preset
- 현재 위치/목적지/주행가능거리 설정
- 자연어 조건 필터
- 추천 결과 카드
- 경로안내 버튼
- 선택 학습 결과 모달
- 차량 전송용 JSON 확인

추천 결과 영역은 차량 전송용 API인 `POST /recommendations/personalized/delivery-payloads`를 호출합니다. 오른쪽 모달에 보이는 JSON은 실제 차량에 전달하는 flat payload와 같은 형식입니다.

경로안내 버튼을 누르면 실제로 다음 API가 호출됩니다.

```text
POST /users/{user_id}/preferences/learn
```

---

## 8. 테스트 코드 구조

테스트는 기능별로 나뉘어 있습니다.

```text
tests/api/
  HTTP API 단위의 통합 테스트

tests/services/
  서비스 로직 테스트

tests/core/
  환경 설정, 백그라운드 sync 설정 테스트

tests/schemas/
  Pydantic schema 검증 테스트
```

중요 테스트:

- `tests/api/test_user_api.py`  
  사용자 생성, 가중치 수정, 선택 학습 API를 검증합니다.

- `tests/api/test_personalized_recommendation_api.py`  
  개인화 추천 API가 추천 결과와 flat `delivery_payload`를 반환하는지 검증합니다.

- `tests/api/test_path_range_api.py`  
  실제 경로 거리 기반 충전소 후보 검색 API를 검증합니다.

- `tests/services/test_personalized_recommendation.py`  
  추천 서비스와 선택 기반 선호도 학습 공식이 의도대로 동작하는지 검증합니다.

- `tests/services/test_recommendation_delivery_payload_service.py`  
  차량 전송용 JSON이 중복 없는 flat 구조인지 검증합니다.

- `tests/core/test_status_sync.py`  
  상태 sync 설정 조건과 기본 5분 주기를 검증합니다.

---

## 9. 초보자를 위한 코드 읽는 순서

처음부터 모든 파일을 읽으려고 하면 어렵습니다. 아래 순서대로 보면 흐름을 잡기 쉽습니다.

1. `app/schemas/recommendation_schema.py`  
   추천 요청과 응답 JSON 모양을 먼저 봅니다.

2. `app/api/recommendation_api.py`  
   추천 API가 어떤 Service를 호출하는지 봅니다.

3. `app/services/recommendation_service.py`  
   실제 추천 점수가 계산되는 흐름을 봅니다.

4. `app/services/recommendation_delivery_payload_service.py`  
   차량으로 보내는 JSON이 어떻게 만들어지는지 봅니다.

5. `app/schemas/user_preference_schema.py`  
   사용자 가중치와 선택 학습 요청 JSON을 봅니다.

6. `app/services/user_preference_service.py`  
   선택 학습 공식이 어떻게 코드로 구현됐는지 봅니다.

7. `app/core/status_sync.py`  
   상태 테이블이 5분마다 갱신되는 루프를 봅니다.

8. `app/src/test_dashboard.html`  
   프론트에서 추천 API와 학습 API를 어떻게 호출하는지 봅니다.

---

## 10. 개발 규칙

### DB 세션

API에서는 반드시 `Depends(get_db)`로 받은 `AsyncSession`을 사용합니다.

### 새 기능 추가 순서

새 기능은 보통 아래 순서로 추가합니다.

```text
Model -> Schema -> Repository -> Service -> Router -> Test
```

화면 기능까지 필요하면 마지막에 HTML/JS를 수정합니다.

### 테스트 데이터 주의

테스트는 실제 Supabase DB를 쓰지 않습니다. 테스트용 SQLite DB를 사용합니다.  
개발 DB와 테스트 DB를 혼동하지 않도록 `.env`와 테스트 fixture를 구분해서 봐야 합니다.

### 모델 import 주의

`Base.metadata.create_all`이 테이블을 만들려면 `index.py`에서 모델 파일이 import되어 있어야 합니다. 새 모델을 추가했다면 `index.py`에도 import를 추가해야 합니다.

---

## 11. 자주 생기는 문제

### 추천 결과가 비어 있음

가능한 원인:

- `hydrogen_stations`에 데이터가 없음
- 충전소의 `oper_yn`이 `Y`가 아님
- `del_at`이 `"0"`이 아님
- 검색 반경이 너무 작음
- 자연어 조건 필터가 모든 후보를 제외함

### 상태 sync가 실행되지 않음

확인할 환경 변수:

```dotenv
HYING_STATUS_SYNC_ENABLED=true
HYING_API_BASE_URL=https://www.h2nbiz.or.kr
HYING_STATION_STATUS_ENDPOINT=/api/chrstnList/currentInfo
```

### 터미널에 상태 갱신 로그가 보이지 않음

서버를 `uvicorn index:app --reload`로 실행했는지 확인합니다.  
정상 실행 중이면 5분마다 상태 sync tick 로그가 출력됩니다.

### Gemini 자연어 필터가 동작하지 않음

`GEMINI_API_KEY` 또는 `GOOGLE_API_KEY`가 설정되어 있는지 확인합니다.  
키가 없어도 일반 추천은 동작합니다.

---

## 12. 프로젝트 핵심 요약

HY-Connect는 단순한 충전소 목록 서비스가 아닙니다.

이 프로젝트의 핵심은 다음 네 가지입니다.

1. 실시간 충전소 상태를 DB에 최신화한다.
2. 차량의 현재 상황과 목적지를 기준으로 실제 도달 가능한 충전소를 계산한다.
3. 사용자별 선호 가중치로 추천 순위를 다르게 만든다.
4. 사용자가 선택한 경로안내 결과를 다시 학습해 다음 추천에 반영한다.

결과적으로 HY-Connect는 "가까운 충전소"가 아니라 "지금 이 사용자에게 실제로 좋은 충전 경유지"를 추천하는 시스템입니다.
