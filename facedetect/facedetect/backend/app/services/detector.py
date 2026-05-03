"""
Face detection service.

Uses MediaPipe's FaceDetection solution – no OpenCV dependency.
All image I/O is done with Pillow.
"""

from __future__ import annotations

import io
import logging
from dataclasses import dataclass
from typing import Optional

import mediapipe as mp
import numpy as np
from PIL import Image, ImageDraw

from app.core.config import settings

logger = logging.getLogger(__name__)

# ── MediaPipe initialisation ───────────────────────────────────────────────────
_mp_face = mp.solutions.face_detection
_detector = _mp_face.FaceDetection(
    model_selection=0,                          # short-range model (≤2 m)
    min_detection_confidence=settings.FACE_DETECTION_CONFIDENCE,
)


@dataclass
class BoundingBox:
    x: int
    y: int
    width: int
    height: int
    confidence: float

    def as_dict(self) -> dict:
        return {
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height,
            "confidence": round(self.confidence, 4),
        }


def _clamp(value: int, lo: int, hi: int) -> int:
    return max(lo, min(value, hi))


def detect_face(image_bytes: bytes) -> tuple[Optional[BoundingBox], int, int]:
    """
    Detect a single face in raw JPEG/PNG bytes.

    Returns (BoundingBox | None, frame_width, frame_height).
    """
    try:
        img: Image.Image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    except Exception as exc:
        logger.warning("Failed to decode image: %s", exc)
        return None, 0, 0

    # Enforce size cap
    img.thumbnail(
        (settings.MAX_FRAME_WIDTH, settings.MAX_FRAME_HEIGHT),
        Image.LANCZOS,
    )
    w, h = img.size

    # MediaPipe expects a uint8 numpy array in RGB
    arr = np.array(img, dtype=np.uint8)
    results = _detector.process(arr)

    if not results.detections:
        return None, w, h

    det = results.detections[0]  # only one face assumed
    bb = det.location_data.relative_bounding_box
    score = det.score[0] if det.score else 0.0

    # Convert relative → absolute pixel coords
    x = _clamp(int(bb.xmin * w), 0, w - 1)
    y = _clamp(int(bb.ymin * h), 0, h - 1)
    bw = _clamp(int(bb.width * w), 1, w - x)
    bh = _clamp(int(bb.height * h), 1, h - y)

    return BoundingBox(x=x, y=y, width=bw, height=bh, confidence=score), w, h


def draw_roi(image_bytes: bytes, box: BoundingBox) -> bytes:
    """
    Draw an axis-aligned bounding rectangle on the image using Pillow only.
    Returns JPEG bytes.
    """
    img: Image.Image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    img.thumbnail(
        (settings.MAX_FRAME_WIDTH, settings.MAX_FRAME_HEIGHT),
        Image.LANCZOS,
    )

    draw = ImageDraw.Draw(img)
    r, g, b = settings.ROI_BOX_COLOR
    color = (r, g, b)
    thickness = settings.ROI_BOX_THICKNESS

    x0, y0 = box.x, box.y
    x1, y1 = box.x + box.width, box.y + box.height

    # Draw rectangle as four filled lines (pure Pillow, no OpenCV)
    for t in range(thickness):
        draw.rectangle(
            [x0 + t, y0 + t, x1 - t, y1 - t],
            outline=color,
        )

    # Confidence label
    label = f"{box.confidence:.0%}"
    draw.text((x0 + thickness + 2, y0 + thickness + 2), label, fill=color)

    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=settings.FRAME_JPEG_QUALITY)
    return buf.getvalue()


def annotate_frame(image_bytes: bytes) -> tuple[bytes, Optional[BoundingBox], int, int]:
    """
    Full pipeline: detect → annotate → return annotated JPEG + box metadata.
    """
    box, fw, fh = detect_face(image_bytes)
    if box is None:
        # Return the (possibly resized) frame unmodified
        img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        img.thumbnail((settings.MAX_FRAME_WIDTH, settings.MAX_FRAME_HEIGHT), Image.LANCZOS)
        fw, fh = img.size
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=settings.FRAME_JPEG_QUALITY)
        return buf.getvalue(), None, fw, fh

    annotated = draw_roi(image_bytes, box)
    return annotated, box, fw, fh
