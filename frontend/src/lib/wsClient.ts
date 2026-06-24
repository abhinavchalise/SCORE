import { ModulationSchedule } from "./api";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const WS_BASE = API_BASE.replace(/^http/, "ws");

export type ControlAction = "pause" | "resume" | "stop";
export type FeedbackKind = "skip" | "edit" | "rating";

export interface SessionHandlers {
  onSchedule: (schedule: ModulationSchedule, sessionId: number, usedFallback: boolean) => void;
  onTick: (elapsedSec: number) => void;
  onEnded: (completionPct: number) => void;
  onError?: (event: Event) => void;
}

type ServerMessage =
  | { type: "schedule"; session_id: number; schedule: ModulationSchedule }
  | { type: "fallback"; session_id: number; reason: string; schedule: ModulationSchedule }
  | { type: "tick"; session_id: number; elapsed_sec: number }
  | { type: "ended"; session_id: number; completion_pct: number };

export class SessionSocket {
  private socket: WebSocket | null = null;

  connect(intent: string, durationMinutes: number, handlers: SessionHandlers): void {
    const socket = new WebSocket(`${WS_BASE}/sessions/ws`);
    this.socket = socket;

    socket.onopen = () => {
      socket.send(JSON.stringify({ intent, duration_minutes: durationMinutes }));
    };

    socket.onmessage = (event) => {
      const message = JSON.parse(event.data) as ServerMessage;
      switch (message.type) {
        case "schedule":
          handlers.onSchedule(message.schedule, message.session_id, false);
          break;
        case "fallback":
          handlers.onSchedule(message.schedule, message.session_id, true);
          break;
        case "tick":
          handlers.onTick(message.elapsed_sec);
          break;
        case "ended":
          handlers.onEnded(message.completion_pct);
          break;
      }
    };

    if (handlers.onError) socket.onerror = handlers.onError;
  }

  sendControl(action: ControlAction): void {
    this.send({ type: "control", action });
  }

  sendFeedback(kind: FeedbackKind, payload: Record<string, unknown>): void {
    this.send({ type: "feedback", kind, payload });
  }

  close(): void {
    this.socket?.close();
    this.socket = null;
  }

  private send(data: unknown): void {
    if (this.socket?.readyState === WebSocket.OPEN) {
      this.socket.send(JSON.stringify(data));
    }
  }
}
