import type { Engine } from "../types";

const options: { value: Engine; label: string }[] = [
  { value: "rule", label: "Rule-Based NLP" },
  { value: "gemini", label: "Gemini AI" },
];

export default function EngineToggle({
  value,
  onChange,
  disabled,
}: {
  value: Engine;
  onChange: (e: Engine) => void;
  disabled?: boolean;
}) {
  return (
    <div className="inline-flex rounded-lg border border-edge bg-panel p-1">
      {options.map((opt) => (
        <button
          key={opt.value}
          disabled={disabled}
          onClick={() => onChange(opt.value)}
          className={`rounded-md px-4 py-1.5 text-sm transition ${
            value === opt.value
              ? "bg-accent text-white"
              : "text-slate-400 hover:text-slate-200"
          }`}
        >
          {opt.label}
        </button>
      ))}
    </div>
  );
}
