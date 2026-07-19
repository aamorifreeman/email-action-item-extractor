"""Integration endpoints: Google Calendar quick-add link generation."""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from app.schemas.task import TaskCreate
from app.services.task_service import bulk_calendar_link, calendar_link

router = APIRouter()


class CalendarRequest(BaseModel):
    tasks: list[TaskCreate]


class CalendarResponse(BaseModel):
    bulk_url: str
    item_urls: list[str]


@router.post("/integrations/calendar-link", response_model=CalendarResponse)
def calendar_links(req: CalendarRequest) -> CalendarResponse:
    """Build a bulk quick-add link plus one per task. Accepts task payloads directly."""
    return CalendarResponse(
        bulk_url=bulk_calendar_link(req.tasks),
        item_urls=[calendar_link(t) for t in req.tasks],
    )
