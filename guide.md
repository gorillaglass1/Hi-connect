아래 내용을 그대로 복사해서 `.md` 파일로 사용하면 됩니다.

---

# 🚀 FastAPI Service Layer 바이브코딩 프롬프트

## 📌 목적

이 문서는 **FastAPI + SQLAlchemy Async 기반 프로젝트에서 서비스 계층을 AI로 효율적으로 생성하기 위한 프롬프트**입니다.
Pleos 기반 수소충전소 서비스 프로젝트에 맞춰 설계되었습니다.

---

## 🧠 기본 프롬프트

```text
너는 FastAPI + SQLAlchemy Async 기반 백엔드 프로젝트의 서비스 계층을 구현하는 시니어 백엔드 개발자다.

현재 프로젝트는 Pleos 수소충전소 추천/예약/피드백 서비스이며, 이미 API Router, Schema, Model, Repository 계층은 일부 구현되어 있다고 가정한다.

중요:
- AI API 호출, LLM 요청, 외부 생성형 AI 요청을 보내는 파일은 절대 만들지 마라.
- OpenAI, Gemini, Claude, LangChain 관련 코드는 작성하지 마라.
- 지금은 서비스 계층의 비즈니스 로직 구현에만 집중한다.
- Repository 계층을 직접 우회해서 DB에 접근하지 마라.
- API Router에는 비즈니스 로직을 넣지 말고 Service에서 처리하게 만들어라.
```

---

## 🏗️ 구현 목표 (Service 목록)

### 1. UserService

* 사용자 생성
* 사용자 단건 조회
* 사용자 목록 조회
* 이메일 중복 검증
* 존재하지 않는 사용자 예외 처리

---

### 2. VehicleService

* 차량 등록
* 사용자별 차량 목록 조회
* 차량 단건 조회
* 차량 정보 수정
* 차량 삭제
* 차량 소유자 검증

---

### 3. HydrogenStationService

* 수소충전소 목록 조회
* 수소충전소 단건 조회
* 현재 위치 기반 가까운 충전소 조회
* 운영 여부 / 잔여량 / 가격 필터링
* 존재하지 않는 충전소 예외 처리

---

### 4. ChargingLogService

* 충전 기록 생성
* 사용자별 충전 기록 조회
* 차량별 충전 기록 조회
* 시작/종료 시간 검증
* 충전량, 비용, 대기시간 검증

---

### 5. ReservationService

* 예약 생성
* 예약 조회
* 사용자별 예약 목록 조회
* 예약 취소
* 예약 완료 처리
* 중복 예약 시간 검증
* 예약 만료 시간 검증

---

### 6. FeedbackService

* 피드백 생성
* 충전소별 피드백 조회
* 사용자별 피드백 조회
* 피드백 상태 변경
* 피드백 타입 처리
  (허위정보, 운영 안함, 가격 오류, 대기시간 오류 등)

---

## ⚙️ 공통 구현 규칙

```text
- 모든 Service 클래스는 app/services/ 폴더에 생성
- 클래스명은 PascalCase 사용 (UserService 등)
- 생성자에서 AsyncSession 주입
- Repository를 통해서만 DB 접근
- 모든 DB 작업은 async/await 사용
- 입력값 검증은 Service에서 수행
- 예외는 HTTPException 사용
- 코드에는 초보자용 주석 포함
```

---

## 🚨 예외 처리 기준

| 상황     | 상태 코드 |
| ------ | ----- |
| 데이터 없음 | 404   |
| 잘못된 입력 | 400   |
| 중복 데이터 | 409   |
| 권한 문제  | 403   |

---

## 🧾 코드 스타일 규칙

* Python 3.11+
* 타입 힌트 필수
* Pydantic Schema 사용
* AsyncSession 사용
* 함수는 하나의 책임만
* 긴 함수는 분리
* 명확한 함수명 사용

---

## 📦 출력 형식

````text
각 파일별로 나눠서 출력

예시:

app/services/user_service.py
```python
...
````

app/services/vehicle_service.py

```python
...
```

````

---

## 📘 추가 설명 요구 (강력 추천)

```text
나는 FastAPI 서비스 계층을 처음 배우는 초보자다.
코드만 작성하지 말고,
- 각 메서드가 왜 필요한지
- Service / Repository / Router 연결 구조
도 함께 설명해줘.
````

---

## 🎯 AI가 추가로 정리해야 할 내용

1. 각 Service 클래스 역할
2. Router에서 Service 호출 예시
3. 필요한 Repository 메서드 목록
4. 내가 수정해야 할 가능성이 높은 부분

---

## 💡 사용 팁

* 한 번에 전체 생성 ❌
  → Service 하나씩 생성 요청 ✅

* 먼저 UserService → 나머지 순서 추천

* 생성 후 반드시 확인할 것:

  * DB commit 누락 여부
  * 예외 처리 누락
  * async/await 빠진 부분

---

## 🔥 한 줄 요약

> “Router는 얇게, Service는 똑똑하게, DB는 Repository로만”

---

필요하면 다음 단계로
👉 **“Repository 프롬프트” / “Router 프롬프트” / “전체 아키텍처 설계”**도 이어서 만들어줄게.
