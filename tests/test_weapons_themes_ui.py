"""Held weapons, floor themes and the UI animation helpers."""
import os

import pytest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
pygame = pytest.importorskip("pygame")

from combat.combat_scene import CombatScene            # noqa: E402
from core import assets, flow                          # noqa: E402
from core.game import Game                             # noqa: E402
from core.run import new_run                           # noqa: E402
from dungeon import sprites                            # noqa: E402
from dungeon.weapon import HeldWeapon, held_weapon     # noqa: E402
from systems.enemies import floor_theme                # noqa: E402
from systems.player import load_data                   # noqa: E402
from ui import anim, theme                             # noqa: E402


@pytest.fixture
def screen():
    pygame.init()
    surface = pygame.display.set_mode((1280, 720))
    assets.clear_cache()
    yield surface
    assets.clear_cache()
    pygame.quit()


@pytest.fixture
def clock(monkeypatch):
    """A fake clock: tests set clock["now"] instead of waiting."""
    state = {"now": 100.0}
    monkeypatch.setattr(anim, "now", lambda: state["now"])
    return state


# --- weapons -----------------------------------------------------------------
def test_every_class_starts_with_a_weapon_that_has_art(screen):
    for class_id, data in load_data("classes.json")["classes"].items():
        player = new_run(class_id, seed=1).player
        assert player.equipped["weapon"] == data["start_weapon"]
        assert held_weapon(player, 3) is not None, class_id


def test_no_weapon_or_no_art_means_nothing_is_drawn(screen, tmp_path, monkeypatch):
    player = new_run("warrior", seed=1).player
    monkeypatch.setattr(assets, "SPRITE_DIR", tmp_path)     # an empty folder: no weapon art
    assert held_weapon(player, 3) is None
    player.equipped.clear()
    assert held_weapon(player, 3) is None


def test_swing_goes_through_different_pictures_and_mirrors_for_the_other_side(screen, tmp_path, monkeypatch):
    monkeypatch.setattr(assets, "SPRITE_DIR", tmp_path)
    art = pygame.Surface((4, 12), pygame.SRCALPHA)
    art.fill((200, 200, 200))
    pygame.image.save(art, str(tmp_path / "weapon_stick.png"))
    weapon = HeldWeapon("stick", 3)
    assert weapon.has_art
    assert weapon.image(False, swing=0.0) is not weapon.image(False, swing=0.99)
    assert weapon.image(False, swing=1.0) is weapon.image(False, swing=0.99)     # never past the last picture
    assert weapon.image(False) is not weapon.image(True)
    x, y, image, lift = weapon.thing(100, 200, facing_left=False)
    assert x > 100 and y > 200                                # in front of the body, drawn after its owner
    assert weapon.thing(100, 200, facing_left=True)[0] < 100


def test_weapon_follows_what_is_equipped_in_the_dungeon(screen):
    game = Game()
    flow.start_new_run(game, "mage")
    scene = game.scenes.current
    assert scene.weapon is not None
    game.run_state.player.equipped.clear()
    scene.update(1 / 60)
    scene.draw(game.screen)
    assert scene.weapon is None


def test_a_hit_starts_the_swing_and_shows_a_damage_number(screen):
    game = Game()
    flow.start_new_run(game, "warrior")
    dungeon = game.scenes.current
    dungeon.start_fight(next(e for e in dungeon.floor.enemies if not e["boss"]))
    fight = game.scenes.current
    assert isinstance(fight, CombatScene) and fight.weapon is not None
    fight.pick_move(0)
    fight.submit(fight.battle.question["answer"])            # a correct answer
    assert fight.attack > 0 and len(fight.floating) == 1
    for _ in range(90):                                      # 1.5 seconds
        fight.update(1 / 60)
        fight.draw(game.screen)
    assert fight.attack == 0


# --- themes ------------------------------------------------------------------
def test_every_floor_has_a_theme_with_a_background_colour():
    for number in range(1, load_data("progression.json")["last_floor"] + 1):
        look = floor_theme(number)
        assert len(look["background"]) == 3
        if look["folder"]:
            assert (assets.SPRITE_DIR / look["folder"]).is_dir(), look["folder"]


def test_a_theme_folder_is_used_first_and_missing_pictures_fall_back(screen, tmp_path, monkeypatch):
    monkeypatch.setattr(assets, "SPRITE_DIR", tmp_path)
    (tmp_path / "ice").mkdir()
    for name, color in (("tile_floor", (10, 20, 30)), ("tile_stairs", (1, 2, 3)), ("ice/tile_floor", (0, 200, 250))):
        art = pygame.Surface((16, 16))
        art.fill(color)
        pygame.image.save(art, str(tmp_path / f"{name}.png"))
    assert sprites.tile_sprite("tile_floor", folder="ice").get_at((5, 5))[:3] == (0, 200, 250)
    assert sprites.tile_sprite("tile_stairs", folder="ice").get_at((5, 5))[:3] == (1, 2, 3)     # not in ice/
    assert sprites.tile_sprite("tile_floor").get_at((5, 5))[:3] == (10, 20, 30)


# --- UI animation helpers ----------------------------------------------------
def test_blend_and_ease_out_stay_in_range():
    assert anim.blend((0, 0, 0), (100, 200, 50), 0.5) == (50, 100, 25)
    assert anim.ease_out(0) == 0 and anim.ease_out(1) == 1
    assert 0.5 < anim.ease_out(0.5) < 1                       # fast first, slow at the end


def test_glow_is_between_the_two_golds(screen):
    for channel, low, high in zip(anim.glow_gold(), theme.GOLD, theme.GOLD_BRIGHT):
        assert low <= channel <= high


def test_trail_lags_behind_a_drop_and_then_catches_up(clock):
    trail = anim.Trail(100)
    clock["now"] += 0.1
    shown = trail.follow(40)                                  # HP just dropped from 100 to 40
    assert 40 < shown < 100
    clock["now"] += 5
    assert trail.follow(40) == 40


def test_trail_does_not_lag_when_the_value_goes_up(clock):
    trail = anim.Trail(40)
    clock["now"] += 0.1
    assert trail.follow(90) == 90


def test_floating_text_disappears_after_a_moment(screen, clock):
    text = anim.FloatingText(pygame.font.Font(None, 48), "-25", theme.GOLD, (300, 300))
    assert text.alive()
    text.draw(screen)
    clock["now"] += anim.FloatingText.SECONDS + 0.1
    assert not text.alive()
