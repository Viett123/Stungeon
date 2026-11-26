"""Adaptive enemies (owner: C). No pygame here.

Watches how the player fights and changes the enemy once per fight:
- spammer rule: the same move several turns in a row -> the enemy hits harder.
  The numbers are "habits" in data/combat.json, the taunt text is in core/strings_en.json.
TODO(C): weak-spot rule.
"""
from systems.player import load_data


class HabitTracker:
    def __init__(self, tracker=None):
        self.history = []        # one entry per answer
        self.tracker = tracker   # the BKT KnowledgeTracker (for the weak-spot rule)
        self.turns = []          # one move id per player turn (an Ultimate's 3 answers = 1 turn)
        self.seen = 0            # how many history entries are already counted in turns
        self.enemy = None        # the enemy of the current fight (the object itself, not its id())
        self.rules = load_data("combat.json")["habits"]   # the numbers for the spammer rule

    def record_move(self, move_id, tier, seconds_ratio, correct, topic=None) -> None:
        self.history.append({"move_id": move_id, "tier": tier,
                             "seconds_ratio": seconds_ratio, "correct": correct,
                             "topic": topic})

    def adapt(self, enemy) -> str | None:
        """Called after every enemy turn, also one the enemy lost. Returns a taunt key when it
        changes the enemy. The mark enemy.adapted makes sure that happens only once per enemy."""
        if enemy is not self.enemy:        # "is" compares the object, not a reusable number
            self.enemy = enemy
            self.turns = []
        self._count_turn()
        if enemy.adapted:
            return None
        last = self.turns[-self.rules["spam_turns"]:]
        if len(last) == self.rules["spam_turns"] and len(set(last)) == 1:
            enemy.damage = round(enemy.damage * self.rules["spam_damage"])
            enemy.adapted = True
            return "taunt_spam"
        return None

    def _count_turn(self) -> None:
        """Turn the answers given since the last call into one turn."""
        new = self.history[self.seen:]
        self.seen = len(self.history)
        if new:
            self.turns.append(new[-1]["move_id"])   # the newest answer belongs to this turn
