"""Tests for the finished parts of the question engine.

 e.g. "grammar topics appear" and "enemy topics are respected".
"""
import random

from questions.engine import QuestionEngine, normalise

engine = QuestionEngine(rng=random.Random(1))

GRAMMAR_FREE = {"vocabulary", "articles", "plurals"}


def test_bank_loads():
    assert len(engine.questions) == 1082


def test_floor_1_only_uses_einheit_1():
    for _ in range(50):
        assert engine.next_question(floor=1, difficulty="medium")["einheit"] == 1


def test_difficulty_is_respected():
    for difficulty in ("easy", "medium", "hard"):
        assert engine.next_question(floor=3, difficulty=difficulty)["difficulty"] == difficulty


def test_next_question_asks_the_choose_hook():
    """Whatever _choose returns is the question that gets asked."""
    seen = {}

    class MyEngine(QuestionEngine):
        def _choose(self, pool, wanted_topics, weakest):
            seen.update(wanted=wanted_topics, weakest=weakest)
            return pool[0]

    mine = MyEngine(rng=random.Random(2))
    question = mine.next_question(floor=1, difficulty="easy", topic="articles", weakest=True)
    assert seen == {"wanted": ["articles"], "weakest": True}
    assert question["id"] == next(q["id"] for q in mine.questions
                                  if q["einheit"] <= 1 and q["difficulty"] == "easy")


def test_question_is_a_shuffled_copy():
    q = engine.next_question(floor=3, difficulty="easy")
    original = next(o for o in engine.questions if o["id"] == q["id"])
    assert sorted(q["choices"]) == sorted(original["choices"])
    q["answer"] = "changed"
    assert original["answer"] != "changed"


def test_typed_answer_ignores_case_spaces_and_umlaut_spelling():
    q = {"answer": "die Förderung", "accept": []}
    assert engine.check_answer(q, "  DIE förderung ")
    assert engine.check_answer(q, "die Foerderung")
    assert not engine.check_answer(q, "der Förderung")
    assert normalise("Straße") == normalise("strasse")


def test_multi_select_needs_exactly_the_right_set():
    q = {"answer": ["die Bühne", "die Rolle"]}
    assert engine.check_answer(q, ["die Rolle", "die Bühne"])
    assert not engine.check_answer(q, ["die Rolle"])


def test_report_answer_counts_per_topic_and_tells_the_tracker():
    told = []


def test_same_seed_asks_the_same_questions():
    first = QuestionEngine(rng=random.Random(5))
    second = QuestionEngine(rng=random.Random(5))
    ids_first = [first.next_question(2, "easy")["id"] for _ in range(20)]
    ids_second = [second.next_question(2, "easy")["id"] for _ in range(20)]
    assert ids_first == ids_second


def test_grammar_topics_are_asked():
    e = QuestionEngine(rng=random.Random(7))
    topics = [e.next_question(1, "medium")["topic"] for _ in range(200)]
    grammar = [t for t in topics if t not in GRAMMAR_FREE]
    assert len(grammar) >= 50


def test_enemy_topic_is_respected():
    e = QuestionEngine(rng=random.Random(8))
    for _ in range(50):
        assert e.next_question(1, "medium", topic=["articles"])["topic"] == "articles"

def test_report_answer_counts_per_topic_and_tells_the_tracker():
    told = []

    class FakeTracker:
        def mastery(self, topic):
            return 0.5

        def update(self, topic, correct, guess = 0.25):
            told.append((topic, correct, guess))
    

    e = QuestionEngine(rng=random.Random(3), tracker=FakeTracker())
    q = e.next_question(1, "easy")
    e.report_answer(q, True, 4)
    e.report_answer(q, False, 4)
    assert e.stats[q["topic"]] == {"asked": 2, "correct": 1}
    expected = 1 / len(q["choices"])
    assert told == [(q["topic"], True, expected), (q["topic"], False, expected)]


def test_to_typed_removes_the_choices():
    q = engine.next_question(floor=1, difficulty="medium")
    typed = engine.to_typed(q)
    assert typed["type"] == "typed" and "choices" not in typed
