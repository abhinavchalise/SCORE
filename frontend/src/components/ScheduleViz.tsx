"use client";

import { ModulationSchedule, ModulationStep } from "@/lib/api";

interface Props {
  schedule: ModulationSchedule;
  currentStep: ModulationStep | null;
  currentStepIndex: number;
  elapsedSec: number;
  carrierFreq: number;
}

export default function ScheduleViz({
  schedule,
  currentStep,
  currentStepIndex,
  elapsedSec,
  carrierFreq,
}: Props) {
  return (
    <div className="score-card p-6">
      <h3 className="text-lg font-semibold mb-4">Now playing</h3>
      {currentStep && (
        <div className="grid grid-cols-2 gap-2 text-sm">
          <span className="score-dim">Elapsed</span>
          <span>
            {elapsedSec}s / {schedule.total_duration_sec}s
          </span>
          <span className="score-dim">Step</span>
          <span>
            {currentStepIndex + 1} / {schedule.steps.length}
          </span>
          <span className="score-dim">Binaural freq</span>
          <span>{currentStep.binaural_freq} Hz</span>
          <span className="score-dim">Target BPM</span>
          <span>{currentStep.target_bpm}</span>
          <span className="score-dim">Ramp</span>
          <span>{currentStep.ramp_duration_sec}s</span>
          <span className="score-dim">Carrier</span>
          <span>
            {carrierFreq} Hz L / {carrierFreq + currentStep.binaural_freq} Hz R
          </span>
        </div>
      )}
      <details className="mt-4">
        <summary className="cursor-pointer score-dim text-sm">Full schedule JSON</summary>
        <pre className="score-card mt-2 p-4 text-xs overflow-auto max-h-80">
          {JSON.stringify(schedule, null, 2)}
        </pre>
      </details>
    </div>
  );
}
