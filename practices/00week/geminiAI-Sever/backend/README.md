# Gemini Chat Backend (FastAPI + uv)

Google Gemini AI(`gemini-3.7-flash`) 기반 실시간 날씨/시간 도구(Function Calling) 지원 대화형 FastAPI 서버입니다.

## 🚀 빠른 시작 (Quickstart with uv)

### 1. 패키지 설치 및 동기화
```bash
uv sync
```

### 2. 서버 실행
```bash
# 방법 1: uv run으로 실행
uv run gemini-chat-server.py

# 방법 2: uvicorn 직접 실행 (Hot-reload)
uv run uvicorn gemini-chat-server:app --host 127.0.0.1 --port 8000 --reload
```

### 3. API 문서 확인
서버 실행 후 브라우저에서 아래 주소로 접속:
- Swagger UI: `http://127.0.0.1:8000/docs`
- Health Check: `http://127.0.0.1:8000/health`
