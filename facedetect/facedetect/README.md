# FaceDetect — Real-Time Face Detection Pipeline

A containerised full-stack application that accepts a live webcam feed, detects faces using **MediaPipe** (no OpenCV), draws axis-aligned bounding boxes with **Pillow**, persists ROI data to **PostgreSQL**, and streams annotated frames back to a **React** frontend.

---

## Architecture

```
┌─────────────────── Docker network: external ──────────────────┐
│                                                                 │
│  ┌──────────────────┐   port 80    ┌──────────────────────┐   │
│  │   Browser        │◄────────────►│  Frontend (nginx)     │   │
│  │  React + MJPEG   │              │  React SPA + reverse  │   │
│  └──────────────────┘              │  proxy → backend      │   │
│                                    └──────────┬─────────────┘   │
│                                               │ /api/*          │
└───────────────────────────────────────────────┼─────────────────┘
                                                │
┌─────────────────── Docker network: internal ──┼─────────────────┐
│                                               ▼                  │
│                              ┌────────────────────────────┐      │
│                              │  Backend (FastAPI/uvicorn) │      │
│                              │                            │      │
│                              │  POST /ingest/session      │      │
│                              │  POST /ingest/frame/{id}   │      │
│                              │  GET  /stream/{id}  MJPEG  │      │
│                              │  WS   /stream/ws/{id}      │      │
│                              │  GET  /roi/{id}            │      │
│                              │  GET  /roi/{id}/latest     │      │
│                              │  GET  /roi/{id}/stats      │      │
│                              └─────────────┬──────────────┘      │
│                                            │ asyncpg             │
│                              ┌─────────────▼──────────────┐      │
│                              │  PostgreSQL 16              │      │
│                              │  tables: sessions, rois    │      │
│                              └────────────────────────────┘      │
└──────────────────────────────────────────────────────────────────┘
```

## Five-Minute Quick Start

### Prerequisites
- Docker ≥ 24
- Docker Compose plugin (`docker compose version`)
- A webcam (for live detection)

### Steps

```bash
# 1. Clone and enter the project
git clone <repo-url> facedetect && cd facedetect

# 2. Copy environment template
cp .env.example .env          # optionally edit SECRET_KEY

# 3. Build and start all services
docker compose up --build -d

# 4. Open the app
open http://localhost          # or http://localhost on Windows/Linux
```

The frontend will open at **http://localhost**.  
Click **START** to grant camera access and begin detection.

### Stopping

```bash
docker compose down            # keep DB volume
docker compose down -v         # also wipe DB
```

---

## API Reference

All endpoints prefixed with `/api/v1`.

### 1. Ingest — Receive Video Feed

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/ingest/session` | Create a new session → returns `session_id` |
| `POST` | `/ingest/frame/{session_id}` | Push a JPEG/PNG frame (multipart `frame` field) |
| `DELETE` | `/ingest/session/{session_id}` | Mark session as ended |

**POST /ingest/frame/{id}** response:
```json
{
  "session_id": "uuid",
  "frame_index": 42,
  "face_detected": true,
  "roi": {
    "x": 120, "y": 80, "width": 200, "height": 220,
    "confidence": 0.9741,
    "frame_width": 640, "frame_height": 480
  }
}
```

### 2. Stream — Serve Annotated Feed

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/stream/{session_id}` | MJPEG HTTP stream (use in `<img src>`) |
| `WS` | `/stream/ws/{session_id}` | WebSocket binary JPEG stream |

### 3. ROI Data

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/roi/{session_id}` | Paginated ROI list (`?limit=50&offset=0`) |
| `GET` | `/roi/{session_id}/latest` | Single most-recent ROI |
| `GET` | `/roi/{session_id}/stats` | Aggregate detection statistics |

Interactive docs: **http://localhost:8000/docs** (in dev mode with `docker-compose.dev.yml`)

---

## Design Decisions

### No OpenCV — Pillow + MediaPipe
The constraint prohibits `cv2`. We use:
- **MediaPipe FaceDetection** — Google's production-grade, CPU-efficient detector. Returns normalised bounding boxes.
- **Pillow (PIL)** — pure-Python image I/O, JPEG encode/decode, and rectangle drawing via `ImageDraw.rectangle`.

### Database — PostgreSQL (not Redis, not SQLite)
ROI records are structured relational data with a clear foreign-key relationship to sessions. PostgreSQL gives us ACID guarantees, efficient time-range queries on `captured_at`, and the `v_session_summary` view for fast analytics. The async driver (`asyncpg`) keeps FastAPI's event loop unblocked.

### Streaming architecture
Each ingest frame is published to an in-process `FrameBroker` (pub/sub, asyncio queues). MJPEG subscribers consume from their queue and write `multipart/x-mixed-replace` chunks. This avoids polling the database and supports multiple simultaneous viewers of the same session.

### Single worker + asyncio
MediaPipe inference is fast enough on a single CPU core for 15 fps webcam input. For higher throughput a `ThreadPoolExecutor` wrapping `annotate_frame` can be added without changing the API surface.

---

## Development

```bash
# Run with hot reload
docker compose -f docker-compose.yml -f docker-compose.dev.yml up

# Run backend tests
cd backend
pip install -r requirements.txt
pytest -v

# Access DB directly (dev only)
psql postgresql://facedetect:facedetect@localhost:5432/facedetect
```

---

## Schema

```sql
sessions
  id            UUID PK
  created_at    TIMESTAMPTZ
  ended_at      TIMESTAMPTZ nullable
  source_label  VARCHAR(255) nullable
  total_frames  BIGINT

rois
  id            UUID PK
  session_id    UUID FK → sessions.id (CASCADE DELETE)
  frame_index   BIGINT
  captured_at   TIMESTAMPTZ  ← indexed
  x, y          INTEGER      (top-left corner, pixel coords)
  width, height INTEGER      (axis-aligned bounding box)
  confidence    FLOAT nullable
  frame_width   INTEGER
  frame_height  INTEGER
```

---

## Security Notes

- Backend is not exposed directly; all traffic routes through nginx.
- DB port is not published in production compose.
- `SECRET_KEY` must be overridden in `.env` before production deployment.
- Frame uploads are validated for content-type and capped at 10 MB.
- App runs as non-root user (`appuser`, UID 1001) inside the container.

---

## AI Collaboration Disclosure

This project was designed and implemented with assistance from **Claude (Anthropic)**. AI was used for:
- Scaffolding FastAPI route structure and async patterns
- Writing Pillow-based bounding-box drawing (replacement for OpenCV)
- Generating pytest fixtures and mocking strategy
- Drafting this README

All code was reviewed, validated, and assembled by the submitting engineer.
