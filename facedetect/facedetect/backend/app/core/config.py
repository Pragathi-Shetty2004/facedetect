"""Central configuration – reads from environment variables."""

from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # ── App ────────────────────────────────────────────────────────────────────
    APP_ENV: str = "development"
    SECRET_KEY: str = "change-me-in-production"

    # ── Database ───────────────────────────────────────────────────────────────
    DATABASE_URL: str = "postgresql+asyncpg://facedetect:facedetect@db:5432/facedetect"

    # ── CORS ───────────────────────────────────────────────────────────────────
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:80", "http://frontend:3000"]

    # ── Streaming ──────────────────────────────────────────────────────────────
    FRAME_JPEG_QUALITY: int = 80          # 1-95
    MAX_FRAME_WIDTH: int = 1280
    MAX_FRAME_HEIGHT: int = 720
    STREAM_FPS_CAP: int = 30

    # ── Face detection ─────────────────────────────────────────────────────────
    FACE_DETECTION_CONFIDENCE: float = 0.5
    ROI_BOX_COLOR: tuple = (0, 255, 0)    # RGB green
    ROI_BOX_THICKNESS: int = 3

    # ── Storage ────────────────────────────────────────────────────────────────
    MAX_ROI_RECORDS: int = 100_000        # soft cap, pruned by background task


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
