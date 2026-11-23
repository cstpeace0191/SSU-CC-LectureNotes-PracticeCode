"""shop-api: Helm 실습용 최소 FastAPI 서비스.

- GET  /healthz      : liveness/readiness 프로브용
- GET  /version      : 배포된 이미지 버전(APP_VERSION) 확인 → 롤백 실습에 사용
- GET  /items        : 상품 목록 조회 (PostgreSQL)
- POST /items        : 상품 추가
"""
import os

import psycopg
from fastapi import FastAPI
from pydantic import BaseModel

DATABASE_URL = os.environ["DATABASE_URL"]
APP_VERSION = os.getenv("APP_VERSION", "dev")
GREETING = os.getenv("GREETING", "Hello from shop-api")

app = FastAPI(title="shop-api", version=APP_VERSION)


@app.get("/")
def root():
    return {
        "service": "shop-api",
        "version": APP_VERSION,
        "greeting": GREETING,
        "endpoints": {
            "items": "/items",
            "version": "/version",
            "healthz": "/healthz",
            "docs": "/docs",
        },
    }


class Item(BaseModel):
    name: str
    price: int


@app.get("/healthz")
def healthz():
    with psycopg.connect(DATABASE_URL, connect_timeout=2) as conn:
        conn.execute("SELECT 1")
    return {"status": "ok"}


@app.get("/version")
def version():
    return {"version": APP_VERSION, "greeting": GREETING}


@app.get("/items")
def list_items():
    with psycopg.connect(DATABASE_URL) as conn:
        rows = conn.execute("SELECT id, name, price FROM items ORDER BY id").fetchall()
    return [{"id": r[0], "name": r[1], "price": r[2]} for r in rows]


@app.post("/items", status_code=201)
def create_item(item: Item):
    with psycopg.connect(DATABASE_URL) as conn:
        row = conn.execute(
            "INSERT INTO items (name, price) VALUES (%s, %s) RETURNING id",
            (item.name, item.price),
        ).fetchone()
    return {"id": row[0], **item.model_dump()}
