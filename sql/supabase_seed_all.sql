-- One-shot Supabase/PostgreSQL seed for users, charging logs, and recommendation history.
-- Copy and paste this whole file into Supabase SQL Editor and run it once.
--
-- Prerequisite:
--   hydrogen_stations must already contain rows from the Hying API sync.
--   This file does NOT insert hydrogen station data.

BEGIN;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM information_schema.tables
        WHERE table_schema = current_schema()
          AND table_name = 'hydrogen_stations'
    ) THEN
        RAISE EXCEPTION 'hydrogen_stations table does not exist. Run the server/Hying sync first.';
    END IF;

    IF (SELECT COUNT(*) FROM hydrogen_stations) < 5 THEN
        RAISE EXCEPTION 'hydrogen_stations needs at least 5 rows. Run the Hying station sync first.';
    END IF;
END $$;

CREATE TABLE IF NOT EXISTS users (
    user_id BIGSERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    phone VARCHAR(20),
    email VARCHAR(255) UNIQUE,
    created_at TIMESTAMP DEFAULT now()
);

CREATE TABLE IF NOT EXISTS charging_log (
    charging_log_id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    vehicle_id BIGINT NOT NULL,
    chrstn_mno VARCHAR(30) NOT NULL REFERENCES hydrogen_stations(chrstn_mno) ON DELETE CASCADE,
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP NOT NULL,
    charged_amount NUMERIC(6, 2),
    charging_cost NUMERIC(10, 2),
    waiting_time INTEGER,
    created_at TIMESTAMP DEFAULT now()
);

CREATE TABLE IF NOT EXISTS recommendation_history (
    recommendation_id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    vehicle_id BIGINT NOT NULL,
    chrstn_mno VARCHAR(30) NOT NULL REFERENCES hydrogen_stations(chrstn_mno) ON DELETE CASCADE,
    recommendation_score NUMERIC(5, 2),
    recommendation_reason VARCHAR(255),
    user_latitude NUMERIC(10, 7),
    user_longitude NUMERIC(10, 7),
    vehicle_remaining_hydrogen NUMERIC(6, 2),
    estimated_arrival_time INTEGER,
    selected BOOLEAN DEFAULT false,
    selected_at TIMESTAMP,
    recommendation_type VARCHAR(50),
    created_at TIMESTAMP DEFAULT now()
);

INSERT INTO users (
    user_id,
    name,
    phone,
    email
) VALUES
(1, '김하나', '010-1000-1001', 'hana@example.com'),
(2, '이도윤', '010-1000-1002', 'doyoon@example.com'),
(3, '박서준', '010-1000-1003', 'seojoon@example.com'),
(4, '최민서', '010-1000-1004', 'minseo@example.com')
ON CONFLICT (user_id) DO UPDATE SET
    name = EXCLUDED.name,
    phone = EXCLUDED.phone,
    email = EXCLUDED.email;

SELECT setval(
    pg_get_serial_sequence('users', 'user_id'),
    GREATEST((SELECT COALESCE(MAX(user_id), 1) FROM users), 1),
    true
);

DELETE FROM charging_log
WHERE user_id IN (1, 2, 3, 4)
  AND vehicle_id IN (101, 201, 301, 401);

WITH station_refs AS (
    SELECT chrstn_mno,
           ROW_NUMBER() OVER (
               ORDER BY
                   CASE
                       WHEN road_nm_addr LIKE '인천%' THEN 0
                       WHEN lotno_addr LIKE '인천%' THEN 0
                       ELSE 1
                   END,
                   chrstn_nm ASC,
                   chrstn_mno ASC
           ) AS station_rank
    FROM hydrogen_stations
),
seed_logs AS (
    SELECT *
    FROM (
        VALUES
            (1, 101, 1, TIMESTAMP '2026-05-22 08:10:00', TIMESTAMP '2026-05-22 08:24:00', 3.80::NUMERIC(6, 2), 36860.00::NUMERIC(10, 2), 0),
            (1, 101, 2, TIMESTAMP '2026-05-21 18:20:00', TIMESTAMP '2026-05-21 18:39:00', 4.10::NUMERIC(6, 2), 40590.00::NUMERIC(10, 2), 3),
            (2, 201, 3, TIMESTAMP '2026-05-21 09:05:00', TIMESTAMP '2026-05-21 09:31:00', 5.20::NUMERIC(6, 2), 49920.00::NUMERIC(10, 2), 8),
            (3, 301, 4, TIMESTAMP '2026-05-20 14:00:00', TIMESTAMP '2026-05-20 14:18:00', 3.40::NUMERIC(6, 2), 34340.00::NUMERIC(10, 2), 2),
            (4, 401, 5, TIMESTAMP '2026-05-19 11:30:00', TIMESTAMP '2026-05-19 11:52:00', 4.80::NUMERIC(6, 2), 47040.00::NUMERIC(10, 2), 4)
    ) AS rows(
        user_id,
        vehicle_id,
        station_rank,
        start_time,
        end_time,
        charged_amount,
        charging_cost,
        waiting_time
    )
)
INSERT INTO charging_log (
    user_id,
    vehicle_id,
    chrstn_mno,
    start_time,
    end_time,
    charged_amount,
    charging_cost,
    waiting_time
)
SELECT seed_logs.user_id,
       seed_logs.vehicle_id,
       station_refs.chrstn_mno,
       seed_logs.start_time,
       seed_logs.end_time,
       seed_logs.charged_amount,
       seed_logs.charging_cost,
       seed_logs.waiting_time
FROM seed_logs
JOIN station_refs
  ON station_refs.station_rank = seed_logs.station_rank;

DELETE FROM recommendation_history
WHERE user_id IN (1, 2, 3, 4)
  AND vehicle_id IN (101, 201, 301, 401);

WITH station_refs AS (
    SELECT chrstn_mno,
           ROW_NUMBER() OVER (
               ORDER BY
                   CASE
                       WHEN road_nm_addr LIKE '인천%' THEN 0
                       WHEN lotno_addr LIKE '인천%' THEN 0
                       ELSE 1
                   END,
                   chrstn_nm ASC,
                   chrstn_mno ASC
           ) AS station_rank
    FROM hydrogen_stations
),
seed_recommendations AS (
    SELECT *
    FROM (
        VALUES
            (1, 101, 1, 96.50::NUMERIC(5, 2), '대기 차량이 가장 적은 충전소입니다.', 37.3920000::NUMERIC(10, 7), 126.6510000::NUMERIC(10, 7), 32.50::NUMERIC(6, 2), 8, true, TIMESTAMP '2026-05-22 08:00:00', 'LOW_WAIT'),
            (1, 101, 2, 88.00::NUMERIC(5, 2), '영업중이며 접근성이 좋습니다.', 37.4605000::NUMERIC(10, 7), 126.4510000::NUMERIC(10, 7), 32.50::NUMERIC(6, 2), 18, false, NULL::TIMESTAMP, 'NEARBY'),
            (2, 201, 3, 72.00::NUMERIC(5, 2), '영업중이나 대기 차량이 많습니다.', 37.4050000::NUMERIC(10, 7), 126.7210000::NUMERIC(10, 7), 18.20::NUMERIC(6, 2), 12, false, NULL::TIMESTAMP, 'LOW_DISTANCE'),
            (3, 301, 4, 84.20::NUMERIC(5, 2), '비교 추천 데이터입니다.', 37.5705000::NUMERIC(10, 7), 126.8810000::NUMERIC(10, 7), 41.00::NUMERIC(6, 2), 15, true, TIMESTAMP '2026-05-20 13:50:00', 'NEARBY'),
            (4, 401, 5, 45.00::NUMERIC(5, 2), '운영상태에 따른 낮은 우선순위 추천입니다.', 37.3910000::NUMERIC(10, 7), 127.1120000::NUMERIC(10, 7), 12.00::NUMERIC(6, 2), 20, false, NULL::TIMESTAMP, 'STATUS_PENALTY')
    ) AS rows(
        user_id,
        vehicle_id,
        station_rank,
        recommendation_score,
        recommendation_reason,
        user_latitude,
        user_longitude,
        vehicle_remaining_hydrogen,
        estimated_arrival_time,
        selected,
        selected_at,
        recommendation_type
    )
)
INSERT INTO recommendation_history (
    user_id,
    vehicle_id,
    chrstn_mno,
    recommendation_score,
    recommendation_reason,
    user_latitude,
    user_longitude,
    vehicle_remaining_hydrogen,
    estimated_arrival_time,
    selected,
    selected_at,
    recommendation_type
)
SELECT seed_recommendations.user_id,
       seed_recommendations.vehicle_id,
       station_refs.chrstn_mno,
       seed_recommendations.recommendation_score,
       seed_recommendations.recommendation_reason,
       seed_recommendations.user_latitude,
       seed_recommendations.user_longitude,
       seed_recommendations.vehicle_remaining_hydrogen,
       seed_recommendations.estimated_arrival_time,
       seed_recommendations.selected,
       seed_recommendations.selected_at,
       seed_recommendations.recommendation_type
FROM seed_recommendations
JOIN station_refs
  ON station_refs.station_rank = seed_recommendations.station_rank;

COMMIT;
