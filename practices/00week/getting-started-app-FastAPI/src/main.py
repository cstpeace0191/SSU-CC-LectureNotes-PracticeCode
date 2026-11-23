import os
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from src.persistence import db
from src.routes.items import router as items_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize Database
    await db.init()
    yield
    # Shutdown: Teardown Database
    await db.teardown()


app = FastAPI(
    title="Getting Started Todo App (FastAPI)",
    lifespan=lifespan,
)

# Enable CORS for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Router
app.include_router(items_router)

# Serve Static Files (HTML/CSS/JS) - Express app.use(express.static(...)) 대체
static_dir = Path(__file__).resolve().parent / "static"
if static_dir.exists():
    app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="static")

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("src.main:app", host="0.0.0.0", port=3000, reload=True)
