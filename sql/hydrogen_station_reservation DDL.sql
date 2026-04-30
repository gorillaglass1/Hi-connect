CREATE TABLE hydrogen_station_reservation (
	hydrogen_station_reservation_id BIGINT PRIMARY KEY AUTO_INCREMENT,
    hydrogen_charger_id BIGINT NOT NULL, -- 충전기 foreign key
    hydrogen_station_id BIGINT NOT NULL, -- 충전소 foreign key
    reservation_status ENUM('RESERVED', 'CANCELLED', 'COMPLETED', 'EXPIRED') NOT NULL, -- 예약 상태
    user_id BIGINT NOT NULL, -- user foreign key
    reservation_time DATETIME NOT NULL, -- 예약 시작 시간
    expire_time DATETIME NOT NULL, -- 예약 종료 시간
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP, -- 예약 생성 시간

    CONSTRAINT fk_reservation_charger FOREIGN KEY (hydrogen_charger_id) REFERENCES hydrogen_charger(hydrogen_charger_id),
    CONSTRAINT fk_reservation_station FOREIGN KEY (hydrogen_station_id) REFERENCES hydrogen_station(hydrogen_station_id),
    CONSTRAINT fk_reservation_users FOREIGN KEY (user_id) REFERENCES users(user_id)
);