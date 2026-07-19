"""Core ML abstractions shared by every extraction engine.

`TaskItem` is the canonical, engine-agnostic representation of a single
action item. Engines populate the extraction fields (task, people,
due_date_text, priority label); the pipeline enriches the rest
(due_date_iso, priority_score, confidence, engine) so both engines gain the
same downstream ML treatment.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class TaskItem:
    task: str
    source_sentence: str
    people: list[str] = field(default_factory=list)
    due_date_text: str | None = None
    due_date_iso: str | None = None
    priority: str = "Normal"
    priority_score: float = 0.0
    confidence: float = 0.0
    engine: str = "rule"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class Extractor(ABC):
    """Interface implemented by every extraction engine."""

    #: Short identifier, e.g. "rule" or "gemini".
    name: str = "base"

    @abstractmethod
    def extract(self, email_text: str) -> list[TaskItem]:
        """Return raw action items. Enrichment happens later in the pipeline."""
        raise NotImplementedError
