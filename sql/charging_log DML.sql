INSERT INTO charging_log (
    user_id,
    hydrogen_station_id,
    vehicle_id,
    start_time,
    end_time,
    charged_amount,
    charging_cost,
    waiting_time
)
VALUES
(
    1,                          -- 사용자 ID
    1,                          -- 충전소 ID
    1,                          -- 차량 ID
    '2026-04-27 09:10:00',     -- 충전 시작 시간
    '2026-04-27 09:25:00',     -- 충전 종료 시간
    4.25,                       -- 충전량 (kg)
    42500.00,                   -- 충전 비용 (원)
    8                           -- 대기시간 (분)
),

(
    2,
    3,
    2,
    '2026-04-27 11:40:00',
    '2026-04-27 11:58:00',
    5.10,
    51000.00,
    15
),

(
    1,
    2,
    1,
    '2026-04-27 18:05:00',
    '2026-04-27 18:20:00',
    3.85,
    38500.00,
    5
);