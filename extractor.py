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
import re

import dateparser
import spacy


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

    parsed = dateparser.search.search_dates(text, languages=["en"])
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
