"use client";

interface Props {
  value: number;
  onChange: (next: number) => void;
}

export default function ParamEditor({ value, onChange }: Props) {
  return (
    <div className="score-card p-6">
      <label className="flex flex-col gap-2 text-sm">
        <span className="score-dim">Binaural frequency override: {value.toFixed(1)} Hz</span>
        <input
          type="range"
          min={0.5}
          max={40}
          step={0.5}
          value={value}
          onChange={(event) => onChange(Number(event.target.value))}
        />
      </label>
    </div>
  );
}
