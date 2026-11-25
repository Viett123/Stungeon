"""Bayesian Knowledge Tracing (ai/mastery.py). The expected numbers were worked out by hand."""
import pytest

from ai.mastery import KnowledgeTracker


def test_right_answer_from_the_start():
    tracker = KnowledgeTracker()
    tracker.update("articles", True, guess=0.25)
    assert tracker.mastery("articles") == pytest.approx(0.553, abs=0.001)

def test_wrong_answer_from_the_start():
    tracker = KnowledgeTracker()
    tracker.update("articles", False, guess=0.25)
    assert tracker.mastery("articles") == pytest.approx(0.177, abs=0.001)

def test_typed_right():
    tracker = KnowledgeTracker()
    tracker.update("articles", True, guess=0.02)
    assert tracker.mastery("articles") == pytest.approx(0.931, abs=0.001)

def test_ten_right_in_a_row():
    tracker = KnowledgeTracker()
    for _ in range(10):
        tracker.update("articles", True, guess=0.25)
    assert tracker.mastery("articles") > 0.9
