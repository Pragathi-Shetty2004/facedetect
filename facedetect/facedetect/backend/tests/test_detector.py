"""Unit tests for the face detection service."""

import io
import pytest
from PIL import Image

from app.services.detector import BoundingBox, detect_face, draw_roi, annotate_frame


def _solid_jpeg(width=320, height=240, color=(100, 149, 237)) -> bytes:
    img = Image.new("RGB", (width, height), color=color)
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


class TestBoundingBox:
    def test_as_dict(self):
        bb = BoundingBox(x=10, y=20, width=80, height=90, confidence=0.92)
        d = bb.as_dict()
        assert d["x"] == 10
        assert d["y"] == 20
        assert d["width"] == 80
        assert d["height"] == 90
        assert abs(d["confidence"] - 0.92) < 1e-3


class TestDetectFace:
    def test_no_face_blank_image(self):
        """A blank solid-colour image should not produce a detection."""
        box, fw, fh = detect_face(_solid_jpeg())
        assert box is None
        assert fw == 320
        assert fh == 240

    def test_invalid_bytes_returns_none(self):
        box, fw, fh = detect_face(b"not-an-image")
        assert box is None
        assert fw == 0
        assert fh == 0

    def test_empty_bytes_returns_none(self):
        box, fw, fh = detect_face(b"")
        assert box is None


class TestDrawROI:
    def test_draw_roi_returns_jpeg(self):
        raw = _solid_jpeg()
        box = BoundingBox(x=10, y=10, width=100, height=100, confidence=0.9)
        result = draw_roi(raw, box)
        # Should be valid JPEG
        img = Image.open(io.BytesIO(result))
        assert img.format == "JPEG"

    def test_draw_roi_preserves_dimensions(self):
        raw = _solid_jpeg(320, 240)
        box = BoundingBox(x=10, y=10, width=50, height=50, confidence=0.8)
        result = draw_roi(raw, box)
        img = Image.open(io.BytesIO(result))
        assert img.size == (320, 240)

    def test_draw_roi_colours_box_pixels(self):
        """Pixels on the bounding-box border should be green (0,255,0)."""
        raw = _solid_jpeg(320, 240, color=(0, 0, 0))
        box = BoundingBox(x=50, y=50, width=100, height=100, confidence=0.9)
        result = draw_roi(raw, box)
        img = Image.open(io.BytesIO(result)).convert("RGB")
        # Sample a pixel on the left edge of the box
        r, g, b = img.getpixel((50, 75))
        # JPEG compression may shift values slightly; green channel dominant
        assert g > r
        assert g > b


class TestAnnotateFrame:
    def test_annotate_blank_returns_bytes(self):
        raw = _solid_jpeg()
        annotated, box, fw, fh = annotate_frame(raw)
        assert isinstance(annotated, bytes)
        assert len(annotated) > 0
        assert box is None  # no face in blank image

    def test_annotate_produces_valid_jpeg(self):
        raw = _solid_jpeg()
        annotated, _, _, _ = annotate_frame(raw)
        img = Image.open(io.BytesIO(annotated))
        assert img.format == "JPEG"
