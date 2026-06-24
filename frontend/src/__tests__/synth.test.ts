import * as Tone from "tone";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { startBinauralBeat, stopAll, updateBinauralBeat } from "@/lib/synth";

vi.mock("tone", () => {
  const registry = {
    oscillators: [] as MockOscillator[],
    panners: [] as MockPanner[],
    gains: [] as MockGain[],
  };

  class MockSignal {
    rampTo = vi.fn();
  }
  class MockOscillator {
    frequency = new MockSignal();
    started = false;
    stopped = false;
    disposed = false;
    constructor(
      public freq: number,
      public type: string,
    ) {
      registry.oscillators.push(this);
    }
    connect() {
      return this;
    }
    start() {
      this.started = true;
      return this;
    }
    stop() {
      this.stopped = true;
      return this;
    }
    dispose() {
      this.disposed = true;
      return this;
    }
  }
  class MockPanner {
    disposed = false;
    constructor(public pan: number) {
      registry.panners.push(this);
    }
    connect() {
      return this;
    }
    dispose() {
      this.disposed = true;
    }
  }
  class MockGain {
    disposed = false;
    constructor(public gain: number) {
      registry.gains.push(this);
    }
    toDestination() {
      return this;
    }
    dispose() {
      this.disposed = true;
    }
  }

  return {
    __registry: registry,
    start: vi.fn(async () => {}),
    now: vi.fn(() => 0),
    Gain: MockGain,
    Panner: MockPanner,
    Oscillator: MockOscillator,
  };
});

type OscNode = {
  freq: number;
  started: boolean;
  stopped: boolean;
  disposed: boolean;
  frequency: { rampTo: ReturnType<typeof vi.fn> };
};
type Registry = {
  oscillators: OscNode[];
  panners: Array<{ pan: number; disposed: boolean }>;
  gains: Array<{ gain: number; disposed: boolean }>;
};

const registry = (Tone as unknown as { __registry: Registry }).__registry;

beforeEach(() => {
  stopAll();
  registry.oscillators.length = 0;
  registry.panners.length = 0;
  registry.gains.length = 0;
  vi.clearAllMocks();
});

describe("synth", () => {
  it("starts two oscillators at base and base+beat", async () => {
    await startBinauralBeat(100, 10, 0.3);

    expect(Tone.start).toHaveBeenCalledOnce();
    expect(registry.oscillators).toHaveLength(2);
    expect(registry.oscillators[0].freq).toBe(100);
    expect(registry.oscillators[1].freq).toBe(110);
    expect(registry.oscillators.every((osc) => osc.started)).toBe(true);
    expect(registry.gains[0].gain).toBe(0.3);
    expect(registry.panners.map((panner) => panner.pan)).toEqual([-1, 1]);
  });

  it("ramps both oscillator frequencies on update", async () => {
    await startBinauralBeat(100, 10);
    const [left, right] = registry.oscillators;

    updateBinauralBeat(200, 20, 3);

    expect(left.frequency.rampTo).toHaveBeenCalledWith(200, 3, 0);
    expect(right.frequency.rampTo).toHaveBeenCalledWith(220, 3, 0);
  });

  it("no-ops update when nothing is playing", () => {
    expect(() => updateBinauralBeat(200, 20, 3)).not.toThrow();
    expect(registry.oscillators).toHaveLength(0);
  });

  it("stops and disposes every node, idempotently", async () => {
    await startBinauralBeat(100, 10);
    const nodes = [...registry.oscillators];

    stopAll();

    expect(nodes.every((osc) => osc.stopped && osc.disposed)).toBe(true);
    expect(registry.panners.every((panner) => panner.disposed)).toBe(true);
    expect(registry.gains.every((gain) => gain.disposed)).toBe(true);
    expect(() => stopAll()).not.toThrow();
  });
});
