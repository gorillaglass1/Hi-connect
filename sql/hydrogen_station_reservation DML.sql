INSERT INTO hydrogen_station_reservation (
    hydrogen_charger_id,
    hydrogen_station_id,
    reservation_status,
    user_id,
    reservation_time,
    expire_time
) VALUES
(
    1,
    1,
    'RESERVED',
    1,
    '2026-04-27 18:00:00',
    '2026-04-27 18:30:00'
),
(
    2,
    1,
    'COMPLETED',
    2,
    '2026-04-27 14:20:00',
    '2026-04-27 14:50:00'
),
(
    3,
    2,
    'EXPIRED',
    3,
    '2026-04-27 15:00:00',
    '2026-04-27 15:20:00'
);