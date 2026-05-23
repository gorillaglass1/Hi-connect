-- Supabase/PostgreSQL seed data for users, charging logs, and recommendation history.
-- Prerequisite: run sql/hydrogen_station_seed.sql first, or make sure the
-- referenced chrstn_mno values already exist in hydrogen_stations.

BEGIN;

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

ALTER TABLE charging_log DROP COLUMN IF EXISTS vehicle_id;
ALTER TABLE recommendation_history DROP COLUMN IF EXISTS vehicle_id;

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
ON CONFLICT (email) DO UPDATE SET
    name = EXCLUDED.name,
    phone = EXCLUDED.phone;

SELECT setval(
    pg_get_serial_sequence('users', 'user_id'),
    GREATEST((SELECT COALESCE(MAX(user_id), 1) FROM users), 1),
    true
);

DELETE FROM charging_log
WHERE user_id IN (1, 2, 3, 4)
  AND chrstn_mno IN (
      'DUMMY-ICN-001',
      'DUMMY-ICN-002',
      'DUMMY-ICN-003',
      'DUMMY-SEOUL-001',
      'DUMMY-GYEONGGI-001'
  );

INSERT INTO charging_log (
    user_id,
    chrstn_mno,
    start_time,
    end_time,
    charged_amount,
    charging_cost,
    waiting_time
) VALUES
(1, 'DUMMY-ICN-002', '2026-05-22 08:10:00', '2026-05-22 08:24:00', 3.80, 36860.00, 0),
(1, 'DUMMY-ICN-001', '2026-05-21 18:20:00', '2026-05-21 18:39:00', 4.10, 40590.00, 3),
(2, 'DUMMY-ICN-003', '2026-05-21 09:05:00', '2026-05-21 09:31:00', 5.20, 49920.00, 8),
(3, 'DUMMY-SEOUL-001', '2026-05-20 14:00:00', '2026-05-20 14:18:00', 3.40, 34340.00, 2),
(4, 'DUMMY-GYEONGGI-001', '2026-05-19 11:30:00', '2026-05-19 11:52:00', 4.80, 47040.00, 4);

DELETE FROM recommendation_history
WHERE user_id IN (1, 2, 3, 4)
  AND chrstn_mno IN (
      'DUMMY-ICN-001',
      'DUMMY-ICN-002',
      'DUMMY-ICN-003',
      'DUMMY-SEOUL-001',
      'DUMMY-GYEONGGI-001'
  );

INSERT INTO recommendation_history (
    user_id,
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
) VALUES
(1, 'DUMMY-ICN-002', 96.50, '인천 주소지 중 대기 차량이 가장 적고 영업중입니다.', 37.3920000, 126.6510000, 32.50, 8, true, '2026-05-22 08:00:00', 'LOW_WAIT'),
(1, 'DUMMY-ICN-001', 88.00, '영업중이며 공항 접근성이 좋습니다.', 37.4605000, 126.4510000, 32.50, 18, false, NULL, 'NEARBY'),
(2, 'DUMMY-ICN-003', 72.00, '영업중이나 대기 차량이 많습니다.', 37.4050000, 126.7210000, 18.20, 12, false, NULL, 'LOW_DISTANCE'),
(3, 'DUMMY-SEOUL-001', 84.20, '서울 지역 비교 추천 데이터입니다.', 37.5705000, 126.8810000, 41.00, 15, true, '2026-05-20 13:50:00', 'NEARBY'),
(4, 'DUMMY-GYEONGGI-001', 45.00, '점검중 상태라 추천 우선순위가 낮습니다.', 37.3910000, 127.1120000, 12.00, 20, false, NULL, 'STATUS_PENALTY');

COMMIT;
