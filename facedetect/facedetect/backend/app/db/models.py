"""SQLAlchemy ORM models."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import BigInteger, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class Session(Base):
    """One ingest session = one connected video source."""

    __tablename__ = "sessions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, nullable=False
    )
    ended_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    source_label: Mapped[str | None] = mapped_column(String(255), nullable=True)
    total_frames: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)

    rois: Mapped[list["ROI"]] = relationship("ROI", back_populates="session", cascade="all, delete-orphan")


class ROI(Base):
    """One bounding-box record per frame where a face was detected."""

    __tablename__ = "rois"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    frame_index: Mapped[int] = mapped_column(BigInteger, nullable=False)
    captured_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, nullable=False, index=True
    )

    # Bounding box in pixel coordinates (top-left origin)
    x: Mapped[int] = mapped_column(Integer, nullable=False)
    y: Mapped[int] = mapped_column(Integer, nullable=False)
    width: Mapped[int] = mapped_column(Integer, nullable=False)
    height: Mapped[int] = mapped_column(Integer, nullable=False)

    # Detection metadata
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    frame_width: Mapped[int] = mapped_column(Integer, nullable=False)
    frame_height: Mapped[int] = mapped_column(Integer, nullable=False)

    session: Mapped["Session"] = relationship("Session", back_populates="rois")

    @property
    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "session_id": str(self.session_id),
            "frame_index": self.frame_index,
            "captured_at": self.captured_at.isoformat(),
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height,
            "confidence": self.confidence,
            "frame_width": self.frame_width,
            "frame_height": self.frame_height,
        }
