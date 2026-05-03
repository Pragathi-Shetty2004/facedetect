import React from 'react';
import { useSession } from './hooks/useSession';
import { VideoViewer } from './components/VideoViewer';
import { ROIPanel } from './components/ROIPanel';
import './App.css';

function App() {
  const {
    sessionId, mode, error, latestROI, stats,
    frameCount, faceDetected, startCapture, stopCapture,
  } = useSession();

  const isRunning = mode === 'streaming' || mode === 'connecting';

  return (
    <div className="app">
      {/* Header */}
      <header className="app-header">
        <div className="header-left">
          <span className="logo-mark">◉</span>
          <span className="logo-text">FACE<span className="logo-accent">DETECT</span></span>
        </div>
        <div className="header-right">
          <span className="header-tag">Real-Time Face Detection Pipeline</span>
        </div>
      </header>

      {/* Main layout */}
      <main className="app-main">
        <div className="left-col">
          <VideoViewer sessionId={sessionId} mode={mode} />

          {error && (
            <div className="error-banner">
              <span>⚠</span> {error}
            </div>
          )}

          <div className="controls">
            <button
              className={`ctrl-btn ${isRunning ? 'btn-stop' : 'btn-start'}`}
              onClick={isRunning ? stopCapture : startCapture}
              disabled={mode === 'connecting'}
            >
              {mode === 'connecting' ? (
                <><span className="btn-spinner" /> CONNECTING…</>
              ) : isRunning ? (
                <><span className="btn-icon">■</span> STOP</>
              ) : (
                <><span className="btn-icon">▶</span> START</>
              )}
            </button>

            <div className="mode-indicator">
              <span className={`mode-dot mode-${mode}`} />
              <span className="mode-text">{mode.toUpperCase()}</span>
            </div>
          </div>
        </div>

        <div className="right-col">
          <ROIPanel
            roi={latestROI}
            stats={stats}
            frameCount={frameCount}
            faceDetected={faceDetected}
            sessionId={sessionId}
          />

          <div className="info-card">
            <div className="section-label">HOW IT WORKS</div>
            <ol className="how-list">
              <li>Camera frames sent to <code>/api/v1/ingest/frame</code></li>
              <li>MediaPipe detects faces (no OpenCV)</li>
              <li>Pillow draws axis-aligned bounding box</li>
              <li>ROI data persisted to PostgreSQL</li>
              <li>Annotated stream served via MJPEG</li>
            </ol>
          </div>
        </div>
      </main>

      <footer className="app-footer">
        <span>FaceDetect v1.0 · FastAPI · MediaPipe · PostgreSQL · React</span>
      </footer>
    </div>
  );
}

export default App;
