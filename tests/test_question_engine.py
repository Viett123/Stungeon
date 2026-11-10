import random

from ai.mastery import KnowledgeTracker
from questions.engine import QuestionEngine, normalise

engine = QuestionEngine(rng=random.Random(1))


def test_bank_loads():
    assert len(engine.questions) == 1082


def test_floor_1_only_uses_einheit_1():
    for _ in range(50):
        assert engine.next_question(floor=1, difficulty="medium")["einheit"] == 1


def test_topic_first_means_grammar_actually_appears():
    topics = {engine.next_question(floor=3, difficulty="easy")["topic"] for _ in range(300)}
    assert len(topics) > 5   # picking questions directly would give almost only vocabulary


def test_enemy_topics_are_respected():
    for _ in range(30):
        q = engine.next_question(floor=1, difficulty="medium", topic=["articles", "um_zu"])
        assert q["topic"] in ("articles", "um_zu")


def test_falls_back_when_topic_has_no_such_question():
    q = engine.next_question(floor=1, difficulty="easy", topic="plurals")   # plurals are all hard
    assert q["difficulty"] == "easy"


def test_weakest_uses_low_mastery_topics():
    tracker = KnowledgeTracker.from_dict({t: 0.9 for t in engine.topics} | {"plurals": 0.1})
    weak_engine = QuestionEngine(rng=random.Random(2), tracker=tracker)
    picked = {weak_engine.next_question(3, "hard", weakest=True)["topic"] for _ in range(30)}
    assert "plurals" in picked and len(picked) <= 3


def test_question_is_a_copy():
    q = engine.next_question(floor=3, difficulty="easy")
    q["answer"] = "changed"
    assert all(original["answer"] != "changed" for original in engine.questions)


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


def test_report_answer_counts_per_topic():
    e = QuestionEngine(rng=random.Random(3))
    q = e.next_question(1, "easy")
    e.report_answer(q, True, 4)
    e.report_answer(q, False, 4)
    assert e.stats[q["topic"]] == {"asked": 2, "correct": 1}
