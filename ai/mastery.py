"""Knowledge tracing per topic"""

P_INIT = 0.2    # the score every topic starts with
P_SLIP = 0.1    # knows it, but answers wrong
P_LEARN = 0.15  # chance one question teaches it

class KnowledgeTracker:
    def __init__(self):
        self._mastery = {}   # topic -> chance (0.0 to 1.0) the player knows it

    def mastery(self, topic) -> float:
        return self._mastery.get(topic, P_INIT)

    def update(self, topic, correct, guess = 0.25) -> None:
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
