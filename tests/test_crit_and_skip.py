"""The fight screen shows "CRIT!" for a critical hit and says so when the enemy loses its turn."""
import os

import pytest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
pygame = pytest.importorskip("pygame")

from combat import effects  # noqa: E402
from core import flow  # noqa: E402
from core.game import Game  # noqa: E402
from core.strings import t  # noqa: E402


@pytest.fixture
def fight():
    game = Game()
    flow.start_new_run(game, "warrior")
    dungeon = game.scenes.current
    dungeon.start_fight(next(e for e in dungeon.floor.enemies if not e["boss"] and not e["guard"]))
    scene = game.scenes.current
    scene.battle.enemy.hp = scene.battle.enemy.max_hp = 10_000     # the enemy must survive every hit
    return scene


def texts(scene):
    return [line[0] for line in scene.lines]


def answer(scene, share_of_time, right=True):
    """Pick the first move and answer after `share_of_time` of the time limit (0.05 = very fast)."""
    scene.pick_move(0)
    scene.elapsed = scene.battle.time_limit * share_of_time
    question = scene.battle.question
    scene.submit(question["answer"] if right else "certainly not the answer")


def test_a_fast_right_answer_says_crit_and_floats_it(fight):
    answer(fight, 0.05)
    assert t("crit_line") in texts(fight)
    fight.finish_attack()                                      # the hit lands now
    assert len(fight.floating) == 2                            # the damage number and "CRIT!"


def test_a_slow_right_answer_is_no_crit(fight):
    answer(fight, 0.8)
    assert t("crit_line") not in texts(fight)
    fight.finish_attack()
    assert len(fight.floating) == 1                            # only the damage number


def test_a_fast_wrong_answer_is_no_crit(fight):
    answer(fight, 0.05, right=False)
    assert t("crit_line") not in texts(fight)
    assert t("miss") in texts(fight)


def test_the_enemy_losing_its_turn_is_said_clearly(fight, monkeypatch):
    monkeypatch.setattr(effects, "enemy_loses_turn", lambda battle: True)
    answer(fight, 0.5, right=False)
    fight.next_step()                                          # on to the enemy's turn
    assert texts(fight)[0] == t("enemy_loses_turn", enemy=fight.enemy_name)


def test_an_attack_that_does_no_damage_keeps_its_own_message(fight, monkeypatch):
    monkeypatch.setattr(effects, "change_enemy_damage", lambda amount, battle: 0)
    answer(fight, 0.5)
    fight.next_step()
    assert texts(fight)[0] == t("enemy_misses", enemy=fight.enemy_name)
