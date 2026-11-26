"""The new-game screens (name, class, dungeon, welcome + level), the level banks and the new title look."""
import json
import os

import pytest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
pygame = pytest.importorskip("pygame")

from core import flow                                # noqa: E402
from core.run import SAVE_VERSION, new_run, run_from_dict, run_to_dict   # noqa: E402
from core.strings import t                           # noqa: E402
from core.title_scene import TitleScene              # noqa: E402
from dungeon.dungeon_scene import DungeonScene       # noqa: E402
from systems import dungeons, save                   # noqa: E402
from ui import hud                                   # noqa: E402
from ui.class_select import ClassSelectScene         # noqa: E402
from ui.new_game import (NAME_LENGTH, DungeonSelectScene, LevelSelectScene,   # noqa: E402
                         NameScene, _can_draw, clean_name)


from core.game import Game                           # noqa: E402


@pytest.fixture
def game():
    g = Game()
    yield g
    pygame.quit()


def key(k):
    return pygame.event.Event(pygame.KEYDOWN, key=k, mod=0, unicode="")


def typed(text):
    return pygame.event.Event(pygame.TEXTINPUT, text=text)


def send(game, *events):
    """Give events to the current scene, then update and draw it once (a draw must not crash)."""
    for event in events:
        game.scenes.current.handle_event(key(event) if isinstance(event, int) else event)
    game.scenes.current.update(1 / 60)
    game.scenes.current.draw(game.screen)


# --- the level banks --------------------------------------------------------------
def test_every_level_of_every_dungeon_has_a_bank_file_with_matching_subject_and_level():
    for dungeon in dungeons.all_dungeons():
        for entry in dungeon["levels"]:
            path = dungeons.bank_path(dungeon["id"], entry["id"])
            bank = json.loads(path.read_text(encoding="utf-8"))
            assert isinstance(bank["questions"], list)
            for question in bank["questions"]:
                assert question["subject"] == dungeon["id"] and question["level"] == entry["id"], question["id"]


def test_only_levels_with_questions_in_open_dungeons_can_be_played():
    assert dungeons.is_playable("german", "B1")
    assert dungeons.is_playable("german", "A1")
    assert not dungeons.is_playable("german", "A2")        # empty for now
    assert not dungeons.is_playable("english", "A1")       # in development, no levels
    assert not dungeons.is_playable("klingon", "B1")       # not a dungeon at all


def test_the_default_level_is_playable():
    assert dungeons.is_playable(*dungeons.default_choice())


def test_every_dungeon_and_level_has_its_text():
    for dungeon in dungeons.all_dungeons():
        assert t(f"dungeon_{dungeon['id']}") != f"dungeon_{dungeon['id']}"
        assert t(f"dungeon_{dungeon['id']}_text") != f"dungeon_{dungeon['id']}_text"
        for entry in dungeon["levels"]:
            name = f"level_{dungeon['id']}_{entry['id']}_text"
            assert t(name) != name


# --- the run remembers name, subject and level ---------------------------------
def test_a_run_saves_and_loads_its_name_subject_and_level():
    run = new_run("archer", seed=3, name="Mia", subject="german", level="B1")
    data = run_to_dict(run)
    assert data["version"] == SAVE_VERSION
    again = run_from_dict(data)
    assert (again.player.name, again.subject, again.level) == ("Mia", "german", "B1")
    assert again.engine.questions == run.engine.questions


def test_old_calls_without_the_new_keywords_still_work():
    run = new_run("warrior", seed=1)
    assert (run.subject, run.level) == dungeons.default_choice() and run.player.name == ""
    assert run.engine.questions                           # the default level has questions


def test_a_save_from_the_previous_version_is_not_loaded():
    data = run_to_dict(new_run("mage", seed=2))
    data["version"] = SAVE_VERSION - 1
    with pytest.raises(ValueError):
        run_from_dict(data)


# --- the name -------------------------------------------------------------------
def test_names_lose_characters_the_font_cannot_draw_and_are_cut_to_length(game):
    font = game.fonts["big"]
    assert clean_name("  Mia   Lena ", font) == "Mia Lena"
    # The default font has no "ệ": its accent marks come off until a letter the font has is left.
    name = clean_name("Việt", font)
    assert name in ("Việt", "Viêt", "Viet")
    assert all(_can_draw(char, font) for char in name)
    assert clean_name("", font) == ""                     # nothing drawable at all
    assert len(clean_name("A" * 40, font)) == NAME_LENGTH


def test_the_longest_name_fits_in_the_hud_panel(game):
    player = new_run("warrior", name="W" * NAME_LENGTH).player
    width = hud.PLAYER_PANEL.width - 28                          # the inside of the panel's frame
    left, right = hud.name_line(game.fonts, player, width)
    full = game.fonts["normal"].size(player.name)[0] + game.fonts["small"].size(right)[0]
    if full > width:                                             # with a wide font the name is too long...
        assert left.endswith("...")                              # ...so it was shortened
    assert game.fonts["normal"].size(left)[0] + game.fonts["small"].size(right)[0] <= width
    short = new_run("warrior", name="Mia").player
    assert hud.name_line(game.fonts, short, width)[0] == "Mia"   # short names are not touched


# --- the whole way from the title to floor 1 ---------------------------------------
def test_new_game_goes_name_class_dungeon_level_then_floor_one(game):
    send(game, pygame.K_RETURN)                                  # New game
    assert isinstance(game.scenes.current, NameScene)
    send(game, typed("Mia"), pygame.K_RETURN)
    assert isinstance(game.scenes.current, ClassSelectScene)
    send(game, pygame.K_3, pygame.K_RETURN)                      # Archer
    assert isinstance(game.scenes.current, DungeonSelectScene)
    send(game, pygame.K_RETURN)                                  # German
    level_screen = game.scenes.current
    assert isinstance(level_screen, LevelSelectScene)
    assert level_screen.levels[level_screen.selected] == "A1"    # the first playable level is picked
    send(game, pygame.K_RETURN)
    assert isinstance(game.scenes.current, DungeonScene)
    run = game.run_state
    assert (run.player.name, run.player.class_id, run.subject, run.level) == ("Mia", "archer", "german", "A1")
    assert save.has_save()


def test_an_empty_name_becomes_the_default_name(game):
    flow.begin_new_game(game)
    send(game, pygame.K_RETURN)
    assert game.new_game["name"] == t("default_hero_name")


def test_escape_goes_back_one_screen_and_keeps_what_was_picked(game):
    flow.begin_new_game(game)
    send(game, typed("Bo"), pygame.K_RETURN, pygame.K_2, pygame.K_RETURN, pygame.K_RETURN)
    assert isinstance(game.scenes.current, LevelSelectScene)
    send(game, pygame.K_ESCAPE)
    assert isinstance(game.scenes.current, DungeonSelectScene)
    send(game, pygame.K_ESCAPE)
    assert isinstance(game.scenes.current, ClassSelectScene) and game.scenes.current.selected == 1
    send(game, pygame.K_ESCAPE)
    assert isinstance(game.scenes.current, NameScene) and game.scenes.current.input.text == "Bo"
    send(game, pygame.K_ESCAPE)
    assert isinstance(game.scenes.current, TitleScene)


def test_a_dungeon_in_development_cannot_be_entered(game):
    flow.begin_new_game(game)
    flow.name_chosen(game, "Mia")
    flow.class_chosen(game, "mage")
    screen = game.scenes.current
    locked = next(i for i, d in enumerate(screen.dungeons) if not d["available"])
    screen.choose(locked)
    send(game)
    assert game.scenes.current is screen and screen.message


def test_an_empty_level_cannot_be_started(game):
    flow.begin_new_game(game)
    flow.name_chosen(game, "Mia")
    flow.class_chosen(game, "mage")
    flow.dungeon_chosen(game, "german")
    screen = game.scenes.current
    send(game, pygame.K_2, pygame.K_RETURN)                      # A2 has no questions yet
    assert game.scenes.current is screen and screen.message
    assert game.run_state is None


def test_the_demo_skips_every_new_game_screen(game):
    send(game, pygame.K_F1)
    assert isinstance(game.scenes.current, DungeonScene) and game.run_state.demo


def test_the_title_screen_animates_and_draws_without_errors(game):
    title = game.scenes.current
    for _ in range(30):
        send(game)
    assert len(title.backdrop.embers) > 0
