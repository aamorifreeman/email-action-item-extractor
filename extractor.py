"""
Rule-based extraction logic for action items inside email text.

This module focuses on:
1) splitting sentences into task-sized clauses (commas, "and")
2) detecting likely tasks via action phrases
3) extracting due-date phrases with dateparser + regex
4) extracting person names with spaCy NER
5) detecting urgency/priority hints
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Dict, List, Optional
import json
import os
from pathlib import Path
import re
import time

import dateparser
import spacy
import streamlit as st
from dateparser.search import search_dates
from google import genai


# Candidate action verbs/phrases for MVP task detection.
ACTION_PHRASES = [
    "send",
    "follow up",
    "review",
    "submit",
    "schedule",
    "call",
    "email",
    "complete",
]

# Words that imply urgency.
URGENCY_WORDS = ["asap", "urgent", "immediately", "priority", "important"]

# Date-ish phrases we want to capture even when NER misses.
DATE_PHRASE_PATTERN = re.compile(
    r"\b("
    r"today|tomorrow|tonight|this week|next week|this month|next month|"
    r"monday|tuesday|wednesday|thursday|friday|saturday|sunday|"
    r"by\s+\w+|before\s+the\s+\w+|end of day|eod"
    r")\b",
    re.IGNORECASE,
)

# Split list-style sentences: "A, B, and C" or "A, B, C"
CLAUSE_SPLIT_PATTERN = re.compile(r",\s*(?:and\s+)?", re.IGNORECASE)

# When a fragment has no commas but chains tasks with "verb ... and verb ..."
AND_SPLIT_PATTERN = re.compile(r"\s+and\s+", re.IGNORECASE)

# spaCy sometimes tags human names as GPE; catch common "with X" patterns.
NAME_AFTER_WITH_PATTERN = re.compile(
    r"(?:follow\s+up\s+with|meet\s+with|sync\s+with|with)\s+([A-Z][a-z]+)\b",
    re.IGNORECASE,
)


@dataclass
class TaskItem:
    task: str
    due_date: Optional[str]
    people: List[str]
    priority: str
    source_sentence: str

    def to_dict(self) -> Dict[str, object]:
        return asdict(self)


def _load_nlp():
    """
    Load spaCy model with a fallback to a blank pipeline.
    """
    try:
        return spacy.load("en_core_web_sm")
    except OSError:
        # Fallback keeps sentence splitting available even without model download.
        nlp = spacy.blank("en")
        nlp.add_pipe("sentencizer")
        return nlp


NLP = _load_nlp()


def _get_gemini_api_key() -> str:
    """
    Resolve Gemini API key from Streamlit secrets first, then env/file fallbacks.
    """
    # Primary path for Streamlit apps.
    try:
        secret_value = st.secrets.get("GEMINI_API_KEY")
        if isinstance(secret_value, str) and secret_value.strip():
            return secret_value.strip()
    except Exception:
        pass

    # Fallback for local/script usage.
    env_key = os.getenv("GEMINI_API_KEY")
    if env_key and env_key.strip():
        return env_key.strip()

    # Optional local fallback to project secrets file.
    candidate_paths = [
        Path(__file__).resolve().parent / ".streamlit" / "secrets.toml",
        Path.cwd() / ".streamlit" / "secrets.toml",
    ]
    for path in candidate_paths:
        if not path.exists():
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            if "=" not in line:
                continue
            left, right = line.split("=", 1)
            if left.strip() != "GEMINI_API_KEY":
                continue
            value = right.strip().strip("\"' ")
            if value:
                return value

    raise KeyError(
        "GEMINI_API_KEY not found. Set it in Streamlit secrets, env var, or .streamlit/secrets.toml."
    )


def _contains_action_phrase(text: str) -> bool:
    lowered = text.lower()
    return any(phrase in lowered for phrase in ACTION_PHRASES)


def _count_action_phrase_hits(text: str) -> int:
    lowered = text.lower()
    return sum(1 for phrase in ACTION_PHRASES if phrase in lowered)


def _split_into_clauses(sentence: str) -> List[str]:
    """
    Break a sentence into smaller task clauses using commas and 'and'.

    Handles common list patterns like "do A, do B, and do C".
    """
    text = sentence.strip()
    if not text:
        return []

    # Primary: comma-separated lists (including ", and " before last item).
    raw_parts = [p.strip() for p in CLAUSE_SPLIT_PATTERN.split(text) if p.strip()]

    clauses: List[str] = []
    for part in raw_parts:
        # Secondary: "task A and task B" when there was no comma between them.
        if " and " in part.lower() and _count_action_phrase_hits(part) >= 2:
            sub = [s.strip() for s in AND_SPLIT_PATTERN.split(part) if s.strip()]
            clauses.extend(sub)
        else:
            clauses.append(part)

    return clauses


def _extract_people(sent_doc, clause_text: str) -> List[str]:
    """Extract PERSON entities from text."""
    people = []
    for ent in sent_doc.ents:
        if ent.label_ == "PERSON":
            people.append(ent.text.strip())
    # Heuristic: names after "with …" / "follow up with …" (often mislabeled as GPE).
    for m in NAME_AFTER_WITH_PATTERN.finditer(clause_text):
        name = m.group(1).strip()
        if name:
            people.append(name)
    unique_people: List[str] = []
    seen = set()
    for person in people:
        key = person.lower()
        if key not in seen:
            seen.add(key)
            unique_people.append(person)
    return unique_people


def _extract_due_date(text: str) -> Optional[str]:
    """Try regex first, then dateparser, for human-readable due phrases."""
    phrase_match = DATE_PHRASE_PATTERN.search(text)
    if phrase_match:
        due = phrase_match.group(0).strip()
        return _normalize_due_display(due)

    parsed = search_dates(text, languages=["en"])
    if parsed:
        return _normalize_due_display(parsed[0][0].strip())

    return None


def _normalize_due_display(due: str) -> str:
    """Prefer 'Friday' over 'by Friday' when the phrase starts with 'by '."""
    due = due.strip()
    if due.lower().startswith("by ") and len(due) > 3:
        return due[3:].strip()
    return due


def _detect_priority(text: str) -> str:
    lowered = text.lower()
    if any(word in lowered for word in URGENCY_WORDS):
        return "High"
    return "Normal"


def _cleanup_polite_prefixes(text: str) -> str:
    """Remove leading softeners like 'can you', 'please'."""
    t = text.strip()
    t = re.sub(
        r"^\s*(can you|could you|would you|please|kindly)\s+",
        "",
        t,
        flags=re.IGNORECASE,
    )
    return t


def _strip_due_from_task(task: str, due: Optional[str]) -> str:
    """
    Remove the due-date phrase from the task so the task line stays action-focused.
    """
    if not due:
        return task

    t = task
    # Remove the due substring (case-insensitive).
    t = re.sub(re.escape(due), "", t, flags=re.IGNORECASE)
    # Remove leftover connectors at the end (e.g. trailing 'by', 'before').
    t = re.sub(
        r"\s*\b(by|before|due)\s*$",
        "",
        t,
        flags=re.IGNORECASE,
    )
    t = re.sub(r"\s+", " ", t).strip(" ,.-?!")
    return t


def _sentence_case_task(task: str) -> str:
    """Capitalize the first letter for display (e.g. 'send the slides' -> 'Send the slides')."""
    task = task.strip()
    if not task:
        return task
    return task[0].upper() + task[1:]


def _finalize_task_text(clause: str) -> tuple[str, Optional[str]]:
    """
    Build display task string and due date from a raw clause.
    """
    due = _extract_due_date(clause)
    task = _cleanup_polite_prefixes(clause)
    task = _strip_due_from_task(task, due)
    task = task.rstrip(" .?!")
    task = _sentence_case_task(task)
    return task, due


def extract_action_items(email_text: str) -> List[Dict[str, object]]:
    """
    Main extraction function used by the Streamlit app.

    Returns a list of dictionaries:
    {
      "task": str,
      "due_date": Optional[str],
      "people": List[str],
      "priority": str,
      "source_sentence": str
    }
    """
    if not email_text or not email_text.strip():
        return []

    doc = NLP(email_text)
    items: List[TaskItem] = []

    for sent in doc.sents:
        sentence = sent.text.strip()
        if not sentence:
            continue

        if not _contains_action_phrase(sentence):
            continue

        for clause in _split_into_clauses(sentence):
            if not _contains_action_phrase(clause):
                continue

            clause_doc = NLP(clause)
            task, due = _finalize_task_text(clause)

            if not task:
                continue

            item = TaskItem(
                task=task,
                due_date=due,
                people=_extract_people(clause_doc, clause),
                priority=_detect_priority(clause),
                source_sentence=sentence,
            )
            items.append(item)

    return [item.to_dict() for item in items]


def _build_gemini_prompt(email_text: str) -> str:
    """Create a strict prompt that asks Gemini for JSON-only task extraction."""
    return f"""
You are an information extraction assistant.
Extract all action items from the email below.

Rules:
1) Split multiple tasks into separate objects.
2) Extract due dates or deadline phrases when present.
3) Extract names of people mentioned in each task.
4) Set priority to "High" if urgency words are present (e.g., ASAP, urgent, immediately, priority, important); otherwise "Normal".
5) Return valid JSON only.
6) Do not return markdown.
7) Do not return explanation text.
8) Output must be a JSON array and every object must include exactly these keys:
   - task (string)
   - due_date (string or null)
   - people (array of strings)
   - priority (string: "High" or "Normal")
   - source_sentence (string)

Expected JSON schema example:
[
  {{
    "task": "Send the slides",
    "due_date": "Friday",
    "people": ["Marcus"],
    "priority": "Normal",
    "source_sentence": "Can you send the slides to Marcus by Friday?"
  }}
]

Email:
\"\"\"
{email_text}
\"\"\"
""".strip()


def _normalize_gemini_items(raw_items: object) -> List[Dict[str, object]]:
    """
    Normalize Gemini output to match app schema exactly.
    """
    if not isinstance(raw_items, list):
        raise ValueError("Gemini output must be a JSON array.")

    normalized: List[Dict[str, object]] = []
    for item in raw_items:
        if not isinstance(item, dict):
            continue

        task = str(item.get("task", "")).strip()
        due_date = item.get("due_date", None)
        people = item.get("people", [])
        priority = str(item.get("priority", "Normal")).strip() or "Normal"
        source_sentence = str(item.get("source_sentence", "")).strip()

        if not task:
            continue
        if due_date is not None:
            due_date = str(due_date).strip() or None
        if not isinstance(people, list):
            people = []
        people = [str(p).strip() for p in people if str(p).strip()]
        if priority not in {"High", "Normal"}:
            priority = "High" if priority.lower() == "high" else "Normal"
        if not source_sentence:
            source_sentence = task

        normalized.append(
            {
                "task": task,
                "due_date": due_date,
                "people": people,
                "priority": priority,
                "source_sentence": source_sentence,
            }
        )

    return normalized


def _parse_gemini_json(response_text: str) -> object:
    """
    Parse Gemini output as JSON with light cleanup for common wrappers.
    """
    text = response_text.strip()
    if not text:
        raise ValueError("Gemini returned an empty response.")

    # 1) Best case: already strict JSON.
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # 2) Common case: fenced markdown around JSON.
    fenced_match = re.search(r"```(?:json)?\s*(.*?)\s*```", text, flags=re.DOTALL | re.IGNORECASE)
    if fenced_match:
        fenced_payload = fenced_match.group(1).strip()
        try:
            return json.loads(fenced_payload)
        except json.JSONDecodeError:
            pass

    # 3) Last attempt: first JSON-like array/object inside response.
    for pattern in (r"(\[.*\])", r"(\{.*\})"):
        match = re.search(pattern, text, flags=re.DOTALL)
        if not match:
            continue
        payload = match.group(1).strip()
        try:
            return json.loads(payload)
        except json.JSONDecodeError:
            continue

    raise ValueError("Could not parse valid JSON from Gemini response.")


def extract_action_items_gemini(email_text: str) -> List[Dict[str, object]]:
    """
    Extract action items with Gemini and return the same schema as rule-based extraction.
    """
    if not email_text or not email_text.strip():
        return []

    client = genai.Client(api_key=_get_gemini_api_key())
    prompt = _build_gemini_prompt(email_text)

    # Retry a few times for transient availability issues, then try a fallback model.
    last_error: Optional[Exception] = None
    candidate_models = ["gemini-2.5-flash-lite", "gemini-2.5-flash"]
    for model_name in candidate_models:
        for attempt in range(3):
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config={"response_mime_type": "application/json"},
                )
                response_text = (response.text or "").strip()
                parsed = _parse_gemini_json(response_text)
                return _normalize_gemini_items(parsed)
            except Exception as exc:
                last_error = exc
                if attempt < 2:
                    time.sleep(1.5 * (attempt + 1))
                    continue

    raise RuntimeError(f"Gemini extraction failed after retries: {last_error}")
