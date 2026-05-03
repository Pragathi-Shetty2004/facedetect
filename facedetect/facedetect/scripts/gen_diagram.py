"""Generate a high-quality architecture diagram PNG using Pillow only."""

from PIL import Image, ImageDraw, ImageFont
import math

W, H = 1600, 1000
BG      = (9, 9, 14)
PANEL   = (15, 15, 23)
CARD    = (19, 19, 30)
BORDER  = (30, 30, 46)
BORDER2 = (42, 42, 64)
ACCENT  = (0, 255, 136)
ACCENT2 = (0, 200, 100)
BLUE    = (60, 120, 255)
ORANGE  = (255, 160, 40)
PURPLE  = (160, 80, 255)
RED     = (255, 60, 90)
TEXT    = (232, 232, 240)
MUTED   = (90, 90, 120)
DIM     = (58, 58, 85)

img = Image.new("RGB", (W, H), BG)
draw = ImageDraw.Draw(img)

# ── Try to get a monospace font, fall back gracefully ─────────────────────────
def get_font(size, bold=False):
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf" if bold else
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf",
        "/usr/share/fonts/truetype/freefont/FreeMono.ttf",
    ]
    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            continue
    return ImageFont.load_default()

F_TITLE  = get_font(32, bold=True)
F_HEAD   = get_font(18, bold=True)
F_BODY   = get_font(14)
F_SMALL  = get_font(11)
F_LABEL  = get_font(12, bold=True)

def rect(x, y, w, h, fill=PANEL, outline=BORDER, radius=8, thickness=1):
    """Draw a rounded-corner rectangle."""
    draw.rounded_rectangle([x, y, x+w, y+h], radius=radius, fill=fill, outline=outline, width=thickness)

def text(x, y, s, font=F_BODY, fill=TEXT, anchor="la"):
    draw.text((x, y), s, font=font, fill=fill, anchor=anchor)

def centered(cx, y, s, font=F_BODY, fill=TEXT):
    draw.text((cx, y), s, font=font, fill=fill, anchor="ma")

def arrow(x1, y1, x2, y2, color=MUTED, width=2, dashed=False):
    """Draw an arrow from (x1,y1) to (x2,y2)."""
    if dashed:
        # Draw dashes
        dx, dy = x2-x1, y2-y1
        length = math.hypot(dx, dy)
        steps = int(length / 12)
        for i in range(0, steps, 2):
            fx = x1 + dx * i / steps
            fy = y1 + dy * i / steps
            tx = x1 + dx * min(i+1, steps) / steps
            ty = y1 + dy * min(i+1, steps) / steps
            draw.line([(fx, fy), (tx, ty)], fill=color, width=width)
    else:
        draw.line([(x1, y1), (x2, y2)], fill=color, width=width)
    # Arrowhead
    dx, dy = x2-x1, y2-y1
    length = math.hypot(dx, dy) or 1
    ux, uy = dx/length, dy/length
    px, py = -uy, ux
    sz = 10
    pts = [
        (x2, y2),
        (x2 - sz*ux + sz*0.4*px, y2 - sz*uy + sz*0.4*py),
        (x2 - sz*ux - sz*0.4*px, y2 - sz*uy - sz*0.4*py),
    ]
    draw.polygon(pts, fill=color)

def tag(x, y, label, color=ACCENT):
    w = len(label) * 8 + 16
    draw.rounded_rectangle([x, y, x+w, y+20], radius=4, fill=(*color, 40), outline=color, width=1)
    draw.text((x + w//2, y+10), label, font=F_SMALL, fill=color, anchor="mm")

# ══════════════════════════════════════════════════════════════════════════════
# Background grid
for gx in range(0, W, 50):
    draw.line([(gx, 0), (gx, H)], fill=(15, 15, 22), width=1)
for gy in range(0, H, 50):
    draw.line([(0, gy), (W, gy)], fill=(15, 15, 22), width=1)

# Glow blobs
for cx, cy, cr, col in [
    (280, 200, 200, (0, 255, 136)),
    (900, 500, 180, (60, 120, 255)),
    (1350, 750, 150, (160, 80, 255)),
]:
    for r in range(cr, 0, -20):
        alpha = int(6 * (1 - r/cr))
        overlay = Image.new("RGB", (W, H), BG)
        od = ImageDraw.Draw(overlay)
        od.ellipse([cx-r, cy-r, cx+r, cy+r], fill=(*col, alpha))
        img.paste(overlay, mask=Image.new("L", (W, H), alpha))

# Title bar
rect(0, 0, W, 64, fill=(12, 12, 20), outline=BORDER, radius=0)
draw.line([(0, 64), (W, 64)], fill=BORDER2, width=1)
draw.text((30, 32), "◉", font=F_TITLE, fill=ACCENT, anchor="lm")
draw.text((72, 32), "FACEDETECT", font=F_TITLE, fill=TEXT, anchor="lm")
draw.text((74 + 220, 32), "— Architecture Diagram", font=get_font(20), fill=MUTED, anchor="lm")
draw.text((W-30, 32), "v1.0  ·  FastAPI · MediaPipe · PostgreSQL · React", font=F_SMALL, fill=DIM, anchor="rm")

# ══════════════════════════════════════════════════════════════════════════════
# DOCKER HOST label
rect(24, 80, W-48, H-100, fill=(12, 12, 19), outline=BORDER2, radius=6, thickness=1)
draw.rounded_rectangle([24, 80, 24+180, 80+22], radius=3, fill=BORDER2, outline=BORDER2)
draw.text((114, 91), "DOCKER HOST", font=F_SMALL, fill=MUTED, anchor="mm")

# ── Network: external ─────────────────────────────────────────────────────────
rect(40, 104, 740, H-130, fill=(14, 14, 22), outline=(30, 30, 50), radius=6, thickness=1)
draw.text((64, 116), "network: external", font=F_SMALL, fill=DIM)

# ── Network: internal ─────────────────────────────────────────────────────────
rect(800, 104, W-840, H-130, fill=(14, 14, 22), outline=(30, 30, 50), radius=6, thickness=1)
draw.text((824, 116), "network: internal", font=F_SMALL, fill=DIM)

# ══════════════════════════════════════════════════════════════════════════════
# BROWSER box
BRX, BRY, BRW, BRH = 56, 136, 260, 180
rect(BRX, BRY, BRW, BRH, fill=CARD, outline=(50, 50, 80), radius=8, thickness=2)
centered(BRX+BRW//2, BRY+22, "BROWSER", font=F_HEAD, fill=TEXT)
tag(BRX+20, BRY+50, "React SPA", color=BLUE)
tag(BRX+120, BRY+50, "Webcam API", color=BLUE)
text(BRX+20, BRY+84, "• getUserMedia() → frames", font=F_SMALL, fill=MUTED)
text(BRX+20, BRY+100, "• POST /ingest/frame/{id}", font=F_SMALL, fill=MUTED)
text(BRX+20, BRY+116, "• <img src=/stream/{id}>", font=F_SMALL, fill=MUTED)
text(BRX+20, BRY+132, "• GET /roi/{id}/stats", font=F_SMALL, fill=MUTED)
text(BRX+20, BRY+152, "port: 80 (nginx)", font=F_SMALL, fill=DIM)

# FRONTEND (nginx) box
FRX, FRY, FRW, FRH = 360, 136, 260, 180
rect(FRX, FRY, FRW, FRH, fill=CARD, outline=ACCENT2, radius=8, thickness=2)
centered(FRX+FRW//2, FRY+22, "FRONTEND", font=F_HEAD, fill=ACCENT)
tag(FRX+16, FRY+50, "nginx:1.27", color=ACCENT)
tag(FRX+130, FRY+50, "Alpine", color=ACCENT)
text(FRX+16, FRY+84, "• Serve React SPA build", font=F_SMALL, fill=MUTED)
text(FRX+16, FRY+100, "• Proxy /api/* → backend:8000", font=F_SMALL, fill=MUTED)
text(FRX+16, FRY+116, "• Proxy WS /stream/ws/*", font=F_SMALL, fill=MUTED)
text(FRX+16, FRY+132, "• Disable buffering (MJPEG)", font=F_SMALL, fill=MUTED)
text(FRX+16, FRY+152, "port: 80:80 (host exposed)", font=F_SMALL, fill=DIM)

# BACKEND box
BEX, BEY, BEW, BEH = 816, 136, 340, 360
rect(BEX, BEY, BEW, BEH, fill=CARD, outline=ORANGE, radius=8, thickness=2)
centered(BEX+BEW//2, BEY+22, "BACKEND", font=F_HEAD, fill=ORANGE)
tag(BEX+16, BEY+50, "FastAPI", color=ORANGE)
tag(BEX+110, BEY+50, "uvicorn", color=ORANGE)
tag(BEX+200, BEY+50, "Python 3.12", color=ORANGE)

# API endpoints sub-box
rect(BEX+16, BEY+78, BEW-32, 180, fill=(20, 18, 12), outline=(60,50,20), radius=4, thickness=1)
text(BEX+26, BEY+90, "API ENDPOINTS", font=F_LABEL, fill=ORANGE)
for i, (method, path, col) in enumerate([
    ("POST", "/api/v1/ingest/session", ACCENT),
    ("POST", "/api/v1/ingest/frame/{id}", ACCENT),
    ("DEL ", "/api/v1/ingest/session/{id}", RED),
    ("GET ", "/api/v1/stream/{id}  → MJPEG", BLUE),
    ("WS  ", "/api/v1/stream/ws/{id}", BLUE),
    ("GET ", "/api/v1/roi/{id}", PURPLE),
    ("GET ", "/api/v1/roi/{id}/latest", PURPLE),
    ("GET ", "/api/v1/roi/{id}/stats", PURPLE),
]):
    yy = BEY+110 + i*18
    draw.text((BEX+26, yy), method, font=F_SMALL, fill=col)
    draw.text((BEX+72, yy), path, font=F_SMALL, fill=MUTED)

text(BEX+16, BEY+272, "port: 8000 (internal only)", font=F_SMALL, fill=DIM)

# Detection pipeline sub-box
rect(BEX+16, BEY+288, BEW-32, 55, fill=(12, 18, 20), outline=(20,50,60), radius=4, thickness=1)
text(BEX+26, BEY+298, "DETECTION PIPELINE", font=F_LABEL, fill=BLUE)
text(BEX+26, BEY+316, "MediaPipe FaceDetection → BoundingBox", font=F_SMALL, fill=MUTED)
text(BEX+26, BEY+332, "Pillow ImageDraw.rectangle() — NO OpenCV", font=F_SMALL, fill=ACCENT)

# POSTGRES box
PGX, PGY, PGW, PGH = 1180, 136, 280, 360
rect(PGX, PGY, PGW, PGH, fill=CARD, outline=BLUE, radius=8, thickness=2)
centered(PGX+PGW//2, PGY+22, "POSTGRESQL 16", font=F_HEAD, fill=BLUE)
tag(PGX+16, PGY+50, "Alpine", color=BLUE)
tag(PGX+100, PGY+50, "asyncpg", color=BLUE)

rect(PGX+16, PGY+78, PGW-32, 186, fill=(12,14,22), outline=(20,30,60), radius=4, thickness=1)
text(PGX+26, PGY+90, "TABLE: sessions", font=F_LABEL, fill=BLUE)
for col in ["id UUID PK", "created_at TIMESTAMPTZ", "ended_at TIMESTAMPTZ", "source_label VARCHAR", "total_frames BIGINT"]:
    idx = ["id UUID PK","created_at TIMESTAMPTZ","ended_at TIMESTAMPTZ","source_label VARCHAR","total_frames BIGINT"].index(col)
    draw.text((PGX+26, PGY+112+idx*16), col, font=F_SMALL, fill=MUTED)

draw.line([(PGX+16, PGY+196), (PGX+PGW-16, PGY+196)], fill=BORDER2, width=1)
text(PGX+26, PGY+202, "TABLE: rois", font=F_LABEL, fill=PURPLE)
for i, col in enumerate(["id UUID PK","session_id UUID FK","frame_index BIGINT","captured_at TIMESTAMPTZ ⬆idx","x, y INTEGER (top-left)","width, height INTEGER","confidence FLOAT","frame_width, frame_height"]):
    draw.text((PGX+26, PGY+222+i*14), col, font=F_SMALL, fill=MUTED)

# Volume
rect(PGX+16, PGY+PGH-54, PGW-32, 36, fill=(10,12,22), outline=BORDER2, radius=3)
draw.text((PGX+26, PGY+PGH-40), "📦 postgres_data (named volume)", font=F_SMALL, fill=DIM)

# ══════════════════════════════════════════════════════════════════════════════
# FRAME BROKER box (inside backend area)
FBX, FBY, FBW, FBH = 816, 520, 340, 100
rect(FBX, FBY, FBW, FBH, fill=(14, 16, 20), outline=PURPLE, radius=6, thickness=1)
centered(FBX+FBW//2, FBY+14, "FRAME BROKER (in-process)", font=F_LABEL, fill=PURPLE)
text(FBX+16, FBY+36, "asyncio.Queue per WebSocket subscriber", font=F_SMALL, fill=MUTED)
text(FBX+16, FBY+52, "Drop oldest frame on backpressure", font=F_SMALL, fill=MUTED)
text(FBX+16, FBY+68, "Pub: ingest endpoint → Sub: MJPEG / WS", font=F_SMALL, fill=MUTED)

# ══════════════════════════════════════════════════════════════════════════════
# ARROWS

# Browser → Frontend (HTTP :80)
arrow(BRX+BRW, BRY+BRH//2, FRX, FRY+FRH//2, color=ACCENT, width=2)
centered((BRX+BRW+FRX)//2, BRY+BRH//2-18, "HTTP :80", font=F_SMALL, fill=ACCENT)

# Frontend → Backend (proxy /api/*)
arrow(FRX+FRW, FRY+60, BEX, BEY+60, color=ORANGE, width=2)
centered((FRX+FRW+BEX)//2, FRY+42, "/api/* proxy", font=F_SMALL, fill=ORANGE)

# Frontend → Backend (MJPEG stream)
arrow(FRX+FRW, FRY+120, BEX, BEY+120, color=BLUE, width=2)
centered((FRX+FRW+BEX)//2, FRY+102, "MJPEG stream", font=F_SMALL, fill=BLUE)

# Backend → Postgres
arrow(BEX+BEW, BEY+200, PGX, PGY+200, color=BLUE, width=2)
centered((BEX+BEW+PGX)//2, BEY+182, "asyncpg", font=F_SMALL, fill=BLUE)

# Backend → Broker (internal)
arrow(BEX+BEW//2, BEY+BEH, FBX+FBW//2, FBY, color=PURPLE, width=2, dashed=True)

# Broker → Frontend (stream out)
arrow(FBX, FBY+FBH//2, FRX+FRW, FRY+120+40, color=PURPLE, width=2, dashed=True)

# ══════════════════════════════════════════════════════════════════════════════
# LEGEND
LX, LY = 56, 660
rect(LX, LY, 700, 200, fill=CARD, outline=BORDER, radius=6, thickness=1)
text(LX+16, LY+14, "LEGEND & FLOW", font=F_LABEL, fill=MUTED)

items = [
    (ACCENT,  "─────",  "HTTP request / API call"),
    (ORANGE,  "─────",  "nginx reverse proxy"),
    (BLUE,    "─────",  "Database / asyncpg"),
    (PURPLE,  "- - -",  "Internal pub/sub (FrameBroker)"),
]
for i, (col, dash, label) in enumerate(items):
    y = LY+40 + i*36
    draw.rounded_rectangle([LX+16, y, LX+80, y+20], radius=3, fill=(*col, 30), outline=col, width=1)
    draw.text((LX+48, y+10), dash, font=F_SMALL, fill=col, anchor="mm")
    text(LX+90, y+4, label, font=F_BODY, fill=MUTED)

# Flow steps
rect(LX+360, LY+14, 325, 170, fill=(14,14,22), outline=BORDER2, radius=4)
text(LX+376, LY+26, "DATA FLOW", font=F_LABEL, fill=DIM)
steps = [
    "① Browser captures webcam frame (Canvas→JPEG)",
    "② POST /ingest/frame → Backend processes",
    "③ MediaPipe detects face → BoundingBox",
    "④ Pillow draws green rectangle on frame",
    "⑤ ROI record saved to PostgreSQL",
    "⑥ Frame published to FrameBroker",
    "⑦ MJPEG subscriber pushes to browser",
    "⑧ Browser displays annotated live feed",
]
for i, s in enumerate(steps):
    draw.text((LX+376, LY+46+i*16), s, font=F_SMALL, fill=MUTED if i%2 else TEXT)

# ══════════════════════════════════════════════════════════════════════════════
# Footer
draw.line([(0, H-28), (W, H-28)], fill=BORDER, width=1)
draw.text((W//2, H-14), "FaceDetect v1.0  ·  No OpenCV — MediaPipe + Pillow  ·  FastAPI · PostgreSQL · React · Docker",
          font=F_SMALL, fill=DIM, anchor="mm")

img.save("/home/claude/facedetect/architecture.png", format="PNG", optimize=True)
print("Diagram saved → architecture.png")
