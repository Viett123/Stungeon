import random

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
    return Battle(player, make_enemy(enemy), FakeEngine(), floor=1, rng=random.Random(0)), player


def test_correct_basic_answer_deals_basic_damage():
    battle, _ = make_battle()
    battle.choose_move("slash")
    out = battle.answer("die", seconds=3)
    assert out["correct"] and out["done"] and out["damage"] == 10
    assert battle.enemy.hp == battle.enemy.max_hp - 10


def test_wrong_answer_misses_but_still_costs():
    battle, player = make_battle()
    before = player.resource
    battle.choose_move("shield_bash")       # skill: costs 15
    out = battle.answer("der", seconds=3)
    assert not out["correct"] and out["damage"] == 0
    assert player.resource == before - 15
    assert battle.enemy.hp == battle.enemy.max_hp


def test_cannot_use_a_move_you_cannot_afford():
    battle, player = make_battle(level=3)
    player.resource = 5
    assert battle.choose_move("berserker_cleave") == {"ok": False}
    assert player.resource == 5


def test_enemy_turn_hurts_the_player():
    battle, player = make_battle()
    out = battle.enemy_turn()
    assert out["damage"] == battle.enemy.damage
    assert player.hp == player.max_hp - battle.enemy.damage


def test_evasion_makes_the_next_attack_miss():
    battle, player = make_battle("archer", level=2)
    assert battle.choose_move("evasion")["utility"]
    assert battle.enemy_turn()["evaded"]
    assert player.hp == player.max_hp
    assert not battle.enemy_turn()["evaded"]      # only once


def test_war_cry_boosts_the_next_attack():
    battle, _ = make_battle("warrior", level=2)
    battle.choose_move("war_cry")
    battle.choose_move("slash")
    assert battle.answer("die", 2)["damage"] == 15   # 10 x 1.5


def test_reveal_leaves_two_choices():
    battle, _ = make_battle("mage", level=2)
    battle.choose_move("reveal")
    battle.choose_move("arcane_bolt")
    assert len(battle.question["choices"]) == 2
    assert "die" in battle.question["choices"]


def test_ultimate_asks_three_and_gives_a_bonus_for_all_right():
    battle, player = make_battle("mage", level=5, enemy="boss_floor_3")
    player.resource = player.max_resource
    battle.choose_move("meteor_storm")
    assert not battle.answer("die", 2)["done"]
    assert not battle.answer("die", 2)["done"]
    last = battle.answer("die", 2)
    assert last["done"] and last["damage"] == 3 * 35 + 45


def test_won_and_lost():
    battle, player = make_battle()
    battle.enemy.hp = 5
    battle.choose_move("slash")
    battle.answer("die", 1)
    assert battle.won and battle.over
    player.hp = 1
    battle.enemy.hp = 10
    battle.enemy_turn()
    assert battle.lost
