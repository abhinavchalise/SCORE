import { describe, expect, it } from "vitest";
import reducer, {
  recordEdit,
  recordRating,
  recordSkip,
  sessionEnded,
  sessionStarted,
} from "@/stores/sessionSlice";

const schedule = {
  intent: "deep_focus",
  total_duration_sec: 1500,
  steps: [
    {
      timestamp_sec: 0,
      target_bpm: 70,
      binaural_freq: 10,
      ramp_duration_sec: 60,
      layer: "binaural",
    },
  ],
};

describe("sessionSlice", () => {
  it("enters playing on sessionStarted", () => {
    const state = reducer(
      undefined,
      sessionStarted({ schedule, sessionId: 1, usedFallback: false }),
    );
    expect(state.phase).toBe("playing");
    expect(state.currentStep).toEqual(schedule.steps[0]);
  });

  it("enters fallback when usedFallback", () => {
    const state = reducer(
      undefined,
      sessionStarted({ schedule, sessionId: 1, usedFallback: true }),
    );
    expect(state.phase).toBe("fallback");
  });

  it("tracks feedback counters", () => {
    let state = reducer(undefined, recordSkip());
    state = reducer(state, recordEdit());
    state = reducer(state, recordEdit());
    state = reducer(state, recordRating(5));
    expect(state.skipCount).toBe(1);
    expect(state.editCount).toBe(2);
    expect(state.rating).toBe(5);
  });

  it("captures completion on end", () => {
    const state = reducer(undefined, sessionEnded(87.5));
    expect(state.phase).toBe("ended");
    expect(state.completionPct).toBe(87.5);
  });
});
