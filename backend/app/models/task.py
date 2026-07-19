"""ORM models: persisted tasks and an audit trail of extraction runs."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import JSON, DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


def _uuid() -> str:
    return str(uuid4())


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    task: Mapped[str] = mapped_column(String, nullable=False)
    source_sentence: Mapped[str] = mapped_column(Text, default="")
    people: Mapped[list[str]] = mapped_column(JSON, default=list)
    due_date_text: Mapped[str | None] = mapped_column(String, nullable=True)
    due_date_iso: Mapped[str | None] = mapped_column(String, nullable=True)
    priority: Mapped[str] = mapped_column(String, default="Normal")
    priority_score: Mapped[float] = mapped_column(Float, default=0.0)
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    engine: Mapped[str] = mapped_column(String, default="rule")
    status: Mapped[str] = mapped_column(String, default="To Do")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)


class Extraction(Base):
    """Audit record of each extraction run (one row per API call)."""

    __tablename__ = "extractions"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    email_text: Mapped[str] = mapped_column(Text, default="")
    engine: Mapped[str] = mapped_column(String, default="rule")
    item_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
