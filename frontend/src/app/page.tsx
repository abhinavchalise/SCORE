import Link from "next/link";

export default function Home() {
  return (
    <main className="max-w-2xl mx-auto p-10">
      <h1 className="text-3xl font-bold mb-4">SCORE</h1>
      <p className="score-dim mb-8">
        Tell SCORE how you want to focus. It composes a binaural-beat schedule on-device and plays
        it in the browser. No cloud, no telemetry.
      </p>
      <Link href="/session" className="score-btn score-btn-accent inline-block px-6 py-3">
        Start a session
      </Link>
    </main>
  );
}
