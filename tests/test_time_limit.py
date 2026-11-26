"""Tests for the time limit (mission 3).

Each question gets a time by its difficulty, typed answers get extra time, a hook can change
the time, and when the time is up the answer counts as a wrong answer.
"""
import random

import pytest

from combat import effects
from combat.battle import Battle
from systems.enemies import make_enemy
from systems.player import Player, load_data

NUMBERS = load_data("combat.json")


class FakeEngine:
    """Asks the same kind of question every time. The test decides whether it is typed."""

    def __init__(self, question_type="multiple_choice"):
        self.question_type = question_type
        self.streak = 0
        self.reported = []

    def next_question(self, floor, difficulty, topic=None, weakest=False):
        return {"topic": "articles", "type": self.question_type, "difficulty": difficulty,
                "question": "___ Bühne", "choices": ["der", "die", "das"], "answer": "die",
                "explanation": "die Bühne = stage"}

    def check_answer(self, question, given):
        return given == question["answer"]

    def report_answer(self, question, correct, seconds):
        self.reported.append(correct)
        self.streak = self.streak + 1 if correct else 0


def make_battle(question_type="multiple_choice"):
    player = Player("mage", level=5)
    player.resource = player.max_resource      # every move is affordable
    return Battle(player, make_enemy("article_goblin"), FakeEngine(question_type), floor=1,
                  rng=random.Random(0))


def pick(battle, tier):
    move = next(m for m in battle.moves() if m["tier"] == tier)
    battle.choose_move(move["id"])
    return move


@pytest.mark.parametrize("tier, difficulty", [("basic", "easy"), ("skill", "medium"), ("ultimate", "hard")])
def test_time_limit_follows_the_difficulty(tier, difficulty):
    battle = make_battle()
    move = pick(battle, tier)
    assert move["difficulty"] == difficulty
    assert battle.time_limit == NUMBERS["time_limit_seconds"][difficulty]


def test_typed_answers_get_extra_time():
    battle = make_battle("typed")
    pick(battle, "basic")
    assert battle.time_limit == NUMBERS["time_limit_seconds"]["easy"] + NUMBERS["typed_extra_seconds"]


def test_a_hook_can_change_the_time_limit(monkeypatch):
    seen = {}

    def more_time(seconds, question, battle):
        seen["question_type"] = question["type"]
        return seconds + 5

    monkeypatch.setattr(effects, "change_time_limit", more_time)
    battle = make_battle()
    pick(battle, "basic")
    assert battle.time_limit == NUMBERS["time_limit_seconds"]["easy"] + 5
    assert seen["question_type"] == "multiple_choice"


def test_time_is_up_exactly_when_the_limit_is_reached():
    battle = make_battle()
    pick(battle, "basic")
    limit = battle.time_limit
    assert not battle.time_is_up(limit - 0.1)
    assert battle.time_is_up(limit)


def test_time_out_is_a_wrong_answer_that_uses_the_whole_time():
    battle = make_battle()
    pick(battle, "basic")
    limit = battle.time_limit
    hp_before = battle.enemy.hp

    out = battle.time_out()

    assert out["correct"] is False
    assert out["done"] is True                 # one question, so the move is over
    assert out["damage"] == 0                  # a miss: no damage
    assert battle.enemy.hp == hp_before
    assert battle.engine.reported == [False]
    assert battle.seconds == [limit]
    assert battle.time_used == [1.0]
    assert battle.missed                       # the enemy's turn may now be skipped (mission 5)
    assert out["question"]["explanation"]      # the screen shows it after a miss


def test_time_out_in_a_three_question_move_asks_the_next_question():
    battle = make_battle()
    pick(battle, "ultimate")
    first = battle.time_out()
    assert not first["done"]
    assert battle.remaining == 2
    assert battle.question is not None


def test_the_fight_screen_says_time_is_up():
    """When the timer runs out in a real fight, the first line says so, then "Wrong."."""
    import os
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
    pytest.importorskip("pygame")
    from core import flow
    from core.game import Game
    from core.strings import t

    game = Game()
    flow.begin_new_game(game)
    flow.name_chosen(game, "Mia")
    flow.class_chosen(game, "warrior")
    flow.dungeon_chosen(game, "german")
    flow.level_chosen(game, "B1")
    dungeon = game.scenes.current
    dungeon.start_fight(next(e for e in dungeon.floor.enemies if not e["boss"] and not e["guard"]))
    fight = game.scenes.current
    fight.pick_move(0)
    limit = fight.battle.time_limit
    for _ in range(int(limit * 60) + 30):      # a little more than the time limit, 60 frames a second
        fight.update(1 / 60)
    assert fight.state == "message"
    assert fight.lines[0][0] == t("time_up")
    assert fight.lines[1][0] == t("wrong")
