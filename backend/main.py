"""AI Psychologist — FastAPI Application (Mini App backend)"""
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from loguru import logger

from backend.config import settings
from backend.database import init_db

# Import routers
from backend.api.auth import router as auth_router
from backend.api.sessions import router as sessions_router
from backend.api.tasks import router as tasks_router
from backend.api.progress import router as progress_router
from backend.api.assessments import router as assessments_router
from backend.api.insights import router as insights_router

FRONTEND_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend", "dist")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown lifecycle."""
    logger.info("Starting AI Psychologist backend...")
    await init_db()
    logger.info(f"Database initialized. Port: {settings.backend_port}")
    yield
    logger.info("Shutting down AI Psychologist backend.")


app = FastAPI(
    title="AI Psychologist",
    description="Personal AI therapy assistant — Mini App backend",
    version="0.2.0",
    lifespan=lifespan,
)

# CORS — Telegram WebApp and local dev
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "").split(",") if os.getenv("CORS_ORIGINS") else [
    "http://localhost:3010",
    "http://localhost:5173",
    "http://127.0.0.1:3010",
    "https://web.telegram.org",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

# Mount API routers
app.include_router(auth_router)
app.include_router(sessions_router)
app.include_router(tasks_router)
app.include_router(progress_router)
app.include_router(assessments_router)
app.include_router(insights_router)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "ai-psychologist"}


# Serve Mini App frontend (built React app)
if os.path.exists(FRONTEND_DIR):
    app.mount("/assets", StaticFiles(directory=os.path.join(FRONTEND_DIR, "assets")), name="assets")

    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        """Serve React SPA — all non-API routes go to index.html."""
        file_path = os.path.join(FRONTEND_DIR, full_path)
        if os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=settings.backend_port,
        reload=True,
        log_level=settings.log_level.lower(),
    )
