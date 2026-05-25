from datetime import datetime, timedelta
from types import SimpleNamespace

import pytest

from app.services.queue_time_estimation_service import (
    MAX_QUEUE_TIME_MINUTES,
    QueueTimeEstimationService,
)


def _station(**overrides):
    values = {
        "oper_yn": "Y",
        "cmpt_yn": "N",
        "chrgr_ty_nm": "승용",
        "echrgeqp_ty_nm": None,
        "chrstn_ty_rm": None,
        "event_cn": None,
        "vhcle_knd_nm": "승용차",
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def _status(**overrides):
    values = {
        "wait_vhcle_alge": 0,
        "tt_pressr": 700,
        "prfect_elctc_posbl_alge": 10,
        "cnf_sttus_nm": "여유",
        "oper_sttus_cd": "30",
        "oper_sttus_nm": "운영중",
        "pos_sttus_cd": "0",
        "pos_sttus_nm": "영업중",
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def _log(station_id: str, start_time: datetime, duration_minutes: int, waiting_time: int):
    return SimpleNamespace(
        chrstn_mno=station_id,
        start_time=start_time,
        end_time=start_time + timedelta(minutes=duration_minutes),
        waiting_time=waiting_time,
    )


def test_queue_estimator_combines_realtime_capacity_history_and_congestion():
    service = QueueTimeEstimationService()
    arrival_time = datetime(2026, 5, 24, 8, 45)
    history = service.build_history_stats(
        [
            _log("QUEUE-ST-001", datetime(2026, 5, 24, 8, 0), 10, 6),
            _log("QUEUE-ST-001", datetime(2026, 5, 24, 8, 20), 10, 6),
        ]
    )

    estimate = service.estimate(
        station=_station(cmpt_yn="Y"),
        status=_status(wait_vhcle_alge=4, cnf_sttus_nm="혼잡"),
        history=history["QUEUE-ST-001"],
        arrival_time=arrival_time,
    )

    assert estimate.active_chargers == 2
    assert estimate.avg_charge_minutes == 10.0
    assert estimate.wait_vehicles == 4
    assert estimate.estimated_wait_minutes == 32
    assert estimate.service_available is True
    assert "실시간 혼잡도가 높습니다." in estimate.reasons


def test_queue_estimator_marks_unavailable_status_as_max_queue_time():
    estimate = QueueTimeEstimationService().estimate(
        station=_station(),
        status=_status(pos_sttus_nm="점검중", prfect_elctc_posbl_alge=0),
    )

    assert estimate.service_available is False
    assert estimate.active_chargers == 0
    assert estimate.estimated_wait_minutes == MAX_QUEUE_TIME_MINUTES
    assert estimate.availability_multiplier < 1.0


def test_queue_estimator_applies_mvp_formula_with_active_charger_capacity():
    estimate = QueueTimeEstimationService().estimate(
        station=_station(cmpt_yn="Y"),
        status=_status(wait_vhcle_alge=4),
    )

    assert estimate.active_chargers == 2
    assert estimate.avg_charge_minutes == 6.0
    assert estimate.wait_vehicles == 4
    assert estimate.estimated_wait_minutes == 15
    assert estimate.confidence == "medium"


def test_queue_estimator_uses_commercial_vehicle_default_charge_time():
    estimate = QueueTimeEstimationService().estimate(
        station=_station(vhcle_knd_nm="버스/상용차", chrgr_ty_nm="버스"),
        status=_status(wait_vhcle_alge=2),
    )

    assert estimate.avg_charge_minutes == 15.0
    assert estimate.estimated_wait_minutes == 38


def test_queue_estimator_parses_charger_count_from_station_text():
    estimate = QueueTimeEstimationService().estimate(
        station=_station(chrgr_ty_nm="700bar 충전기 3기"),
        status=_status(wait_vhcle_alge=3),
    )

    assert estimate.active_chargers == 3
    assert estimate.estimated_wait_minutes == 9


def test_queue_estimator_reduces_availability_when_pressure_is_low():
    estimate = QueueTimeEstimationService().estimate(
        station=_station(),
        status=_status(tt_pressr=500, wait_vhcle_alge=1),
    )

    assert estimate.service_available is True
    assert estimate.availability_multiplier == 0.75
    assert "충전 압력이 낮아 처리 속도가 느릴 수 있습니다." in estimate.reasons


def test_queue_history_stats_group_by_station_and_arrival_hour():
    service = QueueTimeEstimationService()
    stats = service.build_history_stats(
        [
            _log("QUEUE-ST-A", datetime(2026, 5, 24, 8, 0), 6, 2),
            _log("QUEUE-ST-A", datetime(2026, 5, 24, 8, 20), 120, 4),
            _log("QUEUE-ST-A", datetime(2026, 5, 24, 9, 0), 8, None),
            _log("QUEUE-ST-B", datetime(2026, 5, 24, 8, 0), 10, 0),
        ]
    )

    assert stats["QUEUE-ST-A"].avg_charge_minutes == pytest.approx(7.0)
    assert stats["QUEUE-ST-A"].avg_wait_minutes == pytest.approx(3.0)
    assert stats["QUEUE-ST-A"].hourly_avg_wait_minutes[8] == pytest.approx(3.0)
    assert stats["QUEUE-ST-A"].hourly_visit_rates[8] == pytest.approx(2.0)
    assert stats["QUEUE-ST-A"].hourly_visit_rates[9] == pytest.approx(1.0)
    assert stats["QUEUE-ST-A"].sample_count == 2
    assert stats["QUEUE-ST-B"].avg_charge_minutes == pytest.approx(10.0)


def test_queue_estimator_reports_high_confidence_with_status_and_history_samples():
    service = QueueTimeEstimationService()
    history = service.build_history_stats(
        [
            _log("QUEUE-ST-HIGH", datetime(2026, 5, 24, 8, idx), 6, 0)
            for idx in range(5)
        ]
    )

    estimate = service.estimate(
        station=_station(),
        status=_status(),
        history=history["QUEUE-ST-HIGH"],
    )

    assert estimate.confidence == "high"
