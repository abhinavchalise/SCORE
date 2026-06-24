"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import FeedbackBar from "@/components/FeedbackBar";
import ParamEditor from "@/components/ParamEditor";
import RatingWidget from "@/components/RatingWidget";
import ScheduleViz from "@/components/ScheduleViz";
import { startBinauralBeat, stopAll, updateBinauralBeat } from "@/lib/synth";
import { SessionSocket } from "@/lib/wsClient";
import { useAppDispatch, useAppSelector } from "@/stores/hooks";
import {
  recordEdit,
  recordRating,
  recordSkip,
  sessionEnded,
  sessionFailed,
  sessionPaused,
  sessionResumed,
  sessionStarted,
  sessionStopped,
  setIntent,
  setLoading,
  stepChanged,
  tick,
} from "@/stores/sessionSlice";

const INTENTS = [
  { id: "deep_focus", label: "Deep Focus" },
  { id: "light_focus", label: "Light Focus" },
  { id: "creative_flow", label: "Creative Flow" },
  { id: "calm", label: "Calm" },
  { id: "sleep_aid", label: "Sleep" },
];

const CARRIER_FREQ = 200;
const START_VOLUME = 0.3;
const OVERRIDE_RAMP_SEC = 0.5;

export default function SessionPage() {
  const dispatch = useAppDispatch();
  const { phase, intent, schedule, currentStep, currentStepIndex, elapsedSec, rating, error } =
    useAppSelector((s) => s.session);

  const socketRef = useRef<SessionSocket | null>(null);
  const [durationMin, setDurationMin] = useState(25);
  const [override, setOverride] = useState<{ index: number; freq: number } | null>(null);

  const playing = phase === "playing" || phase === "fallback" || phase === "paused";

  useEffect(() => {
    return () => {
      stopAll();
      socketRef.current?.close();
    };
  }, []);

  useEffect(() => {
    if (!schedule || (phase !== "playing" && phase !== "fallback")) return;
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
  }, [elapsedSec, schedule, phase, currentStepIndex, dispatch]);

  const handleStart = useCallback(() => {
    dispatch(setLoading());
    const socket = new SessionSocket();
    socketRef.current = socket;
    socket.connect(intent, durationMin, {
      onSchedule: (sched, sessionId, usedFallback) => {
        void startBinauralBeat(CARRIER_FREQ, sched.steps[0].binaural_freq, START_VOLUME);
        dispatch(sessionStarted({ schedule: sched, sessionId, usedFallback }));
        setOverride(null);
      },
      onTick: (elapsed) => dispatch(tick(elapsed)),
      onEnded: (pct) => {
        stopAll();
        dispatch(sessionEnded(pct));
      },
      onError: () => dispatch(sessionFailed("Connection error")),
    });
  }, [dispatch, intent, durationMin]);

  const handlePauseToggle = useCallback(() => {
    const socket = socketRef.current;
    if (!socket) return;
    if (phase === "paused") {
      socket.sendControl("resume");
      dispatch(sessionResumed());
    } else {
      socket.sendControl("pause");
      dispatch(sessionPaused());
    }
  }, [dispatch, phase]);

  const handleStop = useCallback(() => {
    socketRef.current?.sendControl("stop");
    stopAll();
  }, []);

  const handleSkip = useCallback(() => {
    const socket = socketRef.current;
    if (!socket) return;
    socket.sendFeedback("skip", { elapsed_sec: elapsedSec });
    dispatch(recordSkip());
    socket.sendControl("stop");
    stopAll();
  }, [dispatch, elapsedSec]);

  const handleOverride = useCallback(
    (next: number) => {
      setOverride({ index: currentStepIndex, freq: next });
      updateBinauralBeat(CARRIER_FREQ, next, OVERRIDE_RAMP_SEC);
      socketRef.current?.sendFeedback("edit", {
        field: "binaural_freq",
        old: currentStep?.binaural_freq ?? null,
        new: next,
      });
      dispatch(recordEdit());
    },
    [dispatch, currentStep, currentStepIndex],
  );

  const handleRate = useCallback(
    (value: number) => {
      socketRef.current?.sendFeedback("rating", { value });
      dispatch(recordRating(value));
      socketRef.current?.close();
    },
    [dispatch],
  );

  useEffect(() => {
    const onKey = (event: KeyboardEvent) => {
      if (phase !== "playing" && phase !== "fallback" && phase !== "paused") return;
      if (event.code === "Space") {
        event.preventDefault();
        handlePauseToggle();
      } else if (event.code === "Escape") {
        handleStop();
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [phase, handlePauseToggle, handleStop]);

  return (
    <main className="max-w-2xl mx-auto p-10 flex flex-col gap-6">
      <h1 className="text-2xl font-bold">Session</h1>

      {phase === "idle" && (
        <div className="score-card p-6 flex flex-col gap-4">
          <label className="flex flex-col gap-2 text-sm">
            <span className="score-dim">Intent</span>
            <select
              className="score-input px-3 py-2"
              value={intent}
              onChange={(event) => dispatch(setIntent(event.target.value))}
            >
              {INTENTS.map((option) => (
                <option key={option.id} value={option.id}>
                  {option.label}
                </option>
              ))}
            </select>
          </label>
          <label className="flex flex-col gap-2 text-sm">
            <span className="score-dim">Duration (minutes)</span>
            <input
              className="score-input px-3 py-2"
              type="number"
              min={1}
              max={120}
              value={durationMin}
              onChange={(event) => setDurationMin(Number(event.target.value))}
            />
          </label>
          <button className="score-btn score-btn-accent px-6 py-3 self-start" onClick={handleStart}>
            Start session
          </button>
        </div>
      )}

      {phase === "generating" && <p className="score-dim">Generating schedule...</p>}

      {error && <p className="score-warn">{error}</p>}

      {playing && schedule && (
        <>
          <ScheduleViz
            schedule={schedule}
            currentStep={currentStep}
            currentStepIndex={currentStepIndex}
            elapsedSec={elapsedSec}
            carrierFreq={CARRIER_FREQ}
          />
          <ParamEditor
            value={
              override?.index === currentStepIndex
                ? override.freq
                : (currentStep?.binaural_freq ?? 10)
            }
            onChange={handleOverride}
          />
          <FeedbackBar
            paused={phase === "paused"}
            onPauseToggle={handlePauseToggle}
            onSkip={handleSkip}
            onStop={handleStop}
          />
          <p className="score-dim text-xs">Space: pause/resume · Esc: stop</p>
        </>
      )}

      {phase === "ended" && (
        <>
          {schedule && (
            <ScheduleViz
              schedule={schedule}
              currentStep={currentStep}
              currentStepIndex={currentStepIndex}
              elapsedSec={elapsedSec}
              carrierFreq={CARRIER_FREQ}
            />
          )}
          <RatingWidget rating={rating} onRate={handleRate} />
          <button
            className="score-btn px-4 py-2 self-start"
            onClick={() => dispatch(sessionStopped())}
          >
            New session
          </button>
        </>
      )}
    </main>
  );
}
