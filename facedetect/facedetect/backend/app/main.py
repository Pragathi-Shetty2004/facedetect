"""
FaceDetect – Real-Time Face Detection Streaming API
Entry point for the FastAPI application.
"""

import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from app.api import ingest, stream, roi
from app.core.config import settings
from app.db.session import init_db

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s – %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialise resources on startup, clean up on shutdown."""
    logger.info("Starting FaceDetect API …")
    await init_db()
    yield
    logger.info("Shutting down FaceDetect API …")


app = FastAPI(
    title="FaceDetect API",
    description="Real-time face detection pipeline with ROI storage and WebSocket streaming.",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── Security middleware ────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ────────────────────────────────────────────────────────────────────
app.include_router(ingest.router, prefix="/api/v1", tags=["ingest"])
app.include_router(stream.router, prefix="/api/v1", tags=["stream"])
app.include_router(roi.router, prefix="/api/v1", tags=["roi"])


@app.get("/health", tags=["health"])
async def health() -> dict:
    return {"status": "ok", "version": "1.0.0"}
