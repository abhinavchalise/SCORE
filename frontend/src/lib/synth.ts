import * as Tone from "tone";

interface BinauralState {
  leftOsc: Tone.Oscillator | null;
  rightOsc: Tone.Oscillator | null;
  leftPanner: Tone.Panner | null;
  rightPanner: Tone.Panner | null;
  gainNode: Tone.Gain | null;
}

const state: BinauralState = {
  leftOsc: null,
  rightOsc: null,
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

  state.leftOsc = new Tone.Oscillator(leftFreq, "sine").connect(state.leftPanner);
  state.rightOsc = new Tone.Oscillator(rightFreq, "sine").connect(state.rightPanner);

  state.leftOsc.start();
  state.rightOsc.start();
}

export function updateBinauralBeat(
  baseFreq: number,
  beatFreq: number,
  rampTimeSec: number = 2,
): void {
  if (!state.leftOsc || !state.rightOsc) return;

  const now = Tone.now();
  state.leftOsc.frequency.rampTo(baseFreq, rampTimeSec, now);
  state.rightOsc.frequency.rampTo(baseFreq + beatFreq, rampTimeSec, now);
}

export function stopAll(): void {
  if (state.leftOsc) {
    state.leftOsc.stop();
    state.leftOsc.dispose();
  }
  if (state.rightOsc) {
    state.rightOsc.stop();
    state.rightOsc.dispose();
  }
  if (state.leftPanner) state.leftPanner.dispose();
  if (state.rightPanner) state.rightPanner.dispose();
  if (state.gainNode) state.gainNode.dispose();

  state.leftOsc = null;
  state.rightOsc = null;
  state.leftPanner = null;
  state.rightPanner = null;
  state.gainNode = null;
}
