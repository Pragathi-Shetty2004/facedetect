import { useCallback, useRef, useState } from 'react';
import { IngestResponse, ROIRecord, SessionCreateResponse, SessionStats, StreamMode } from '../types';

const API_BASE = '/api/v1';

export function useSession() {
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [mode, setMode] = useState<StreamMode>('idle');
  const [error, setError] = useState<string | null>(null);
  const [latestROI, setLatestROI] = useState<ROIRecord | null>(null);
  const [stats, setStats] = useState<SessionStats | null>(null);
  const [frameCount, setFrameCount] = useState(0);
  const [faceDetected, setFaceDetected] = useState(false);

  const wsRef = useRef<WebSocket | null>(null);
  const streamImgRef = useRef<HTMLImageElement | null>(null);
  const mediaStreamRef = useRef<MediaStream | null>(null);
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const intervalRef = useRef<number | null>(null);
  const sessionIdRef = useRef<string | null>(null);

  const createSession = useCallback(async (label?: string): Promise<string> => {
    const url = label
      ? `${API_BASE}/ingest/session?source_label=${encodeURIComponent(label)}`
      : `${API_BASE}/ingest/session`;
    const res = await fetch(url, { method: 'POST' });
    if (!res.ok) throw new Error(`Failed to create session: ${res.statusText}`);
    const data: SessionCreateResponse = await res.json();
    return data.session_id;
  }, []);

  const sendFrame = useCallback(async (sid: string, blob: Blob): Promise<IngestResponse> => {
    const fd = new FormData();
    fd.append('frame', blob, 'frame.jpg');
    const res = await fetch(`${API_BASE}/ingest/frame/${sid}`, { method: 'POST', body: fd });
    if (!res.ok) throw new Error(`Frame ingest failed: ${res.statusText}`);
    return res.json();
  }, []);

  const fetchStats = useCallback(async (sid: string) => {
    try {
      const res = await fetch(`${API_BASE}/roi/${sid}/stats`);
      if (res.ok) setStats(await res.json());
    } catch { /* non-critical */ }
  }, []);

  const startCapture = useCallback(async () => {
    setError(null);
    setMode('connecting');
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: { width: 640, height: 480 }, audio: false });
      mediaStreamRef.current = stream;

      const video = document.createElement('video');
      video.srcObject = stream;
      video.playsInline = true;
      await video.play();
      videoRef.current = video;

      const canvas = document.createElement('canvas');
      canvas.width = 640;
      canvas.height = 480;
      canvasRef.current = canvas;

      const sid = await createSession('webcam');
      setSessionId(sid);
      sessionIdRef.current = sid;
      setMode('streaming');

      // Push frames at ~15 fps
      intervalRef.current = window.setInterval(async () => {
        const ctx = canvas.getContext('2d');
        if (!ctx || !videoRef.current) return;
        ctx.drawImage(videoRef.current, 0, 0, 640, 480);
        canvas.toBlob(async (blob) => {
          if (!blob || !sessionIdRef.current) return;
          try {
            const resp = await sendFrame(sessionIdRef.current, blob);
            setFrameCount(resp.frame_index + 1);
            setFaceDetected(resp.face_detected);
            if (resp.roi) setLatestROI(resp.roi);
          } catch { /* frame dropped */ }
        }, 'image/jpeg', 0.8);
      }, 67); // ~15 fps

      // Refresh stats every 3s
      const statsInterval = window.setInterval(() => {
        if (sessionIdRef.current) fetchStats(sessionIdRef.current);
      }, 3000);
      (intervalRef as any)._statsInterval = statsInterval;

    } catch (err: any) {
      setError(err.message || 'Failed to start camera');
      setMode('error');
    }
  }, [createSession, sendFrame, fetchStats]);

  const stopCapture = useCallback(async () => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      clearInterval((intervalRef as any)._statsInterval);
    }
    mediaStreamRef.current?.getTracks().forEach(t => t.stop());
    wsRef.current?.close();

    if (sessionIdRef.current) {
      await fetch(`${API_BASE}/ingest/session/${sessionIdRef.current}`, { method: 'DELETE' }).catch(() => {});
      await fetchStats(sessionIdRef.current);
    }
    setMode('stopped');
  }, [fetchStats]);

  return {
    sessionId,
    mode,
    error,
    latestROI,
    stats,
    frameCount,
    faceDetected,
    startCapture,
    stopCapture,
    streamImgRef,
  };
}
