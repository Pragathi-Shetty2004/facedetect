export interface ROIRecord {
  id: string;
  session_id: string;
  frame_index: number;
  captured_at: string;
  x: number;
  y: number;
  width: number;
  height: number;
  confidence: number | null;
  frame_width: number;
  frame_height: number;
}

export interface SessionStats {
  session_id: string;
  total_frames: number;
  frames_with_face: number;
  detection_rate: number | null;
  source_label: string | null;
  created_at: string;
  ended_at: string | null;
}

export interface IngestResponse {
  session_id: string;
  frame_index: number;
  face_detected: boolean;
  roi: ROIRecord | null;
  frame_width: number;
  frame_height: number;
}

export interface SessionCreateResponse {
  session_id: string;
  created_at: string;
}

export type StreamMode = 'idle' | 'connecting' | 'streaming' | 'error' | 'stopped';
