"""
Endpoint 2 – Annotated Video Stream

GET  /api/v1/stream/{session_id}          → MJPEG HTTP stream
WS   /api/v1/stream/ws/{session_id}       → WebSocket binary frame stream
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from typing import AsyncGenerator

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse

from app.services.broker import frame_broker

logger = logging.getLogger(__name__)
router = APIRouter()

MJPEG_BOUNDARY = b"--frame"
MJPEG_HEADER = (
    b"--frame\r\n"
    b"Content-Type: image/jpeg\r\n"
    b"Content-Length: {length}\r\n\r\n"
)


# ── MJPEG HTTP stream ──────────────────────────────────────────────────────────

async def _mjpeg_generator(session_id: str) -> AsyncGenerator[bytes, None]:
    q = frame_broker.subscribe(session_id)
    try:
        while True:
            try:
                frame: bytes = await asyncio.wait_for(q.get(), timeout=10.0)
            except asyncio.TimeoutError:
                # Send keepalive comment to prevent browser from closing
                yield b"--frame\r\nContent-Type: text/plain\r\n\r\nkeepalive\r\n"
                continue

            header = MJPEG_HEADER.replace(b"{length}", str(len(frame)).encode())
            yield header + frame + b"\r\n"
    except asyncio.CancelledError:
        pass
    finally:
        frame_broker.unsubscribe(session_id, q)


@router.get(
    "/stream/{session_id}",
    response_class=StreamingResponse,
    summary="MJPEG video stream for a session",
)
async def mjpeg_stream(session_id: uuid.UUID) -> StreamingResponse:
    """
    Returns a multipart/x-mixed-replace MJPEG stream.
    Compatible with <img src="…"> tags and most video players.
    """
    sid = str(session_id)
    return StreamingResponse(
        _mjpeg_generator(sid),
        media_type="multipart/x-mixed-replace; boundary=frame",
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
        },
    )


# ── WebSocket binary stream ────────────────────────────────────────────────────

@router.websocket("/stream/ws/{session_id}")
async def ws_stream(websocket: WebSocket, session_id: uuid.UUID) -> None:
    """
    WebSocket endpoint that pushes annotated JPEG frames as binary messages.
    The client receives raw JPEG bytes which can be decoded to a Blob URL.
    """
    await websocket.accept()
    sid = str(session_id)
    q = frame_broker.subscribe(sid)
    logger.info("WS client connected to session %s", sid)

    try:
        while True:
            try:
                frame: bytes = await asyncio.wait_for(q.get(), timeout=15.0)
                await websocket.send_bytes(frame)
            except asyncio.TimeoutError:
                # Send ping to keep WS alive
                await websocket.send_json({"type": "ping"})
    except WebSocketDisconnect:
        logger.info("WS client disconnected from session %s", sid)
    except Exception as exc:
        logger.warning("WS error on session %s: %s", sid, exc)
    finally:
        frame_broker.unsubscribe(sid, q)
