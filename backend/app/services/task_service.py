"""Task persistence, CSV export, and Google Calendar link helpers.

Ported from the original Streamlit `inboxiq_state.py`, but backed by the
database instead of session state.
"""

from __future__ import annotations

import csv
import io
from datetime import datetime, timedelta, timezone
from urllib.parse import quote_plus

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.task import Task
from app.schemas.task import TaskCreate


def _signature(task: str, due: str | None, people: list[str]) -> str:
    people_key = ",".join(sorted(p.lower() for p in people))
    return f"{task.strip().lower()}|{(due or '').strip().lower()}|{people_key}"


def list_tasks(db: Session) -> list[Task]:
    return list(db.scalars(select(Task).order_by(Task.created_at.desc())).all())


def _existing_signatures(db: Session) -> set[str]:
    return {
        _signature(t.task, t.due_date_text, list(t.people or []))
        for t in db.scalars(select(Task)).all()
    }


def save_task(db: Session, payload: TaskCreate, *, _seen: set[str] | None = None) -> bool:
    """Persist a task unless an identical one already exists. Returns True if added."""
    seen = _seen if _seen is not None else _existing_signatures(db)
    signature = _signature(payload.task, payload.due_date_text, payload.people)
    if signature in seen:
        return False
    seen.add(signature)

    db.add(
        Task(
            task=payload.task.strip() or "Untitled task",
            source_sentence=payload.source_sentence,
            people=payload.people,
            due_date_text=payload.due_date_text,
            due_date_iso=payload.due_date_iso,
            priority=payload.priority or "Normal",
            priority_score=payload.priority_score,
            confidence=payload.confidence,
            engine=payload.engine,
            status="To Do",
        )
    )
    return True


def save_many(db: Session, payloads: list[TaskCreate]) -> tuple[int, int]:
    seen = _existing_signatures(db)
    added = 0
    for payload in payloads:
        if save_task(db, payload, _seen=seen):
            added += 1
    skipped = len(payloads) - added
    db.commit()
    return added, skipped


def get_task(db: Session, task_id: str) -> Task | None:
    return db.get(Task, task_id)


def toggle_status(db: Session, task: Task) -> Task:
    task.status = "To Do" if task.status == "Done" else "Done"
    db.commit()
    db.refresh(task)
    return task


def update_task(db: Session, task: Task, fields: dict) -> Task:
    for key, value in fields.items():
        if value is not None and hasattr(task, key):
            setattr(task, key, value)
    db.commit()
    db.refresh(task)
    return task


def delete_task(db: Session, task: Task) -> None:
    db.delete(task)
    db.commit()


def tasks_to_csv(tasks: list[Task], include_status: bool = True) -> str:
    output = io.StringIO()
    fieldnames = ["task", "due_date", "person", "priority", "confidence"]
    if include_status:
        fieldnames.append("status")
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    for task in tasks:
        row = {
            "task": task.task,
            "due_date": task.due_date_iso or task.due_date_text or "",
            "person": ", ".join(task.people or []),
            "priority": task.priority,
            "confidence": task.confidence,
        }
        if include_status:
            row["status"] = task.status
        writer.writerow(row)
    return output.getvalue()


# --- Google Calendar quick-add links ---


def _calendar_dates(iso_date: str | None, due_text: str | None) -> str | None:
    """Build a Calendar dates range from a resolved ISO date (all-day-ish, 9am)."""
    target: datetime | None = None
    if iso_date:
        try:
            d = datetime.fromisoformat(iso_date)
            target = d.replace(hour=9, minute=0, second=0, microsecond=0, tzinfo=timezone.utc)
        except ValueError:
            target = None
    if target is None:
        return None
    end = target + timedelta(hours=1)
    return f"{target.strftime('%Y%m%dT%H%M%SZ')}/{end.strftime('%Y%m%dT%H%M%SZ')}"


def calendar_link(task: Task) -> str:
    title = f"Task: {task.task}"
    people = ", ".join(task.people or []) or "Not specified"
    due = task.due_date_iso or task.due_date_text or "Not specified"
    details = f"Due: {due}\nPeople: {people}\nPriority: {task.priority}"
    base = "https://calendar.google.com/calendar/render?action=TEMPLATE"
    dates = _calendar_dates(task.due_date_iso, task.due_date_text)
    dates_part = f"&dates={dates}" if dates else ""
    return f"{base}&text={quote_plus(title)}&details={quote_plus(details)}{dates_part}"


def bulk_calendar_link(tasks: list[Task]) -> str:
    if not tasks:
        return "https://calendar.google.com/calendar/render"
    n = len(tasks)
    title = f"InboxIQ: {n} action item{'s' if n != 1 else ''}"
    lines = []
    for i, task in enumerate(tasks, start=1):
        due = task.due_date_iso or task.due_date_text or "—"
        people = ", ".join(task.people or []) or "—"
        lines.append(f"{i}. {task.task}\n   Due: {due} | People: {people} | Priority: {task.priority}")
    details = "Action items (InboxIQ)\n\n" + "\n\n".join(lines)
    base = "https://calendar.google.com/calendar/render?action=TEMPLATE"
    return f"{base}&text={quote_plus(title)}&details={quote_plus(details)}"
