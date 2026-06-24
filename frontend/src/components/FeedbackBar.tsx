"use client";

interface Props {
  paused: boolean;
  onPauseToggle: () => void;
  onSkip: () => void;
  onStop: () => void;
}

export default function FeedbackBar({ paused, onPauseToggle, onSkip, onStop }: Props) {
  return (
    <div className="flex gap-3">
      <button className="score-btn px-4 py-2" onClick={onPauseToggle}>
        {paused ? "Resume" : "Pause"}
      </button>
      <button className="score-btn px-4 py-2" onClick={onSkip}>
        Skip
      </button>
      <button className="score-btn score-btn-warn px-4 py-2" onClick={onStop}>
        Stop
      </button>
    </div>
  );
}
