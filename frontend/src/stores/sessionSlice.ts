import { createSlice, PayloadAction } from "@reduxjs/toolkit";
import { ModulationSchedule, ModulationStep } from "@/lib/api";

interface SessionState {
  status: "idle" | "loading" | "playing";
  intent: string;
  schedule: ModulationSchedule | null;
  currentStep: ModulationStep | null;
  currentStepIndex: number;
  elapsedSec: number;
  error: string | null;
  latencyMs: number | null;
}

const initialState: SessionState = {
  status: "idle",
  intent: "Deep Focus - Coding",
  schedule: null,
  currentStep: null,
  currentStepIndex: 0,
  elapsedSec: 0,
  error: null,
  latencyMs: null,
};

const sessionSlice = createSlice({
  name: "session",
  initialState,
  reducers: {
    setIntent(state, action: PayloadAction<string>) {
      state.intent = action.payload;
    },
    setLoading(state) {
      state.status = "loading";
      state.error = null;
    },
    sessionStarted(
      state,
      action: PayloadAction<{ schedule: ModulationSchedule; latencyMs: number }>,
    ) {
      state.status = "playing";
      state.schedule = action.payload.schedule;
      state.currentStep = action.payload.schedule.steps[0];
      state.currentStepIndex = 0;
      state.latencyMs = action.payload.latencyMs;
      state.elapsedSec = 0;
    },
    sessionFailed(state, action: PayloadAction<string>) {
      state.status = "idle";
      state.error = action.payload;
    },
    sessionStopped(state) {
      state.status = "idle";
      state.elapsedSec = 0;
      state.schedule = null;
      state.currentStep = null;
      state.currentStepIndex = 0;
    },
    tick(state, action: PayloadAction<number>) {
      state.elapsedSec = action.payload;
    },
    stepChanged(state, action: PayloadAction<{ step: ModulationStep; index: number }>) {
      state.currentStep = action.payload.step;
      state.currentStepIndex = action.payload.index;
    },
  },
});

export const {
  setIntent,
  setLoading,
  sessionStarted,
  sessionFailed,
  sessionStopped,
  tick,
  stepChanged,
} = sessionSlice.actions;

export default sessionSlice.reducer;
