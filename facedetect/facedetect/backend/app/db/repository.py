"""Database repository for ROI and Session records."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import select, update, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import ROI, Session


# ── Session ───────────────────────────────────────────────────────────────────

async def create_session(db: AsyncSession, source_label: Optional[str] = None) -> Session:
    session = Session(source_label=source_label)
    db.add(session)
    await db.flush()
    return session


async def close_session(db: AsyncSession, session_id: uuid.UUID) -> None:
    await db.execute(
        update(Session)
        .where(Session.id == session_id)
        .values(ended_at=datetime.now(timezone.utc))
    )


async def increment_frame_count(db: AsyncSession, session_id: uuid.UUID, delta: int = 1) -> None:
    await db.execute(
        update(Session)
        .where(Session.id == session_id)
        .values(total_frames=Session.total_frames + delta)
    )


async def get_session(db: AsyncSession, session_id: uuid.UUID) -> Optional[Session]:
    result = await db.execute(select(Session).where(Session.id == session_id))
    return result.scalar_one_or_none()


# ── ROI ───────────────────────────────────────────────────────────────────────

async def save_roi(
    db: AsyncSession,
    *,
    session_id: uuid.UUID,
    frame_index: int,
    x: int,
    y: int,
    width: int,
    height: int,
    confidence: Optional[float],
    frame_width: int,
    frame_height: int,
) -> ROI:
    roi = ROI(
        session_id=session_id,
        frame_index=frame_index,
        x=x,
        y=y,
        width=width,
        height=height,
        confidence=confidence,
        frame_width=frame_width,
        frame_height=frame_height,
    )
    db.add(roi)
    await db.flush()
    return roi


async def list_rois(
    db: AsyncSession,
    session_id: uuid.UUID,
    limit: int = 100,
    offset: int = 0,
) -> List[ROI]:
    result = await db.execute(
        select(ROI)
        .where(ROI.session_id == session_id)
        .order_by(ROI.frame_index.asc())
        .limit(limit)
        .offset(offset)
    )
    return list(result.scalars().all())


async def get_latest_roi(db: AsyncSession, session_id: uuid.UUID) -> Optional[ROI]:
    result = await db.execute(
        select(ROI)
        .where(ROI.session_id == session_id)
        .order_by(ROI.captured_at.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


async def count_rois(db: AsyncSession, session_id: uuid.UUID) -> int:
    result = await db.execute(
        select(func.count()).select_from(ROI).where(ROI.session_id == session_id)
    )
    return result.scalar_one()
