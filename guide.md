# Postman Test Data

## Base URL
`http://127.0.0.1:8000`

## 1) User Signup
- Method: `POST`
- URL: `/user/signup`
- Body (JSON):
```json
{
  "name": "Postman User",
  "phone": "010-1234-5678",
  "email": "postman-user@example.com"
}
```
- Save: `user_id`

## 2) Create Hydrogen Station
- Method: `POST`
- URL: `/hydrogen-stations`
- Body (JSON):
```json
{
  "name": "Postman Station",
  "address": "Seoul Gangnam-gu",
  "latitude": 37.4979,
  "longitude": 127.0276,
  "contact_number": "02-123-4567",
  "start_time": "08:00:00",
  "end_time": "22:00:00",
  "total_chargers": 4,
  "payment_supported": "CARD"
}
```
- Save: `hydrogen_station_id`

## 3) Create Vehicle
- Method: `POST`
- URL: `/vehicles`
- Body (JSON):
```json
{
  "user_id": 1,
  "vehicle_number": "12가3456",
  "model": "NEXO",
  "vehicle_type": "SUV",
  "fuel_type": "hydrogen",
  "tank_capacity": 6.33,
  "avg_efficiency": 95.5
}
```
- Replace `user_id` with value from step 1 if needed.
- Save: `vehicle_id`

## 4) Create Hydrogen Charger
- Method: `POST`
- URL: `/hydrogen-chargers`
- Body (JSON):
```json
{
  "hydrogen_station_id": 1,
  "charger_status": "충분",
  "charger_type": "FAST",
  "hydrogen_pressure_bar": 700,
  "pressure_type": "700bar",
  "restock_schedule": "2026-05-04T15:00:00"
}
```
- Replace `hydrogen_station_id` with value from step 2.
- Save: `hydrogen_charger_id`

## 5) Upsert Station Realtime
- Method: `POST`
- URL: `/hydrogen-station-realtime`
- Body (JSON):
```json
{
  "hydrogen_station_id": 1,
  "available_chargers": 2,
  "in_use_chargers": 1,
  "queue_count": 3,
  "avg_wait_time": 12,
  "hydrogen_stock_kg": 145.5,
  "station_status": "운영중",
  "last_restock_at": "2026-05-04T10:00:00",
  "next_restock_schedule": "2026-05-04T18:00:00",
  "utilization_rate": 75.5
}
```
- Replace `hydrogen_station_id` with value from step 2.

## 6) Create Charging Log
- Method: `POST`
- URL: `/charging-logs`
- Body (JSON):
```json
{
  "user_id": 1,
  "hydrogen_station_id": 1,
  "vehicle_id": 1,
  "start_time": "2026-05-04T10:00:00",
  "end_time": "2026-05-04T10:25:00",
  "charged_amount": 3.25,
  "charging_cost": 22000,
  "waiting_time": 5
}
```
- Replace `user_id`, `hydrogen_station_id`, `vehicle_id` with saved values.
- Save: `charging_log_id`

## 7) Create Reservation
- Method: `POST`
- URL: `/hydrogen-station-reservations`
- Body (JSON):
```json
{
  "hydrogen_charger_id": 1,
  "hydrogen_station_id": 1,
  "reservation_status": "RESERVED",
  "user_id": 1,
  "reservation_time": "2026-05-04T11:00:00",
  "expire_time": "2026-05-04T11:30:00"
}
```
- Replace `hydrogen_charger_id`, `hydrogen_station_id`, `user_id` with saved values.
- Save: `hydrogen_station_reservation_id`

## 8) Create Recommendation History
- Method: `POST`
- URL: `/recommendation-histories`
- Body (JSON):
```json
{
  "user_id": 1,
  "vehicle_id": 1,
  "hydrogen_station_id": 1,
  "recommendation_score": 92.8,
  "recommendation_reason": "가장 가까운 충전소",
  "user_latitude": 37.5001,
  "user_longitude": 127.0360,
  "vehicle_remaining_hydrogen": 1.8,
  "estimated_arrival_time": 9,
  "selected": true,
  "selected_at": "2026-05-04T10:55:00",
  "recommendation_type": "distance"
}
```
- Replace `user_id`, `vehicle_id`, `hydrogen_station_id` with saved values.

## 9) GET Test Queries

### Vehicles
- `GET /vehicles`
- `GET /vehicles/{vehicle_id}`

### Stations
- `GET /hydrogen-stations`
- `GET /hydrogen-stations/{hydrogen_station_id}`

### Chargers
- `GET /hydrogen-chargers?hydrogen_station_id=1`

### Realtime
- `GET /hydrogen-station-realtime?hydrogen_station_id=1`

### Charging Logs
- `GET /charging-logs?user_id=1`

### Reservations
- `GET /hydrogen-station-reservations?user_id=1`

### Recommendation Histories
- `GET /recommendation-histories?user_id=1`
