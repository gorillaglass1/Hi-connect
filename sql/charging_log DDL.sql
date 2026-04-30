CREATE TABLE charging_log (

    charging_log_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    -- 충전 로그 고유 ID

    user_id BIGINT NOT NULL,
    -- 충전 사용자 ID

    hydrogen_station_id BIGINT NOT NULL,
    -- 충전소 ID

    vehicle_id BIGINT NOT NULL,
    -- 충전 차량 ID

    start_time DATETIME NOT NULL,
    -- 충전 시작 시간

    end_time DATETIME NOT NULL,
    -- 충전 종료 시간

    charged_amount DECIMAL(6,2),
    -- 충전된 수소량 (kg)

    charging_cost DECIMAL(10,2),
    -- 충전 비용 (원)

    waiting_time INT,
    -- 충전 대기시간 (분)

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    -- 로그 생성 시간

	CONSTRAINT fk_log_users FOREIGN KEY (user_id) REFERENCES users(user_id),
	CONSTRAINT fk_log_stations FOREIGN KEY (hydrogen_station_id) REFERENCES hydrogen_station(hydrogen_station_id),
	CONSTRAINT fk_log_vehicle FOREIGN KEY (vehicle_id) REFERENCES vehicles(vehicle_id)
);