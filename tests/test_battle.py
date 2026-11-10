"""Tests for the ORDER of a fight (combat/battle.py).

They check that the battle calls the hooks in combat/damage.py and combat/effects.py
and uses what they return. They do not check any damage numbers: those belong to B.
"""
import random

from combat import damage, effects
from combat.battle import Battle
from systems.enemies import make_enemy
from systems.player import Player


class FakeEngine:
    """Always asks the same question, so the test decides right or wrong."""

    def __init__(self):
        self.reported = []

    def next_question(self, floor, difficulty, topic=None, weakest=False):
        return {"topic": "articles", "type": "multiple_choice", "difficulty": difficulty,
                "question": "___ Bühne", "choices": ["der", "die", "das"], "answer": "die"}

    def check_answer(self, question, given):
        return given == question["answer"]

    def report_answer(self, question, correct, seconds):
        self.reported.append(correct)


def make_battle(class_id="warrior", level=1, enemy="article_goblin"):
    player = Player(class_id, level=level)
    player.resource = player.max_resource     # so every move is affordable
    return Battle(player, make_enemy(enemy), FakeEngine(), floor=1, rng=random.Random(0)), player


def first_move(battle, tier):
    return next(m for m in battle.moves() if m["tier"] == tier)


def test_answer_uses_the_damage_hook(monkeypatch):
    seen = {}

    def fake_damage(move, results, player, enemy):
        seen["results"] = results
        return 7

    monkeypatch.setattr(damage, "player_damage", fake_damage)
    battle, _ = make_battle()
    battle.choose_move(first_move(battle, "basic")["id"])
    out = battle.answer("die", seconds=3)
    assert out["correct"] and out["done"] and out["damage"] == 7
    assert seen["results"] == [True]
    assert battle.enemy.hp == battle.enemy.max_hp - 7
    assert battle.engine.reported == [True]


def test_effect_hooks_can_change_damage_and_question(monkeypatch):
    monkeypatch.setattr(damage, "player_damage", lambda *args: 10)
    monkeypatch.setattr(effects, "change_player_damage", lambda amount, battle: amount * 2)
    monkeypatch.setattr(effects, "change_question", lambda q, battle: dict(q, marked=True))
    battle, _ = make_battle()
    battle.choose_move(first_move(battle, "basic")["id"])
    assert battle.question["marked"]
    assert battle.answer("die", 1)["damage"] == 20


def test_wrong_answer_still_costs_and_ends_the_move():
    battle, player = make_battle()
    move = first_move(battle, "skill")
    before = player.resource
    battle.choose_move(move["id"])
    out = battle.answer("der", seconds=3)
    assert not out["correct"] and out["done"]
    assert player.resource == before - move["cost"] + move.get("gain", 0)
    assert battle.question is None


def test_cannot_use_a_move_you_cannot_afford():
    battle, player = make_battle(level=3)
    player.resource = 0
    move = next(m for m in battle.moves() if m["cost"] > 0)
    assert battle.choose_move(move["id"]) == {"ok": False}
    assert player.resource == 0


def test_utility_move_calls_its_hook_and_asks_no_question(monkeypatch):
    used = []
    monkeypatch.setattr(effects, "use_utility", lambda move, battle: used.append(move["id"]))
    battle, _ = make_battle("mage", level=2)
    move = first_move(battle, "utility")
    assert battle.choose_move(move["id"]) == {"ok": True, "utility": True}
    assert used == [move["id"]] and battle.question is None


def test_enemy_turn_uses_the_hooks(monkeypatch):
    rounds = []
    monkeypatch.setattr(damage, "enemy_damage", lambda enemy, player: 9)
    monkeypatch.setattr(effects, "change_enemy_damage", lambda amount, battle: amount - 4)
    monkeypatch.setattr(effects, "end_of_round", lambda battle: rounds.append(1))
    battle, player = make_battle()
    assert battle.enemy_turn()["damage"] == 5
    assert player.hp == player.max_hp - 5
    assert rounds == [1]


def test_a_move_with_three_questions_asks_three():
    battle, _ = make_battle("mage", level=5, enemy="boss_floor_3")
    battle.choose_move(first_move(battle, "ultimate")["id"])
    assert not battle.answer("die", 2)["done"]
    assert not battle.answer("der", 2)["done"]
    assert battle.answer("die", 2)["done"]
    assert battle.engine.reported == [True, False, True]


def test_won_and_lost(monkeypatch):
    monkeypatch.setattr(damage, "player_damage", lambda *args: 999)
    monkeypatch.setattr(damage, "enemy_damage", lambda *args: 999)
    battle, _ = make_battle()
    battle.choose_move(first_move(battle, "basic")["id"])
    battle.answer("die", 1)
    assert battle.won and battle.over
    battle.enemy_turn()
    assert battle.lost
