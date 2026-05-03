"""
Endpoint 1 – Video Feed Ingest

POST /api/v1/ingest/session          → create a session, get session_id
POST /api/v1/ingest/frame/{session_id} → push a single JPEG frame
DELETE /api/v1/ingest/session/{session_id} → close session
"""

from __future__ import annotations

import logging
import uuid
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.repository import (
    close_session,
    create_session,
    get_session,
    increment_frame_count,
    save_roi,
)
from app.db.session import get_db
from app.services.broker import frame_broker
from app.services.detector import annotate_frame

logger = logging.getLogger(__name__)
router = APIRouter()

# Rough per-session frame counter (avoids DB read on every frame)
_frame_counters: dict[str, int] = {}

ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_FRAME_BYTES = 10 * 1024 * 1024  # 10 MB


# ── Create session ─────────────────────────────────────────────────────────────

@router.post("/ingest/session", status_code=status.HTTP_201_CREATED)
async def create_ingest_session(
    source_label: Optional[str] = Query(None, max_length=255),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Create a new ingest session and return the session_id."""
    session = await create_session(db, source_label=source_label)
    _frame_counters[str(session.id)] = 0
    logger.info("Created session %s (label=%s)", session.id, source_label)
    return {"session_id": str(session.id), "created_at": session.created_at.isoformat()}


# ── Push frame ─────────────────────────────────────────────────────────────────

@router.post("/ingest/frame/{session_id}", status_code=status.HTTP_200_OK)
async def ingest_frame(
    session_id: uuid.UUID,
    frame: Annotated[UploadFile, File(description="Raw JPEG/PNG/WebP frame")],
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Accept a single frame, run face detection, annotate, publish to broker,
    and persist ROI data if a face is detected.
    """
    sid = str(session_id)

    # Validate content type
    ct = (frame.content_type or "").lower()
    if ct not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported media type '{ct}'. Send image/jpeg, image/png, or image/webp.",
        )

    raw = await frame.read()
    if len(raw) > MAX_FRAME_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Frame exceeds 10 MB limit.",
        )
    if len(raw) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Empty frame body.",
        )

    # Increment frame counter
    frame_idx = _frame_counters.get(sid, 0)
    _frame_counters[sid] = frame_idx + 1

    # Run detection + annotation (CPU-bound but kept synchronous for simplicity;
    # can be moved to a thread pool executor for high throughput)
    annotated_bytes, box, fw, fh = annotate_frame(raw)

    # Publish annotated frame to WebSocket subscribers
    await frame_broker.publish(sid, annotated_bytes)

    # Persist ROI if face found
    roi_data: dict | None = None
    if box is not None:
        roi = await save_roi(
            db,
            session_id=session_id,
            frame_index=frame_idx,
            x=box.x,
            y=box.y,
            width=box.width,
            height=box.height,
            confidence=box.confidence,
            frame_width=fw,
            frame_height=fh,
        )
        await increment_frame_count(db, session_id)
        roi_data = roi.to_dict

    return {
        "session_id": sid,
        "frame_index": frame_idx,
        "face_detected": box is not None,
        "roi": roi_data,
        "frame_width": fw,
        "frame_height": fh,
    }


# ── Close session ──────────────────────────────────────────────────────────────

@router.delete("/ingest/session/{session_id}", status_code=status.HTTP_200_OK)
async def end_ingest_session(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Mark a session as ended."""
    sid = str(session_id)
    await close_session(db, session_id)
    _frame_counters.pop(sid, None)
    logger.info("Closed session %s", session_id)
    return {"session_id": sid, "status": "closed"}
