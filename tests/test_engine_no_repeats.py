"""The engine asks every question of a topic once before it asks one again."""
import random
from collections import Counter

from questions.engine import QuestionEngine


def test_a_small_topic_goes_through_all_its_questions_before_repeating():
    engine = QuestionEngine(rng=random.Random(4))
    pool_size = len([q for q in engine.questions
                     if q["topic"] == "konjunktiv2_praesens" and q["difficulty"] == "medium" and q["einheit"] <= 3])
    asked = [engine.next_question(3, "medium", topic="konjunktiv2_praesens")["id"] for _ in range(pool_size * 2)]
    first, second = asked[:pool_size], asked[pool_size:]
    assert len(set(first)) == pool_size                     # no repeat in the first round
    assert Counter(asked) == Counter({q: 2 for q in first})  # then each exactly once more


def test_the_same_seed_still_asks_the_same_questions():
    one = QuestionEngine(rng=random.Random(9))
    two = QuestionEngine(rng=random.Random(9))
    assert [one.next_question(2, "easy")["id"] for _ in range(30)] == [two.next_question(2, "easy")["id"] for _ in range(30)]


def test_every_b1_grammar_topic_has_enough_questions_per_difficulty():
    """8 easy, 8 medium, 6 hard: more than one run asks (tools/simulate_players.py counted up to
    13 easy questions of one topic in a run, most runs fewer than 8). Together with the no-repeat
    pick, a fight no longer asks the same question twice."""
    engine = QuestionEngine()
    counts = Counter((q["topic"], q["difficulty"]) for q in engine.questions)
    grammar = {q["topic"] for q in engine.questions} - {"vocabulary", "articles", "plurals"}
    for topic in grammar:
        assert counts[(topic, "easy")] >= 8, topic
        assert counts[(topic, "medium")] >= 8, topic
        assert counts[(topic, "hard")] >= 6, topic
