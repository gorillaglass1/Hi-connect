-- Vehicles 데이터 삽입 (user_id가 1부터 순차적으로 생성되었다고 가정)
INSERT INTO vehicles (user_id, vehicle_number, model, vehicle_type, fuel_type, tank_capacity, avg_efficiency) VALUES
(1, '12가 3456', '넥쏘(NEXO)', 'SUV', 'hydrogen', 6.33, 96.20),
(2, '57나 8901', '미라이(Mirai)', 'Sedan', 'hydrogen', 5.60, 128.00),
(3, '24다 1357', '엑시언트 FCEV', 'Truck', 'hydrogen', 31.00, 14.50),
(4, '88라 2468', '일렉시티 수소', 'Bus', 'hydrogen', 33.90, 18.00),
(5, '01마 1111', '비전 FK', 'Sports', 'hydrogen', 4.00, 85.00);