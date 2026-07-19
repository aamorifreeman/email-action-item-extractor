import type { CompareResponse } from "../types";
import TaskCard from "./TaskCard";

export default function ComparePanel({ data }: { data: CompareResponse }) {
  const { rule, gemini, agreement, gemini_error } = data;

  return (
    <div className="space-y-5">
      <div className="grid grid-cols-4 gap-3">
        <Stat label="Matched" value={agreement.matched} />
        <Stat label="Rule only" value={agreement.rule_only} />
        <Stat label="Gemini only" value={agreement.gemini_only} />
        <Stat label="Mean similarity" value={agreement.mean_similarity.toFixed(2)} />
      </div>

      {gemini_error && (
        <div className="rounded-lg border border-amber-500/30 bg-amber-500/10 p-3 text-sm text-amber-200">
          Gemini unavailable — showing rule-based results only.
          <div className="mt-1 text-xs text-amber-300/70">{gemini_error}</div>
        </div>
      )}

      <div className="grid grid-cols-2 gap-5">
        <Column title="Rule-Based NLP" items={rule} />
        <Column title="Gemini AI" items={gemini} />
      </div>
    </div>
  );
}

function Stat({ label, value }: { label: string; value: number | string }) {
  return (
    <div className="rounded-xl border border-edge bg-panel/70 p-3 text-center">
      <div className="text-2xl font-semibold text-white">{value}</div>
      <div className="mt-1 text-xs text-slate-400">{label}</div>
    </div>
  );
}

function Column({ title, items }: { title: string; items: CompareResponse["rule"] }) {
  return (
    <div className="space-y-3">
      <div className="text-sm font-medium text-slate-300">
        {title} <span className="text-slate-500">({items.length})</span>
      </div>
      {items.length === 0 ? (
        <div className="rounded-lg border border-dashed border-edge p-4 text-sm text-slate-500">
          No items.
        </div>
      ) : (
        items.map((item, i) => <TaskCard key={i} task={item} />)
      )}
    </div>
  );
}
