CREATE TABLE hydrogen_station_realtime (

    realtime_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    -- 실시간 상태 고유 ID

    hydrogen_station_id BIGINT NOT NULL,
    -- 충전소 ID (station 테이블 FK)

    available_chargers INT DEFAULT 0,
    -- 현재 사용 가능한 충전기 수

    in_use_chargers INT DEFAULT 0,
    -- 현재 사용 중인 충전기 수

    queue_count INT DEFAULT 0,
    -- 현재 대기 차량 수

    avg_wait_time INT,
    -- 평균 예상 대기시간 (분)

    hydrogen_stock_kg DECIMAL(8,2),
    -- 충전소 내 남은 수소 총량 (kg)

    station_status VARCHAR(50),
    -- 충전소 상태 (운영중 / 점검중 / 재고부족 / 혼잡 등)

    last_restock_at DATETIME,
    -- 마지막 수소 보충 시각

    next_restock_schedule DATETIME,
    -- 다음 수소 보충 예정 시각

    utilization_rate DECIMAL(5,2),
    -- 충전소 사용률 (%)

    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP,
    -- 실시간 데이터 갱신 시각

	CONSTRAINT fk_realtime_station FOREIGN KEY (hydrogen_station_id) REFERENCES hydrogen_station(hydrogen_station_id)

);