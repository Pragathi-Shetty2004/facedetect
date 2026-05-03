"""Integration tests for API endpoints (mocked DB)."""

import io
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from PIL import Image

from app.main import app
from app.db.session import get_db
from app.db.models import Session as DBSession, ROI


def _blank_jpeg() -> bytes:
    img = Image.new("RGB", (320, 240), color=(80, 80, 80))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


def _mock_session(label=None) -> DBSession:
    s = MagicMock(spec=DBSession)
    s.id = uuid.uuid4()
    s.source_label = label
    s.total_frames = 0
    from datetime import datetime, timezone
    s.created_at = datetime.now(timezone.utc)
    s.ended_at = None
    return s


@pytest_asyncio.fixture
async def api_client() -> AsyncClient:
    """Client with a realistic DB mock."""
    mock_db = AsyncMock()
    mock_db.flush = AsyncMock()
    mock_db.commit = AsyncMock()
    mock_db.rollback = AsyncMock()
    mock_db.add = MagicMock()

    async def _db():
        yield mock_db

    app.dependency_overrides[get_db] = _db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_health(api_client):
    r = await api_client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_create_session(api_client):
    fake_session = _mock_session("webcam-1")

    with patch("app.api.ingest.create_session", new_callable=AsyncMock) as mock_create:
        mock_create.return_value = fake_session
        r = await api_client.post("/api/v1/ingest/session?source_label=webcam-1")

    assert r.status_code == 201
    body = r.json()
    assert "session_id" in body
    assert "created_at" in body


@pytest.mark.asyncio
async def test_ingest_frame_invalid_content_type(api_client):
    r = await api_client.post(
        f"/api/v1/ingest/frame/{uuid.uuid4()}",
        files={"frame": ("f.txt", b"hello", "text/plain")},
    )
    assert r.status_code == 415


@pytest.mark.asyncio
async def test_ingest_frame_empty_body(api_client):
    r = await api_client.post(
        f"/api/v1/ingest/frame/{uuid.uuid4()}",
        files={"frame": ("f.jpg", b"", "image/jpeg")},
    )
    assert r.status_code == 400


@pytest.mark.asyncio
async def test_ingest_frame_no_face(api_client):
    """Blank image → no face → still 200 with face_detected=False."""
    sid = uuid.uuid4()
    jpeg = _blank_jpeg()

    with patch("app.api.ingest.save_roi", new_callable=AsyncMock), \
         patch("app.api.ingest.increment_frame_count", new_callable=AsyncMock), \
         patch("app.services.broker.FrameBroker.publish", new_callable=AsyncMock):
        r = await api_client.post(
            f"/api/v1/ingest/frame/{sid}",
            files={"frame": ("frame.jpg", jpeg, "image/jpeg")},
        )

    assert r.status_code == 200
    body = r.json()
    assert body["face_detected"] is False
    assert body["roi"] is None


@pytest.mark.asyncio
async def test_get_rois_session_not_found(api_client):
    with patch("app.api.roi.get_session", new_callable=AsyncMock) as mock_gs:
        mock_gs.return_value = None
        r = await api_client.get(f"/api/v1/roi/{uuid.uuid4()}")
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_get_rois_empty(api_client):
    fake_session = _mock_session()
    with patch("app.api.roi.get_session", new_callable=AsyncMock, return_value=fake_session), \
         patch("app.api.roi.list_rois", new_callable=AsyncMock, return_value=[]), \
         patch("app.api.roi.count_rois", new_callable=AsyncMock, return_value=0):
        r = await api_client.get(f"/api/v1/roi/{fake_session.id}")
    assert r.status_code == 200
    body = r.json()
    assert body["total"] == 0
    assert body["items"] == []


@pytest.mark.asyncio
async def test_get_stats(api_client):
    fake_session = _mock_session()
    fake_session.total_frames = 100
    with patch("app.api.roi.get_session", new_callable=AsyncMock, return_value=fake_session), \
         patch("app.api.roi.count_rois", new_callable=AsyncMock, return_value=73):
        r = await api_client.get(f"/api/v1/roi/{fake_session.id}/stats")
    assert r.status_code == 200
    body = r.json()
    assert body["frames_with_face"] == 73
    assert abs(body["detection_rate"] - 0.73) < 0.01


@pytest.mark.asyncio
async def test_close_session(api_client):
    sid = uuid.uuid4()
    with patch("app.api.ingest.close_session", new_callable=AsyncMock):
        r = await api_client.delete(f"/api/v1/ingest/session/{sid}")
    assert r.status_code == 200
    assert r.json()["status"] == "closed"
