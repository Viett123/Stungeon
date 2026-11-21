"""The looks of the moves in a fight (combat/skill_looks.py, data/skill_looks.json). Pictures only."""
import os
import random

import pytest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
pygame = pytest.importorskip("pygame")

from combat.skill_looks import AURA_SECONDS, KINDS, SkillLook, look_for   # noqa: E402
from core import flow                                                    # noqa: E402
from core.game import Game                                               # noqa: E402
from dungeon.weapon import IMPACT                                        # noqa: E402
from systems.player import load_data                                     # noqa: E402

MOVES = load_data("moves.json")["moves"]
LOOKS = load_data("skill_looks.json")


@pytest.fixture
def screen():
    pygame.init()
    surface = pygame.display.set_mode((1280, 720))
    yield surface
    pygame.quit()


def play(look, surface, dt=1 / 60):
    """Run a look from start to end, drawing every frame. Returns how many frames it took."""
    frames = 0
    while look.alive():
        look.update(dt)
        look.draw(surface)
        frames += 1
        assert frames < 600, "a look must end"
    return frames


def test_every_move_has_its_own_look_with_a_known_kind():
    for move in MOVES:
        assert move["id"] in LOOKS["looks"], move["id"]
        look = look_for(move["id"])
        assert look["kind"] in KINDS
        assert len(look["color"]) == 3 and all(0 <= c <= 255 for c in look["color"])


def test_utility_moves_have_an_aura_and_attacks_do_not():
    for move in MOVES:
        assert (look_for(move["id"])["kind"] == "aura") == (move["tier"] == "utility"), move["id"]


def test_a_move_without_a_look_uses_the_default():
    assert look_for("no_such_move") == LOOKS["default"]


def test_every_look_plays_to_the_end_and_draws_without_errors(screen):
    for move in MOVES:
        seconds = AURA_SECONDS if look_for(move["id"])["kind"] == "aura" else 0.6
        look = SkillLook(move["id"], (1000, 120), (640, 120), seconds, rng=random.Random(1))
        assert play(look, screen) > 0


def test_an_attack_bursts_into_sparks_when_it_lands():
    look = SkillLook("fireball", (1000, 120), (640, 120), 1.0, rng=random.Random(1))
    look.update(IMPACT - 0.01)
    assert not look.sparks
    look.update(0.02)
    assert look.sparks


def test_every_falling_thing_of_a_rain_lands():
    look = SkillLook("arrow_rain", (1000, 120), (640, 120), 0.6, rng=random.Random(1))
    look.update(0.6)
    assert look.landed == look_for("arrow_rain")["count"]


def test_skipping_ends_a_look_at_once():
    look = SkillLook("titans_wrath", (1000, 120), (640, 120), 0.6, rng=random.Random(1))
    look.update(0.4)
    look.finish()
    assert not look.alive()


# --- in the fight screen ----------------------------------------------------------
def fight_for(class_id):
    game = Game()
    flow.start_new_run(game, class_id)
    dungeon = game.scenes.current
    dungeon.start_fight(next(e for e in dungeon.floor.enemies if not e["boss"] and not e["guard"]))
    return game, game.scenes.current


def test_a_hit_plays_the_look_of_the_move_that_was_used(screen):
    game, fight = fight_for("mage")
    fight.draw(game.screen)                                   # sets where the hand and the enemy are
    fight.pick_move(0)
    move_id = fight.battle.move["id"]
    fight.submit(fight.battle.question["answer"])              # a correct answer
    assert fight.skill is not None and fight.skill.move_id == move_id
    for _ in range(120):                                      # 2 seconds: the look ends and is removed
        fight.update(1 / 60)
        fight.draw(game.screen)
    assert fight.skill is None


def test_a_miss_plays_no_look(screen):
    game, fight = fight_for("warrior")
    fight.pick_move(0)
    question = fight.battle.question
    wrong = "zzz" if question["type"] == "typed" else next(c for c in question["choices"] if c != question["answer"])
    fight.submit([wrong] if question["type"] == "multi_select" else wrong)
    assert fight.skill is None


def test_a_utility_move_shows_a_ring_around_the_player(screen):
    game, fight = fight_for("archer")
    fight.player.level = 2                                    # utility moves unlock at level 2
    fight.player.resource = fight.player.max_resource
    fight.refresh_moves()
    index = next(i for i, m in enumerate(fight.moves) if m["tier"] == "utility")
    fight.pick_move(index)
    assert fight.skill is not None and fight.skill.kind == "aura"
    fight.draw(game.screen)
