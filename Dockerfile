# 1. 파이썬 기본 환경 준비
FROM python:3.10-slim

# 2. 도커 박스 내부의 작업 공간 설정
WORKDIR /workspace

# 3. 라이브러리 목록을 복사하고 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. 프로젝트의 모든 소스코드를 도커 박스 안으로 복사
COPY . .

# 5. 구글 클라우드(Cloud Run)에 도착했을 때 서버를 켜는 최종 명령어
# 로컬에서는 8000 포트를 썼지만, GCP 배포를 위해 8080 포트로 설정합니다.
CMD ["uvicorn", "index:app", "--host", "0.0.0.0", "--port", "8080"]