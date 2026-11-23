# 1. Base image (경량 Python 3.11 slim 이미지 사용)
FROM python:3.11-slim

# 2. 환경 변수 설정
# - PYTHONUNBUFFERED: 로그가 버퍼링 없이 즉시 출력되도록 설정
# - PYTHONDONTWRITEBYTECODE: .pyc 파일 생성을 방지하여 컨테이너 용량 최적화
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# 3. 작업 디렉터리 설정
WORKDIR /app

# 4. 의존성 파일 복사 및 설치 (Docker 캐싱 최적화)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. 소스 코드 복사
COPY . .

# 6. SQLite 기본 데이터 저장 경로 생성 (선택 사항)
RUN mkdir -p /etc/todos

# 7. 서비스 포트 오픈 (3000번 포트)
EXPOSE 3000

# 8. Uvicorn 서버 실행 명령어
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "3000"]
