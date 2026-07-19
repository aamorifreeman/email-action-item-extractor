"""Rule engine, date resolver, priority, and pipeline unit tests."""

from __future__ import annotations

from datetime import datetime

from app.ml.base import TaskItem
from app.ml.date_resolver import resolve_due_date
from app.ml.pipeline import compare_engines, enrich, run_pipeline, semantic_dedup
from app.ml.priority import score_priority
from app.ml.rule_based import RuleBasedExtractor

SAMPLE = (
    "Hey team, can you send the final slides to Marcus by Friday, "
    "follow up with Jasmine next week, and review the budget before the meeting?"
)


def test_rule_engine_extracts_and_is_deterministic():
    engine = RuleBasedExtractor()
    first = [i.task for i in engine.extract(SAMPLE)]
    second = [i.task for i in engine.extract(SAMPLE)]
    assert first == second
    assert len(first) >= 3
    # Polite prefix should be stripped and text sentence-cased.
    assert any(t.startswith("Send the final slides") for t in first)
    assert all(not t.lower().startswith("can you") for t in first)


def test_date_resolver_relative_phrases():
    base = datetime(2026, 7, 19)  # a Sunday
    assert resolve_due_date("today", base=base) == "2026-07-19"
    assert resolve_due_date("tomorrow", base=base) == "2026-07-20"
    assert resolve_due_date("eod", base=base) == "2026-07-19"
    assert resolve_due_date(None) is None
    assert resolve_due_date("", base=base) is None
    # A weekday resolves to a concrete future date.
    assert resolve_due_date("Friday", base=base) is not None


def test_priority_scoring():
    high_label, high_score = score_priority("finish this ASAP", None)
    normal_label, normal_score = score_priority("review the budget", None)
    assert high_label == "High"
    assert high_score > normal_score
    assert normal_label == "Normal"


def test_enrich_populates_scores():
    items = [TaskItem(task="Send the slides to Marcus", source_sentence="x", due_date_text="today")]
    enriched = enrich(items)
    assert enriched[0].due_date_iso is not None
    assert enriched[0].confidence > 0.0
    assert enriched[0].priority in {"High", "Normal"}


def test_semantic_dedup_merges_duplicates():
    items = [
        TaskItem(task="Send the report to Alex", source_sentence="a", people=["Alex"]),
        TaskItem(task="Send the report to Alex", source_sentence="b", people=["Sam"]),
    ]
    deduped = semantic_dedup(items, threshold=0.9)
    assert len(deduped) == 1
    # People from the merged duplicate are folded in.
    assert set(deduped[0].people) == {"Alex", "Sam"}


def test_compare_identical_sets_fully_match():
    rule = run_pipeline(RuleBasedExtractor().extract(SAMPLE))
    report = compare_engines(rule, rule, threshold=0.9)
    assert report.matched == len(rule)
    assert report.rule_only == 0
    assert report.gemini_only == 0
