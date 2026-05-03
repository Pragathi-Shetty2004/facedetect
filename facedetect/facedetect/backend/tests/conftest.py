"""Pytest fixtures for FaceDetect API tests."""

import io
import uuid
from typing import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.db.session import get_db


# ── Minimal JPEG fixture ───────────────────────────────────────────────────────

def make_blank_jpeg(width: int = 320, height: int = 240) -> bytes:
    """Create a small blank JPEG in memory (no file I/O)."""
    from PIL import Image
    img = Image.new("RGB", (width, height), color=(128, 128, 128))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


@pytest.fixture
def blank_jpeg() -> bytes:
    return make_blank_jpeg()


# ── Mock DB session ────────────────────────────────────────────────────────────

@pytest.fixture
def mock_db():
    """Return a mock async DB session that no-ops all operations."""
    db = AsyncMock()
    db.flush = AsyncMock()
    db.commit = AsyncMock()
    db.rollback = AsyncMock()
    db.execute = AsyncMock()
    db.add = MagicMock()
    return db


# ── HTTP test client ───────────────────────────────────────────────────────────

@pytest_asyncio.fixture
async def client(mock_db) -> AsyncGenerator[AsyncClient, None]:
    """AsyncClient with DB dependency overridden."""
    async def _override_db():
        yield mock_db

    app.dependency_overrides[get_db] = _override_db

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c

    app.dependency_overrides.clear()
