-- 1. 수소 충전소 테이블
CREATE TABLE hydrogen_station (
    hydrogen_station_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    address VARCHAR(255) NOT NULL,
    latitude DECIMAL(10,7) NOT NULL,
    longitude DECIMAL(10,7) NOT NULL,
    contact_number VARCHAR(30),
    start_hour TIME,
    end_hour TIME,
    total_chargers INT DEFAULT 0,
    payment_supported VARCHAR(50)
);