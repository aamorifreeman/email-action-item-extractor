"""
Shared session state and task/calendar/CSV helpers for Inbox IQ.
Used by all pages — extraction logic stays in extractor.py.
"""

from __future__ import annotations

import csv
import io
from datetime import datetime, timedelta, timezone
from urllib.parse import quote_plus
from uuid import uuid4

import streamlit as st


def init_session_state() -> None:
    """Initialize session keys used across Extract, Tasks, and Integrations."""
    defaults = {
        "email_text": "",
        "results": [],
        "saved_tasks": [],
        "has_run": False,
        "gemini_error": "",
        "save_feedback": "",
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def normalize_people(task: dict) -> list[str]:
    people = task.get("people", [])
    if not isinstance(people, list):
        return []
    return [str(p).strip() for p in people if str(p).strip()]


def task_signature(task: dict) -> str:
    task_text = str(task.get("task", "")).strip().lower()
    due_date = str(task.get("due_date") or "").strip().lower()
    people = ",".join(sorted(p.lower() for p in normalize_people(task)))
    return f"{task_text}|{due_date}|{people}"


def save_task(task: dict) -> bool:
    signature = task_signature(task)
    existing = {task_signature(t): t for t in st.session_state.saved_tasks}
    if signature in existing:
        return False

    st.session_state.saved_tasks.append(
        {
            "id": str(uuid4()),
            "task": str(task.get("task", "")).strip() or "Untitled task",
            "due_date": str(task.get("due_date") or "").strip() or None,
            "people": normalize_people(task),
            "priority": str(task.get("priority", "Normal")).strip() or "Normal",
            "status": "To Do",
            "source_sentence": str(task.get("source_sentence", "")).strip(),
        }
    )
    return True


def save_all_tasks(tasks: list[dict]) -> tuple[int, int]:
    added = 0
    skipped = 0
    for task in tasks:
        if save_task(task):
            added += 1
        else:
            skipped += 1
    return added, skipped


def toggle_task_status(task_id: str) -> None:
    for task in st.session_state.saved_tasks:
        if task["id"] == task_id:
            task["status"] = "Done" if task.get("status") != "Done" else "To Do"
            return


def delete_task(task_id: str) -> None:
    st.session_state.saved_tasks = [
        t for t in st.session_state.saved_tasks if t.get("id") != task_id
    ]


def tasks_to_csv(tasks: list[dict], include_status: bool) -> str:
    output = io.StringIO()
    fieldnames = ["task", "due_date", "person", "priority"]
    if include_status:
        fieldnames.append("status")
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()

    for task in tasks:
        row = {
            "task": str(task.get("task", "")).strip(),
            "due_date": str(task.get("due_date") or "").strip(),
            "person": ", ".join(normalize_people(task)),
            "priority": str(task.get("priority", "Normal")).strip(),
        }
        if include_status:
            row["status"] = str(task.get("status", "To Do")).strip()
        writer.writerow(row)
    return output.getvalue()


def _calendar_dates_from_due_text(due_text: str | None) -> str | None:
    if not due_text:
        return None
    lowered = due_text.lower().strip()
    now = datetime.now(timezone.utc)
    if lowered == "today":
        start = now.replace(hour=9, minute=0, second=0, microsecond=0)
    elif lowered == "tomorrow":
        start = (now + timedelta(days=1)).replace(hour=9, minute=0, second=0, microsecond=0)
    else:
        return None
    end = start + timedelta(hours=1)
    return f"{start.strftime('%Y%m%dT%H%M%SZ')}/{end.strftime('%Y%m%dT%H%M%SZ')}"


def generate_calendar_link(task: dict) -> str:
    title = f"Task: {task.get('task', 'Untitled task')}"
    due_text = str(task.get("due_date") or "").strip()
    people = ", ".join(normalize_people(task)) or "Not specified"
    priority = str(task.get("priority", "Normal")).strip() or "Normal"
    details = f"Due (original text): {due_text or 'Not specified'}\nPeople: {people}\nPriority: {priority}"
    base = "https://calendar.google.com/calendar/render?action=TEMPLATE"
    text_part = f"&text={quote_plus(title)}"
    details_part = f"&details={quote_plus(details)}"
    dates = _calendar_dates_from_due_text(due_text)
    dates_part = f"&dates={dates}" if dates else ""
    return f"{base}{text_part}{details_part}{dates_part}"


def generate_bulk_calendar_link(tasks: list[dict]) -> str:
    if not tasks:
        return "https://calendar.google.com/calendar/render"
    n = len(tasks)
    title = f"Inbox IQ: {n} action item{'s' if n != 1 else ''}"
    lines: list[str] = []
    for i, task in enumerate(tasks, start=1):
        t = str(task.get("task", "")).strip() or "Untitled task"
        d = str(task.get("due_date") or "").strip() or "—"
        ppl = ", ".join(normalize_people(task)) or "—"
        pr = str(task.get("priority", "Normal")).strip() or "Normal"
        lines.append(f"{i}. {t}\n   Due: {d} | People: {ppl} | Priority: {pr}")
    details = "Action items (Inbox IQ)\n\n" + "\n\n".join(lines)
    base = "https://calendar.google.com/calendar/render?action=TEMPLATE"
    return f"{base}&text={quote_plus(title)}&details={quote_plus(details)}"


