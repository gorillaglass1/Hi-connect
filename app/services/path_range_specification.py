import math
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.hydrogen_station import HydrogenStation


EARTH_RADIUS_KM = 6371.0
KM_PER_LAT_DEG = math.pi * EARTH_RADIUS_KM / 180.0


def haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    lat1_r = math.radians(lat1)
    lat2_r = math.radians(lat2)
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1_r) * math.cos(lat2_r) * math.sin(dlng / 2) ** 2
    )
    return 2 * EARTH_RADIUS_KM * math.asin(math.sqrt(a))


def find_theta_binary_search(detour_ratio: float, iterations: int = 50) -> float:
    if detour_ratio < 1.0:
        raise ValueError(
            f"detour_ratio must be >= 1.0 (got {detour_ratio}); "
            "actual route cannot be shorter than straight-line distance."
        )
    if detour_ratio == 1.0:
        return 0.0

    lo, hi = 1e-12, 2 * math.pi - 1e-12
    for _ in range(iterations):
        mid = (lo + hi) / 2
        val = mid / (2 * math.sin(mid / 2))
        if val < detour_ratio:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def km_to_lat_deg(km: float) -> float:
    return km / KM_PER_LAT_DEG


def km_to_lng_deg(km: float, ref_lat: float) -> float:
    return km / (KM_PER_LAT_DEG * math.cos(math.radians(ref_lat)))


def calc_circumscribed_box(
    x_lat: float,
    x_lng: float,
    y_lat: float,
    y_lng: float,
    r_km: float,
    theta: float,
) -> dict[str, float]:
    mid_lat = (x_lat + y_lat) / 2.0

    offset_km = r_km * math.cos(theta / 2)
    offset_lat = km_to_lat_deg(offset_km)
    r_lat = km_to_lat_deg(r_km)

    upper_apex_lat = mid_lat + (r_lat - offset_lat)
    lower_apex_lat = mid_lat - (r_lat - offset_lat)

    return {
        "lat_min": lower_apex_lat,
        "lat_max": upper_apex_lat,
        "lng_min": min(x_lng, y_lng),
        "lng_max": max(x_lng, y_lng),
    }


def calc_inscribed_box(
    x_lat: float,
    x_lng: float,
    y_lat: float,
    y_lng: float,
    r_km: float,
    theta: float,
) -> dict[str, float]:
    mid_lat = (x_lat + y_lat) / 2.0
    mid_lng = (x_lng + y_lng) / 2.0

    offset_km = r_km * math.cos(theta / 2)
    offset_lat = km_to_lat_deg(offset_km)
    r_lat = km_to_lat_deg(r_km)

    upper_apex_lat = mid_lat + (r_lat - offset_lat)
    lower_apex_lat = mid_lat - (r_lat - offset_lat)

    upper_center_lat = mid_lat - offset_lat
    dy_km = (lower_apex_lat - upper_center_lat) * KM_PER_LAT_DEG
    dx_sq_km = r_km**2 - dy_km**2
    dx_km = math.sqrt(max(0.0, dx_sq_km))
    dx_lng = km_to_lng_deg(dx_km, mid_lat)

    return {
        "lat_min": lower_apex_lat,
        "lat_max": upper_apex_lat,
        "lng_min": mid_lng - dx_lng,
        "lng_max": mid_lng + dx_lng,
    }


def clamp_inscribed_to_circumscribed(
    inscribed_box: dict[str, float],
    circumscribed_box: dict[str, float],
) -> dict[str, float]:
    return {
        **inscribed_box,
        "lng_min": max(inscribed_box["lng_min"], circumscribed_box["lng_min"]),
        "lng_max": min(inscribed_box["lng_max"], circumscribed_box["lng_max"]),
    }


def apply_padding(box: dict[str, float], padding_km: float) -> dict[str, float]:
    padding_lat = km_to_lat_deg(padding_km)
    return {
        "lat_min": box["lat_min"] - padding_lat,
        "lat_max": box["lat_max"] + padding_lat,
        "lng_min": box["lng_min"],
        "lng_max": box["lng_max"],
    }


def split_ring_into_boxes(
    inscribed_box: dict[str, float],
    circumscribed_box: dict[str, float],
) -> tuple[dict[str, float], dict[str, float], dict[str, float], dict[str, float]]:
    top_box = {
        "lat_min": circumscribed_box["lat_min"],
        "lat_max": inscribed_box["lat_min"],
        "lng_min": inscribed_box["lng_min"],
        "lng_max": inscribed_box["lng_max"],
    }
    bottom_box = {
        "lat_min": inscribed_box["lat_max"],
        "lat_max": circumscribed_box["lat_max"],
        "lng_min": inscribed_box["lng_min"],
        "lng_max": inscribed_box["lng_max"],
    }
    left_box = {
        "lat_min": circumscribed_box["lat_min"],
        "lat_max": circumscribed_box["lat_max"],
        "lng_min": circumscribed_box["lng_min"],
        "lng_max": inscribed_box["lng_min"],
    }
    right_box = {
        "lat_min": circumscribed_box["lat_min"],
        "lat_max": circumscribed_box["lat_max"],
        "lng_min": inscribed_box["lng_max"],
        "lng_max": circumscribed_box["lng_max"],
    }
    return top_box, bottom_box, left_box, right_box


def is_in_box(lat: float, lng: float, box: dict[str, float]) -> bool:
    return (
        box["lat_min"] <= lat <= box["lat_max"]
        and box["lng_min"] <= lng <= box["lng_max"]
    )


async def find_charging_stations(
    db: AsyncSession,
    x_lat: float,
    x_lng: float,
    y_lat: float,
    y_lng: float,
    actual_distance_km: float,
    padding_km: float = 5.0,
) -> dict[str, Any]:
    straight_distance_km = haversine_km(x_lat, x_lng, y_lat, y_lng)
    if straight_distance_km == 0:
        raise ValueError("Start and end points must be different.")

    detour_ratio = actual_distance_km / straight_distance_km
    theta = find_theta_binary_search(detour_ratio)
    if theta == 0.0:
        circumscribed_box = {
            "lat_min": min(x_lat, y_lat),
            "lat_max": max(x_lat, y_lat),
            "lng_min": min(x_lng, y_lng),
            "lng_max": max(x_lng, y_lng),
        }
        inscribed_box = dict(circumscribed_box)
    else:
        r_km = (straight_distance_km / 2) / math.sin(theta / 2)
        circumscribed_box = calc_circumscribed_box(
            x_lat, x_lng, y_lat, y_lng, r_km, theta
        )
        inscribed_box = calc_inscribed_box(
            x_lat, x_lng, y_lat, y_lng, r_km, theta
        )
        inscribed_box = clamp_inscribed_to_circumscribed(
            inscribed_box,
            circumscribed_box,
        )

    circumscribed_box = apply_padding(circumscribed_box, padding_km)
    inscribed_box = apply_padding(inscribed_box, -padding_km)

    top_box, bottom_box, left_box, right_box = split_ring_into_boxes(
        inscribed_box,
        circumscribed_box,
    )

    result = await db.execute(
        select(HydrogenStation).where(
            HydrogenStation.let.isnot(None),
            HydrogenStation.lon.isnot(None),
            HydrogenStation.let.between(
                circumscribed_box["lat_min"], circumscribed_box["lat_max"]
            ),
            HydrogenStation.lon.between(
                circumscribed_box["lng_min"], circumscribed_box["lng_max"]
            ),
        )
    )
    stations_in_outer = list(result.scalars().all())

    candidate_stations = [
        station
        for station in stations_in_outer
        if (
            is_in_box(float(station.let), float(station.lon), top_box)
            or is_in_box(float(station.let), float(station.lon), bottom_box)
            or is_in_box(float(station.let), float(station.lon), left_box)
            or is_in_box(float(station.let), float(station.lon), right_box)
        )
    ]

    return {
        "circumscribed_box": circumscribed_box,
        "inscribed_box": inscribed_box,
        "top_box": top_box,
        "bottom_box": bottom_box,
        "left_box": left_box,
        "right_box": right_box,
        "candidate_stations": candidate_stations,
    }
