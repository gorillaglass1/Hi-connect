from app.services.geo_utils import haversine_km, location_grid_key


def test_same_point_is_zero():
    assert haversine_km(37.5665, 126.9780, 37.5665, 126.9780) == 0.0


def test_known_distance_seoul_cityhall_to_gangnam():
    # 서울시청 <-> 강남역 직선거리는 대략 8.8km.
    distance = haversine_km(37.5665, 126.9780, 37.4979, 127.0276)
    assert 8.0 < distance < 9.5


def test_is_symmetric():
    a = haversine_km(37.5665, 126.9780, 35.1796, 129.0756)
    b = haversine_km(35.1796, 129.0756, 37.5665, 126.9780)
    assert abs(a - b) < 1e-9


def test_location_grid_key_quantizes():
    assert location_grid_key(37.56651, 126.97801) == "37.57,126.98"


def test_location_grid_key_groups_nearby_points():
    # 인근 좌표는 동일 그리드 키로 묶여 캐시를 공유한다.
    assert location_grid_key(37.561, 126.982) == location_grid_key(37.564, 126.984)
