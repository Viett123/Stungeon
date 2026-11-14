"""The Credits screen, the class animations and the art frame."""
import os

import pytest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
pygame = pytest.importorskip("pygame")

from core import assets, flow                      # noqa: E402
from core.game import Game                         # noqa: E402
from core.title_scene import TitleScene            # noqa: E402
from dungeon import sprites                        # noqa: E402
from dungeon.actor import Actor                    # noqa: E402
from systems.player import load_data               # noqa: E402
from ui import theme                               # noqa: E402
from ui.credits_screen import CreditsScene         # noqa: E402


def key(k):
    return pygame.event.Event(pygame.KEYDOWN, key=k, mod=0, unicode="")


@pytest.fixture
def game():
    g = Game()
    yield g
    pygame.quit()


# --- credits -----------------------------------------------------------------
def test_every_credit_names_what_pack_and_author():
    credits = load_data("credits.json")["credits"]
    for entry in credits:
        assert entry["what"] and entry["pack"] and entry["author"] and "license" in entry
    # Art that must be credited (CC BY) is on the list.
    assert any(entry["author"] == "KingBell" for entry in credits)


def test_credits_open_from_the_title_menu_and_close_again(game):
    title = game.scenes.current
    credits_index = next(i for i, action in enumerate(title.actions) if action == title.show_credits)
    title.selected = credits_index
    title.handle_event(key(pygame.K_RETURN))
    screen = game.scenes.current
    assert isinstance(screen, CreditsScene)
    screen.draw(game.screen)
    screen.handle_event(key(pygame.K_ESCAPE))
    assert isinstance(game.scenes.current, TitleScene)


# --- class animations --------------------------------------------------------
def test_every_class_has_all_its_animations(game):
    for class_id in load_data("classes.json")["classes"]:
        for action in ("idle", "run", "attack", "hit", "die", "use"):
            assert sprites.has_frames(f"player_{class_id}", action), (class_id, action)


def test_a_play_once_animation_starts_at_the_first_picture_and_stops_at_the_last():
    frames = [pygame.Surface((2, 2)) for _ in range(4)]
    actor = Actor((0, 0), {"idle": [pygame.Surface((2, 2))], "attack": frames})
    assert actor.image_at("attack", 0.0) is frames[0]
    assert actor.image_at("attack", 0.5) is frames[2]
    assert actor.image_at("attack", 1.0) is frames[3]
    assert actor.image_at("attack", 7.0) is frames[3]            # never past the last picture
    assert actor.image_at("die", 0.5) is actor.image("idle")     # no die pictures: idle is used


def test_defeat_plays_the_die_animation_and_holds_its_last_picture(game):
    flow.start_new_run(game, "mage")
    dungeon = game.scenes.current
    dungeon.start_fight(next(e for e in dungeon.floor.enemies if not e["guard"]))
    fight = game.scenes.current
    standing = fight.player_image()
    fight.defeat()
    for _ in range(120):
        fight.update(1 / 60)
        fight.draw(game.screen)
    assert fight.player_image() is not standing
    assert fight.player_image() is fight.player_actor.image_at("die", 1.0)


# --- the frame from art ------------------------------------------------------
def test_panel_border_is_built_once_per_size_and_has_a_see_through_middle(game):
    border = theme._art_border((300, 200))
    assert border is not None and border.get_size() == (300, 200)
    assert theme._art_border((300, 200)) is border               # remembered, not rebuilt
    assert border.get_at((150, 100)).a == 0                      # the middle is empty
    assert border.get_at((2, 100)).a > 0 and border.get_at((150, 2)).a > 0   # the edges are drawn


def test_without_frame_art_the_code_drawn_frame_is_used(game, tmp_path, monkeypatch):
    monkeypatch.setattr(assets, "SPRITE_DIR", tmp_path)          # an empty folder: no ui_frame.png
    monkeypatch.setattr(theme, "_borders", {})
    assets.clear_cache()
    assert theme._art_border((300, 200)) is None
    inside = theme.draw_frame(game.screen, (10, 10, 300, 200))   # still draws, with plain rectangles
    assert inside == theme.inner((10, 10, 300, 200))
    assets.clear_cache()
