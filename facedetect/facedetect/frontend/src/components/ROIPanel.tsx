import React from 'react';
import { ROIRecord, SessionStats } from '../types';

interface Props {
  roi: ROIRecord | null;
  stats: SessionStats | null;
  frameCount: number;
  faceDetected: boolean;
  sessionId: string | null;
}

export const ROIPanel: React.FC<Props> = ({ roi, stats, frameCount, faceDetected, sessionId }) => {
  const pct = (n: number | null) => n != null ? `${(n * 100).toFixed(1)}%` : '—';

  return (
    <div className="roi-panel">
      <div className="panel-header">
        <span className="panel-title">DETECTION DATA</span>
        <span className={`status-dot ${faceDetected ? 'active' : ''}`} />
      </div>

      <div className="data-grid">
        <DataRow label="SESSION" value={sessionId ? `${sessionId.slice(0, 8)}…` : '—'} mono />
        <DataRow label="FRAMES" value={frameCount.toLocaleString()} mono />
        <DataRow label="FACE" value={faceDetected ? '✓ DETECTED' : '✗ NONE'} highlight={faceDetected} />
      </div>

      {roi && (
        <div className="roi-box-section">
          <div className="section-label">BOUNDING BOX</div>
          <div className="bbox-grid">
            <BBoxVal label="X" value={roi.x} />
            <BBoxVal label="Y" value={roi.y} />
            <BBoxVal label="W" value={roi.width} />
            <BBoxVal label="H" value={roi.height} />
          </div>
          <div className="confidence-bar-wrap">
            <div className="conf-label">
              <span>CONFIDENCE</span>
              <span className="conf-value">{pct(roi.confidence)}</span>
            </div>
            <div className="conf-track">
              <div className="conf-fill" style={{ width: pct(roi.confidence) }} />
            </div>
          </div>
        </div>
      )}

      {stats && (
        <div className="stats-section">
          <div className="section-label">SESSION STATS</div>
          <DataRow label="TOTAL FRAMES" value={stats.total_frames.toLocaleString()} mono />
          <DataRow label="FRAMES W/ FACE" value={stats.frames_with_face.toLocaleString()} mono />
          <DataRow label="DETECTION RATE" value={pct(stats.detection_rate)} mono />
        </div>
      )}
    </div>
  );
};

const DataRow: React.FC<{ label: string; value: string; mono?: boolean; highlight?: boolean }> = ({ label, value, mono, highlight }) => (
  <div className="data-row">
    <span className="data-label">{label}</span>
    <span className={`data-value${mono ? ' mono' : ''}${highlight ? ' highlight' : ''}`}>{value}</span>
  </div>
);

const BBoxVal: React.FC<{ label: string; value: number }> = ({ label, value }) => (
  <div className="bbox-val">
    <span className="bbox-label">{label}</span>
    <span className="bbox-num">{value}</span>
  </div>
);
