"""Pydantic schemas for extraction endpoints."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

Engine = Literal["rule", "gemini"]


class TaskItemSchema(BaseModel):
    task: str
    source_sentence: str
    people: list[str] = []
    due_date_text: str | None = None
    due_date_iso: str | None = None
    priority: str = "Normal"
    priority_score: float = 0.0
    confidence: float = 0.0
    engine: str = "rule"


class ExtractRequest(BaseModel):
    email_text: str = Field(..., description="Raw email or thread text.")
    engine: Engine = "rule"


class ExtractResponse(BaseModel):
    engine: str
    count: int
    items: list[TaskItemSchema]
    fallback_used: bool = False
    fallback_reason: str | None = None


class AgreementReportSchema(BaseModel):
    matched: int
    rule_only: int
    gemini_only: int
    mean_similarity: float


class CompareRequest(BaseModel):
    email_text: str


class CompareResponse(BaseModel):
    rule: list[TaskItemSchema]
    gemini: list[TaskItemSchema]
    agreement: AgreementReportSchema
    gemini_error: str | None = None


class BatchRequest(BaseModel):
    emails: list[str]
    engine: Engine = "rule"


class BatchResponse(BaseModel):
    results: list[ExtractResponse]
