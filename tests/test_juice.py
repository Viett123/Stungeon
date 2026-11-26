"""How a hit feels: number sizes, the red flash, the "3 in a row!" pop-up. No rules change here."""
import os

import pytest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
pygame = pytest.importorskip("pygame")

from combat import combat_scene                       # noqa: E402
from combat.combat_scene import CombatScene, is_weak_hit  # noqa: E402
from core import flow                                 # noqa: E402
from core.game import Game                            # noqa: E402
from systems.enemies import make_enemy                # noqa: E402
from ui import hud                                    # noqa: E402


@pytest.fixture
def scene():
    game = Game()
    game.run_state = flow.new_run("warrior", seed=1)
    flow.enter_floor(game)
    return CombatScene(game, game.run_state.player, make_enemy("article_goblin"), lambda *a: None)


def height(floating):
    return floating.image.get_height()


@pytest.mark.parametrize("results, weak", [
    ([True], False), ([False], False),              # one question: a hit or a miss, never "weak"
    ([True, True, True], False),
    ([True, False, False], True),                   # 1 of an Ultimate's 3: weak
    ([False, False, False], False),                 # all wrong is a miss
])
def test_a_weak_hit_is_a_move_with_only_some_right_answers(results, weak):
    assert is_weak_hit(results) is weak


@pytest.mark.parametrize("crit, weak, font", [
    (True, False, "title"),      # a crit: huge
    (False, False, "big"),       # a normal hit
    (False, True, "normal"),     # a weak hit: small
])
def test_the_damage_number_shows_how_good_the_hit_was(scene, crit, weak, font):
    scene.pending_damage, scene.pending_crit, scene.pending_weak = 12, crit, weak
    scene.land_hit()
    assert height(scene.floating[0]) == scene.game.fonts[font].get_height()
    assert scene.pending_weak is False                   # reset for the next hit


def test_being_hit_flashes_the_screen_red_and_it_fades(scene):
    scene.battle.enemy_turn = lambda: {"damage": 5, "taunt": None, "skipped": False}
    scene.enemy_turn()
    assert scene.red_flash == combat_scene.RED_FLASH_SECONDS
    scene.draw(scene.game.screen)                        # draws with the red layer on top
    scene.update(combat_scene.RED_FLASH_SECONDS + 0.1)
    assert scene.red_flash == 0


def test_no_red_flash_when_the_enemy_misses_or_loses_its_turn(scene):
    scene.battle.enemy_turn = lambda: {"damage": 0, "taunt": None, "skipped": True}
    scene.enemy_turn()
    assert scene.red_flash == 0


def test_the_streak_pop_up_starts_at_two_and_grows_at_the_top(scene):
    scene.streak_popup(1)
    assert scene.floating == []                          # one right answer is no streak yet
    scene.streak_popup(2)
    small = scene.floating[-1]
    scene.streak_popup(hud.streak_boxes())               # the streak where the bonus is at its biggest
    big = scene.floating[-1]
    assert height(small) == scene.game.fonts["big"].get_height()
    assert height(big) == scene.game.fonts["title"].get_height()
    left, right = big.center[0] - big.image.get_width() / 2, big.center[0] + big.image.get_width() / 2
    assert left >= 0 and right <= scene.game.screen.get_width() - 10     # the biggest one fits on the screen


def test_a_right_answer_shows_the_streak_pop_up(scene):
    scene.battle.engine.streak = 3
    question = {"question": "?", "type": "multiple_choice", "choices": ["a", "b"], "answer": "a"}
    scene.show_result({"correct": True, "question": question, "done": False, "damage": 0}, "slash")
    assert scene.floating                                # "3 in a row!"
