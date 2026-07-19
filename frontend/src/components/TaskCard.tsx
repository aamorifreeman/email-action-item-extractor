import type { SavedTask, TaskItem } from "../types";
import ConfidenceBar from "./ConfidenceBar";

interface Props {
  task: TaskItem | SavedTask;
  actions?: React.ReactNode;
}

function isSaved(t: TaskItem | SavedTask): t is SavedTask {
  return "status" in t;
}

export default function TaskCard({ task, actions }: Props) {
  const due = task.due_date_iso || task.due_date_text || "No due date";
  const people = task.people.length ? task.people.join(", ") : "No person";
  const high = task.priority === "High";

  return (
    <div className="rounded-xl border border-edge bg-panel/70 p-4">
      <div className="flex items-start justify-between gap-4">
        <div className="font-medium text-white">{task.task}</div>
        <ConfidenceBar value={task.confidence} />
      </div>

      <div className="mt-3 flex flex-wrap items-center gap-2 text-xs">
        <span className="rounded-full bg-white/5 px-2.5 py-1 text-slate-300">📅 {due}</span>
        <span className="rounded-full bg-white/5 px-2.5 py-1 text-slate-300">👤 {people}</span>
        <span
          className={`rounded-full px-2.5 py-1 ${
            high ? "bg-rose-500/20 text-rose-300" : "bg-white/5 text-slate-400"
          }`}
        >
          {high ? "⚡ High" : "○ Normal"}
        </span>
        <span className="rounded-full bg-indigo-500/10 px-2.5 py-1 text-indigo-300">
          {task.engine}
        </span>
        {isSaved(task) && (
          <span className="rounded-full bg-white/5 px-2.5 py-1 text-slate-300">
            {task.status === "Done" ? "✓ Done" : "○ To Do"}
          </span>
        )}
      </div>

      {actions && <div className="mt-3 flex gap-2">{actions}</div>}
    </div>
  );
}
