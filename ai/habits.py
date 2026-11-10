"""Adaptive enemies (owner: C). No pygame here.

PLACEHOLDER: remembers moves but never changes the enemy.
TODO(C): the 3 adaptation rules + taunt lines (text goes in core/strings_en.json).
"""


class HabitTracker:
    def __init__(self):
        self.history = []

    def record_move(self, move_id, tier, seconds_ratio, correct) -> None:
        self.history.append({"move_id": move_id, "tier": tier,
                             "seconds_ratio": seconds_ratio, "correct": correct})

    def adapt(self, enemy) -> str | None:
        return None   # returns a taunt key when it changes the enemy
