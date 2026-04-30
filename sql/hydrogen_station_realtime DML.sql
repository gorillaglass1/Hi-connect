INSERT INTO hydrogen_station_realtime (
    hydrogen_station_id,
    available_chargers,
    in_use_chargers,
    queue_count,
    avg_wait_time,
    hydrogen_stock_kg,
    station_status,
    last_restock_at,
    next_restock_schedule,
    utilization_rate
) VALUES
(
    1,
    2,
    3,
    4,
    12,
    185.50,
    'BUSY',
    '2026-04-27 06:30:00',
    '2026-04-27 18:00:00',
    60.00
),
(
    2,
    4,
    1,
    0,
    3,
    320.75,
    'AVAILABLE',
    '2026-04-27 08:00:00',
    '2026-04-28 08:00:00',
    20.00
),
(
    3,
    0,
    5,
    8,
    25,
    42.30,
    'LOW_HYDROGEN',
    '2026-04-26 22:15:00',
    '2026-04-27 12:30:00',
    100.00
);