import os
import sys
import datetime
from typing import Optional
from zoneinfo import ZoneInfo
import requests
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
import uvicorn

from google import genai
from google.genai import types

import mimetypes

# Windows 환경에서 .js MIME 타입이 text/plain으로 잘못 인식되는 문제 방지
mimetypes.add_type("application/javascript", ".js")
mimetypes.add_type("application/javascript", ".mjs")
mimetypes.add_type("text/css", ".css")

# UTF-8 출력 보장 (Windows 콘솔 한글 깨짐 방지)
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# .env 환경 변수 로드
load_dotenv(override=True)
API_KEY = os.environ.get("GEMINI_API_KEY")

# google.genai 클라이언트 생성
client = genai.Client(vertexai=False, api_key=API_KEY)


# ─────────────────────────────────────────────
# 주요 한글 도시명 영문 매핑 사전
# ─────────────────────────────────────────────
CITY_MAP = {
    "서울": "Seoul", "부산": "Busan", "인천": "Incheon", "대구": "Daegu",
    "대전": "Daejeon", "광주": "Gwangju", "울산": "Ulsan", "수원": "Suwon",
    "제주": "Jeju", "성남": "Seongnam", "고양": "Goyang", "용인": "Yongin",
    "부천": "Bucheon", "안산": "Ansan", "청주": "Cheongju", "전주": "Jeonju",
    "천안": "Cheonan", "창원": "Changwon", "포항": "Pohang", "김해": "Gimhae",
    "파리": "Paris", "런던": "London", "도쿄": "Tokyo", "오사카": "Osaka",
    "교토": "Kyoto", "뉴욕": "New York", "로스앤젤레스": "Los Angeles",
    "샌프란시스코": "San Francisco", "시카고": "Chicago", "워싱턴": "Washington",
    "시애틀": "Seattle", "보스턴": "Boston", "토론토": "Toronto", "밴쿠버": "Vancouver",
    "베이징": "Beijing", "상하이": "Shanghai", "홍콩": "Hong Kong", "타이베이": "Taipei",
    "방콕": "Bangkok", "싱가포르": "Singapore", "하노이": "Hanoi", "호치민": "Ho Chi Minh City",
    "시드니": "Sydney", "멜버른": "Melbourne", "오클랜드": "Auckland",
    "로마": "Rome", "밀라노": "Milan", "베를린": "Berlin", "뮌헨": "Munich",
    "프랑크푸르트": "Frankfurt", "마드리드": "Madrid", "바르셀로나": "Barcelona",
    "암스테르담": "Amsterdam", "취리히": "Zurich", "제네바": "Geneva", "비엔나": "Vienna",
    "프라하": "Prague", "모스크바": "Moscow", "두바이": "Dubai", "카이로": "Cairo",
}


# ─────────────────────────────────────────────
# 도시명 → 위도/경도/타임존 조회 (Open-Meteo Geocoding, 무료·키 불필요)
# ─────────────────────────────────────────────
def _geocode(city: str):
    """도시명을 위도, 경도, 타임존으로 변환합니다."""
    clean_name = city.strip()
    search_name = CITY_MAP.get(clean_name, clean_name)

    url = "https://geocoding-api.open-meteo.com/v1/search"
    resp = requests.get(url, params={"name": search_name, "count": 1, "language": "en"}, timeout=5)
    results = resp.json().get("results")

    # 매핑 이름으로 검색 실패 시 원본 이름으로 재시도
    if not results and search_name != clean_name:
        resp = requests.get(url, params={"name": clean_name, "count": 1, "language": "en"}, timeout=5)
        results = resp.json().get("results")

    if not results:
        return None
    r = results[0]
    return r["latitude"], r["longitude"], r["timezone"]


# ─────────────────────────────────────────────
# Tool 1: 전 세계 날씨 조회 (Open-Meteo Weather API, 무료·키 불필요)
# ─────────────────────────────────────────────
def get_weather(city: str) -> dict:
    """Retrieves current weather, temperature, humidity, and condition for a city.
    도시의 현재 실시간 날씨, 기온, 습도, 풍속 정보를 조회합니다.

    Args:
        city: The name of the city in Korean or English (e.g. 서울, Seoul, 도쿄, Paris, New York).

    Returns:
        A dictionary containing weather status, temperature, humidity, and weather description.
    """
    geo = _geocode(city)
    if geo is None:
        return {"status": "error", "error_message": f"'{city}' 도시의 위치를 찾을 수 없습니다."}

    lat, lon, _ = geo
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": "temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m",
        "wind_speed_unit": "ms",
    }
    data = requests.get("https://api.open-meteo.com/v1/forecast", params=params, timeout=5).json()
    cur = data.get("current", {})

    wmo_desc = {
        0: "맑음", 1: "대체로 맑음", 2: "구름 조금", 3: "흐림",
        45: "안개", 48: "서리 안개",
        51: "가벼운 이슬비", 53: "보통 이슬비", 55: "강한 이슬비",
        61: "약한 비", 63: "보통 비", 65: "강한 비",
        71: "약한 눈", 73: "보통 눈", 75: "강한 눈",
        80: "약한 소나기", 81: "보통 소나기", 82: "강한 소나기",
        95: "뇌우", 96: "우박을 동반한 뇌우", 99: "강한 우박을 동반한 뇌우",
    }
    code = cur.get("weather_code", -1)
    condition = wmo_desc.get(code, "맑음/보통")
    temp = cur.get("temperature_2m", "N/A")
    humidity = cur.get("relative_humidity_2m", "N/A")
    wind = cur.get("wind_speed_10m", "N/A")

    return {
        "status": "success",
        "city": city,
        "날씨상태": condition,
        "현재기온_섭씨": f"{temp}°C",
        "습도": f"{humidity}%",
        "풍속": f"{wind} m/s",
        "요약": f"{city}의 현재 날씨는 {condition}이며, 기온은 {temp}°C, 습도는 {humidity}%, 풍속은 {wind} m/s 입니다."
    }


# ─────────────────────────────────────────────
# Tool 2: 전 세계 현재 시간 조회 (Geocoding API 타임존 활용)
# ─────────────────────────────────────────────
def get_current_time(city: str) -> dict:
    """Returns the current local time, date, and timezone for any city in the world.
    도시의 현재 현지 시각, 날짜, 타임존 정보를 조회합니다.

    Args:
        city: The name of the city in Korean or English (e.g. 서울, Seoul, 도쿄, Paris, London).

    Returns:
        A dictionary containing local time, date, and timezone report.
    """
    geo = _geocode(city)
    if geo is None:
        return {"status": "error", "error_message": f"'{city}' 도시의 위치를 찾을 수 없습니다."}

    _, _, tz_name = geo
    try:
        tz = ZoneInfo(tz_name)
    except Exception:
        return {"status": "error", "error_message": f"타임존 정보를 확인할 수 없습니다: {tz_name}"}

    now = datetime.datetime.now(tz)
    time_str = now.strftime("%Y년 %m월 %d일 %H시 %M분 %S초")

    return {
        "status": "success",
        "city": city,
        "타임존": tz_name,
        "현재시각": time_str,
        "요약": f"{city}(타임존: {tz_name})의 현재 현지 시각은 {time_str} 입니다."
    }


# ─────────────────────────────────────────────
# Chat 세션 설정 & 팩토리
# ─────────────────────────────────────────────
MODEL_ID = "gemini-3.7-flash"
system_instruction = (
    "당신은 친절하고 유능하며 정중한 AI 어시스턴트입니다.\n"
    "일반 지식, 과학적 설명, 일상 대화, 프로그래밍 질문에 답변할 수 있으며, "
    "전 세계 도시의 실시간 날씨와 현재 시각을 도구(Tools)를 활용하여 정확하게 제공합니다.\n\n"
    "★ 최우선 언어 규칙 (CRITICAL LANGUAGE MANDATE):\n"
    "1. 사용자가 질문한 언어와 동일한 언어로 반드시 답변해야 합니다.\n"
    "2. 사용자가 한국어로 질문하면, 최종 답변 전체를 반드시 100% 자연스럽고 정중한 한국어(~입니다, ~해요)로만 작성하세요. 절대로 영어나 다른 언어로 답변하지 마세요.\n"
    "3. 도구(날씨, 시간)가 호출되어 반환된 결과가 있더라도, 이를 종합하여 최종 사용자에게 친절한 한국어 문장으로 설명하세요.\n"
    "4. 사용자가 영어로 질문하면 영어로, 일본어로 질문하면 일본어로 답변하세요.\n\n"
    "도구 사용 가이드:\n"
    "- 특정 도시의 현재 날씨나 기온을 물어보면 `get_weather` 도구를 호출하세요.\n"
    "- 특정 도시의 현재 시각이나 날짜, 타임존을 물어보면 `get_current_time` 도구를 호출하세요.\n"
    "- 일반 상식, 과학 질문(예: '하늘이 파란 이유'), 대화 질문은 도구 호출 없이 바로 답변하세요."
)

config = types.GenerateContentConfig(
    system_instruction=system_instruction,
    tools=[get_weather, get_current_time],
    temperature=0.7,
)

# 세션별 대화 관리 딕셔너리
sessions = {}

def get_or_create_chat(session_id: str):
    if session_id not in sessions:
        sessions[session_id] = client.chats.create(model=MODEL_ID, config=config)
    return sessions[session_id]


# ─────────────────────────────────────────────
# FastAPI 앱 및 스키마 정의
# ─────────────────────────────────────────────
app = FastAPI(
    title="Gemini Chat Server",
    description="google.genai 기반의 실시간 날씨/시간 도구 및 대화 지원 FastAPI 서버",
    version="1.0.0",
)

# CORS 설정 (웹 브라우저에서의 요청 허용)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = "default"


class ChatResponse(BaseModel):
    response: str
    session_id: str


class ResetRequest(BaseModel):
    session_id: Optional[str] = "default"


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
def chat_endpoint(request: ChatRequest):
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="메시지가 비어 있습니다.")

    try:
        chat = get_or_create_chat(request.session_id)
        response = chat.send_message(request.message)
        answer = response.text.strip() if response.text else "(응답 없음)"
        return ChatResponse(response=answer, session_id=request.session_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"요청 처리 중 오류 발생: {str(e)}")


@app.post("/reset")
def reset_session(request: ResetRequest):
    if request.session_id in sessions:
        del sessions[request.session_id]
        return {"status": "success", "message": f"세션 '{request.session_id}'이 초기화되었습니다."}
    return {"status": "not_found", "message": f"세션 '{request.session_id}'이 존재하지 않습니다."}


# ─────────────────────────────────────────────
# 프론트엔드 정적 파일 @app.get 라우트 핸들러
# ─────────────────────────────────────────────
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
FRONTEND_DIST_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend", "dist"))

def _get_static_base_dir() -> Optional[str]:
    if os.path.exists(STATIC_DIR):
        return STATIC_DIR
    elif os.path.exists(FRONTEND_DIST_DIR):
        return FRONTEND_DIST_DIR
    return None


@app.get("/", summary="프론트엔드 메인 페이지 (index.html)")
def serve_root():
    """루트 경로 접속 시 static 폴더의 index.html을 반환합니다."""
    base_dir = _get_static_base_dir()
    if base_dir:
        index_path = os.path.join(base_dir, "index.html")
        if os.path.isfile(index_path):
            return FileResponse(index_path, media_type="text/html")

    return {
        "status": "online",
        "service": "Gemini Chat Server (google.genai)",
        "model": MODEL_ID,
        "available_endpoints": ["/chat", "/reset", "/health", "/docs"]
    }


@app.get("/{full_path:path}", summary="정적 에셋 서빙 (JS, CSS, 이미지 등)")
def serve_static_file(full_path: str):
    """static 폴더의 JS, CSS, 이미지 등 정적 파일을 탐색하여 반환합니다."""
    # API 전용 경로는 404 처리하여 라우팅 충돌 방지
    if full_path.startswith(("docs", "redoc", "openapi.json", "chat", "reset", "health")):
        raise HTTPException(status_code=404, detail="Not Found")

    base_dir = _get_static_base_dir()
    if base_dir:
        file_path = os.path.join(base_dir, full_path)
        if os.path.isfile(file_path):
            mime_type, _ = mimetypes.guess_type(file_path)
            return FileResponse(file_path, media_type=mime_type or "application/octet-stream")

        # SPA 라우팅을 위한 index.html 폴백
        index_path = os.path.join(base_dir, "index.html")
        if os.path.isfile(index_path):
            return FileResponse(index_path, media_type="text/html")

    raise HTTPException(status_code=404, detail="Static file not found")



# ─────────────────────────────────────────────
# Uvicorn 서버 실행
# ─────────────────────────────────────────────
if __name__ == "__main__":
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", 8000))
    print("=" * 60)
    print(f"  🚀 Gemini Chat Server 시작 중... (FastAPI + Uvicorn) on {host}:{port}")
    print(f"  API 문서: http://{host}:{port}/docs")
    print("=" * 60)
    uvicorn.run(app, host=host, port=port)
