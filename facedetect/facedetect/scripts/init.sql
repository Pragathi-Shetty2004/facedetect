-- Idempotent PostgreSQL initialisation script
-- Runs only on first-time DB creation

-- Enable UUID support (used by SQLAlchemy models)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Tables are created by SQLAlchemy on startup (see app/db/session.py → init_db)
-- This script is a hook for any manual tweaks, seed data, or extra extensions.

-- Useful view for quick inspection
CREATE OR REPLACE VIEW v_session_summary AS
SELECT
    s.id              AS session_id,
    s.source_label,
    s.created_at,
    s.ended_at,
    s.total_frames,
    COUNT(r.id)       AS face_frames,
    ROUND(
        COUNT(r.id)::numeric /
        NULLIF(s.total_frames, 0) * 100,
        2
    )                 AS detection_pct,
    AVG(r.confidence) AS avg_confidence
FROM sessions s
LEFT JOIN rois r ON r.session_id = s.id
GROUP BY s.id;

COMMENT ON VIEW v_session_summary IS 'Aggregate detection statistics per session';
