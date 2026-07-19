import { useEffect, useState } from "react";
import { api } from "../api/client";
import TaskCard from "../components/TaskCard";
import type { SavedTask } from "../types";

export default function Tasks() {
  const [tasks, setTasks] = useState<SavedTask[]>([]);
  const [loading, setLoading] = useState(true);

  async function load() {
    setLoading(true);
    try {
      setTasks(await api.listTasks());
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  async function toggle(id: string) {
    await api.toggleTask(id);
    load();
  }

  async function remove(id: string) {
    await api.deleteTask(id);
    load();
  }

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-3xl font-bold text-white">Saved tasks</h1>
        <p className="mt-1 text-slate-400">
          Items saved from Extract, persisted in the database.
        </p>
      </header>

      {tasks.length > 0 && (
        <a
          href={api.csvUrl}
          className="inline-block rounded-lg border border-edge px-3 py-1.5 text-sm text-slate-200 hover:bg-white/5"
        >
          Export CSV
        </a>
      )}

      {loading ? (
        <div className="text-slate-500">Loading…</div>
      ) : tasks.length === 0 ? (
        <div className="rounded-xl border border-dashed border-edge p-6 text-center text-slate-500">
          No saved tasks yet. Extract an email and use “Save Task”.
        </div>
      ) : (
        <div className="space-y-3">
          {tasks.map((task) => (
            <TaskCard
              key={task.id}
              task={task}
              actions={
                <>
                  <button
                    onClick={() => toggle(task.id)}
                    className="rounded-lg border border-edge px-3 py-1.5 text-xs text-slate-300 hover:bg-white/5"
                  >
                    {task.status === "Done" ? "Mark active" : "Mark done"}
                  </button>
                  <button
                    onClick={() => remove(task.id)}
                    className="rounded-lg border border-edge px-3 py-1.5 text-xs text-rose-300 hover:bg-rose-500/10"
                  >
                    Delete
                  </button>
                </>
              }
            />
          ))}
        </div>
      )}
    </div>
  );
}
