"""Panels drawn on top of the game: player status, floor number, messages (owner: B)."""
import pygame

from core import settings
from core.strings import t
from ui import theme, widgets
from ui.anim import Trail

PLAYER_PANEL = pygame.Rect(12, 12, 330, 128)
MESSAGE_WIDTH = 520
LINE_HEIGHT = 26


_trails = {}   # player -> (HP trail, resource trail); only the current player is kept


def _trails_for(player):
    """The two bar trails of this player. They are remembered between frames."""
    if id(player) not in _trails:
        _trails.clear()      # a new run has a new player: forget the old one
        _trails[id(player)] = (Trail(player.hp), Trail(player.resource))
    return _trails[id(player)]


def player_label(player):
    """"Mia  Mage  Lv 2", or just "Mage  Lv 2" for a hero without a name (old saves, the demo)."""
    if player.name:
        return t("player_label_named", name=player.name, cls=player.class_name, level=player.level)
    return t("player_label", cls=player.class_name, level=player.level)


def fit(font, string, width):
    """The string, shortened with "..." at the end if it is wider than `width` pixels."""
    if font.size(string)[0] <= width:
        return string
    while string and font.size(string + "...")[0] > width:
        string = string[:-1]
    return string.rstrip() + "..."


def name_line(fonts, player, width):
    """(left text, right text) for the top line of the player panel.

    With a name: the name on the left, "Warrior  Lv 1" small on the right, and the
    name is shortened if both do not fit. Without a name: "Warrior  Lv 1" on the left.
    """
    level_text = t("player_label", cls=player.class_name, level=player.level)
    if not player.name:
        return level_text, ""
    room = width - fonts["small"].size(level_text)[0] - 12
    return fit(fonts["normal"], player.name, room), level_text


def draw_player_panel(surface, fonts, player, rect=PLAYER_PANEL):
    """Name, class and level, a red HP bar, a blue resource bar, then XP and gold."""
    inside = theme.draw_frame(surface, rect)
    small = fonts["small"]
    left, right = name_line(fonts, player, inside.width)
    widgets.text(surface, fonts["normal"], left, theme.GOLD, inside.topleft)
    if right:
        widgets.text(surface, small, right, theme.TEXT_DIM, (inside.right, inside.y + 3), "topright")
    hp_trail, resource_trail = _trails_for(player)
    widgets.bar(surface, (inside.x, inside.y + 28, inside.width, 22), player.hp, player.max_hp,
                theme.HP, theme.HP_BACK, t("hp_label", hp=player.hp, max_hp=player.max_hp), small,
                trail=hp_trail.follow(player.hp))
    widgets.bar(surface, (inside.x, inside.y + 54, inside.width, 22), player.resource, player.max_resource,
                theme.RESOURCE, theme.RESOURCE_BACK,
                t("res_label", res=player.resource_name, r=player.resource, max_r=player.max_resource), small,
                trail=resource_trail.follow(player.resource))
    widgets.text(surface, small, t("xp_gold", xp=player.xp, gold=player.gold), theme.TEXT_DIM,
                 (inside.x, inside.y + 82))


def draw_floor_label(surface, fonts, floor_number):
    """A small panel in the top-right corner."""
    rect = pygame.Rect(0, 12, 150, 54)
    rect.right = settings.SCREEN_W - 12
    theme.draw_frame(surface, rect)
    widgets.text(surface, fonts["normal"], t("floor_title", n=floor_number), theme.GOLD, rect.center, "center")


def draw_messages(surface, fonts, lines, bottom):
    """A framed box of text lines, centred, with its lower edge at `bottom`."""
    if not lines:
        return
    height = len(lines) * LINE_HEIGHT + 2 * theme.FRAME_PAD + 4
    # Wide enough for the longest line, but never narrower than MESSAGE_WIDTH.
    longest = max(fonts["small"].size(widgets.drawable(line))[0] for line, _ in lines)
    width = max(MESSAGE_WIDTH, longest + 2 * theme.FRAME_PAD + 24)
    rect = pygame.Rect(0, 0, width, height)
    rect.midbottom = (settings.SCREEN_W // 2, bottom)
    inside = theme.draw_frame(surface, rect)
    y = inside.y + 2
    for line, color in lines:
        widgets.text(surface, fonts["small"], line, color, (inside.centerx, y), "midtop")
        y += LINE_HEIGHT
