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
        self.seconds = []      # how long each of those answers took, for B's rules (faster = stronger)
        self.time_used = []    # share of each question's time limit used
        self.time_limit = 0
        self.base_time_limit = 1     # the time limit before items change it (set for each question)
        self.missed = False
        self.war_cry = False
        self.reveal = False
        self.evasion_attacks = 0
        self.stunned = False   # Shield Bash: the enemy loses its next turn (effects.after_hit)
        self.poison_turns = 0  # Poison Arrow: enemy turns the poison still hurts (effects.poison_tick)
        self.last_crit = False # set by effects.change_player_damage: was the last hit a critical hit?

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

    def start(self) -> dict:
        """Called once when the fight opens. The enemy may already change because of how the
        player fought before (ai/habits.py). Returns {"taunt": key or None, "taunt_values": {...}}."""
        return self._adapt()

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
        self.seconds = []
        self.time_used = []
        self.missed = False
        self.last_crit = False
        self._next_question()
        return {"ok": True, "utility": False}

    def _next_question(self):
        question = self.engine.next_question(self.floor, self.move["difficulty"],
                                             topic=self.enemy.topics or None,
                                             weakest=self.move.get("weakest_topics", False))
        self.question = effects.change_question(question, self)
        numbers = load_data("combat.json")
        self.time_limit = numbers["time_limit_seconds"][self.move["difficulty"]]
        if self.question["type"] == "typed":
            self.time_limit += numbers["typed_extra_seconds"]
        # The crit is measured on this normal limit. Items that give more seconds give more time
        # to think, not an easier crit.
        self.base_time_limit = self.time_limit
        self.time_limit = effects.change_time_limit(self.time_limit, self.question, self)

    def time_is_up(self, seconds) -> bool:
        return seconds >= self.time_limit

    def time_out(self) -> dict:
        """Record the current answer as wrong after its time limit expires."""
        return self._record_answer(self.question, False, self.time_limit)

    # --- 2. answer ---------------------------------------------------------
    def answer(self, given, seconds) -> dict:
        """Check one answer. Returns {"correct", "question", "done", "damage"}."""
        question = self.question
        correct = self.engine.check_answer(question, given)
        return self._record_answer(question, correct, seconds)

    def _record_answer(self, question, correct, seconds) -> dict:
        self.engine.report_answer(question, correct, seconds)
        if self.habits:
            self.habits.record_move(self.move["id"], self.move["tier"], seconds / self.expected_seconds, correct, question.get("topic"))

        self.results.append(correct)
        self.seconds.append(seconds)
        self.time_used.append(min(seconds / self.base_time_limit, 1.0))
        self.missed = self.missed or not correct
        self.remaining -= 1
        result = {"correct": correct, "question": question, "done": False, "damage": 0, "crit": False}
        if self.remaining > 0:
            self._next_question()
            return result

        amount = damage.player_damage(self.move, self.results, self.player, self.enemy)
        amount = effects.change_player_damage(amount, self)
        result["done"] = True
        result["damage"] = self.enemy.take_damage(amount)
        # Only a hit that does damage can be critical (a fast WRONG answer is not a crit).
        result["crit"] = bool(result["damage"]) and self.last_crit
        # "stun", "poison" or None: what the move's effect did (Shield Bash, Poison Arrow).
        result["effect"] = effects.after_hit(self.move, result["damage"], self) if self.enemy.alive else None
        self.move = None
        self.question = None
        return result

    # --- 3. enemy turn -----------------------------------------------------
    def enemy_turn(self) -> dict:
        """Returns {"damage": hp the player lost, "taunt": a strings key or None,
        "taunt_values": what fills the taunt's {placeholders} (e.g. {"topic": "articles"}),
        "skipped": True if the enemy lost its turn (see effects.enemy_loses_turn),
        "poison": HP the poison took from the enemy first (0 if none; it can kill the enemy)}."""
        poison = effects.poison_tick(self)
        if poison and self.won:               # the poison killed it: no attack, no taunt
            return {"damage": 0, "skipped": True, "poison": poison, "taunt": None, "taunt_values": {}}
        if effects.enemy_loses_turn(self):
            self.missed = False
            return {"damage": 0, "skipped": True, "poison": poison, **self._adapt()}
        amount = damage.enemy_damage(self.enemy, self.player)
        amount = effects.change_enemy_damage(amount, self)
        lost = self.player.take_damage(amount)
        self.missed = False
        effects.end_of_round(self)
        return {"damage": lost, "skipped": False, "poison": poison, **self._adapt()}

    def _adapt(self) -> dict:
        """Let ai/habits.py change the enemy. {"taunt": key or None, "taunt_values": {...}}."""
        if not self.habits:
            return {"taunt": None, "taunt_values": {}}
        taunt = self.habits.adapt(self.enemy)
        return {"taunt": taunt, "taunt_values": dict(self.habits.taunt_values) if taunt else {}}
