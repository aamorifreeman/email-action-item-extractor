"""Composite confidence score for an extracted task item.

Confidence combines signal completeness: does the task contain a real action
verb, did we resolve a concrete date, is a person attached, is the phrasing a
plausible task length. Engine-agnostic and deterministic.
"""

from __future__ import annotations

from app.ml.base import TaskItem
from app.ml.rule_based import ACTION_PHRASES

_BASE = 0.4


def score_confidence(item: TaskItem) -> float:
    score = _BASE
    lowered = item.task.lower()

    if any(phrase in lowered for phrase in ACTION_PHRASES):
        score += 0.2
    if item.due_date_iso:
        score += 0.15
    elif item.due_date_text:
        score += 0.05
    if item.people:
        score += 0.15

    word_count = len(item.task.split())
    if 3 <= word_count <= 15:
        score += 0.1
    elif word_count < 2:
        score -= 0.15

    return round(max(0.0, min(1.0, score)), 3)
