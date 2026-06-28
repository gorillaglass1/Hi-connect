# HyConnect API 입출력 레퍼런스 (통합)

Android 클라이언트(`com.hyconnect.pleos`)가 호출하는 **FastAPI 서버 전체 엔드포인트**의 요청/응답 JSON을
한 문서로 정리한다. 출처는 `data/network/*Dto.kt` + `HyConnectService.kt`이며 각 DTO와 1:1 대응한다.

## 공통 규칙

- 모든 경로는 `BuildConfig.HYCONNECT_BASE_URL` 기준 상대 경로. `Content-Type: application/json; charset=utf-8`.
- **JSON 키는 snake_case**가 기본. (단, `delivery-payloads` 응답만 예외적으로 camelCase — 차량/UI 직송용.)
- ⚠️ **위도 키는 `lat`이 아니라 `let`** 이다(서버 기존 계약, 오타 아님). 사용처: `nearest-recommendation`, `hydrogen-stations`.
  반면 `recommendations/personalized*`·`delivery-payloads`는 `latitude`/`current_latitude` 등 풀네임을 쓴다(혼동 주의).
- **요청에서 값이 `null`인 필드는 직렬화에서 생략**된다(Gson 기본). 예: `user_id`, `driving_habit`, 목적지 좌표.
- 충전소 식별자는 정수가 아니라 **문자열 `chrstn_mno`**. 수소 단가는 `ntsl_pc`(원/kg).
- 가격/거리/비용은 **포맷 없는 raw 숫자**로 내려준다(표시 포맷은 클라이언트가 처리).

## 엔드포인트 요약

| # | Method | Path | Req | Resp |
|---|---|---|---|---|
| 1 | POST | `/nearest-recommendation` | `NearestRecommendationRequest` | `SufficientDashboard` |
| 2 | POST | `/recommendations/personalized` | `PersonalizedRecommendationRequest` | `RecommendedStationResponse[]` |
| 3 | POST | `/recommendations/personalized/delivery-payloads` | `PersonalizedRecommendationRequest` | `DeliveryStation[]` (camelCase) |
| 4 | GET | `/hydrogen-stations` | (query params) | `HydrogenStationResponse[]` |
| 5 | POST | `/users/{user_id}/preferences/learn` | `PreferenceLearningRequest` | `UserPreferenceResponse` |
| 6 | GET | `/users/{user_id}/preferences` | – | `UserPreferenceResponse` |
| 7 | POST | `/charging-logs` | `ChargingLogRequest` | `ChargingLogResponse[]` (1개) |

> 차량 상태(`getVehicleState`)는 서버 엔드포인트가 아니라 클라이언트 임시값/Vehicle SDK에서 온다(서버에 차량 테이블 없음).

---

## 1. POST `/nearest-recommendation`

연료 충분(`battery_sufficient`) 대시보드. 운전습관을 Gemini로 합성해 개인화 인사이트 + 대표 추천소를 반환.
상세 계약/Gemini 가이드: `personalized-charging-recommendation-api.md`, 구현 프롬프트: `fastapi-server-implementation-prompt.md`.

### Request — `NearestRecommendationRequest`
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
- `location.let` = **위도**, `location.lon` = 경도.
- `context.radius_km`: 검색 반경(km, 기본 10).
- `driving_habit`: 누적 운전습관. **기록 없으면 키 전체 생략.** `style` ∈ `calm|moderate|aggressive|unknown`.

### Response — `SufficientDashboard`
```json
{
  "screen": "battery_sufficient",
  "vehicle": { "fuel_type": "hydrogen", "fuel_percent": 83, "remaining_range": 500.0 },
  "ai_insight": {
    "status": "sufficient",
    "status_label": "수소 잔량 충분",
    "subtitle": "지금 충전이 급하지 않아요",
    "message": "급가속·급정거가 다소 잦은 편이라 평소보다 연료 소모가 빨라요. 다음 정차 때 미리 채워두면 여유로워요.",
    "updated_at": "2026-06-27T14:30:00+09:00",
    "metrics": [
      { "label": "주행 가능 거리", "value": "500", "unit": "km", "tone": "neutral" },
      { "label": "권장 충전 시점", "value": "약 2시간 후", "unit": null, "tone": "neutral" },
      { "label": "예상 소모율", "value": "다소 높음", "unit": null, "tone": "warning" }
    ]
  },
  "recommended_station": {
    "chrstn_mno": "ST_SANGAM_001", "name": "상암 수소충전소", "road_nm_addr": "서울 마포구 상암동",
    "distance_km": 2.4, "ntsl_pc": 8250, "price_diff_from_avg": -430.0, "estimated_cost": 41200,
    "wait_vhcle_alge": 1, "is_open": true, "let": 37.5791, "lon": 126.8895
  }
}
```
- `ai_insight.status` ∈ `sufficient|recommend|urgent`. `metrics[].tone` ∈ `positive|warning|neutral`(누락 시 neutral).
- `recommended_station`이 **`null`이면** 클라이언트가 추천 카드/내비 버튼을 숨긴다. 좌표 위도 키는 `let`.

---

## 2. POST `/recommendations/personalized`

개인화 추천 충전소 목록(점수순 정렬). `nl_query`로 자연어 검색도 이 엔드포인트로 전달.

### Request — `PersonalizedRecommendationRequest`
```json
{
  "user_id": 1,
  "current_latitude": 37.405,
  "current_longitude": 126.721,
  "destination_latitude": 37.5665,
  "destination_longitude": 126.9780,
  "remaining_range": 120.0,
  "nl_query": "제일 가까운 충전소 추천해줘"
}
```
- `user_id`: 비로그인 시 **생략**. `nl_query`: 선택(없으면 생략).
- 목적지(`destination_*`)는 경로안내 중이 아니면 **둘 다 생략**(한쪽만 보내면 서버가 거부) → 현재 위치 근처 추천.

### Response — `RecommendedStationResponse[]`
```json
[
  {
    "chrstn_mno": "ST_YANGJAE_001",
    "chrstn_nm": "현대 수소충전소 양재",
    "road_nm_addr": "서울 서초구 바우뫼로 12길 73",
    "vhcle_knd_cd": "01", "vhcle_knd_nm": "승용",
    "ntsl_pc": 8800,
    "distance_to_station": 3.2,
    "distance_to_destination": 12.4,
    "detour_distance": 1.1,
    "wait_vehicles": 1, "wait_time_minutes": 5,
    "facilities": ["대기실", "편의점", "화장실"],
    "is_reachable": true,
    "sub_scores": { "price": 0.82, "waiting_time": 0.9, "distance": 0.76, "facilities": 0.6 },
    "final_score": 0.81,
    "recommendation_reason": "경로에서 가깝고 단가가 저렴해요.",
    "delivery_payload": {
      "chrstn_mno": "ST_YANGJAE_001", "chrstn_nm": "현대 수소충전소 양재",
      "road_nm_addr": "서울 서초구 바우뫼로 12길 73",
      "latitude": 37.468164, "longitude": 127.038703,
      "vhcle_knd_cd": "01", "vhcle_knd_nm": "승용", "ntsl_pc": 8800,
      "distance_to_station": 3.2, "detour_distance": 1.1,
      "wait_vehicles": 1, "wait_time_minutes": 5,
      "facilities": ["대기실", "편의점", "화장실"],
      "is_reachable": true, "final_score": 0.81,
      "recommendation_reason": "경로에서 가깝고 단가가 저렴해요."
    }
  }
]
```
- `sub_scores`/`final_score`는 0~1 가중 점수. `delivery_payload`는 차량 직송용 flat 페이로드(좌표 포함).

---

## 3. POST `/recommendations/personalized/delivery-payloads`

위 2번과 **요청 동일**(`PersonalizedRecommendationRequest`). 응답만 **이미 정제된 camelCase** 배열.
`isRecommended=true`인 1위가 대표 추천. (저연료 화면 `StationListCard`가 이 응답을 직접 소비.)

### Response — `DeliveryStation[]` (⚠️ camelCase)
```json
[
  {
    "id": "ST_YANGJAE_001",
    "name": "현대 수소충전소 양재",
    "address": "서울 서초구 바우뫼로 12길 73",
    "status": "도달 가능",
    "pressureInfo": "대기실 · 편의점 · 화장실",
    "distanceKm": 3.2,
    "waitMinutes": 5,
    "isRecommended": true,
    "latitude": 37.468164,
    "longitude": 127.038703
  }
]
```

---

## 4. GET `/hydrogen-stations`

충전소 원장 조회. Query: `chrstn_mno`, `chrstn_nm`, `oper_yn`, `rltm_info_yn`, `limit`(기본 100), `offset`(기본 0).

### Response — `HydrogenStationResponse[]`
```json
[
  {
    "chrstn_mno": "ST_SANGAM_001",
    "chrstn_nm": "상암 수소충전소",
    "road_nm_addr": "서울 마포구 상암동",
    "lon": 126.8895,
    "let": 37.5791,
    "ntsl_pc": 8250,
    "oper_yn": "Y",
    "rltm_info_yn": "Y"
  }
]
```
- 좌표: 경도 `lon`, **위도 `let`**. `oper_yn`/`rltm_info_yn`: `"Y"`/`"N"`.

---

## 5. POST `/users/{user_id}/preferences/learn`

추천 카드에서 경로안내(선택) 시 호출 → 선호 가중치 학습. 본문은 선택한 충전소 번호만.

### Request — `PreferenceLearningRequest`
```json
{ "chrstn_mno": "ST_SANGAM_001" }
```

### Response — `UserPreferenceResponse`
```json
{
  "user_id": 1,
  "weight_price": "0.97",
  "weight_waiting_time": "0.85",
  "weight_distance": "1.02",
  "weight_facilities": "0.60",
  "safety_margin": "0.15",
  "created_at": "2026-06-20T10:00:00+09:00",
  "updated_at": "2026-06-27T14:30:00+09:00"
}
```
- ⚠️ 가중치/소수값은 **숫자가 아니라 Decimal 문자열**("0.97")로 내려간다(클라이언트가 `toDouble`).

---

## 6. GET `/users/{user_id}/preferences`

현재 선호 가중치 조회. 응답 스키마는 **5번 응답(`UserPreferenceResponse`)과 동일**.

---

## 7. POST `/charging-logs`

충전 완료 로그 생성. (서버에 차량 테이블이 없어 `vehicle_id`는 없음.)

### Request — `ChargingLogRequest`
```json
{
  "user_id": 1,
  "chrstn_mno": "ST_SANGAM_001",
  "start_time": "2026-06-27T14:00:00+09:00",
  "end_time": "2026-06-27T14:08:00+09:00",
  "charged_amount": 4.2,
  "charging_cost": 34650.0,
  "waiting_time": 5
}
```
- `charged_amount`(kg), `charging_cost`(원), `waiting_time`(분)은 선택(없으면 생략 가능).

### Response — `ChargingLogResponse[]` (요소 1개)
```json
[
  {
    "charging_log_id": 1024,
    "user_id": 1,
    "chrstn_mno": "ST_SANGAM_001",
    "start_time": "2026-06-27T14:00:00+09:00",
    "end_time": "2026-06-27T14:08:00+09:00",
    "charged_amount": 4.2,
    "charging_cost": 34650.0,
    "waiting_time": 5,
    "created_at": "2026-06-27T14:08:05+09:00"
  }
]
```
- 응답은 **배열**이며 클라이언트는 `.first()`로 단건을 취한다.
