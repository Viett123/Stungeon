"""Tests for the UI kit, run without a window."""
import os

import pytest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
pygame = pytest.importorskip("pygame")

from core import settings                          # noqa: E402
from systems.player import Player                  # noqa: E402
from ui import hud, move_info, theme, widgets      # noqa: E402
from ui.button import Button                       # noqa: E402
from ui.hotbar import Hotbar                       # noqa: E402
from ui.text_input import TextInput                # noqa: E402
from ui.tooltip import draw_tooltip, tooltip_rect  # noqa: E402


@pytest.fixture
def screen():
    pygame.init()
    surface = pygame.display.set_mode((settings.SCREEN_W, settings.SCREEN_H))
    yield surface
    pygame.quit()


@pytest.fixture
def fonts(screen):
    return {"big": pygame.font.Font(None, 48), "normal": pygame.font.Font(None, 32),
            "small": pygame.font.Font(None, 26)}


def typed(text):
    return pygame.event.Event(pygame.TEXTINPUT, text=text)


def test_frame_returns_the_area_inside_it(screen):
    inside = theme.draw_frame(screen, (100, 100, 300, 200))
    assert inside == pygame.Rect(114, 114, 272, 172)


def test_button_only_reacts_when_enabled_and_under_the_mouse():
    button = Button((10, 10, 100, 40), "Go")
    assert button.hit((50, 30)) and not button.hit((500, 30))
    button.enabled = False
    assert not button.hit((50, 30))


def test_text_input_types_and_deletes():
    box = TextInput()
    for event in (typed("d"), typed("ie"), typed("x")):
        box.handle_event(event)
    box.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_BACKSPACE))
    assert box.text == "die"
    box.clear()
    assert box.text == ""


def test_text_input_has_a_length_limit():
    box = TextInput()
    box.handle_event(typed("a" * 500))
    assert len(box.text) == 60


def test_tooltip_stays_on_the_screen():
    area = pygame.Rect(0, 0, 1280, 720)
    for anchor in (pygame.Rect(0, 0, 64, 64), pygame.Rect(1250, 700, 64, 64), pygame.Rect(600, 650, 64, 64)):
        assert area.contains(tooltip_rect((300, 120), anchor, area))


def test_tooltip_sits_above_its_anchor_when_there_is_room():
    anchor = pygame.Rect(600, 650, 64, 64)
    assert tooltip_rect((300, 120), anchor, pygame.Rect(0, 0, 1280, 720)).bottom <= anchor.top


def test_hotbar_has_one_centred_slot_per_move(fonts):
    player = Player("warrior", level=5)
    hotbar = Hotbar()
    hotbar.set_entries(move_info.hotbar_entries(player.unlocked_moves(), player.resource_name, fonts["small"]))
    assert len(hotbar.rects) == 5
    middle = (hotbar.rects[0].left + hotbar.rects[-1].right) // 2
    assert abs(middle - settings.SCREEN_W // 2) <= 1
    assert hotbar.index_at(hotbar.rects[2].center) == 2
    assert hotbar.index_at((5, 5)) is None


def test_move_lines_start_with_the_name_and_mark_unaffordable_cost():
    move = dict(Player("mage").unlocked_moves()[1], affordable=False)
    lines = move_info.move_lines(move, "Mana")
    assert lines[0] == (move["name"], theme.GOLD)
    assert lines[-1][1] == theme.BAD


def test_initials():
    assert move_info.initials("Shield Bash") == "SB"
    assert move_info.initials("Slash") == "Sl"


def test_everything_draws_without_crashing(screen, fonts):
    player = Player("archer", level=5)
    hotbar = Hotbar()
    hotbar.set_entries(move_info.hotbar_entries(player.unlocked_moves(), player.resource_name, fonts["small"]))
    hud.draw_player_panel(screen, fonts, player)
    hud.draw_floor_label(screen, fonts, 2)
    hud.draw_messages(screen, fonts, [("Hello", theme.GOLD), ("World", theme.TEXT)], bottom=600)
    hotbar.draw(screen, fonts, hotbar.rects[0].center, selected=1)       # with a tooltip
    hotbar.draw(screen, fonts, (0, 0), active=False)
    Button((10, 300, 200, 40), "Answer").draw(screen, fonts["normal"], (20, 310), selected=True)
    TextInput((10, 400, 300, 52)).draw(screen, fonts["big"])
    widgets.bar(screen, (10, 500, 200, 22), 0, 0, theme.HP, theme.HP_BACK, "empty", fonts["small"])
    draw_tooltip(screen, fonts["small"], [], pygame.Rect(0, 0, 10, 10))   # no lines: draws nothing
