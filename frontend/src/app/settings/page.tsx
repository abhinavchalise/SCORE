"use client";

import Link from "next/link";
import { useAppSelector } from "@/stores/hooks";

const MODEL_ID = "Qwen/Qwen3-8B · 8-bit · on-device";

export default function SettingsPage() {
  const { user, status } = useAppSelector((s) => s.auth);

  return (
    <main className="max-w-2xl mx-auto p-10 flex flex-col gap-6">
      <h1 className="text-2xl font-bold">Settings</h1>

      <section className="score-card p-6">
        <h2 className="text-lg font-semibold mb-3">Account</h2>
        {status === "authenticated" && user ? (
          <div className="grid grid-cols-2 gap-2 text-sm">
            <span className="score-dim">Username</span>
            <span>{user.username}</span>
            <span className="score-dim">Email</span>
            <span>{user.email}</span>
          </div>
        ) : (
          <p className="score-dim text-sm">
            Not signed in.{" "}
            <Link href="/login" className="score-link">
              Log in
            </Link>
          </p>
        )}
      </section>

      <section className="score-card p-6">
        <h2 className="text-lg font-semibold mb-3">Model</h2>
        <div className="grid grid-cols-2 gap-2 text-sm">
          <span className="score-dim">Inference</span>
          <span>{MODEL_ID}</span>
          <span className="score-dim">Privacy</span>
          <span>On-device only. No cloud, no telemetry.</span>
        </div>
      </section>
    </main>
  );
}
