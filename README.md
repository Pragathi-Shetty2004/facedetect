# facedetect
# 🎯 FaceDetect — Real-Time Face Detection Pipeline

A full-stack, containerized application that captures live webcam input, detects faces using **MediaPipe**, draws bounding boxes with **Pillow**, stores ROI data in **PostgreSQL**, and streams annotated frames to a **React frontend**.

---

## 🚀 Quick Start (5 Minutes)

### 🔧 Prerequisites

* Docker installed (v24+)
* Docker Compose
* Webcam access

---

### ⚡ Steps to Run

```bash
# 1. Clone repository
git clone https://github.com/Pragathi-Shetty2004/facedetect.git
cd facedetect

# 2. Setup environment
cp .env.example .env

# 3. Build & start services
docker compose up --build -d

# 4. Open application
http://localhost
```

👉 Click **START** and allow camera access.

---

### 🛑 Stop Application

```bash
docker compose down
```

To remove database:

```bash
docker compose down -v
```

---

## 🏗️ Architecture Overview

* **Frontend**: React (served via Nginx)
* **Backend**: FastAPI (Python)
* **Database**: PostgreSQL
* **Face Detection**: MediaPipe
* **Image Processing**: Pillow
* **Streaming**: MJPEG / WebSockets
* **Containerization**: Docker

---

## 📡 API Endpoints

Base URL: `/api/v1`

### 🔹 Ingest

* `POST /ingest/session` → Create session
* `POST /ingest/frame/{id}` → Upload frame
* `DELETE /ingest/session/{id}` → End session

---

### 🔹 Streaming

* `GET /stream/{id}` → MJPEG stream
* `WS /stream/ws/{id}` → WebSocket stream

---

### 🔹 ROI Data

* `GET /roi/{id}` → All detections
* `GET /roi/{id}/latest` → Latest detection
* `GET /roi/{id}/stats` → Stats

---

## 🧠 Tech Stack

* React (Frontend UI)
* FastAPI (Backend API)
* PostgreSQL (Database)
* MediaPipe (Face Detection)
* Pillow (Image Processing)
* Docker (Deployment)

---

## 📁 Project Structure

```
facedetect/
│
├── backend/        # FastAPI backend
├── frontend/       # React frontend
├── docker-compose.yml
├── .env.example
└── README.md
```

---



## 🧪 Development Mode

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml up
```

Backend API docs:

```
http://localhost:8000/docs
```

---

## 📊 Database Schema

### sessions

* id (UUID)
* created_at
* ended_at
* total_frames

### rois

* id
* session_id
* frame_index
* coordinates (x, y, width, height)
* confidence
* frame size

---

## 💡 Key Features

* Real-time face detection 🎥
* Live streaming (MJPEG + WebSocket)
* Scalable async backend ⚡
* Clean containerized setup 🐳
* No OpenCV (uses MediaPipe + Pillow)

---

## 🤝 Contribution

Feel free to fork and improve this project!

---

## 📌 Author

**Pragathi Shetty**

---

## 📜 License

This project is for educational and demonstration purposes.
