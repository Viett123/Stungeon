"""Adaptive enemies (owner: C). No pygame here.

Watches how the player fights and changes the enemy once per fight (at most one rule per enemy):
- weak-spot rule: a topic the player was asked and knows badly (mastery below weak_below) ->
  the enemy asks about that topic. Checked first: it makes the player practise, not lose.
- spammer rule: the same move several turns in a row -> the enemy hits harder. The turns are
  counted over the whole floor, not per fight: fights are short (about 3 answers), so counting
  per fight meant the enemy was usually dead before it could notice (play-test, 26 Nov 2026).
adapt() is called when a fight opens and after every enemy turn, so an enemy can greet you with
what it noticed in your earlier fights.
The numbers are "habits" in data/combat.json, the taunt texts are in core/strings_en.json.
"""
from systems.player import load_data


class HabitTracker:
    def __init__(self, tracker=None):
        self.history = []        # one entry per answer
        self.tracker = tracker   # the BKT KnowledgeTracker (for the weak-spot rule)
        self.turns = []          # one move id per player turn (an Ultimate's 3 answers = 1 turn)
        self.seen = 0            # how many history entries are already counted in turns
        self.rules = load_data("combat.json")["habits"]   # the numbers for both rules
        self.taunt_values = {}   # what goes into the last taunt's {placeholders}, e.g. {"topic": "articles"}

    def record_move(self, move_id, tier, seconds_ratio, correct, topic=None) -> None:
        self.history.append({"move_id": move_id, "tier": tier,
                             "seconds_ratio": seconds_ratio, "correct": correct,
                             "topic": topic})

    def adapt(self, enemy) -> str | None:
        """Called when a fight opens and after every enemy turn (also one the enemy lost).
        Returns a taunt key when it changes the enemy. The mark enemy.adapted makes sure that
        happens only once per enemy."""
        self._count_turn()
        self.taunt_values = {}
        if enemy.adapted:
            return None
        weak = self.weak_topic()
        if weak and enemy.topics != [weak]:
            enemy.topics = [weak]          # the next questions of this fight are about it
            enemy.adapted = True
            self.taunt_values = {"topic": weak}
            return "taunt_weak_spot"
        last = self.turns[-self.rules["spam_turns"]:]
        if len(last) == self.rules["spam_turns"] and len(set(last)) == 1:
            enemy.damage = round(enemy.damage * self.rules["spam_damage"])
            enemy.adapted = True
            return "taunt_spam"
        return None

    def weak_topic(self) -> str | None:
        """The asked topic with the lowest mastery, if it is below weak_below. None until the
        player has answered min_moves questions (too early to call anything a weak spot)."""
        if self.tracker is None or len(self.history) < self.rules["min_moves"]:
            return None
        asked = {entry["topic"] for entry in self.history if entry["topic"]}
        weak = [topic for topic in asked if self.tracker.mastery(topic) < self.rules["weak_below"]]
        if not weak:
            return None
        return min(sorted(weak), key=self.tracker.mastery)    # sorted first: the same answer every time

    def _count_turn(self) -> None:
        """Turn the answers given since the last call into one turn."""
        new = self.history[self.seen:]
        self.seen = len(self.history)
        if new:
            self.turns.append(new[-1]["move_id"])   # the newest answer belongs to this turn
