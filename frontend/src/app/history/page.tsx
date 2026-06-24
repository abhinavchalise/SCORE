"use client";

import { useEffect, useState } from "react";
import { fetchHistory, SessionHistoryEntry } from "@/lib/api";

export default function HistoryPage() {
  const [sessions, setSessions] = useState<SessionHistoryEntry[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchHistory()
      .then(setSessions)
      .catch((e) => setError(e instanceof Error ? e.message : "Failed to load history"));
  }, []);

  return (
    <main className="max-w-2xl mx-auto p-10 flex flex-col gap-4">
      <h1 className="text-2xl font-bold">History</h1>
      {error && <p className="score-warn">{error}</p>}
      {sessions.length === 0 && !error && <p className="score-dim">No sessions yet.</p>}
      {sessions.map((session) => (
        <div key={session.id} className="score-card p-4">
          <div className="flex justify-between text-sm">
            <span className="font-semibold">{session.intent}</span>
            <span className="score-dim">
              {session.started_at ? new Date(session.started_at).toLocaleString() : "—"}
            </span>
          </div>
          <div className="flex gap-4 text-sm score-dim mt-1">
            <span>
              Completion:{" "}
              {session.completion_pct === null ? "—" : `${Math.round(session.completion_pct)}%`}
            </span>
            <span>Rating: {session.rating ?? "—"}</span>
          </div>
          {session.schedule && (
            <details className="mt-2">
              <summary className="cursor-pointer score-dim text-sm">Schedule</summary>
              <pre className="score-card mt-2 p-4 text-xs overflow-auto max-h-80">
                {JSON.stringify(session.schedule, null, 2)}
              </pre>
            </details>
          )}
        </div>
      ))}
    </main>
  );
}
