CREATE TABLE recommendation_history (

    recommendation_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    -- 추천 기록 고유 ID

    user_id BIGINT NOT NULL,
    -- 추천을 받은 사용자 ID

    vehicle_id BIGINT NOT NULL,
    -- 추천 당시 사용된 차량 ID

    hydrogen_station_id BIGINT NOT NULL,
    -- 추천된 충전소 ID

    recommendation_score DECIMAL(5,2),
    -- 추천 점수 (AI 추천 점수 / 우선순위)

    recommendation_reason VARCHAR(255),
    -- 추천 이유 (예: 거리 우선, 대기시간 짧음, 잔여 수소 충분)

    user_latitude DECIMAL(10,7),
    -- 추천 시점 사용자 위도

    user_longitude DECIMAL(10,7),
    -- 추천 시점 사용자 경도

    vehicle_remaining_hydrogen DECIMAL(6,2),
    -- 추천 시점 차량 수소 잔량 (kg)

    estimated_arrival_time INT,
    -- 충전소까지 예상 이동 시간 (분)

    estimated_wait_time INT,
    -- 추천 당시 예상 대기시간 (분)

    selected BOOLEAN DEFAULT FALSE,
    -- 사용자가 실제 해당 충전소를 선택했는지 여부

    selected_at DATETIME,
    -- 실제 선택 시간

    recommendation_type VARCHAR(50),
    -- 추천 방식 (AI / 거리기반 / 혼잡도 기반 등)

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    -- 추천 생성 시각

		CONSTRAINT fk_history_users FOREIGN KEY (user_id) REFERENCES users(user_id),
		CONSTRAINT fk_history_vehicle FOREIGN KEY (vehicle_id) REFERENCES vehicles(vehicle_id),
		CONSTRAINT fk_history_station FOREIGN KEY (hydrogen_station_id) REFERENCES hydrogen_station(hydrogen_station_id)

);