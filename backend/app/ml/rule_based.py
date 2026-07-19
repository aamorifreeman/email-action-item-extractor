"""Rule-based extraction engine (spaCy + regex).

Ported from the original Streamlit `extractor.py`, with all Streamlit and
secrets handling removed. Produces raw :class:`TaskItem` objects; date
resolution, priority scoring, confidence and dedup are handled by the
pipeline so both engines share the same enrichment.
"""

from __future__ import annotations

import re
from functools import lru_cache

import spacy

from app.ml.base import Extractor, TaskItem

# Candidate action verbs/phrases for task detection.
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

# Date-ish phrases we want to capture even when NER misses.
DATE_PHRASE_PATTERN = re.compile(
    r"\b("
    r"today|tomorrow|tonight|this week|next week|this month|next month|"
    r"monday|tuesday|wednesday|thursday|friday|saturday|sunday|"
    r"by\s+\w+|before\s+the\s+\w+|end of day|eod"
    r")\b",
    re.IGNORECASE,
)

# Split list-style sentences: "A, B, and C" or "A, B, C".
CLAUSE_SPLIT_PATTERN = re.compile(r",\s*(?:and\s+)?", re.IGNORECASE)

# When a fragment chains tasks with "verb ... and verb ..." without commas.
AND_SPLIT_PATTERN = re.compile(r"\s+and\s+", re.IGNORECASE)

# spaCy sometimes tags human names as GPE; catch common "with X" patterns.
NAME_AFTER_WITH_PATTERN = re.compile(
    r"(?:follow\s+up\s+with|meet\s+with|sync\s+with|with)\s+([A-Z][a-z]+)\b",
    re.IGNORECASE,
)


@lru_cache(maxsize=1)
def get_nlp():
    """Load spaCy once, falling back to a blank pipeline if the model is absent."""
    try:
        return spacy.load("en_core_web_sm")
    except OSError:
        nlp = spacy.blank("en")
        nlp.add_pipe("sentencizer")
        return nlp


def _contains_action_phrase(text: str) -> bool:
    lowered = text.lower()
    return any(phrase in lowered for phrase in ACTION_PHRASES)


def _count_action_phrase_hits(text: str) -> int:
    lowered = text.lower()
    return sum(1 for phrase in ACTION_PHRASES if phrase in lowered)


def _split_into_clauses(sentence: str) -> list[str]:
    """Break a sentence into task clauses using commas and 'and'."""
    text = sentence.strip()
    if not text:
        return []

    raw_parts = [p.strip() for p in CLAUSE_SPLIT_PATTERN.split(text) if p.strip()]

    clauses: list[str] = []
    for part in raw_parts:
        if " and " in part.lower() and _count_action_phrase_hits(part) >= 2:
            clauses.extend(s.strip() for s in AND_SPLIT_PATTERN.split(part) if s.strip())
        else:
            clauses.append(part)
    return clauses


def _extract_people(sent_doc, clause_text: str) -> list[str]:
    """Extract PERSON entities plus names after 'with ...' patterns."""
    people = [ent.text.strip() for ent in sent_doc.ents if ent.label_ == "PERSON"]
    for m in NAME_AFTER_WITH_PATTERN.finditer(clause_text):
        name = m.group(1).strip()
        if name:
            people.append(name)

    unique: list[str] = []
    seen: set[str] = set()
    for person in people:
        key = person.lower()
        if key not in seen:
            seen.add(key)
            unique.append(person)
    return unique


def _extract_due_phrase(text: str) -> str | None:
    """Return a human-readable due phrase; ISO resolution happens in the pipeline."""
    match = DATE_PHRASE_PATTERN.search(text)
    if not match:
        return None
    due = match.group(0).strip()
    if due.lower().startswith("by ") and len(due) > 3:
        due = due[3:].strip()
    return due


def _cleanup_polite_prefixes(text: str) -> str:
    return re.sub(
        r"^\s*(can you|could you|would you|please|kindly)\s+",
        "",
        text.strip(),
        flags=re.IGNORECASE,
    )


def _strip_due_from_task(task: str, due: str | None) -> str:
    if not due:
        return task
    t = re.sub(re.escape(due), "", task, flags=re.IGNORECASE)
    t = re.sub(r"\s*\b(by|before|due)\s*$", "", t, flags=re.IGNORECASE)
    return re.sub(r"\s+", " ", t).strip(" ,.-?!")


def _sentence_case(task: str) -> str:
    task = task.strip()
    return task[0].upper() + task[1:] if task else task


def _finalize_task_text(clause: str) -> tuple[str, str | None]:
    due = _extract_due_phrase(clause)
    task = _cleanup_polite_prefixes(clause)
    task = _strip_due_from_task(task, due)
    task = _sentence_case(task.rstrip(" .?!"))
    return task, due


class RuleBasedExtractor(Extractor):
    name = "rule"

    def extract(self, email_text: str) -> list[TaskItem]:
        if not email_text or not email_text.strip():
            return []

        nlp = get_nlp()
        doc = nlp(email_text)
        items: list[TaskItem] = []

        for sent in doc.sents:
            sentence = sent.text.strip()
            if not sentence or not _contains_action_phrase(sentence):
                continue

            for clause in _split_into_clauses(sentence):
                if not _contains_action_phrase(clause):
                    continue

                clause_doc = nlp(clause)
                task, due = _finalize_task_text(clause)
                if not task:
                    continue

                items.append(
                    TaskItem(
                        task=task,
                        source_sentence=sentence,
                        people=_extract_people(clause_doc, clause),
                        due_date_text=due,
                        engine=self.name,
                    )
                )
        return items
