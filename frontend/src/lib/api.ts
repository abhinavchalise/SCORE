const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface ModulationStep {
  timestamp_sec: number;
  target_bpm: number;
  binaural_freq: number;
  ramp_duration_sec: number;
  layer: string;
}

export interface ModulationSchedule {
  intent: string;
  total_duration_sec: number;
  steps: ModulationStep[];
}

export interface SessionStartResponse {
  success: boolean;
  message: string;
  data: {
    session_id: number;
    schedule: ModulationSchedule;
  };
}

export async function startSession(
  intent: string,
  durationMinutes: number = 25,
): Promise<SessionStartResponse> {
  const res = await fetch(`${API_BASE}/sessions/start`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ intent, duration_minutes: durationMinutes }),
  });
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}
