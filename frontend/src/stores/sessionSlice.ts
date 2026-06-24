import { createSlice, PayloadAction } from "@reduxjs/toolkit";
import { ModulationSchedule, ModulationStep } from "@/lib/api";

export type SessionPhase = "idle" | "generating" | "playing" | "fallback" | "paused" | "ended";

interface SessionState {
  phase: SessionPhase;
  intent: string;
  sessionId: number | null;
  schedule: ModulationSchedule | null;
  currentStep: ModulationStep | null;
  currentStepIndex: number;
  elapsedSec: number;
  completionPct: number | null;
  usedFallback: boolean;
  editCount: number;
  skipCount: number;
  rating: number | null;
  error: string | null;
}

const initialState: SessionState = {
  phase: "idle",
  intent: "deep_focus",
  sessionId: null,
  schedule: null,
  currentStep: null,
  currentStepIndex: 0,
  elapsedSec: 0,
  completionPct: null,
  usedFallback: false,
  editCount: 0,
  skipCount: 0,
  rating: null,
  error: null,
};

const sessionSlice = createSlice({
  name: "session",
  initialState,
  reducers: {
    setIntent(state, action: PayloadAction<string>) {
      state.intent = action.payload;
    },
    setLoading(state) {
      state.phase = "generating";
      state.error = null;
      state.elapsedSec = 0;
      state.completionPct = null;
      state.editCount = 0;
      state.skipCount = 0;
      state.rating = null;
    },
    sessionStarted(
      state,
      action: PayloadAction<{
        schedule: ModulationSchedule;
        sessionId: number;
        usedFallback: boolean;
      }>,
    ) {
      state.phase = action.payload.usedFallback ? "fallback" : "playing";
      state.schedule = action.payload.schedule;
      state.sessionId = action.payload.sessionId;
      state.usedFallback = action.payload.usedFallback;
      state.currentStep = action.payload.schedule.steps[0];
      state.currentStepIndex = 0;
      state.elapsedSec = 0;
    },
    sessionFailed(state, action: PayloadAction<string>) {
      state.phase = "idle";
      state.error = action.payload;
    },
    sessionStopped(state) {
      return { ...initialState, intent: state.intent };
    },
    sessionPaused(state) {
      state.phase = "paused";
    },
    sessionResumed(state) {
      state.phase = state.usedFallback ? "fallback" : "playing";
    },
    sessionEnded(state, action: PayloadAction<number>) {
      state.phase = "ended";
      state.completionPct = action.payload;
    },
    tick(state, action: PayloadAction<number>) {
      state.elapsedSec = action.payload;
    },
    stepChanged(state, action: PayloadAction<{ step: ModulationStep; index: number }>) {
      state.currentStep = action.payload.step;
      state.currentStepIndex = action.payload.index;
    },
    recordSkip(state) {
      state.skipCount += 1;
    },
    recordEdit(state) {
      state.editCount += 1;
    },
    recordRating(state, action: PayloadAction<number>) {
      state.rating = action.payload;
    },
    setCompletion(state, action: PayloadAction<number>) {
      state.completionPct = action.payload;
    },
  },
});

export const {
  setIntent,
  setLoading,
  sessionStarted,
  sessionFailed,
  sessionStopped,
  sessionPaused,
  sessionResumed,
  sessionEnded,
  tick,
  stepChanged,
  recordSkip,
  recordEdit,
  recordRating,
  setCompletion,
} = sessionSlice.actions;

export default sessionSlice.reducer;
