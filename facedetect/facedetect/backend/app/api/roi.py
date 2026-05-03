"""
Endpoint 3 – ROI Data

GET /api/v1/roi/{session_id}         → paginated list of ROI records
GET /api/v1/roi/{session_id}/latest  → most recent ROI for a session
GET /api/v1/roi/{session_id}/stats   → aggregate statistics
"""

from __future__ import annotations

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.repository import (
    count_rois,
    get_latest_roi,
    get_session,
    list_rois,
)
from app.db.session import get_db

router = APIRouter()


@router.get("/roi/{session_id}", summary="Paginated ROI records for a session")
async def get_rois(
    session_id: uuid.UUID,
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
) -> dict:
    session = await get_session(db, session_id)
    if session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found.")

    rois = await list_rois(db, session_id, limit=limit, offset=offset)
    total = await count_rois(db, session_id)

    return {
        "session_id": str(session_id),
        "total": total,
        "limit": limit,
        "offset": offset,
        "items": [r.to_dict for r in rois],
    }


@router.get("/roi/{session_id}/latest", summary="Most recent ROI for a session")
async def get_latest(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> dict:
    session = await get_session(db, session_id)
    if session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found.")

    roi = await get_latest_roi(db, session_id)
    if roi is None:
        return {"session_id": str(session_id), "roi": None}

    return {"session_id": str(session_id), "roi": roi.to_dict}


@router.get("/roi/{session_id}/stats", summary="ROI statistics for a session")
async def get_stats(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> dict:
    session = await get_session(db, session_id)
    if session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found.")

    total_faces = await count_rois(db, session_id)
    detection_rate: Optional[float] = None
    if session.total_frames and session.total_frames > 0:
        detection_rate = round(total_faces / session.total_frames, 4)

    return {
        "session_id": str(session_id),
        "total_frames": session.total_frames,
        "frames_with_face": total_faces,
        "detection_rate": detection_rate,
        "source_label": session.source_label,
        "created_at": session.created_at.isoformat(),
        "ended_at": session.ended_at.isoformat() if session.ended_at else None,
    }
