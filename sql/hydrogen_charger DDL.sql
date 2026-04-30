-- 2. 수소 충전기 테이블
CREATE TABLE hydrogen_charger (
    hydrogen_charger_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    hydrogen_station_id BIGINT NOT NULL,
    charger_status ENUM('충분', '여유', '부족') NOT NULL,
    charger_type VARCHAR(50),
    hydrogen_pressure_bar INT,
    pressure_type ENUM('350bar', '700bar') NOT NULL,
    restock_schedule DATETIME,
    reservation_type BOOLEAN DEFAULT FALSE,
    CONSTRAINT fk_charger_station
        FOREIGN KEY (hydrogen_station_id)
        REFERENCES hydrogen_station(hydrogen_station_id)
        ON DELETE CASCADE
);