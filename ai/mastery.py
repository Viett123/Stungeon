"""Knowledge tracing per topic (owner: C). No pygame here.

PLACEHOLDER: every topic starts at 0.5 and never changes.
TODO(C): Bayesian Knowledge Tracing (prior, learn, slip, guess) updated after each answer.
"""


class KnowledgeTracker:
    def __init__(self):
        self._mastery = {}   # topic -> chance (0.0 to 1.0) the player knows it

    def mastery(self, topic) -> float:
        return self._mastery.get(topic, 0.5)

    def weakest(self, n, topics) -> list[str]:
        return sorted(topics, key=self.mastery)[:n]

    def to_dict(self):
        return dict(self._mastery)

    @classmethod
    def from_dict(cls, data):
        tracker = cls()
        tracker._mastery = dict(data)
        return tracker
