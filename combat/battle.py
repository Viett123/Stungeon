"""The rules of one fight, without any drawing (owner: B). No pygame here, so it can be tested.

One round:
  1. choose_move(move_id)  - pay the cost. Utility moves take effect at once (no question).
  2. answer(given, seconds) - once per question (an ultimate asks 3). The last answer deals the damage.
  3. enemy_turn()          - the enemy hits back (unless the player used Evasion).
A wrong answer is a miss: the cost is still spent and the enemy still gets its turn.
"""
import random

from systems.player import load_data


class Battle:
    def __init__(self, player, enemy, engine, floor, habits=None, rng=None):
        self.player = player
        self.enemy = enemy
        self.engine = engine
        self.floor = floor
        self.habits = habits
        self.rng = rng or random.Random()
        self.rules = load_data("progression.json")

        self.move = None          # the move being answered right now
        self.question = None      # the question on screen right now
        self.remaining = 0        # questions still to answer for this move
        self.results = []         # True/False per answered question of this move
        self.power_up = False     # War Cry: next attack does more damage
        self.reveal = False       # Reveal: next multiple-choice question has fewer choices
        self.evade = False        # Evasion: the enemy's next attack misses

    # --- state -------------------------------------------------------------
    @property
    def won(self):
        return not self.enemy.alive

    @property
    def lost(self):
        return not self.player.alive

    @property
    def over(self):
        return self.won or self.lost

    def moves(self) -> list[dict]:
        """The player's moves, each with "affordable": can the player pay for it now?"""
        return [dict(m, affordable=m["cost"] <= self.player.resource) for m in self.player.unlocked_moves()]

    # --- 1. choose a move --------------------------------------------------
    def choose_move(self, move_id) -> dict:
        move = next((m for m in self.player.unlocked_moves() if m["id"] == move_id), None)
        if move is None or not self.player.spend(move["cost"]):
            return {"ok": False}
        self.player.gain_resource(move.get("gain", 0))

        if move["questions"] == 0:   # utility move
            effect = move.get("effect")
            if effect == "power_up":
                self.power_up = True
            elif effect == "reveal":
                self.reveal = True
            elif effect == "evade":
                self.evade = True
            return {"ok": True, "utility": True, "effect": effect}

        self.move = move
        self.remaining = move["questions"]
        self.results = []
        self._next_question()
        return {"ok": True, "utility": False}

    def _next_question(self):
        question = self.engine.next_question(self.floor, self.move["difficulty"],
                                             topic=self.enemy.topics or None,
                                             weakest=self.move.get("weakest_topics", False))
        if self.reveal and question.get("type") == "multiple_choice":
            wrong = [c for c in question["choices"] if c != question["answer"]]
            keep = [question["answer"]] + wrong[: self.rules["reveal_keeps_choices"] - 1]
            question["choices"] = self.rng.sample(keep, len(keep))
            self.reveal = False
        self.question = question

    # --- 2. answer ---------------------------------------------------------
    def answer(self, given, seconds) -> dict:
        """Check one answer. Returns {"correct", "question", "done", "damage"}."""
        question = self.question
        correct = self.engine.check_answer(question, given)
        self.engine.report_answer(question, correct, seconds)
        if self.habits:
            ratio = seconds / self.rules["expected_answer_seconds"]
            self.habits.record_move(self.move["id"], self.move["tier"], ratio, correct)

        self.results.append(correct)
        self.remaining -= 1
        result = {"correct": correct, "question": question, "done": False, "damage": 0}
        if self.remaining > 0:
            self._next_question()
            return result

        result["done"] = True
        result["damage"] = self.enemy.take_damage(self._move_damage())
        self.move = None
        self.question = None
        return result

    def _move_damage(self):
        hits = sum(self.results)
        damage = self.move["damage"] * hits
        if len(self.results) > 1 and all(self.results):
            damage += self.move.get("bonus_damage", 0)   # ultimate: all 3 right
        if self.power_up:
            damage *= self.rules["power_up_multiplier"]
            self.power_up = False
        return round(damage * self.player.damage_multiplier())

    # --- 3. enemy turn -----------------------------------------------------
    def enemy_turn(self) -> dict:
        """Returns {"damage", "evaded", "taunt"}."""
        self.player.gain_resource(self.rules["resource_per_turn"])   # a little back every round
        if self.evade:
            self.evade = False
            return {"damage": 0, "evaded": True, "taunt": None}
        lost = self.player.take_damage(self.enemy.damage)
        taunt = self.habits.adapt(self.enemy) if self.habits else None
        return {"damage": lost, "evaded": False, "taunt": taunt}
