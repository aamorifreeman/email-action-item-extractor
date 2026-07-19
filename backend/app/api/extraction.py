"""Extraction endpoints: single, compare, and batch."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.extraction import (
    BatchRequest,
    BatchResponse,
    CompareRequest,
    CompareResponse,
    ExtractRequest,
    ExtractResponse,
)
from app.services.extraction_service import run_compare, run_extraction

router = APIRouter()


@router.post("/extract", response_model=ExtractResponse)
def extract(req: ExtractRequest, db: Session = Depends(get_db)) -> ExtractResponse:
    """Extract action items with the chosen engine (Gemini falls back to rules)."""
    return run_extraction(db, req.email_text, req.engine)


@router.post("/extract/compare", response_model=CompareResponse)
def compare(req: CompareRequest, db: Session = Depends(get_db)) -> CompareResponse:
    """Run both engines on one email and report their agreement."""
    return run_compare(db, req.email_text)


@router.post("/extract/batch", response_model=BatchResponse)
def batch(req: BatchRequest, db: Session = Depends(get_db)) -> BatchResponse:
    """Extract action items across many emails in one call."""
    results = [run_extraction(db, email, req.engine) for email in req.emails]
    return BatchResponse(results=results)
