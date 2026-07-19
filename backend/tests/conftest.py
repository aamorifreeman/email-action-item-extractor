"""Shared test fixtures.

Point the app at a throwaway SQLite file *before* importing anything that
builds the engine, then give each test a clean schema.
"""

from __future__ import annotations

import os

os.environ.setdefault("DATABASE_URL", "sqlite:///./test_inboxiq.db")
os.environ.setdefault("GEMINI_API_KEY", "")

import pytest
from fastapi.testclient import TestClient

from app.database import Base, engine
from app.main import app


@pytest.fixture(autouse=True)
def _fresh_schema():
    """Drop and recreate all tables around every test for isolation."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


SAMPLE_EMAIL = (
    "Hey team, can you send the final slides to Marcus by Friday, "
    "follow up with Jasmine next week, and review the budget before the meeting? "
    "This is important and should be done ASAP."
)
