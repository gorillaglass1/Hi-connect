# 모의주행 상태 변경 가이드

Pleos Vehicle SDK 환경(Pleos Connect Emulator)에서 모의주행(Mock Driving) 상태를
ADB 명령어로 직접 변경하는 방법을 설명합니다. 기어/속도/조향각 등 차량 속성값을
주입하여 안전운전 점수 로직, 내비게이션, 차량 상태 UI 등을 테스트할 때 사용합니다.

> 참고 문서: https://document.pleos.ai/docs/pleos-only/tutorial/vehicle-sdk

---

## 1. 사전 준비

- **Pleos Connect Emulator** 실행 중일 것
- 개발 환경: Android SDK 26+, Gradle 8.0+, Kotlin
- 앱 `AndroidManifest.xml`에 권한 선언:
  ```xml
  <uses-permission android:name="pleos.car.permission.CAR_DRIVE" />
  <uses-permission android:name="android.car.permission.CAR_SPEED" />
  ```

---

## 2. 상태 주입 기본 명령어

VHAL(Vehicle HAL) FIFO에 값을 써서 차량 속성을 변경합니다.

```bash
# 루트 권한 획득 (1회)
adb root

# 단일 값 주입
adb shell "echo 'propId: {프로퍼티ID} areaId: {영역ID} values: {값}' > /data/vendor/vsomeip/vhal_fifo"

# 배열 값 주입
adb shell "echo 'propId: {프로퍼티ID} areaId: {영역ID} values: [{값1},{값2}]' > /data/vendor/vsomeip/vhal_fifo"
```

- `areaId`는 전역 속성의 경우 보통 `0`을 사용합니다.

---

## 3. 주요 제어 항목

### 3-1. 기어 변경 — `GEAR_SELECTION`
| 항목 | 값 |
|------|-----|
| propId | `289408000` |
| P단 (주차) | `values: 4` |
| D단 (드라이브) | `values: 8` |

```bash
# 주행 시작: D단으로 변경
adb shell "echo 'propId: 289408000 areaId: 0 values: 8' > /data/vendor/vsomeip/vhal_fifo"

# 주차: P단으로 변경
adb shell "echo 'propId: 289408000 areaId: 0 values: 4' > /data/vendor/vsomeip/vhal_fifo"
```

### 3-2. 속도 변경 — `PERF_VEHICLE_SPEED`
| 항목 | 값 |
|------|-----|
| propId | `291504647` |
| 단위 | **m/s** (60km/h ≈ 16.67 m/s) |

> 급가속/급감속 판정: 현재 속도 대비 **30km/h 이상** 변화 시 감지

```bash
# 60km/h 주행 (60 / 3.6 ≈ 16.67)
adb shell "echo 'propId: 291504647 areaId: 0 values: 16.67' > /data/vendor/vsomeip/vhal_fifo"

# 정지
adb shell "echo 'propId: 291504647 areaId: 0 values: 0' > /data/vendor/vsomeip/vhal_fifo"
```

km/h → m/s 변환: `m/s = km/h ÷ 3.6`

### 3-3. 핸들(조향각) 변경 — `PERF_STEERING_ANGLE`
| 항목 | 값 |
|------|-----|
| propId | `291504649` |
| 범위 | `-470` ~ `500` |

> 조향 미숙 판정: **50도 이상** 좌우 급변경 시 감점

```bash
# 우측 30도 조향
adb shell "echo 'propId: 291504649 areaId: 0 values: 30' > /data/vendor/vsomeip/vhal_fifo"

# 좌측 30도 조향
adb shell "echo 'propId: 291504649 areaId: 0 values: -30' > /data/vendor/vsomeip/vhal_fifo"

# 중립
adb shell "echo 'propId: 291504649 areaId: 0 values: 0' > /data/vendor/vsomeip/vhal_fifo"
```

---

## 4. 앱에서 상태 값 읽기

### 단발성 조회 (Get)
```kotlin
vehicleSdkRepository.getCurrentSteeringWheelAngle(
    onComplete = { angle -> /* 현재 조향각 */ },
    onFailed = { error -> /* 실패 처리 */ }
)
```

### 실시간 모니터링 (Callback)
```kotlin
// 등록
vehicleSdkRepository.registerSteeringWheelAngle(listener)

// 해제 (반드시 onDestroy 등에서 호출)
vehicleSdkRepository.unregisterSteeringWheelAngle(listener)
```

### SDK 생명주기
```kotlin
@Inject lateinit var vehicle: Vehicle

override fun onCreate(savedInstanceState: Bundle?) {
    super.onCreate(savedInstanceState)
    vehicle.initialize()
}

override fun onDestroy() {
    vehicle.release()
    super.onDestroy()
}
```
> `Vehicle` 인스턴스는 Hilt 모듈에서 `@Provides` + `@Singleton`으로 제공합니다.

---

## 5. 모의주행 시나리오 예시

아래는 "출발 → 가속 → 급감속(감점) → 정지 → 주차" 흐름을 재현하는 예시입니다.

```bash
adb root

# 1) D단 전환 후 출발
adb shell "echo 'propId: 289408000 areaId: 0 values: 8' > /data/vendor/vsomeip/vhal_fifo"

# 2) 60km/h 가속
adb shell "echo 'propId: 291504647 areaId: 0 values: 16.67' > /data/vendor/vsomeip/vhal_fifo"

# 3) 급감속 유발 (30km/h 이상 급변 → 감점 트리거)
adb shell "echo 'propId: 291504647 areaId: 0 values: 2.78' > /data/vendor/vsomeip/vhal_fifo"

# 4) 정지
adb shell "echo 'propId: 291504647 areaId: 0 values: 0' > /data/vendor/vsomeip/vhal_fifo"

# 5) P단 주차
adb shell "echo 'propId: 289408000 areaId: 0 values: 4' > /data/vendor/vsomeip/vhal_fifo"
```

### 안전운전 점수 로직 참고
- 시작 점수: **100P**
- 감점 단위: 감지 항목당 **5점**
- 감점 요소: ① 급가속 ② 급감속 ③ 핸들 조향 미숙

---

## 6. 빠른 참조 표

| 속성 | propId | 단위/범위 | 비고 |
|------|--------|-----------|------|
| GEAR_SELECTION | `289408000` | P=4, D=8 | 기어 |
| PERF_VEHICLE_SPEED | `291504647` | m/s | 30km/h↑ 급변 시 감점 |
| PERF_STEERING_ANGLE | `291504649` | -470 ~ 500 | 50도↑ 급변 시 감점 |

FIFO 경로: `/data/vendor/vsomeip/vhal_fifo`

---

## 7. 모의주행 중 위치(GPS) 변경

> 차량 속성(기어/속도/조향)은 VHAL FIFO로 주입하지만, **위치는 VHAL이 아니라
> 에뮬레이터 GPS**를 통해 변경합니다. Navi 앱이 그 GPS를 읽어 내비게이션 위치로 사용합니다.

### 7-1. NaviHelper SDK의 위치 처리 방식 (읽기 전용)
프로젝트의 `PleosNaviHelperNavigationClient`에서 확인되는 동작:

- **위치 조회만 가능**: `NaviHelper.getCurrentLocationInfo()` 호출 → `onCurrentLocationInfo(CurrentLocationInfo)` 콜백으로 통지
  ```kotlin
  override fun onCurrentLocationInfo(info: CurrentLocationInfo) {
      // info.latitude, info.longitude, info.address, info.routeId, info.currentRouteIndex
      CurrentLocationStore.update(CurrentLocation(info.latitude, info.longitude, info.address))
  }
  ```
- **NaviHelper SDK(v2.0.3)에는 위치를 "설정"하는 공개 API가 없습니다.** 즉 코드로 차량의
  현재 위치를 임의 좌표로 바꿀 수 없고, 위치 소스(에뮬레이터 GPS)를 바꿔야 합니다.
- 경로/경유지는 설정 가능: `requestRoute(RouteInfo)`, `addWaypoint(RequestWaypointInfo)`,
  `cancelRoute()`, `removeWaypoint(...)` — 단, `addWaypoint`는 **진행 중인 경로가 있어야** 동작.

### 7-2. 위치 소스 (실측 확인됨)
- 위치는 표준 에뮬레이터 GNSS HAL(`android.hardware.gnss-service.ranchu`)에서 나옵니다.
- Navi 앱(`ai.umos.maps.android.navigation.app`)은 GPS를 **PASSIVE**(수동)로만 구독합니다.
- GNSS HAL은 **누군가 능동(active) 위치 요청을 할 때만 위치를 내보냅니다.**
  대기 상태에서는 `gps provider: ProviderRequest[OFF]`라서, 좌표를 주입해도 전달되지 않습니다.
  → **경로 안내를 실제로 시작해야** GNSS가 켜지고 위치가 흐릅니다.

### 7-3. 방법 A — `adb emu geo fix` (경로 안내 중 권장)

```bash
# 형식: adb emu geo fix <경도(longitude)> <위도(latitude)> [고도]
#  주의: 위도가 아니라 "경도"가 먼저 옵니다.

adb emu geo fix 126.9779 37.5663   # 서울시청 (경도, 위도)
adb emu geo fix 129.0756 35.1796   # 부산시청
```

- **전제**: 내비 경로 안내가 진행 중이어야 합니다(GNSS active 상태). 대기 상태에서 주입하면
  `OK`만 뜨고 실제 위치는 바뀌지 않습니다(실측: `dumpsys location` last location 불변).
- 위치 스위치가 꺼져 있으면: `adb shell cmd location set-location-enabled true`
- 연속 이동(주행 트랙) 흉내는 짧은 간격으로 반복 주입:
  ```bash
  adb emu geo fix 126.9779 37.5663
  adb emu geo fix 126.9785 37.5670
  adb emu geo fix 126.9791 37.5677
  ```

### 7-4. 방법 B — Android Studio Extended Controls → Location (가장 쉬움)
1. 에뮬레이터 옆 `⋯`(Extended controls) → **Location** 탭
2. **Single points**: 좌표 입력 후 `SET LOCATION` → 한 점으로 순간이동
3. **Routes**: GPX/KML 가져오기 또는 지도에서 경로 작성 → `PLAY ROUTE` → 좌표를 능동적으로
   연속 송출하므로 GNSS가 켜지고, **주행 이동 시뮬레이션에 가장 안정적**입니다.

### 7-5. 방법 C — Mock Location (test provider, 능동 강제)
대기 상태에서도 위치를 강제하려면 mock location을 써야 합니다. 단, **개발자 옵션에서
"모의 위치 앱"으로 지정**된 앱만 가능합니다(순수 adb shell 주입은 이 빌드에서 `MOCK_LOCATION`
거부됨 — 실측 확인).
```bash
# 개발자 옵션 > "모의 위치 앱" 지정 후
adb shell cmd location providers add-test-provider gps
adb shell cmd location providers set-test-provider-enabled gps true
# --location 은 "위도,경도" 순서
adb shell cmd location providers set-test-provider-location gps --location 37.5663,126.9779
```

> **인자 순서 정리**
> - `adb emu geo fix` → `경도 위도`
> - `set-test-provider-location --location` → `위도,경도`
> - 앱의 `CurrentLocationInfo` → `(longitude, latitude)`, `RouteInfo`/`RequestWaypointInfo` → `(latitude, longitude)`
>
> 앱 서비스 좌표 범위(코드 검증 기준): 위도 `33.0 ~ 39.6`, 경도 `124.5 ~ 132.0` (대한민국).

### 7-4. 위치 변경 검증
```bash
# 현재 시스템이 인식하는 마지막 위치 확인
adb shell "dumpsys location" | grep -iE "last location|gps provider"

# 앱/SDK가 위치를 수신하는지 로그로 확인
adb logcat | grep -iE "onCurrentLocationInfo|CurrentLocation"
```

### 7-6. 참고: Navi 내부 시뮬레이션 주행
navi-data SDK에는 `NaviEvent.RequestSimulatedDrive`,
`RequestMoveMapToCurrentLocation` 같은 내부 이벤트가 정의되어 있으나, **NaviHelper 공개
API로는 노출되지 않습니다.** 따라서 외부 앱에서 직접 호출할 수 없고, Navi 앱 자체의
시뮬레이션 주행 기능에 의해 사용됩니다. 외부에서의 위치 모의는 위 7-2 방식(에뮬레이터 GPS)을
사용하세요.
