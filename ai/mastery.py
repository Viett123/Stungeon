"""Knowledge tracing per topic (owner: C). No pygame here.

Bayesian Knowledge Tracing (BKT) keeps, for every topic, a guess of how likely it is
that the player really knows it (0.0 to 1.0). After each answer that guess is updated:

  1. A right answer can mean "knows it and did not slip" or "did not know it and guessed".
     A wrong answer can mean "knows it but slipped" or "did not know it".
     Bayes' rule weighs these against each other to get the new chance.
  2. Then the player may have learned from the question: a share (learn) of what
     is left to know is added.

The four numbers of BKT:
  init   how likely a new topic is already known
  slip   the chance of a wrong answer although the player knows it
  learn  the chance one question teaches the topic
  guess  the chance of a right answer by luck; it depends on the question type,
         so the question engine passes it in (a typed answer is hard to guess)
The numbers are in data/progression.json, under "mastery".
"""
from systems.player import load_data

_NUMBERS = load_data("progression.json")["mastery"]
P_INIT = _NUMBERS["p_init"]      # the score every topic starts with
P_SLIP = _NUMBERS["p_slip"]      # knows it, but answers wrong
P_LEARN = _NUMBERS["p_learn"]    # chance one question teaches it


class KnowledgeTracker:
    def __init__(self):
        self._mastery = {}   # topic -> chance (0.0 to 1.0) the player knows it

    def mastery(self, topic) -> float:
        return self._mastery.get(topic, P_INIT)

    def update(self, topic, correct, guess=0.25) -> None:
        """guess: the chance of a right answer by luck (the engine works it out from the question type)."""
        p = self.mastery(topic)

        if correct:
            knows = p * (1 - P_SLIP)
            guessed = (1 - p) * guess
            after = knows / (knows + guessed)
        else:
            knows = p * P_SLIP
            missed = (1 - p) * (1 - guess)
            after = knows / (knows + missed)

        self._mastery[topic] = after + P_LEARN * (1 - after)

    def weakest(self, n, topics) -> list[str]:
        return sorted(topics, key=self.mastery)[:n]

    def to_dict(self):
        return dict(self._mastery)

    @classmethod
    def from_dict(cls, data):
        tracker = cls()
        tracker._mastery = dict(data)
        return tracker
