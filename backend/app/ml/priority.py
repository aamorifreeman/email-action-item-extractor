"""Priority scoring from a weighted urgency lexicon.

Replaces the original binary keyword check with a continuous score in
[0, 1]. The score is derived from weighted urgency cues plus a small bump
for a near-term deadline; the High/Normal label is a threshold on the score.
Deterministic and engine-agnostic so both engines are scored identically.
"""

from __future__ import annotations

import re

# Urgency cue -> weight. Stronger words contribute more.
URGENCY_WEIGHTS: dict[str, float] = {
    "asap": 1.0,
    "urgent": 1.0,
    "immediately": 0.9,
    "right away": 0.9,
    "critical": 0.9,
    "priority": 0.7,
    "important": 0.6,
    "today": 0.6,
    "tonight": 0.6,
    "eod": 0.6,
    "end of day": 0.6,
    "tomorrow": 0.4,
    "soon": 0.3,
}

HIGH_THRESHOLD = 0.6

# Due phrases that indicate a near-term (<= a couple of days) deadline.
_NEAR_TERM = re.compile(r"\b(today|tonight|tomorrow|eod|end of day)\b", re.IGNORECASE)


def score_priority(text: str, due_phrase: str | None = None) -> tuple[str, float]:
    """Return (label, score) where label is 'High' or 'Normal'."""
    lowered = f"{text} {due_phrase or ''}".lower()

    best = 0.0
    accumulated = 0.0
    for cue, weight in URGENCY_WEIGHTS.items():
        if cue in lowered:
            best = max(best, weight)
            accumulated += weight * 0.15  # multiple cues nudge the score up

    if due_phrase and _NEAR_TERM.search(due_phrase):
        best = max(best, 0.6)

    score = min(1.0, best + accumulated)
    label = "High" if score >= HIGH_THRESHOLD else "Normal"
    return label, round(score, 3)
