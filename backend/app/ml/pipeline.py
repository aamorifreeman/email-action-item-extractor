"""Extraction pipeline: shared enrichment, semantic dedup, engine comparison.

Whichever engine produces the raw items, they flow through the same
post-processing so both engines gain identical treatment:

    extract -> resolve dates -> score priority -> score confidence -> dedup
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from app.config import get_settings
from app.ml.base import Extractor, TaskItem
from app.ml.confidence import score_confidence
from app.ml.date_resolver import resolve_due_date
from app.ml.embeddings import cosine_matrix, get_embedder
from app.ml.gemini import GeminiExtractor
from app.ml.priority import score_priority
from app.ml.rule_based import RuleBasedExtractor

_EXTRACTORS: dict[str, type[Extractor]] = {
    "rule": RuleBasedExtractor,
    "gemini": GeminiExtractor,
}


def get_extractor(name: str) -> Extractor:
    try:
        return _EXTRACTORS[name]()
    except KeyError:
        raise ValueError(f"Unknown engine '{name}'. Choose from {list(_EXTRACTORS)}.")


def enrich(items: list[TaskItem]) -> list[TaskItem]:
    """Resolve dates and attach priority + confidence scores in place."""
    for item in items:
        item.due_date_iso = resolve_due_date(item.due_date_text)
        item.priority, item.priority_score = score_priority(
            f"{item.source_sentence} {item.task}", item.due_date_text
        )
        item.confidence = score_confidence(item)
    return items


def semantic_dedup(items: list[TaskItem], threshold: float | None = None) -> list[TaskItem]:
    """Merge near-duplicate tasks, keeping the higher-confidence representative."""
    if len(items) < 2:
        return items
    threshold = threshold if threshold is not None else get_settings().dedup_threshold

    vectors = get_embedder().encode([item.task for item in items])
    sims = cosine_matrix(vectors, vectors)

    kept: list[int] = []
    removed: set[int] = set()
    for i in range(len(items)):
        if i in removed:
            continue
        kept.append(i)
        for j in range(i + 1, len(items)):
            if j not in removed and sims[i, j] >= threshold:
                removed.add(j)
                # Fold people from the duplicate into the survivor.
                for person in items[j].people:
                    if person not in items[i].people:
                        items[i].people.append(person)
    return [items[i] for i in kept]


def run_pipeline(items: list[TaskItem]) -> list[TaskItem]:
    """Full enrichment + dedup chain applied to raw engine output."""
    return semantic_dedup(enrich(items))


@dataclass
class AgreementReport:
    matched: int
    rule_only: int
    gemini_only: int
    mean_similarity: float

    def to_dict(self) -> dict[str, float | int]:
        return {
            "matched": self.matched,
            "rule_only": self.rule_only,
            "gemini_only": self.gemini_only,
            "mean_similarity": self.mean_similarity,
        }


def compare_engines(
    rule_items: list[TaskItem],
    gemini_items: list[TaskItem],
    threshold: float | None = None,
) -> AgreementReport:
    """Match items across engines via embedding similarity and report overlap."""
    threshold = threshold if threshold is not None else get_settings().dedup_threshold
    if not rule_items or not gemini_items:
        return AgreementReport(
            matched=0,
            rule_only=len(rule_items),
            gemini_only=len(gemini_items),
            mean_similarity=0.0,
        )

    embedder = get_embedder()
    rule_vecs = embedder.encode([i.task for i in rule_items])
    gem_vecs = embedder.encode([i.task for i in gemini_items])
    sims = cosine_matrix(rule_vecs, gem_vecs)

    matched_sims: list[float] = []
    matched_gemini: set[int] = set()
    for r in range(len(rule_items)):
        j = int(np.argmax(sims[r]))
        if sims[r, j] >= threshold and j not in matched_gemini:
            matched_gemini.add(j)
            matched_sims.append(float(sims[r, j]))

    matched = len(matched_sims)
    return AgreementReport(
        matched=matched,
        rule_only=len(rule_items) - matched,
        gemini_only=len(gemini_items) - matched,
        mean_similarity=round(sum(matched_sims) / matched, 3) if matched else 0.0,
    )
