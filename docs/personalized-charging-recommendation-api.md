# 개인화 충전 추천 API 계약 (서버 개발용)

연료 충분(`battery_sufficient`) 대시보드의 **개인화 충전 추천/인사이트**를 위한 서버 계약 문서다.
클라이언트는 로컬에서 집계한 **운전습관(driving_habit)** 을 함께 보내고, 서버는 이를 **Gemini API**
프롬프트에 합성해 개인화된 `ai_insight`(및 추천 충전소)를 내려준다.

- 엔드포인트: `POST /nearest-recommendation`
- 클라이언트 매핑: `HyConnectService.getSufficientDashboard()`
  - 요청: `NearestRecommendationRequestDto`
  - 응답: `SufficientDashboardDto` → 매퍼 → `SufficientDashboard`(Compose UI)
- 인코딩: `application/json; charset=utf-8`

> ⚠️ **서버 스펙 주의**: 위도 키는 `lat`이 아니라 **`let`** 이다(오타 아님, 기존 계약 유지).

---

## 1. Request

```json
{
  "vehicle": {
    "fuel_percent": 83,
    "remaining_range": 500.0,
    "fuel_type": "hydrogen"
  },
  "location": {
    "let": 37.5791,
    "lon": 126.8895
  },
  "context": {
    "radius_km": 10
  },
  "driving_habit": {
    "total_sessions": 12,
    "total_driving_minutes": 372,
    "harsh_accel_count": 8,
    "harsh_brake_count": 5,
    "incautious_count": 3,
    "avg_score": 78,
    "style": "moderate",
    "events_per_hour": 2.58
  }
}
```

### 필드 설명

| 경로 | 타입 | 필수 | 설명 |
|---|---|---|---|
| `vehicle.fuel_percent` | int | ✅ | 연료 잔량(%) 0~100 |
| `vehicle.remaining_range` | number | ✅ | 주행가능거리(km) |
| `vehicle.fuel_type` | string | ✅ | 연료 종류. 현재 `"hydrogen"` |
| `location.let` | number | ✅ | **위도** (키 이름이 `let`) |
| `location.lon` | number | ✅ | 경도 |
| `context.radius_km` | int | ✅ | 검색 반경(km). 기본 10 |
| `driving_habit` | object\|null | ❌ | 누적 운전습관. **기록이 없으면 키 자체가 생략된다.** 있을 때 Gemini 개인화에 사용 |

### `driving_habit` 객체

클라이언트가 주행 세션마다 로컬(DataStore)에 누적한 통산 운전습관 요약이다.
"안전운전 점수"가 목적이 아니라 **연료 소모 성향/충전 추천 개인화**의 입력 신호다.

| 필드 | 타입 | 설명 |
|---|---|---|
| `total_sessions` | int | 누적 주행 세션 수 |
| `total_driving_minutes` | int | 누적 주행 시간(분) |
| `harsh_accel_count` | int | 급가속 횟수(속도 변화 ≥ +30km/h) |
| `harsh_brake_count` | int | 급정거 횟수(속도 변화 ≤ −30km/h) |
| `incautious_count` | int | 부주의(조향각 변화 ≥ 50°) 횟수 |
| `avg_score` | int | 세션 평균 점수(0~100, 100점 만점에서 이벤트당 −5점) |
| `style` | string | `calm` / `moderate` / `aggressive` / `unknown` |
| `events_per_hour` | number | 주행 1시간당 위험 이벤트 빈도(소수 둘째 자리) |

`style` 산출 기준(클라이언트): `avg_score ≥ 90 → calm`, `≥ 70 → moderate`, 그 미만 → `aggressive`,
기록 없음 → `unknown`.

---

## 2. Response

```json
{
  "screen": "battery_sufficient",
  "vehicle": {
    "fuel_type": "hydrogen",
    "fuel_percent": 83,
    "remaining_range": 500.0
  },
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

### 필드 설명

| 경로 | 타입 | 설명 |
|---|---|---|
| `screen` | string | 화면 구분. `battery_sufficient` |
| `vehicle.*` | - | 응답 시점 차량 상태(요청 echo 또는 서버 보정값) |
| `ai_insight.status` | string | `sufficient` / `recommend` / `urgent` → 카드 강조색 분기 |
| `ai_insight.status_label` | string | 상태 라벨(예: "수소 잔량 충분") |
| `ai_insight.subtitle` | string | 큰 제목 한 줄 |
| `ai_insight.message` | string | **Gemini가 운전습관을 반영해 생성한 개인화 문구** |
| `ai_insight.updated_at` | string\|null | 인사이트 생성 시각(ISO-8601). null이면 시각 미표시 |
| `ai_insight.metrics[]` | array | 지표 카드. `label`/`value`/`unit`/`tone` |
| `ai_insight.metrics[].tone` | string | `positive` / `warning`(=`negative`) / `neutral`. 값 강조색 |
| `recommended_station` | object\|null | 대표 추천 충전소. null이면 추천 카드/내비 버튼 숨김 |
| `recommended_station.chrstn_mno` | string | 충전소 관리번호(식별자) |
| `recommended_station.ntsl_pc` | int | 수소 단가(원/kg) |
| `recommended_station.price_diff_from_avg` | number | 지역 평균 대비 단가 차(원). 음수면 평균보다 저렴 |
| `recommended_station.estimated_cost` | int | 예상 충전 비용(원) |
| `recommended_station.wait_vhcle_alge` | int | 대기 차량 수 |
| `recommended_station.let` / `lon` | number | 위/경도(내비 좌표). 위도 키는 `let` |

> 응답에는 버튼(actions)이 없다. 추천소가 있으면 클라이언트가 "경로 안내 시작" 버튼을 구성한다.

---

## 3. 서버 측 Gemini 연동 가이드

1. 요청의 `driving_habit`(있을 때)과 `vehicle`/`location`/주변 충전소 후보를 입력으로 프롬프트를 구성한다.
2. Gemini가 다음을 생성하도록 지시한다.
   - `ai_insight.message`: 운전습관을 반영한 1~2문장 개인화 안내(한국어).
   - `ai_insight.subtitle` / `status` / `metrics[].tone`: 상태에 맞는 톤.
3. 개인화 방향 예시(프롬프트 설계 참고):
   - `style = aggressive` 또는 `events_per_hour` 높음 → 연료 소모가 빠르므로 **더 이른 충전 타이밍/여유 추천**.
   - `style = calm` → 가격/거리 효율 우선 추천.
   - `driving_habit` 없음(`unknown`) → 일반 추천(운전습관 언급 없이).
4. **개인정보/안전**: API 키는 서버에만 두고 클라이언트로 노출하지 않는다.
   Gemini 호출 실패 시에도 200으로 **운전습관을 뺀 기본 인사이트**를 내려주면 클라이언트가 그대로 표시한다.

### 폴백 동작(클라이언트)

- 네트워크/서버 오류 시 클라이언트는 `DummyHyConnectData.sufficientDashboard`(데모 대시보드)로 폴백한다.
- 따라서 서버 미연동 상태에서도 화면 검증이 가능하다(개인화 문구만 더미).

---

## 4. cURL 예시

```bash
curl -X POST "$BASE_URL/nearest-recommendation" \
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
