import * as Tone from "tone";

interface BinauralState {
  leftOscillator: Tone.Oscillator | null;
  rightOscillator: Tone.Oscillator | null;
  leftPanner: Tone.Panner | null;
  rightPanner: Tone.Panner | null;
  gainNode: Tone.Gain | null;
}

const state: BinauralState = {
  leftOscillator: null,
  rightOscillator: null,
  leftPanner: null,
  rightPanner: null,
  gainNode: null,
};

export async function startBinauralBeat(
  baseFreq: number,
  beatFreq: number,
  volume: number = 0.3,
): Promise<void> {
  await Tone.start();
  stopAll();

  // Left ear: base frequency
  // Right ear: base + beat frequency
  // User perceives the difference as the binaural beat
  const leftFreq = baseFreq;
  const rightFreq = baseFreq + beatFreq;

  state.gainNode = new Tone.Gain(volume).toDestination();

  state.leftPanner = new Tone.Panner(-1).connect(state.gainNode);
  state.rightPanner = new Tone.Panner(1).connect(state.gainNode);

  state.leftOscillator = new Tone.Oscillator(leftFreq, "sine").connect(state.leftPanner);
  state.rightOscillator = new Tone.Oscillator(rightFreq, "sine").connect(state.rightPanner);

  state.leftOscillator.start();
  state.rightOscillator.start();
}

export function updateBinauralBeat(
  baseFreq: number,
  beatFreq: number,
  rampDurationSec: number = 2,
): void {
  if (!state.leftOscillator || !state.rightOscillator) return;

  const now = Tone.now();
  state.leftOscillator.frequency.rampTo(baseFreq, rampDurationSec, now);
  state.rightOscillator.frequency.rampTo(baseFreq + beatFreq, rampDurationSec, now);
}

export function stopAll(): void {
  if (state.leftOscillator) {
    state.leftOscillator.stop();
    state.leftOscillator.dispose();
  }
  if (state.rightOscillator) {
    state.rightOscillator.stop();
    state.rightOscillator.dispose();
  }
  if (state.leftPanner) state.leftPanner.dispose();
  if (state.rightPanner) state.rightPanner.dispose();
  if (state.gainNode) state.gainNode.dispose();

  state.leftOscillator = null;
  state.rightOscillator = null;
  state.leftPanner = null;
  state.rightPanner = null;
  state.gainNode = null;
}
