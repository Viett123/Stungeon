"""Knowledge tracing per topic (owner: C). No pygame here.

PLACEHOLDER: every topic stays at 0.5, so the question engine treats all topics the same.
TODO(C): Bayesian Knowledge Tracing in update(): P(known) changes after each answer
using four parameters (prior, learn, slip, guess). This is the part to write by hand.
"""


class KnowledgeTracker:
    def __init__(self):
        self._mastery = {}   # topic -> chance (0.0 to 1.0) the player knows it

    def mastery(self, topic) -> float:
        return self._mastery.get(topic, 0.5)

    def update(self, topic, correct) -> None:
        pass   # TODO(C): the BKT update goes here

    def weakest(self, n, topics) -> list[str]:
        return sorted(topics, key=self.mastery)[:n]

    def to_dict(self):
        return dict(self._mastery)

    @classmethod
    def from_dict(cls, data):
        tracker = cls()
        tracker._mastery = dict(data)
        return tracker
