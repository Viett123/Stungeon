"""Question engine (owner: C). No pygame here.

How a question is picked (README rules 4 and 5):
  1. Keep only questions from Einheiten 1..floor with the wanted difficulty.
  2. Pick a TOPIC first, weighted so low-mastery topics come up more often.
     (Without this, grammar would almost never appear: ~70 grammar vs ~1,000 vocab questions.)
  3. Pick a random question inside that topic.
  weakest=True (ultimate moves, bosses) only uses the player's 3 weakest topics.

`topic` may be one topic name or a list of them (an enemy's topics). If none of those
topics has a question at this floor and difficulty, any topic is used instead.
"""
import json
import random
from collections import defaultdict
from pathlib import Path

BANK_PATH = Path(__file__).parent / "data" / "questions_german_b1.json"

_UMLAUTS = {"ä": "ae", "ö": "oe", "ü": "ue"}   # many keyboards have no umlaut keys


def normalise(text):
    """Make answers comparable: ignore case and extra spaces, accept ae/oe/ue/ss."""
    text = " ".join(str(text).split()).casefold()   # casefold also turns ß into ss
    for umlaut, plain in _UMLAUTS.items():
        text = text.replace(umlaut, plain)
    return text


class QuestionEngine:
    def __init__(self, bank_path=BANK_PATH, rng=None, tracker=None):
        bank = json.loads(Path(bank_path).read_text(encoding="utf-8"))
        self.questions = bank["questions"]
        self.topics = sorted({q["topic"] for q in self.questions})
        self.rng = rng or random.Random()
        self.tracker = tracker            # a KnowledgeTracker, or None
        self.stats = defaultdict(lambda: {"asked": 0, "correct": 0})   # topic -> counts

    # --- picking -----------------------------------------------------------
    def _pool(self, floor, difficulty):
        return [q for q in self.questions if q["einheit"] <= floor and q["difficulty"] == difficulty]

    def _mastery(self, topic):
        return self.tracker.mastery(topic) if self.tracker else 0.5

    def next_question(self, floor, difficulty, topic=None, weakest=False) -> dict:
        pool = self._pool(floor, difficulty)
        if not pool:
            raise ValueError(f"no {difficulty} question for floor {floor}")
        by_topic = defaultdict(list)
        for q in pool:
            by_topic[q["topic"]].append(q)

        wanted = [topic] if isinstance(topic, str) else list(topic or [])
        candidates = [t for t in wanted if t in by_topic] or sorted(by_topic)
        if weakest:
            candidates = sorted(candidates, key=self._mastery)[:3]

        # Lower mastery -> bigger weight. +0.1 so a mastered topic still shows up sometimes.
        weights = [1.0 - self._mastery(t) + 0.1 for t in candidates]
        chosen_topic = self.rng.choices(candidates, weights=weights)[0]

        question = dict(self.rng.choice(by_topic[chosen_topic]))   # a copy, never change the bank
        if "choices" in question:
            # Correct answers are listed first in the file, so always shuffle.
            question["choices"] = self.rng.sample(question["choices"], len(question["choices"]))
        return question

    # --- checking ----------------------------------------------------------
    def check_answer(self, question, given) -> bool:
        answer = question["answer"]
        if isinstance(answer, list):   # multi_select: exactly the right set
            return {normalise(g) for g in given} == {normalise(a) for a in answer}
        accepted = [answer] + question.get("accept", [])
        return normalise(given) in {normalise(a) for a in accepted}

    def report_answer(self, question, correct, seconds) -> None:
        stats = self.stats[question["topic"]]
        stats["asked"] += 1
        stats["correct"] += int(bool(correct))
        if self.tracker:
            self.tracker.update(question["topic"], correct)

    def to_typed(self, question) -> dict:
        """Blind debuff: turn a multiple-choice question into a typed one (README rule 3)."""
        typed = dict(question, type="typed")
        typed.pop("choices", None)
        if question["topic"] == "vocabulary" and "word" in question:
            typed["answer"] = question["word"]
        return typed


def answer_text(question) -> str:
    """The correct answer as one line of text, for the feedback screen."""
    answer = question["answer"]
    return ", ".join(answer) if isinstance(answer, list) else str(answer)
