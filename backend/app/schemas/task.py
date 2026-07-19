"""Pydantic schemas for task persistence endpoints."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class TaskCreate(BaseModel):
    task: str
    source_sentence: str = ""
    people: list[str] = []
    due_date_text: str | None = None
    due_date_iso: str | None = None
    priority: str = "Normal"
    priority_score: float = 0.0
    confidence: float = 0.0
    engine: str = "rule"


class TaskUpdate(BaseModel):
    status: str | None = None
    priority: str | None = None
    due_date_text: str | None = None


class TaskRead(TaskCreate):
    model_config = ConfigDict(from_attributes=True)

    id: str
    status: str
    created_at: datetime


class BulkSaveRequest(BaseModel):
    tasks: list[TaskCreate]


class BulkSaveResponse(BaseModel):
    added: int
    skipped: int
