// Typed fetch wrapper around the InboxIQ API. Defaults to relative /api (the
// Vite dev server proxies it to FastAPI); set VITE_API_BASE for a deployed
// backend on a different origin.

import type {
  BulkSaveResponse,
  CompareResponse,
  Engine,
  ExtractResponse,
  SavedTask,
  TaskItem,
} from "../types";

const API_BASE = import.meta.env.VITE_API_BASE ?? "/api";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    const detail = await res.text().catch(() => res.statusText);
    throw new Error(`${res.status}: ${detail}`);
  }
  return res.json() as Promise<T>;
}

export const api = {
  extract(email_text: string, engine: Engine) {
    return request<ExtractResponse>("/extract", {
      method: "POST",
      body: JSON.stringify({ email_text, engine }),
    });
  },

  compare(email_text: string) {
    return request<CompareResponse>("/extract/compare", {
      method: "POST",
      body: JSON.stringify({ email_text }),
    });
  },

  listTasks() {
    return request<SavedTask[]>("/tasks");
  },

  bulkSave(tasks: TaskItem[]) {
    return request<BulkSaveResponse>("/tasks/bulk", {
      method: "POST",
      body: JSON.stringify({ tasks }),
    });
  },

  toggleTask(id: string) {
    return request<SavedTask>(`/tasks/${id}/toggle`, { method: "POST" });
  },

  deleteTask(id: string) {
    return fetch(`${API_BASE}/tasks/${id}`, { method: "DELETE" });
  },

  async calendarLinks(tasks: TaskItem[]) {
    return request<{ bulk_url: string; item_urls: string[] }>(
      "/integrations/calendar-link",
      { method: "POST", body: JSON.stringify({ tasks }) }
    );
  },

  csvUrl: `${API_BASE}/tasks/export.csv`,
};
