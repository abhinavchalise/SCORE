"use client";

import { useRef, useEffect, useCallback } from "react";
import { startSession } from "@/lib/api";
import { startBinauralBeat, updateBinauralBeat, stopAll } from "@/lib/synth";
import { useAppDispatch, useAppSelector } from "@/stores/hooks";
import {
  setIntent,
  setLoading,
  sessionStarted,
  sessionFailed,
  sessionStopped,
  tick,
  stepChanged,
} from "@/stores/sessionSlice";

const INTENTS = [
  { id: "deep_focus", label: "Deep Focus" },
  { id: "light_focus", label: "Light Focus" },
  { id: "creative_flow", label: "Creative Flow" },
  { id: "calm", label: "Calm" },
  { id: "sleep_aid", label: "Sleep" },
];

const CARRIER_FREQ = 200; // Hz, base carrier for binaural beats
const SESSION_DURATION_MIN = 25;
const START_VOLUME = 0.3;

export default function Home() {
  const dispatch = useAppDispatch();
  const {
    status,
    intent: selectedIntent,
    schedule,
    currentStep,
    currentStepIndex,
    elapsedSec,
    error,
    latencyMs,
  } = useAppSelector((s) => s.session);

  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const startTimeRef = useRef<number>(0);

  useEffect(() => {
    return () => {
      stopAll();
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, []);

  // Step scheduler: when elapsed time crosses a step's timestamp, update audio
  useEffect(() => {
    if (!schedule || status !== "playing") return;

    const steps = schedule.steps;
    for (let i = steps.length - 1; i >= 0; i--) {
      if (elapsedSec >= steps[i].timestamp_sec) {
        if (i !== currentStepIndex) {
          dispatch(stepChanged({ step: steps[i], index: i }));
          updateBinauralBeat(CARRIER_FREQ, steps[i].binaural_freq, steps[i].ramp_duration_sec);
        }
        break;
      }
    }
  }, [elapsedSec, schedule, status, currentStepIndex, dispatch]);

  const handleStart = useCallback(async () => {
    dispatch(setLoading());
    const t0 = performance.now();

    try {
      const res = await startSession(selectedIntent, SESSION_DURATION_MIN);
      const t1 = performance.now();
      const latency = Math.round(t1 - t0);

      const sched = res.data.schedule;
      dispatch(sessionStarted({ schedule: sched, latencyMs: latency }));

      // Start audio with first step's parameters
      await startBinauralBeat(CARRIER_FREQ, sched.steps[0].binaural_freq, START_VOLUME);

      startTimeRef.current = Date.now();

      timerRef.current = setInterval(() => {
        dispatch(tick(Math.floor((Date.now() - startTimeRef.current) / 1000)));
      }, 1000);
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : "Unknown error";
      dispatch(sessionFailed(msg));
    }
  }, [selectedIntent, dispatch]);

  const handleStop = useCallback(() => {
    stopAll();
    if (timerRef.current) clearInterval(timerRef.current);
    dispatch(sessionStopped());
  }, [dispatch]);

  return (
    <main className="max-w-2xl mx-auto p-10 font-mono text-white bg-black min-h-screen">
      <h1 className="text-3xl font-bold mb-8">SCORE</h1>

      {/* Intent selector */}
      <div className="mb-6">
        <label className="text-zinc-400 mr-2">Intent:</label>
        <select
          value={selectedIntent}
          onChange={(e) => dispatch(setIntent(e.target.value))}
          disabled={status !== "idle"}
          className="bg-zinc-900 border border-zinc-700 rounded px-3 py-1.5 text-white"
        >
          {INTENTS.map((i) => (
            <option key={i.id} value={i.id}>
              {i.label}
            </option>
          ))}
        </select>
      </div>

      <div className="mb-6">
        {status === "idle" && (
          <button
            onClick={handleStart}
            className="bg-emerald-600 hover:bg-emerald-500 text-white px-6 py-2 rounded font-medium transition-colors"
          >
            Start Session
          </button>
        )}
        {status === "loading" && (
          <p className="text-yellow-400 animate-pulse">Generating schedule...</p>
        )}
        {status === "playing" && (
          <button
            onClick={handleStop}
            className="bg-red-600 hover:bg-red-500 text-white px-6 py-2 rounded font-medium transition-colors"
          >
            Stop
          </button>
        )}
      </div>

      {error && <p className="text-red-400 mb-4">Error: {error}</p>}

      {latencyMs !== null && (
        <p className="mb-4 text-zinc-400">
          Generated in <span className="font-bold text-white">{latencyMs}ms</span>
        </p>
      )}

      {/* Current parameters */}
      {currentStep && status === "playing" && (
        <div className="mt-6 p-4 border border-zinc-700 rounded-lg bg-zinc-900">
          <h3 className="text-lg font-semibold mb-3">Now Playing</h3>
          <div className="grid grid-cols-2 gap-2 text-sm">
            <p className="text-zinc-400">Elapsed:</p>
            <p>
              {elapsedSec}s / {schedule?.total_duration_sec}s
            </p>
            <p className="text-zinc-400">Step:</p>
            <p>
              {currentStepIndex + 1} / {schedule?.steps.length}
            </p>
            <p className="text-zinc-400">Binaural Freq:</p>
            <p className="text-emerald-400 font-bold">{currentStep.binaural_freq} Hz</p>
            <p className="text-zinc-400">Target BPM:</p>
            <p>{currentStep.target_bpm}</p>
            <p className="text-zinc-400">Ramp Duration:</p>
            <p>{currentStep.ramp_duration_sec}s</p>
            <p className="text-zinc-400">Carrier:</p>
            <p>
              {CARRIER_FREQ} Hz L / {CARRIER_FREQ + currentStep.binaural_freq} Hz R
            </p>
          </div>
        </div>
      )}

      {schedule && (
        <details className="mt-6">
          <summary className="cursor-pointer text-zinc-400 hover:text-white transition-colors">
            Full Schedule JSON
          </summary>
          <pre className="mt-2 text-xs bg-zinc-900 p-4 rounded overflow-auto max-h-80 border border-zinc-800">
            {JSON.stringify(schedule, null, 2)}
          </pre>
        </details>
      )}
    </main>
  );
}
