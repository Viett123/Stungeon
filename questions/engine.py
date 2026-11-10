"""Question engine (owner: C). No pygame here.

PLACEHOLDER: picks a random question that fits the floor and difficulty.
TODO(C): pick the topic first, weighted by low mastery (README rule 4), and for
weakest=True draw from KnowledgeTracker.weakest() (rule 5).
"""
import json
import random
from pathlib import Path

BANK_PATH = Path(__file__).parent / "data" / "questions_german_b1.json"


def _normalise(text):
    # casefold() also turns "ß" into "ss", so "Straße" and "strasse" match.
    return " ".join(str(text).split()).casefold()


class QuestionEngine:
    def __init__(self, bank_path=BANK_PATH, rng=None):
        bank = json.loads(Path(bank_path).read_text(encoding="utf-8"))
        self.questions = bank["questions"]
        self.topics = sorted({q["topic"] for q in self.questions})
        self.rng = rng or random.Random()

    def next_question(self, floor, difficulty, topic=None, weakest=False) -> dict:
        # Floor n uses Einheiten 1..n (cumulative floors).
        pool = [q for q in self.questions
                if q["einheit"] <= floor and q["difficulty"] == difficulty
                and (topic is None or q["topic"] == topic)]
        if not pool:
            raise ValueError(f"no {difficulty} question for floor {floor}, topic {topic}")
        question = dict(self.rng.choice(pool))   # a copy, so we never change the bank
        if "choices" in question:
            # Correct answers are listed first in the file, so always shuffle.
            question["choices"] = self.rng.sample(question["choices"], len(question["choices"]))
        return question

    def check_answer(self, question, given) -> bool:
        answer = question["answer"]
        if isinstance(answer, list):   # multi_select: exactly the right set
            return {_normalise(g) for g in given} == {_normalise(a) for a in answer}
        accepted = [answer] + question.get("accept", [])
        return _normalise(given) in {_normalise(a) for a in accepted}
        # TODO(C): optionally accept ae/oe/ue for ä/ö/ü (README rule 2)

    def report_answer(self, question, correct, seconds) -> None:
        pass   # TODO(C): update the KnowledgeTracker for question["topic"]

    def to_typed(self, question) -> dict:
        """Blind debuff: turn a multiple-choice question into a typed one (README rule 3)."""
        typed = dict(question, type="typed")
        typed.pop("choices", None)
        if question["topic"] == "vocabulary" and "word" in question:
            typed["answer"] = question["word"]
        return typed
