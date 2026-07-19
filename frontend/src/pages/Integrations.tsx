import { useEffect, useState } from "react";
import { api } from "../api/client";
import type { SavedTask } from "../types";

export default function Integrations() {
  const [tasks, setTasks] = useState<SavedTask[]>([]);
  const [bulkUrl, setBulkUrl] = useState<string>("");

  useEffect(() => {
    api.listTasks().then(setTasks);
  }, []);

  async function buildCalendar() {
    if (!tasks.length) return;
    const { bulk_url } = await api.calendarLinks(tasks);
    setBulkUrl(bulk_url);
    window.open(bulk_url, "_blank");
  }

  return (
    <div className="space-y-8">
      <header>
        <h1 className="text-3xl font-bold text-white">Integrations</h1>
        <p className="mt-1 text-slate-400">
          Connect InboxIQ outputs to your tools.
        </p>
      </header>

      <Section title="Google Calendar" hint="Opens Google’s prefilled event composer.">
        <button
          onClick={buildCalendar}
          disabled={!tasks.length}
          className="rounded-lg bg-accent px-4 py-2 text-sm font-medium text-white hover:bg-indigo-500 disabled:opacity-50"
        >
          Add saved tasks to Calendar
        </button>
        {!tasks.length && (
          <p className="mt-2 text-xs text-slate-500">Save tasks first to enable this.</p>
        )}
        {bulkUrl && (
          <p className="mt-2 break-all text-xs text-slate-500">{bulkUrl}</p>
        )}
      </Section>

      <Section title="Export" hint="CSV includes task, due date, person, priority, confidence, status.">
        <a
          href={api.csvUrl}
          className="inline-block rounded-lg border border-edge px-4 py-2 text-sm text-slate-200 hover:bg-white/5"
        >
          Download saved tasks (CSV)
        </a>
      </Section>

      <Section title="Roadmap" hint="Coming next.">
        <div className="space-y-3">
          <Placeholder title="Google Tasks" body="Push saved items as Tasks with due dates (needs OAuth)." />
          <Placeholder title="Notion" body="Append rows to a database for team visibility." />
        </div>
      </Section>
    </div>
  );
}

function Section({
  title,
  hint,
  children,
}: {
  title: string;
  hint: string;
  children: React.ReactNode;
}) {
  return (
    <section className="rounded-2xl border border-edge bg-panel/40 p-6">
      <div className="text-lg font-semibold text-white">{title}</div>
      <div className="mb-4 mt-1 text-sm text-slate-400">{hint}</div>
      {children}
    </section>
  );
}

function Placeholder({ title, body }: { title: string; body: string }) {
  return (
    <div className="rounded-lg border border-dashed border-edge p-4">
      <div className="font-medium text-slate-200">{title}</div>
      <div className="mt-1 text-sm text-slate-500">{body}</div>
    </div>
  );
}
