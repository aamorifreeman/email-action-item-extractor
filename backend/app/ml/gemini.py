"""Gemini extraction engine with structured JSON output.

Ported from the original Streamlit app, with Streamlit/secrets handling
removed. Upgraded to request structured output via a response schema instead
of prompt-only JSON plus regex scraping. Retries transient failures and falls
back across candidate models. Raising on failure is intentional — the
extraction service decides whether to fall back to the rule engine.
"""

from __future__ import annotations

import json
import re
import time

from pydantic import BaseModel

from app.config import get_settings
from app.ml.base import Extractor, TaskItem


class _GeminiTask(BaseModel):
    """Response schema handed to Gemini for structured decoding."""

    task: str
    due_date: str | None = None
    people: list[str] = []
    source_sentence: str = ""


_PROMPT = """You are an information extraction assistant.
Extract every action item from the email below.

Rules:
1) Split multiple tasks into separate objects.
2) Extract due dates or deadline phrases when present (keep the human phrasing).
3) Extract names of people mentioned in each task.
4) source_sentence must be the sentence from the email the task came from.

Email:
\"\"\"
{email}
\"\"\"
"""


def _get_api_key() -> str:
    key = get_settings().gemini_api_key.strip()
    if not key:
        raise RuntimeError(
            "GEMINI_API_KEY is not set. Add it to your environment or .env file."
        )
    return key


def _parse_json(text: str) -> object:
    """Parse model output as JSON, tolerating markdown fences."""
    text = (text or "").strip()
    if not text:
        raise ValueError("Gemini returned an empty response.")
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    fenced = re.search(r"```(?:json)?\s*(.*?)\s*```", text, re.DOTALL | re.IGNORECASE)
    if fenced:
        try:
            return json.loads(fenced.group(1).strip())
        except json.JSONDecodeError:
            pass
    for pattern in (r"(\[.*\])", r"(\{.*\})"):
        m = re.search(pattern, text, re.DOTALL)
        if m:
            try:
                return json.loads(m.group(1).strip())
            except json.JSONDecodeError:
                continue
    raise ValueError("Could not parse valid JSON from Gemini response.")


def _to_task_items(raw: object) -> list[TaskItem]:
    if not isinstance(raw, list):
        raise ValueError("Gemini output must be a JSON array.")
    items: list[TaskItem] = []
    for entry in raw:
        if not isinstance(entry, dict):
            continue
        task = str(entry.get("task", "")).strip()
        if not task:
            continue
        due = entry.get("due_date")
        due_text = str(due).strip() if due not in (None, "") else None
        people_raw = entry.get("people", [])
        people = (
            [str(p).strip() for p in people_raw if str(p).strip()]
            if isinstance(people_raw, list)
            else []
        )
        source = str(entry.get("source_sentence", "")).strip() or task
        items.append(
            TaskItem(
                task=task,
                source_sentence=source,
                people=people,
                due_date_text=due_text,
                engine="gemini",
            )
        )
    return items


class GeminiExtractor(Extractor):
    name = "gemini"

    def extract(self, email_text: str) -> list[TaskItem]:
        if not email_text or not email_text.strip():
            return []

        from google import genai

        client = genai.Client(api_key=_get_api_key())
        prompt = _PROMPT.format(email=email_text)

        last_error: Exception | None = None
        for model_name in get_settings().gemini_model_list:
            for attempt in range(3):
                try:
                    response = client.models.generate_content(
                        model=model_name,
                        contents=prompt,
                        config={
                            "response_mime_type": "application/json",
                            "response_schema": list[_GeminiTask],
                        },
                    )
                    parsed = getattr(response, "parsed", None)
                    if parsed:
                        raw = [
                            p.model_dump() if isinstance(p, _GeminiTask) else p
                            for p in parsed
                        ]
                    else:
                        raw = _parse_json(response.text)
                    return _to_task_items(raw)
                except Exception as exc:  # transient or parse failure
                    last_error = exc
                    if attempt < 2:
                        time.sleep(1.5 * (attempt + 1))
        raise RuntimeError(f"Gemini extraction failed after retries: {last_error}")
