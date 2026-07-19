"""API tests: extraction, task CRUD, Gemini fallback and mocked success."""

from __future__ import annotations

import app.services.extraction_service as extraction_service
from app.ml.base import TaskItem
from tests.conftest import SAMPLE_EMAIL


def test_extract_rule_engine(client):
    resp = client.post("/api/extract", json={"email_text": SAMPLE_EMAIL, "engine": "rule"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["engine"] == "rule"
    assert body["count"] >= 3
    assert body["fallback_used"] is False
    item = body["items"][0]
    assert {"task", "confidence", "priority_score", "due_date_iso"} <= item.keys()


def test_extract_gemini_without_key_falls_back(client):
    # No GEMINI_API_KEY in the test env -> Gemini raises -> rule fallback.
    resp = client.post("/api/extract", json={"email_text": SAMPLE_EMAIL, "engine": "gemini"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["fallback_used"] is True
    assert body["engine"] == "rule"
    assert body["fallback_reason"]


def test_extract_gemini_mocked_success(client, monkeypatch):
    def fake_extract(self, email_text):
        return [TaskItem(task="Ship the release", source_sentence=email_text, engine="gemini")]

    monkeypatch.setattr(
        "app.ml.gemini.GeminiExtractor.extract", fake_extract, raising=True
    )
    resp = client.post("/api/extract", json={"email_text": "ship it", "engine": "gemini"})
    body = resp.json()
    assert body["engine"] == "gemini"
    assert body["fallback_used"] is False
    assert body["items"][0]["task"] == "Ship the release"


def test_task_crud_and_bulk_dedup(client):
    extracted = client.post(
        "/api/extract", json={"email_text": SAMPLE_EMAIL, "engine": "rule"}
    ).json()["items"]

    added = client.post("/api/tasks/bulk", json={"tasks": extracted}).json()
    assert added["added"] >= 3
    # Saving the same set again should be fully skipped (dedup).
    again = client.post("/api/tasks/bulk", json={"tasks": extracted}).json()
    assert again["added"] == 0
    assert again["skipped"] == added["added"]

    tasks = client.get("/api/tasks").json()
    assert len(tasks) == added["added"]

    tid = tasks[0]["id"]
    assert client.post(f"/api/tasks/{tid}/toggle").json()["status"] == "Done"
    assert client.delete(f"/api/tasks/{tid}").status_code == 204
    assert len(client.get("/api/tasks").json()) == added["added"] - 1


def test_csv_export(client):
    extracted = client.post(
        "/api/extract", json={"email_text": SAMPLE_EMAIL, "engine": "rule"}
    ).json()["items"]
    client.post("/api/tasks/bulk", json={"tasks": extracted})
    resp = client.get("/api/tasks/export.csv")
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("text/csv")
    assert resp.text.splitlines()[0] == "task,due_date,person,priority,confidence,status"


def test_calendar_links(client):
    extracted = client.post(
        "/api/extract", json={"email_text": SAMPLE_EMAIL, "engine": "rule"}
    ).json()["items"]
    resp = client.post("/api/integrations/calendar-link", json={"tasks": extracted})
    body = resp.json()
    assert body["bulk_url"].startswith("https://calendar.google.com")
    assert len(body["item_urls"]) == len(extracted)


def test_compare_endpoint(client):
    resp = client.post("/api/extract/compare", json={"email_text": SAMPLE_EMAIL})
    assert resp.status_code == 200
    body = resp.json()
    assert body["rule"]
    # No Gemini key in tests -> gemini side empty with an error string.
    assert body["gemini"] == []
    assert body["gemini_error"]
    assert set(body["agreement"]) == {"matched", "rule_only", "gemini_only", "mean_similarity"}
