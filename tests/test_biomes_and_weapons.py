"""Tests for the biome frames, the three-biome title screen, the new monster art and how weapons are held."""
import os

import pytest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
pygame = pytest.importorskip("pygame")

from core import assets, flow, title_scene               # noqa: E402
from core.game import Game                               # noqa: E402
from dungeon import sprites                              # noqa: E402
from dungeon.weapon import HeldWeapon, grip_rules, pixel_size   # noqa: E402
from systems.player import load_data                     # noqa: E402
from ui import backdrop, theme                           # noqa: E402

THEMES = load_data("themes.json")["themes"]


@pytest.fixture
def game():
    return Game()


# --- frames ---------------------------------------------------------------------------
def test_every_floor_look_has_its_own_frame(game):
    pictures = [theme.frame_art(t["folder"]) for t in THEMES.values()]
    assert all(p is not None for p in pictures)
    as_bytes = [pygame.image.tobytes(p, "RGBA") for p in pictures]
    assert len(set(as_bytes)) == len(as_bytes)                    # all three look different


def test_a_floor_sets_its_frame_and_the_title_sets_it_back(game):
    flow.start_new_run(game, "warrior")
    folder = game.scenes.current.renderer.folder
    assert theme.frame_style() == folder
    title_scene.TitleScene(game)
    assert theme.frame_style() == ""


def test_borders_are_remembered_per_look(game):
    jungle = theme._art_border((300, 200), "jungle")
    desert = theme._art_border((300, 200), "desert")
    assert jungle is not desert
    assert theme._art_border((300, 200), "jungle") is jungle


# --- title screen -----------------------------------------------------------------------
def test_the_title_is_cut_into_the_three_biomes(game):
    columns = backdrop.biome_columns()
    assert [folder for _, folder, _ in columns] == [THEMES[name]["folder"] for name in backdrop.TITLE_BIOMES]
    assert columns[0][0] == 0 and columns[1][0] < columns[2][0]
    scene = title_scene.TitleScene(game)
    assert scene.backdrop.picture is not backdrop.Backdrop().picture   # other menus keep the plain room
    scene.draw(game.screen)


def test_the_mixed_frame_uses_each_biome_frame_and_restores_the_clip(game):
    surface = pygame.Surface((600, 300), pygame.SRCALPHA)
    surface.set_clip(pygame.Rect(0, 0, 590, 290))
    title_scene.draw_mixed_frame(surface, (0, 0, 600, 300))
    assert surface.get_clip() == pygame.Rect(0, 0, 590, 290)
    left, right = surface.get_at((2, 150)), surface.get_at((585, 150))
    assert left != right                                          # jungle on the left, desert on the right


# --- monsters ---------------------------------------------------------------------------
def test_every_enemy_has_art(game):
    for enemy_id in load_data("enemies.json")["enemies"]:
        name = f"enemy_{enemy_id}"
        assert sprites.has_frames(name, "idle") or assets.load_sprite(name) is not None, enemy_id


# --- holding weapons ----------------------------------------------------------------------
def test_pixel_size_shrinks_long_weapons_by_a_whole_number():
    assert pixel_size(16, 3, 20) == 3                             # short enough: as big as the hero
    assert pixel_size(30, 3, 20) == 2                             # too long: 2 screen pixels per art pixel
    assert pixel_size(200, 3, 20) == 1                            # never smaller than 1
    assert isinstance(pixel_size(30, 4, 22), int)


def test_grips_come_from_data_and_a_weapon_can_change_its_own():
    data = load_data("weapon_grips.json")
    assert grip_rules("old_sword", "melee") == data["styles"]["melee"]
    spear = grip_rules("spear", "melee")
    assert spear["grip"] == data["weapons"]["spear"]["grip"] and spear["hand"] == data["styles"]["melee"]["hand"]
    assert grip_rules("hunting_bow", "bow")["max_length"] == data["styles"]["bow"]["max_length"]


def test_a_big_bow_may_be_bigger(monkeypatch):
    data = load_data("weapon_grips.json")
    rules = dict(data, weapons={"giant_bow": {"big": True}})
    monkeypatch.setattr("dungeon.weapon.load_data", lambda name: rules)
    assert grip_rules("giant_bow", "bow")["max_length"] == data["styles"]["bow"]["big_max_length"]


def test_staffs_are_held_higher_than_swords_and_bows_at_arms_length(game):
    sword, staff, bow = HeldWeapon("old_sword", 3), HeldWeapon("oak_staff", 3), HeldWeapon("hunting_bow", 3)
    assert staff.hand(0, 0, False)[1] < sword.hand(0, 0, False)[1]          # higher up (smaller y)
    assert bow.hand(0, 0, False)[0] > sword.hand(0, 0, False)[0]            # further in front


@pytest.mark.parametrize("item_id", ["hunting_bow", "short_bow", "knight_sword", "lavish_sword", "oak_staff"])
def test_weapons_are_not_much_taller_than_the_hero(game, item_id):
    weapon = HeldWeapon(item_id, 3)
    rules = grip_rules(item_id, weapon.style)
    art = pygame.image.load(f"assets/sprites/weapon_{item_id}.png")
    length = art.get_bounding_rect().height * weapon.pixel / 3              # in the hero's art pixels
    assert length <= rules["max_length"] * 1.25


# --- fonts ----------------------------------------------------------------------------------
LETTERS = "äöüßÄÖÜ" + "ĐđệữảỗắẫơƯ"        # German and Vietnamese


def _picture(font, char):
    return pygame.image.tobytes(font.render(char, False, (255, 255, 255)), "RGBA")


@pytest.mark.parametrize("name", ["title", "big", "normal", "small", "question", "question_small", "answer"])
def test_the_pixel_fonts_can_draw_german_and_vietnamese(game, name):
    from core import settings
    file_name, size = settings.FONTS[name]
    assert (settings.FONT_DIR / file_name).exists()
    font = game.fonts[name]
    missing = _picture(font, "")                           # a character no font has: the "missing" box
    for char in LETTERS:
        assert _picture(font, char) != missing, (name, char)


def test_a_missing_font_file_falls_back_to_the_built_in_font(monkeypatch, tmp_path):
    from core import game as game_module, settings
    monkeypatch.setattr(settings, "FONT_DIR", tmp_path)          # an empty folder
    assert game_module.load_font("normal") is not None


# --- credits ------------------------------------------------------------------------------
def test_every_credit_fits_on_the_screen_above_the_hint(game):
    from ui.credits_screen import HINT_SPACE, PANEL, CreditsScene
    scene = CreditsScene(game)
    bottom = theme.inner(PANEL).bottom - HINT_SPACE
    for font, line, _, (x, y) in scene.layout:
        width, height = game.fonts[font].size(line)
        assert y + height <= bottom + 4 and x + width <= PANEL.right, line
    names = " ".join(entry["author"] for entry in scene.entries)
    assert "conchuotbiluoc" in names                                # the team's artist is named
