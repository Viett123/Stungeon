"""Question engine (owner: C). No pygame here.

It loads the bank, keeps floors cumulative, shuffles the answers, checks answers and
counts right and wrong per topic. It also chooses WHICH question to ask (_choose):
first a topic, weighted towards the topics the player knows least (ai/mastery.py),
then a question inside that topic.
"""
import json
import random
from collections import Counter, defaultdict
from pathlib import Path

from systems.player import load_data

_NUMBERS = load_data("progression.json")["mastery"]
# Added to every topic's weight, so topics the player already knows still come back now and then.
REVIEW_WEIGHT = _NUMBERS["review_weight"]
GUESS_MULTI_SELECT = _NUMBERS["guess_multi_select"]   # ticking exactly the right set by luck is rare
GUESS_TYPED = _NUMBERS["guess_typed"]                 # typing the right answer by luck is very rare

BANK_PATH = Path(__file__).parent / "data" / "questions_german_b1.json"

_UMLAUTS = {"ä": "ae", "ö": "oe", "ü": "ue"}   # many keyboards have no umlaut keys


def normalise(text):
    """Make answers comparable: ignore case and extra spaces, accept ae/oe/ue/ss (README rule 2)."""
    text = " ".join(str(text).split()).casefold()   # casefold also turns ß into ss
    for umlaut, plain in _UMLAUTS.items():
        text = text.replace(umlaut, plain)
    return text


class QuestionEngine:
    def __init__(self, bank_path=BANK_PATH, rng=None, tracker=None):
        bank = json.loads(Path(bank_path).read_text(encoding="utf-8"))
        self.questions = bank["questions"]
        # The highest Einheit each floor asks about, e.g. A1 has 16 Einheiten on 3 floors.
        # A bank without "floor_einheiten" (B1) uses Einheit n on floor n.
        self.floor_einheiten = {int(floor): last for floor, last in bank.get("floor_einheiten", {}).items()}
        self.topics = sorted({q["topic"] for q in self.questions})
        self.rng = rng or random.Random()
        self.tracker = tracker            # a KnowledgeTracker (ai/mastery.py), or None
        self.stats = defaultdict(lambda: {"asked": 0, "correct": 0})   # topic -> counts, for the end screen
        self.streak = 0                   # right answers in a row; a wrong answer sets it back to 0
        self.asked = Counter()            # question id -> how often it was asked this run (no repeats)

    def last_einheit(self, floor) -> int:
        """The highest Einheit asked on this floor (the bank's "floor_einheiten", or the floor number)."""
        return self.floor_einheiten.get(floor, floor)

    # --- picking -----------------------------------------------------------
    def next_question(self, floor, difficulty, topic=None, weakest=False) -> dict:
        """Return one question for this floor and difficulty.

        topic   - one topic name, or a list of them (an enemy's topics), or None for any
        weakest - True for ultimate moves and bosses: prefer the player's weakest topics
        """
        # Floors are cumulative (README rule 5): floor n uses Einheiten 1 to last_einheit(n).
        last = self.last_einheit(floor)
        pool = [q for q in self.questions if q["einheit"] <= last and q["difficulty"] == difficulty]
        if not pool:
            raise ValueError(f"no {difficulty} question for floor {floor}")
        wanted = [topic] if isinstance(topic, str) else list(topic or [])

        question = dict(self._choose(pool, wanted, weakest))   # a copy, so the bank never changes
        if "choices" in question:
            # Correct answers are listed first in the file, so always shuffle (README rule 1).
            question["choices"] = self.rng.sample(question["choices"], len(question["choices"]))
        return question

    def _choose(self, pool, wanted_topics, weakest) -> dict:
        """Pick one question out of `pool` (written by owner C).

        The bank has ~1,000 vocabulary questions and ~70 grammar questions, so picking a
        question at random would almost never ask grammar. Instead (questions/README.md):
          - rule 4: pick a TOPIC first, weighted by low mastery, then a question inside it.
            weight = 1 - mastery + REVIEW_WEIGHT, so weak topics come up most.
          - the enemy's topics (wanted_topics) are used when the pool has questions for them
          - rule 5: when weakest is True (ultimates), only the 3 weakest topics are used
        Always returns one of the dicts in `pool`. Uses self.rng (not the random module),
        so a run with the same seed asks the same questions.
        """
        by_topic = {}
        for question in pool:
            by_topic.setdefault(question["topic"], []).append(question)
        topics = sorted(by_topic)
        if wanted_topics:
            topics = [t for t in topics if t in wanted_topics] or topics

        def score(topic):
            if self.tracker:
                mastery = self.tracker.mastery(topic)
                return mastery
            return 0.5   # no tracker, so all topics are equal
        if weakest:
            topics = sorted(topics, key=score)[:3]
        weights = []
        for topic in topics:
            weights.append(1.0 - score(topic) + REVIEW_WEIGHT)
        topic = self.rng.choices(topics, weights=weights)[0]
        # Inside the topic, only the questions asked the fewest times: every question is asked
        # once before any comes back (play-test, 26 Nov 2026: the same question kept repeating).
        fewest = min(self.asked[question_key(q)] for q in by_topic[topic])
        question = self.rng.choice([q for q in by_topic[topic] if self.asked[question_key(q)] == fewest])
        self.asked[question_key(question)] += 1
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
        self.streak = self.streak + 1 if correct else 0
        if self.tracker:
            if question.get("type") == "multiple_choice":
                guess = 1.0 / len(question["choices"])
            elif question.get("type") == "multi_select":
                guess = GUESS_MULTI_SELECT
            else:              # typed, or anything unexpected
                guess = GUESS_TYPED
            self.tracker.update(question["topic"], correct, guess)

    def to_typed(self, question) -> dict:
        """Blind debuff: turn a multiple-choice question into a typed one (README rule 3)."""
        typed = dict(question, type="typed")
        typed.pop("choices", None)
        if question["topic"] == "vocabulary" and "word" in question:
            typed["answer"] = question["word"]
        return typed


def question_key(question):
    """What tells questions apart: the id (every bank question has one), else the text."""
    return question.get("id") or question.get("question")


def answer_text(question) -> str:
    """The correct answer as one line of text, for the feedback screen."""
    answer = question["answer"]
    return ", ".join(answer) if isinstance(answer, list) else str(answer)
