"""Orchestrates extraction runs: engine selection, Gemini fallback, audit."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.ml.base import TaskItem
from app.ml.pipeline import compare_engines, get_extractor, run_pipeline
from app.models.task import Extraction
from app.schemas.extraction import (
    AgreementReportSchema,
    CompareResponse,
    ExtractResponse,
    TaskItemSchema,
)


def _to_schema(items: list[TaskItem]) -> list[TaskItemSchema]:
    return [TaskItemSchema(**item.to_dict()) for item in items]


def _audit(db: Session, email_text: str, engine: str, count: int) -> None:
    db.add(Extraction(email_text=email_text, engine=engine, item_count=count))
    db.commit()


def run_extraction(db: Session, email_text: str, engine: str) -> ExtractResponse:
    """Run one engine, transparently falling back to rule-based if Gemini fails."""
    fallback_used = False
    fallback_reason: str | None = None

    try:
        raw = get_extractor(engine).extract(email_text)
    except Exception as exc:
        if engine == "gemini":
            fallback_used = True
            fallback_reason = str(exc)
            raw = get_extractor("rule").extract(email_text)
        else:
            raise

    items = run_pipeline(raw)
    effective_engine = "rule" if fallback_used else engine
    _audit(db, email_text, effective_engine, len(items))

    return ExtractResponse(
        engine=effective_engine,
        count=len(items),
        items=_to_schema(items),
        fallback_used=fallback_used,
        fallback_reason=fallback_reason,
    )


def run_compare(db: Session, email_text: str) -> CompareResponse:
    """Run both engines and report their agreement."""
    rule_items = run_pipeline(get_extractor("rule").extract(email_text))

    gemini_error: str | None = None
    try:
        gemini_items = run_pipeline(get_extractor("gemini").extract(email_text))
    except Exception as exc:
        gemini_error = str(exc)
        gemini_items = []

    report = compare_engines(rule_items, gemini_items)
    _audit(db, email_text, "compare", len(rule_items) + len(gemini_items))

    return CompareResponse(
        rule=_to_schema(rule_items),
        gemini=_to_schema(gemini_items),
        agreement=AgreementReportSchema(**report.to_dict()),
        gemini_error=gemini_error,
    )
