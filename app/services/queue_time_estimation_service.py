from __future__ import annotations

import math
import re
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Iterable

from app.models.charging_log import ChargingLog
from app.models.hydrogen_station import HydrogenStation
from app.models.hydrogen_station_status import HydrogenStationStatus

DEFAULT_PASSENGER_CHARGE_MINUTES = 6.0
DEFAULT_COMMERCIAL_CHARGE_MINUTES = 15.0
MAX_QUEUE_TIME_MINUTES = 180
MIN_VALID_CHARGE_MINUTES = 2.0
MAX_VALID_CHARGE_MINUTES = 90.0

UNAVAILABLE_STATUS_KEYWORDS = (
    "점검",
    "마감",
    "중지",
    "중단",
    "휴무",
    "고장",
    "불가",
)
COMMERCIAL_VEHICLE_KEYWORDS = ("버스", "상용", "트럭", "화물")


@dataclass(frozen=True)
class ChargingHistoryStats:
    avg_charge_minutes: float | None = None
    avg_wait_minutes: float | None = None
    hourly_avg_wait_minutes: dict[int, float] = field(default_factory=dict)
    hourly_visit_rates: dict[int, float] = field(default_factory=dict)
    sample_count: int = 0


@dataclass(frozen=True)
class QueueTimeEstimate:
    wait_vehicles: int
    estimated_wait_minutes: int
    avg_charge_minutes: float
    active_chargers: int
    service_available: bool
    availability_multiplier: float
    confidence: str
    reasons: tuple[str, ...] = ()


class QueueTimeEstimationService:
    """Estimates hydrogen station queue time from realtime status and usage history."""

    def build_history_stats(
        self,
        logs: Iterable[ChargingLog],
    ) -> dict[str, ChargingHistoryStats]:
        station_charge_minutes: dict[str, list[float]] = defaultdict(list)
        station_wait_minutes: dict[str, list[float]] = defaultdict(list)
        hourly_wait_minutes: dict[str, dict[int, list[float]]] = defaultdict(
            lambda: defaultdict(list)
        )
        hourly_visit_dates: dict[str, dict[int, set]] = defaultdict(
            lambda: defaultdict(set)
        )
        hourly_visit_counts: dict[str, dict[int, int]] = defaultdict(
            lambda: defaultdict(int)
        )

        for log in logs:
            station_id = log.chrstn_mno
            duration = _duration_minutes(log.start_time, log.end_time)
            if duration is not None:
                station_charge_minutes[station_id].append(duration)

            wait_minutes = _safe_float(log.waiting_time)
            if wait_minutes is not None:
                wait_minutes = _clamp(wait_minutes, 0.0, float(MAX_QUEUE_TIME_MINUTES))
                station_wait_minutes[station_id].append(wait_minutes)

            if log.start_time is None:
                continue

            hour = log.start_time.hour
            hourly_visit_counts[station_id][hour] += 1
            hourly_visit_dates[station_id][hour].add(log.start_time.date())
            if wait_minutes is not None:
                hourly_wait_minutes[station_id][hour].append(wait_minutes)

        station_ids = (
            set(station_charge_minutes)
            | set(station_wait_minutes)
            | set(hourly_visit_counts)
        )
        stats: dict[str, ChargingHistoryStats] = {}
        for station_id in station_ids:
            hourly_rates = {}
            for hour, count in hourly_visit_counts[station_id].items():
                service_days = max(1, len(hourly_visit_dates[station_id][hour]))
                hourly_rates[hour] = count / service_days

            stats[station_id] = ChargingHistoryStats(
                avg_charge_minutes=_average_or_none(station_charge_minutes[station_id]),
                avg_wait_minutes=_average_or_none(station_wait_minutes[station_id]),
                hourly_avg_wait_minutes={
                    hour: avg
                    for hour, values in hourly_wait_minutes[station_id].items()
                    if (avg := _average_or_none(values)) is not None
                },
                hourly_visit_rates=hourly_rates,
                sample_count=len(station_charge_minutes[station_id]),
            )

        return stats

    def estimate(
        self,
        *,
        station: HydrogenStation,
        status: HydrogenStationStatus | None,
        history: ChargingHistoryStats | None = None,
        arrival_time: datetime | None = None,
    ) -> QueueTimeEstimate:
        history = history or ChargingHistoryStats()
        wait_vehicles = max(0, _safe_int(getattr(status, "wait_vhcle_alge", None)) or 0)
        avg_charge_minutes = _clamp(
            history.avg_charge_minutes or _default_charge_minutes(station),
            MIN_VALID_CHARGE_MINUTES,
            MAX_VALID_CHARGE_MINUTES,
        )
        service_available, availability_multiplier, status_reasons = (
            _service_availability(station, status)
        )
        active_chargers = _infer_active_chargers(station, status)
        if not service_available:
            return QueueTimeEstimate(
                wait_vehicles=wait_vehicles,
                estimated_wait_minutes=MAX_QUEUE_TIME_MINUTES,
                avg_charge_minutes=round(avg_charge_minutes, 1),
                active_chargers=0,
                service_available=False,
                availability_multiplier=availability_multiplier,
                confidence=_confidence(status, history),
                reasons=tuple(status_reasons),
            )

        active_chargers = max(1, active_chargers)
        base_queue_minutes = (wait_vehicles * avg_charge_minutes) / active_chargers
        residual_service_minutes = (avg_charge_minutes * 0.5) if wait_vehicles > 0 else 0.0
        historical_delay = _historical_wait_delay(history, arrival_time)
        arrival_pressure_delay = _arrival_pressure_delay(
            history,
            arrival_time,
            active_chargers,
            avg_charge_minutes,
        )
        realtime_status_delay, realtime_reasons = _realtime_status_delay(
            status,
            avg_charge_minutes,
        )

        estimated_minutes = (
            base_queue_minutes
            + residual_service_minutes
            + historical_delay
            + arrival_pressure_delay
            + realtime_status_delay
        )
        estimated_minutes = int(
            round(_clamp(estimated_minutes, 0.0, float(MAX_QUEUE_TIME_MINUTES)))
        )

        reasons = tuple(status_reasons + realtime_reasons)
        return QueueTimeEstimate(
            wait_vehicles=wait_vehicles,
            estimated_wait_minutes=estimated_minutes,
            avg_charge_minutes=round(avg_charge_minutes, 1),
            active_chargers=active_chargers,
            service_available=True,
            availability_multiplier=availability_multiplier,
            confidence=_confidence(status, history),
            reasons=reasons,
        )


def _duration_minutes(start_time: datetime | None, end_time: datetime | None) -> float | None:
    if start_time is None or end_time is None or end_time <= start_time:
        return None

    minutes = (end_time - start_time).total_seconds() / 60.0
    if MIN_VALID_CHARGE_MINUTES <= minutes <= MAX_VALID_CHARGE_MINUTES:
        return minutes
    return None


def _historical_wait_delay(
    history: ChargingHistoryStats,
    arrival_time: datetime | None,
) -> float:
    if arrival_time is not None:
        hourly_wait = history.hourly_avg_wait_minutes.get(arrival_time.hour)
        if hourly_wait is not None:
            return min(60.0, hourly_wait) * 0.35

    if history.avg_wait_minutes is None:
        return 0.0
    return min(60.0, history.avg_wait_minutes) * 0.20


def _arrival_pressure_delay(
    history: ChargingHistoryStats,
    arrival_time: datetime | None,
    active_chargers: int,
    avg_charge_minutes: float,
) -> float:
    if arrival_time is None:
        return 0.0

    hourly_visit_rate = history.hourly_visit_rates.get(arrival_time.hour, 0.0)
    excess_arrivals = max(0.0, hourly_visit_rate - active_chargers)
    return min(20.0, excess_arrivals * avg_charge_minutes * 0.25)


def _realtime_status_delay(
    status: HydrogenStationStatus | None,
    avg_charge_minutes: float,
) -> tuple[float, list[str]]:
    if status is None:
        return 0.0, []

    delay = 0.0
    reasons: list[str] = []
    congestion_name = _normalize_text(getattr(status, "cnf_sttus_nm", None))
    if "혼잡" in congestion_name:
        delay += avg_charge_minutes * 0.5
        reasons.append("실시간 혼잡도가 높습니다.")
    elif "보통" in congestion_name:
        delay += avg_charge_minutes * 0.2

    full_charge_capacity = _safe_int(getattr(status, "prfect_elctc_posbl_alge", None))
    if full_charge_capacity is not None and 0 < full_charge_capacity <= 2:
        delay += 5.0
        reasons.append("잔여 완충 가능 대수가 낮습니다.")

    return delay, reasons


def _service_availability(
    station: HydrogenStation,
    status: HydrogenStationStatus | None,
) -> tuple[bool, float, list[str]]:
    reasons: list[str] = []

    if getattr(station, "oper_yn", None) == "N":
        return False, 0.15, ["충전소 운영 여부가 비활성입니다."]

    if status is None:
        return True, 1.0, reasons

    status_text = " ".join(
        _normalize_text(value)
        for value in (
            getattr(status, "oper_sttus_cd", None),
            getattr(status, "oper_sttus_nm", None),
            getattr(status, "pos_sttus_cd", None),
            getattr(status, "pos_sttus_nm", None),
        )
        if value is not None
    )
    if any(keyword in status_text for keyword in UNAVAILABLE_STATUS_KEYWORDS):
        return False, 0.15, ["현재 영업/충전 가능 상태가 아닙니다."]

    pressure = _safe_int(getattr(status, "tt_pressr", None))
    full_charge_capacity = _safe_int(getattr(status, "prfect_elctc_posbl_alge", None))
    if pressure == 0 or full_charge_capacity == 0:
        return False, 0.15, ["압력 또는 완충 가능 대수가 부족합니다."]

    if pressure is not None and pressure < 700:
        reasons.append("충전 압력이 낮아 처리 속도가 느릴 수 있습니다.")
        return True, 0.75, reasons

    return True, 1.0, reasons


def _infer_active_chargers(
    station: HydrogenStation,
    status: HydrogenStationStatus | None,
) -> int:
    if status is not None:
        status_text = " ".join(
            _normalize_text(value)
            for value in (
                getattr(status, "oper_sttus_nm", None),
                getattr(status, "pos_sttus_nm", None),
            )
            if value is not None
        )
        if any(keyword in status_text for keyword in UNAVAILABLE_STATUS_KEYWORDS):
            return 0

    text_values = [
        getattr(station, "chrgr_ty_nm", None),
        getattr(station, "echrgeqp_ty_nm", None),
        getattr(station, "chrstn_ty_rm", None),
        getattr(station, "event_cn", None),
    ]
    joined_text = " ".join(_normalize_text(value) for value in text_values if value)
    parsed_counts = [
        int(match.group(1))
        for match in re.finditer(r"(\d+)\s*(?:기|대|라인|line)", joined_text)
    ]
    if parsed_counts:
        return int(_clamp(max(parsed_counts), 1, 8))

    if getattr(station, "cmpt_yn", None) == "Y":
        return 2

    return 1


def _default_charge_minutes(station: HydrogenStation) -> float:
    station_text = " ".join(
        _normalize_text(value)
        for value in (
            getattr(station, "vhcle_knd_nm", None),
            getattr(station, "chrgr_ty_nm", None),
            getattr(station, "chrstn_ty_rm", None),
        )
        if value
    )
    if any(keyword in station_text for keyword in COMMERCIAL_VEHICLE_KEYWORDS):
        return DEFAULT_COMMERCIAL_CHARGE_MINUTES
    return DEFAULT_PASSENGER_CHARGE_MINUTES


def _confidence(
    status: HydrogenStationStatus | None,
    history: ChargingHistoryStats,
) -> str:
    if status is not None and history.sample_count >= 5:
        return "high"
    if status is not None or history.sample_count > 0:
        return "medium"
    return "low"


def _safe_float(value) -> float | None:
    if value is None:
        return None
    if isinstance(value, Decimal):
        return float(value)
    try:
        if math.isnan(float(value)):
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _safe_int(value) -> int | None:
    number = _safe_float(value)
    if number is None:
        return None
    return int(number)


def _average_or_none(values: list[float]) -> float | None:
    if not values:
        return None
    return sum(values) / len(values)


def _clamp(value: float, lower: float, upper: float) -> float:
    return max(lower, min(upper, value))


def _normalize_text(value) -> str:
    return str(value or "").strip().lower()
