"""Tests for mission 5: the enemy may lose its turn after a miss, and whether an item uses your turn.

The chance uses battle.rng. In these tests a fixed number stands in for it, so each test knows the outcome.
"""
import random

from combat import damage, effects
from combat.battle import Battle
from systems.enemies import make_enemy
from systems.player import Player, load_data

CHANCE = load_data("combat.json")["enemy_skip_chance"]


class FixedRng:
    """Always gives the same number from random(), so the test knows what the roll will be."""

    def __init__(self, value):
        self.value = value

    def random(self):
        return self.value


class FakeEngine:
    """Asks the same question every time. The test decides right or wrong."""

    def __init__(self):
        self.streak = 0

    def next_question(self, floor, difficulty, topic=None, weakest=False):
        return {"topic": "articles", "type": "multiple_choice", "difficulty": difficulty,
                "question": "___ Bühne", "choices": ["der", "die", "das"], "answer": "die"}

    def check_answer(self, question, given):
        return given == question["answer"]

    def report_answer(self, question, correct, seconds):
        self.streak = self.streak + 1 if correct else 0


def make_battle(rng=None):
    player = Player("warrior")
    player.resource = player.max_resource
    return Battle(player, make_enemy("article_goblin"), FakeEngine(), floor=1, rng=rng or random.Random(0))


def answer_basic(battle, right):
    move = next(m for m in battle.moves() if m["id"] == "slash")
    battle.choose_move(move["id"])
    return battle.answer("die" if right else "der", 3)


def test_no_miss_means_the_enemy_always_acts():
    battle = make_battle(FixedRng(0.0))        # a roll that would skip, if it were asked
    answer_basic(battle, right=True)
    assert effects.enemy_loses_turn(battle) is False


def test_a_miss_and_a_low_roll_skips_the_enemy_turn():
    battle = make_battle(FixedRng(0.0))
    answer_basic(battle, right=False)
    out = battle.enemy_turn()
    assert out["damage"] == 0
    assert battle.player.hp == battle.player.max_hp


def test_a_miss_and_a_high_roll_the_enemy_hits():
    battle = make_battle(FixedRng(0.99))
    answer_basic(battle, right=False)
    expected = damage.enemy_damage(battle.enemy, battle.player)
    assert battle.enemy_turn()["damage"] == expected
    assert battle.player.hp == battle.player.max_hp - expected


def test_the_chance_is_the_number_in_data():
    battle = make_battle(FixedRng(CHANCE - 0.001))      # just under the chance: skip
    answer_basic(battle, right=False)
    assert effects.enemy_loses_turn(battle) is True

    battle = make_battle(FixedRng(CHANCE))              # exactly the chance: no skip
    answer_basic(battle, right=False)
    assert effects.enemy_loses_turn(battle) is False


def test_a_miss_only_counts_for_the_enemy_turn_right_after_it():
    battle = make_battle(FixedRng(0.99))
    answer_basic(battle, right=False)
    battle.enemy_turn()                         # the enemy hits, and the miss is used up
    battle.rng = FixedRng(0.0)                  # now the roll would skip...
    assert effects.enemy_loses_turn(battle) is False   # ...but there was no miss this round


def test_the_skip_uses_battle_rng_not_the_random_module(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("the random module must not be used here")

    monkeypatch.setattr(random, "random", forbidden)
    battle = make_battle(FixedRng(0.0))
    answer_basic(battle, right=False)
    assert effects.enemy_loses_turn(battle) is True


def test_the_same_seed_always_gives_the_same_skips():
    def rolls(seed):
        battle = make_battle(random.Random(seed))
        results = []
        for _ in range(20):
            battle.missed = True
            results.append(effects.enemy_loses_turn(battle))
        return results

    assert rolls(7) == rolls(7)


def test_drinking_a_potion_costs_your_turn():
    battle = make_battle()
    assert effects.item_costs_turn(battle) is True
