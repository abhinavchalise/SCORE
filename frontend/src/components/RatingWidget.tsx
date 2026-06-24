"use client";

interface Props {
  rating: number | null;
  onRate: (value: number) => void;
}

const VALUES = [1, 2, 3, 4, 5];

export default function RatingWidget({ rating, onRate }: Props) {
  return (
    <div className="score-card p-6">
      <h3 className="text-lg font-semibold mb-3">Rate this session</h3>
      <div className="flex gap-2">
        {VALUES.map((value) => (
          <button
            key={value}
            className={`score-btn px-4 py-2 ${rating === value ? "score-btn-accent" : ""}`}
            onClick={() => onRate(value)}
          >
            {value}
          </button>
        ))}
      </div>
    </div>
  );
}
