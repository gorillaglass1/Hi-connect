# 📘 Hy-connect 팀 개발 가이드 (FastAPI + ORM)

이 문서는 **수소 충전소 시스템 백엔드**의 구조와 개발 규칙을 설명합니다. 팀원들은 아래 절차에 따라 로컬 환경을 구축하고 개발에 참여해 주세요.

---

## ⚙️ 1. 환경 설정 및 라이브러리 설치

우리 프로젝트는 의존성 충돌을 방지하기 위해 가상환경 사용을 원칙으로 합니다.

### 1) 가상환경 생성 및 활성화
```bash
# 리포지토리 클론 후 이동
git clone https://github.com/gorillaglass1/Hi-connect.git
cd Hi-connect

# 가상환경 생성 (Python 3.10 이상 권장) -- Pycharm 사용시 자동 생성할 수 있음
python -m venv .venv

# 가상환경 활성화
# Windows:
.venv\Scripts\activate
# Mac/Linux:
source .venv/bin/activate
```

### 2) 필수 라이브러리 설치
가장 핵심이 되는 라이브러리들입니다.
```bash
# 한 번에 설치하기
pip install fastapi[all] sqlalchemy aiosqlite pytest pytest-asyncio httpx email-validator greenlet
```

**핵심 라이브러리 용도:**
* **fastapi[all]**: 웹 프레임워크 및 데이터 검증(Pydantic), 서버(Uvicorn) 포함
* **sqlalchemy**: 비동기 지원 ORM
* **aiosqlite**: SQLite를 비동기로 제어하기 위한 드라이버
* **pytest & pytest-asyncio**: 비동기 API 테스트용
* **email-validator**: Pydantic에서 이메일 형식 검증 시 필요

---

## 🏛 2. 시스템 아키텍처 및 데이터 흐름

우리 백엔드는 4단계 계층 구조를 따릅니다. 요청은 항상 위에서 아래로 흐르며, 각 레이어는 바로 아래 레이어에만 의존합니다.



* **Router (Gateway)**: 클라이언트의 요청을 받는 창구 (`app/api/`)
* **Service (Business Logic)**: 핵심 비즈니스 규칙 및 권한 검증 (`app/services/`)
* **Repository (Data Access)**: DB 직접 접근 및 SQL 쿼리 담당 (`app/repositories/`)
* **Model/Entity (Data Definition)**: DB 테이블 설계도 (`app/models/`)

---

## 🗂 3. 프로젝트 디렉토리 구조

```plaintext
project_root/
├── app/
│   ├── api/             # [Router] 엔드포인트 정의 (HTTP 요청 처리)
│   ├── core/            # [Core] DB 연결 설정 및 공통 설정 (database.py)
│   ├── models/          # [Model] SQLAlchemy ORM 테이블 정의 (Entity)
│   ├── repositories/    # [Repository] DB 직접 쿼리 로직 (SQL 중심)
│   ├── schemas/         # [Schema] Pydantic 모델 (JSON 검증 및 직렬화)
│   └── services/        # [Service] 비즈니스 로직 (API의 핵심 로직)
├── tests/               # [Test] Pytest 기반 API 통합 테스트
├── index.py             # 앱 실행 진입점 (Lifespan으로 DB 자동 생성)
└── .pytest.ini          # 테스트 경로 설정 파일
```

---

## 🛠 4. 개발 워크플로우 (신규 기능 추가 시)

새로운 기능을 추가할 때는 `Model -> Schema -> Repository -> Service -> Router` 순으로 작업하는 것이 가장 효율적입니다.

1.  **Model**: `app/models/`에 테이블 정의 (ID는 `Integer` 권장)
2.  **Schema**: `app/schemas/`에 요청(`Create`) 및 응답(`Response`) 규격 정의
3.  **Repository**: `app/repositories/`에 `db.add()`, `select()` 등 순수 쿼리 함수 작성
4.  **Service**: `app/services/`에서 중복 체크 등 비즈니스 로직 적용 및 예외(409, 404 등) 발생 처리
5.  **Router**: `app/api/`에서 최종 엔드포인트 개방

---

## 🧪 5. 테스트 및 실행

코드 수정 후에는 아래 명령어로 안정성을 확인합니다.

* **서버 실행**: `uvicorn index:app --reload`
  * 더미 DML 자동 주입이 필요하면 실행 전에 `ENABLE_STARTUP_DUMMY_DATA=true` 설정
* **테스트 실행**: `pytest -q`
* **API 문서 확인**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

---

## ⚠️ 팀원 주의사항
* **DB 세션**: 반드시 `Depends(get_db)`를 통해 주입받은 `AsyncSession`을 사용하세요.
* **테스트 DB**: 테스트 실행 시 `test_user_api.db`가 자동으로 생성 및 삭제됩니다. 실제 개발 DB와 혼동하지 않도록 주의하세요.
* **Import 주의**: `index.py`에서 `Base.metadata.create_all`이 동작하려면 새로운 모델 추가 시 반드시 `index.py` 상단에서 해당 모델을 import해줘야 합니다.

---
