import random

from questions.engine import QuestionEngine

engine = QuestionEngine(rng=random.Random(1))


def test_bank_loads():
    assert len(engine.questions) == 1082


def test_floor_1_only_uses_einheit_1():
    for _ in range(50):
        assert engine.next_question(floor=1, difficulty="medium")["einheit"] == 1


def test_question_is_a_copy():
    q = engine.next_question(floor=3, difficulty="easy")
    q["answer"] = "changed"
    assert all(original["answer"] != "changed" for original in engine.questions)


def test_typed_answer_ignores_case_and_spaces():
    q = {"answer": "die Bühne", "accept": ["Bühne"]}
    assert engine.check_answer(q, "  DIE bühne ")
    assert engine.check_answer(q, "bühne")
    assert not engine.check_answer(q, "der Bühne")


def test_multi_select_needs_exactly_the_right_set():
    q = {"answer": ["die Bühne", "die Rolle"]}
    assert engine.check_answer(q, ["die Rolle", "die Bühne"])
    assert not engine.check_answer(q, ["die Rolle"])
