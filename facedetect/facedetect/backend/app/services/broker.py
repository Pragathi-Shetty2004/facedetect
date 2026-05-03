"""
In-process frame broker.

The ingest endpoint publishes annotated JPEG bytes here;
WebSocket stream consumers subscribe and receive frames in real time.
"""

from __future__ import annotations

import asyncio
import logging
from collections import defaultdict
from typing import Dict, Set

logger = logging.getLogger(__name__)


class FrameBroker:
    """Lightweight pub/sub broker keyed by session_id."""

    def __init__(self) -> None:
        # session_id → set of asyncio.Queue objects (one per subscriber)
        self._subscribers: Dict[str, Set[asyncio.Queue]] = defaultdict(set)

    def subscribe(self, session_id: str) -> asyncio.Queue:
        q: asyncio.Queue = asyncio.Queue(maxsize=8)
        self._subscribers[session_id].add(q)
        logger.debug("New subscriber for session %s (total: %d)", session_id, len(self._subscribers[session_id]))
        return q

    def unsubscribe(self, session_id: str, q: asyncio.Queue) -> None:
        self._subscribers[session_id].discard(q)
        if not self._subscribers[session_id]:
            del self._subscribers[session_id]
        logger.debug("Subscriber removed for session %s", session_id)

    async def publish(self, session_id: str, frame: bytes) -> None:
        """Publish a frame to all subscribers of the given session."""
        for q in list(self._subscribers.get(session_id, [])):
            if q.full():
                # Drop oldest frame to avoid backpressure buildup (real-time priority)
                try:
                    q.get_nowait()
                except asyncio.QueueEmpty:
                    pass
            try:
                q.put_nowait(frame)
            except asyncio.QueueFull:
                pass  # already handled above

    def active_sessions(self) -> list[str]:
        return list(self._subscribers.keys())


# Singleton instance shared across the app
frame_broker = FrameBroker()
