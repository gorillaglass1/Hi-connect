"""위치 관련 순수 계산 유틸 (외부 의존성 없음)."""

import math

EARTH_RADIUS_KM = 6371.0088


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """두 좌표(위도/경도, degree) 사이의 대원 거리를 km로 반환한다.

    LLM의 SQL에서 거리 계산을 하면 부정확하므로, 충전소 정렬/최근접 선정은
    반드시 이 함수로 백엔드에서 계산한다.
    """
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lon2 - lon1)

    a = (
        math.sin(d_phi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2
    )
    return 2 * EARTH_RADIUS_KM * math.asin(min(1.0, math.sqrt(a)))


def location_grid_key(lat: float, lon: float, precision: int = 2) -> str:
    """캐시 키에 쓰일 위치 그리드 문자열. 소수 precision 자리로 양자화한다.

    precision=2 이면 약 1km 격자 단위로 묶여 인근 요청이 캐시를 공유한다.
    """
    return f"{round(lat, precision)},{round(lon, precision)}"
