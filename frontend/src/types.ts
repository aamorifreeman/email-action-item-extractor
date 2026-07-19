// Types mirroring the backend Pydantic schemas.

export type Engine = "rule" | "gemini";

export interface TaskItem {
  task: string;
  source_sentence: string;
  people: string[];
  due_date_text: string | null;
  due_date_iso: string | null;
  priority: string;
  priority_score: number;
  confidence: number;
  engine: string;
}

export interface ExtractResponse {
  engine: string;
  count: number;
  items: TaskItem[];
  fallback_used: boolean;
  fallback_reason: string | null;
}

export interface AgreementReport {
  matched: number;
  rule_only: number;
  gemini_only: number;
  mean_similarity: number;
}

export interface CompareResponse {
  rule: TaskItem[];
  gemini: TaskItem[];
  agreement: AgreementReport;
  gemini_error: string | null;
}

export interface SavedTask extends TaskItem {
  id: string;
  status: string;
  created_at: string;
}

export interface BulkSaveResponse {
  added: number;
  skipped: number;
}
