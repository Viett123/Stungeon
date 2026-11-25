"""The German A1 question bank (questions/data/questions_german_a1.json) and how floors use it."""
import json
import random
from pathlib import Path

import pytest

from core.run import new_run
from questions.engine import QuestionEngine
from systems import dungeons

DATA = Path(__file__).resolve().parent.parent / "questions" / "data"
A1 = DATA / "questions_german_a1.json"
B1 = DATA / "questions_german_b1.json"
BANK = json.loads(A1.read_text(encoding="utf-8"))
QUESTIONS = BANK["questions"]


def test_the_a1_bank_has_many_questions_with_unique_ids():
    assert len(QUESTIONS) > 3000
    ids = [q["id"] for q in QUESTIONS]
    assert len(ids) == len(set(ids))
    assert all(q["level"] == "A1" and q["subject"] == "german" for q in QUESTIONS)


def test_every_einheit_from_1_to_16_has_questions():
    assert {q["einheit"] for q in QUESTIONS} == set(range(1, 17))


def test_answers_are_among_the_choices_and_no_choice_is_listed_twice():
    for q in QUESTIONS:
        if q["type"] == "multiple_choice":
            assert q["answer"] in q["choices"], q["id"]
        if q["type"] == "multi_select":
            assert set(q["answer"]) <= set(q["choices"]), q["id"]
        if "choices" in q:
            assert len(set(q["choices"])) == len(q["choices"]), q["id"]


def test_a_typed_question_has_only_one_right_answer():
    """The same prompt must never expect two different words (e.g. "to know": kennen or wissen)."""
    answers = {}
    for q in QUESTIONS:
        if q["type"] == "typed" and q["topic"] == "vocabulary":
            answers.setdefault(q["question"], set()).add(q["answer"])
    assert all(len(found) == 1 for found in answers.values())


def test_plural_only_nouns_get_no_article_question():
    assert not [q for q in QUESTIONS if q["topic"] == "articles" and q["question"].startswith("___ Eltern")]


def test_grammar_topics_are_big_enough_to_be_picked_often():
    """_choose picks a topic first, so a topic with one question would repeat it again and again."""
    grammar = [q for q in QUESTIONS if q["source"] == "einheit_text_grammar"]
    counts = {}
    for q in grammar:
        counts[q["topic"]] = counts.get(q["topic"], 0) + 1
    assert min(counts.values()) >= 4


@pytest.mark.parametrize("floor", [1, 2, 3])
def test_every_floor_has_easy_medium_and_hard_questions(floor):
    engine = QuestionEngine(A1, rng=random.Random(1))
    for difficulty in ("easy", "medium", "hard"):
        assert engine.next_question(floor, difficulty)


def test_floors_spread_the_16_einheiten_and_stay_cumulative():
    engine = QuestionEngine(A1, rng=random.Random(2))
    assert [engine.last_einheit(floor) for floor in (1, 2, 3)] == [5, 10, 16]
    asked = {engine.next_question(1, "medium")["einheit"] for _ in range(300)}
    assert max(asked) <= 5
    asked = {engine.next_question(3, "medium")["einheit"] for _ in range(600)}
    assert max(asked) > 10 and min(asked) <= 5               # the last floor still asks early Einheiten


def test_b1_still_uses_einheit_n_on_floor_n():
    engine = QuestionEngine(B1, rng=random.Random(3))
    assert [engine.last_einheit(floor) for floor in (1, 2, 3)] == [1, 2, 3]


def test_a_run_at_level_a1_asks_a1_questions():
    assert dungeons.is_playable("german", "A1")
    run = new_run("mage", seed=4, subject="german", level="A1")
    question = run.engine.next_question(1, "easy")
    assert question["level"] == "A1"
