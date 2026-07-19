import { useState } from "react";
import { api } from "../api/client";
import EngineToggle from "../components/EngineToggle";
import ComparePanel from "../components/ComparePanel";
import TaskCard from "../components/TaskCard";
import type { CompareResponse, Engine, ExtractResponse, TaskItem } from "../types";

const SAMPLE =
  "Hey team, can you send the final slides to Marcus by Friday, " +
  "follow up with Jasmine next week, and review the budget before the meeting? " +
  "This is important and should be done ASAP.";

export default function Extract() {
  const [email, setEmail] = useState("");
  const [engine, setEngine] = useState<Engine>("rule");
  const [compareMode, setCompareMode] = useState(false);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<ExtractResponse | null>(null);
  const [compare, setCompare] = useState<CompareResponse | null>(null);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  async function run() {
    if (!email.trim()) return;
    setLoading(true);
    setError("");
    setNotice("");
    setResult(null);
    setCompare(null);
    try {
      if (compareMode) {
        setCompare(await api.compare(email));
      } else {
        setResult(await api.extract(email, engine));
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Extraction failed");
    } finally {
      setLoading(false);
    }
  }

  async function saveAll(items: TaskItem[]) {
    const res = await api.bulkSave(items);
    setNotice(`Saved ${res.added} task(s); skipped ${res.skipped} duplicate(s).`);
  }

  async function openCalendar(items: TaskItem[]) {
    const { bulk_url } = await api.calendarLinks(items);
    window.open(bulk_url, "_blank");
  }

  return (
    <div className="space-y-8">
      <header>
        <div className="inline-block rounded-full bg-accent/20 px-3 py-1 text-xs text-indigo-300">
          NLP extraction
        </div>
        <h1 className="mt-3 text-4xl font-bold tracking-tight text-white">InboxIQ</h1>
        <p className="mt-2 max-w-2xl text-slate-400">
          Paste a message and InboxIQ surfaces tasks, deadlines, people, and urgency —
          with confidence scores and resolved dates.
        </p>
      </header>

      <section className="space-y-4 rounded-2xl border border-edge bg-panel/40 p-6">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <EngineToggle value={engine} onChange={setEngine} disabled={compareMode} />
          <label className="flex items-center gap-2 text-sm text-slate-400">
            <input
              type="checkbox"
              checked={compareMode}
              onChange={(e) => setCompareMode(e.target.checked)}
              className="accent-indigo-500"
            />
            Compare both engines
          </label>
        </div>

        <textarea
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          placeholder="Paste a full email or thread here…"
          className="h-56 w-full resize-none rounded-xl border border-edge bg-ink/60 p-4 text-sm text-slate-200 outline-none focus:border-accent"
        />

        <div className="flex gap-3">
          <button
            onClick={run}
            disabled={loading || !email.trim()}
            className="rounded-lg bg-accent px-5 py-2 text-sm font-medium text-white transition hover:bg-indigo-500 disabled:opacity-50"
          >
            {loading ? "Extracting…" : "Extract action items"}
          </button>
          <button
            onClick={() => setEmail(SAMPLE)}
            className="rounded-lg border border-edge px-4 py-2 text-sm text-slate-300 hover:bg-white/5"
          >
            Use sample
          </button>
        </div>
      </section>

      {error && (
        <div className="rounded-lg border border-rose-500/30 bg-rose-500/10 p-3 text-sm text-rose-200">
          {error}
        </div>
      )}
      {notice && (
        <div className="rounded-lg border border-emerald-500/30 bg-emerald-500/10 p-3 text-sm text-emerald-200">
          {notice}
        </div>
      )}

      {compare && <ComparePanel data={compare} />}

      {result && (
        <section className="space-y-4">
          {result.fallback_used && (
            <div className="rounded-lg border border-amber-500/30 bg-amber-500/10 p-3 text-sm text-amber-200">
              Gemini failed — used rule-based NLP instead.
              <div className="mt-1 text-xs text-amber-300/70">{result.fallback_reason}</div>
            </div>
          )}

          <div className="flex items-center justify-between">
            <div className="text-sm text-slate-400">
              {result.count} item(s) · engine: {result.engine}
            </div>
            {result.items.length > 0 && (
              <div className="flex gap-2">
                <button
                  onClick={() => saveAll(result.items)}
                  className="rounded-lg border border-edge px-3 py-1.5 text-sm text-slate-200 hover:bg-white/5"
                >
                  Save all to Tasks
                </button>
                <button
                  onClick={() => openCalendar(result.items)}
                  className="rounded-lg border border-edge px-3 py-1.5 text-sm text-slate-200 hover:bg-white/5"
                >
                  Add all to Calendar
                </button>
              </div>
            )}
          </div>

          {result.items.length === 0 ? (
            <div className="rounded-xl border border-dashed border-edge p-6 text-center text-slate-500">
              No action items detected.
            </div>
          ) : (
            result.items.map((item, i) => (
              <TaskCard
                key={i}
                task={item}
                actions={
                  <button
                    onClick={() => saveAll([item])}
                    className="rounded-lg border border-edge px-3 py-1.5 text-xs text-slate-300 hover:bg-white/5"
                  >
                    Save Task
                  </button>
                }
              />
            ))
          )}
        </section>
      )}
    </div>
  );
}
