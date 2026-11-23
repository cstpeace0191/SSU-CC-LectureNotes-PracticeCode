FROM python:3.11-slim

# uv 바이너리 복사
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# 의존성 정의 파일 복사 및 패키지 동기화
COPY pyproject.toml .python-version ./
RUN uv sync

# 애플리케이션 소스 복사
COPY . .

# 환경변수 기본값 설정
ENV HOST=0.0.0.0
ENV PORT=8000
ENV PYTHONUNBUFFERED=1

EXPOSE 8000

# FastAPI 서버 실행
CMD ["uv", "run", "python", "gemini-chat-server.py"]
