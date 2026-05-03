import React, { useEffect, useRef } from 'react';
import { StreamMode } from '../types';

interface Props {
  sessionId: string | null;
  mode: StreamMode;
}

export const VideoViewer: React.FC<Props> = ({ sessionId, mode }) => {
  const imgRef = useRef<HTMLImageElement>(null);

  useEffect(() => {
    if (!imgRef.current) return;
    if (sessionId && mode === 'streaming') {
      imgRef.current.src = `/api/v1/stream/${sessionId}?t=${Date.now()}`;
    } else {
      imgRef.current.src = '';
    }
  }, [sessionId, mode]);

  return (
    <div className="video-viewer">
      <div className="viewer-inner">
        {mode === 'idle' && (
          <div className="viewer-placeholder">
            <div className="placeholder-icon">◉</div>
            <p>Press START to begin detection</p>
          </div>
        )}
        {mode === 'connecting' && (
          <div className="viewer-placeholder">
            <div className="spinner" />
            <p>Initialising camera…</p>
          </div>
        )}
        {mode === 'error' && (
          <div className="viewer-placeholder error">
            <div className="placeholder-icon">⚠</div>
            <p>Camera error — check permissions</p>
          </div>
        )}
        {mode === 'stopped' && (
          <div className="viewer-placeholder">
            <div className="placeholder-icon">◎</div>
            <p>Session ended</p>
          </div>
        )}
        <img
          ref={imgRef}
          className={`mjpeg-feed ${mode === 'streaming' ? 'visible' : ''}`}
          alt="Live annotated feed"
        />
        {mode === 'streaming' && (
          <div className="live-badge">
            <span className="live-dot" />
            LIVE
          </div>
        )}
      </div>
    </div>
  );
};
