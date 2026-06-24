const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const TOKEN_KEY = "score_token";

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

export interface AuthUser {
  id: number;
  username: string;
  email: string;
}

export interface AuthResponse {
  success: boolean;
  message: string;
  data: { token: string; expires_in: number; user_id: number };
}

export interface SessionHistoryEntry {
  id: number;
  intent: string;
  schedule: ModulationSchedule | null;
  completion_pct: number | null;
  rating: number | null;
  started_at: string | null;
}

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(TOKEN_KEY);
}

export function saveToken(token: string): void {
  if (typeof window !== "undefined") window.localStorage.setItem(TOKEN_KEY, token);
}

export function clearToken(): void {
  if (typeof window !== "undefined") window.localStorage.removeItem(TOKEN_KEY);
}

function authHeaders(): Record<string, string> {
  const token = getToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
}

async function postJson<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const payload = await res.json();
  if (!res.ok) {
    const detail = (payload as { detail?: string }).detail;
    throw new Error(detail ?? `API error: ${res.status}`);
  }
  return payload as T;
}

export async function startSession(
  intent: string,
  durationMinutes: number = 25,
): Promise<SessionStartResponse> {
  return postJson<SessionStartResponse>("/sessions/start", {
    intent,
    duration_minutes: durationMinutes,
  });
}

export async function register(
  email: string,
  username: string,
  password: string,
): Promise<AuthResponse> {
  return postJson<AuthResponse>("/auth/register", { email, username, password });
}

export async function login(email: string, password: string): Promise<AuthResponse> {
  return postJson<AuthResponse>("/auth/login", { email, password });
}

export async function getMe(): Promise<AuthUser> {
  const res = await fetch(`${API_BASE}/auth/me`, { headers: authHeaders() });
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  const payload = await res.json();
  return payload.data as AuthUser;
}

export async function fetchHistory(limit: number = 20): Promise<SessionHistoryEntry[]> {
  const res = await fetch(`${API_BASE}/sessions/history?limit=${limit}`, {
    headers: authHeaders(),
  });
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  const payload = await res.json();
  return payload.data.sessions as SessionHistoryEntry[];
}
