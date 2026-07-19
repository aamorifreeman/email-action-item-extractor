"""Resolve human due-date phrases to concrete ISO dates.

Turns "Friday", "next week", "EOD" into an absolute YYYY-MM-DD using
dateparser, relative to the current day. The original phrase is always
preserved separately on the TaskItem.
"""

from __future__ import annotations

from datetime import datetime

import dateparser

# "EOD"/"end of day" mean today; dateparser doesn't handle them.
_TODAY_ALIASES = {"eod", "end of day", "tonight", "cob", "close of business"}


def resolve_due_date(phrase: str | None, *, base: datetime | None = None) -> str | None:
    """Resolve a due phrase to an ISO date string (YYYY-MM-DD), or None."""
    if not phrase or not phrase.strip():
        return None

    base = base or datetime.now()
    text = phrase.strip().lower()

    if text in _TODAY_ALIASES:
        return base.date().isoformat()

    parsed = dateparser.parse(
        phrase,
        languages=["en"],
        settings={
            "RELATIVE_BASE": base,
            "PREFER_DATES_FROM": "future",
            "RETURN_AS_TIMEZONE_AWARE": False,
        },
    )
    return parsed.date().isoformat() if parsed else None
