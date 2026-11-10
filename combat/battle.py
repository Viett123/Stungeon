"""The order of one fight, without any drawing. No pygame here, so it can be tested.

This file only decides WHEN things happen. The rules themselves live elsewhere:
  combat/damage.py   - how much damage (owner B)
  combat/effects.py  - buffs, debuffs, utility moves (owners B and D)
  questions/engine.py - which question (owner C)

One round:
  1. choose_move(move_id)   - pay the cost. A utility move has no question.
  2. answer(given, seconds) - once per question (an ultimate asks 3). The last answer deals the damage.
  3. enemy_turn()           - the enemy hits back.
From docs/HANDOFF.md: a wrong answer is a miss, the cost is still spent, the enemy still gets its turn.
"""
import random

from combat import damage, effects
from systems.player import load_data


class Battle:
    def __init__(self, player, enemy, engine, floor, habits=None, rng=None):
        self.player = player
        self.enemy = enemy
        self.engine = engine
        self.floor = floor
        self.habits = habits
        self.rng = rng or random.Random()
        # Used to tell the HabitTracker if an answer was fast or slow.
        self.expected_seconds = load_data("progression.json")["expected_answer_seconds"]

        self.move = None       # the move being answered right now
        self.question = None   # the question on screen right now
        self.remaining = 0     # questions still to answer for this move
        self.results = []      # True/False per answered question of this move

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
        """Returns {"ok": False} if the move can't be used, else {"ok": True, "utility": bool}."""
        move = next((m for m in self.player.unlocked_moves() if m["id"] == move_id), None)
        if move is None or not self.player.spend(move["cost"]):
            return {"ok": False}
        self.player.gain_resource(move.get("gain", 0))

        if move["questions"] == 0:
            effects.use_utility(move, self)
            return {"ok": True, "utility": True}

        self.move = move
        self.remaining = move["questions"]
        self.results = []
        self._next_question()
        return {"ok": True, "utility": False}

    def _next_question(self):
        question = self.engine.next_question(self.floor, self.move["difficulty"],
                                             topic=self.enemy.topics or None,
                                             weakest=self.move.get("weakest_topics", False))
        self.question = effects.change_question(question, self)

    # --- 2. answer ---------------------------------------------------------
    def answer(self, given, seconds) -> dict:
        """Check one answer. Returns {"correct", "question", "done", "damage"}."""
        question = self.question
        correct = self.engine.check_answer(question, given)
        self.engine.report_answer(question, correct, seconds)
        if self.habits:
            self.habits.record_move(self.move["id"], self.move["tier"], seconds / self.expected_seconds, correct)

        self.results.append(correct)
        self.remaining -= 1
        result = {"correct": correct, "question": question, "done": False, "damage": 0}
        if self.remaining > 0:
            self._next_question()
            return result

        amount = damage.player_damage(self.move, self.results, self.player, self.enemy)
        amount = effects.change_player_damage(amount, self)
        result["done"] = True
        result["damage"] = self.enemy.take_damage(amount)
        self.move = None
        self.question = None
        return result

    # --- 3. enemy turn -----------------------------------------------------
    def enemy_turn(self) -> dict:
        """Returns {"damage": hp the player lost, "taunt": a strings key or None}."""
        amount = damage.enemy_damage(self.enemy, self.player)
        amount = effects.change_enemy_damage(amount, self)
        lost = self.player.take_damage(amount)
        effects.end_of_round(self)
        taunt = self.habits.adapt(self.enemy) if self.habits else None
        return {"damage": lost, "taunt": taunt}
