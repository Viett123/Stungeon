"""Panels drawn on top of the game: player status, floor number, messages (owner: B)."""
import pygame

from core import settings
from core.strings import t
from ui import theme, widgets

PLAYER_PANEL = pygame.Rect(12, 12, 330, 128)
MESSAGE_WIDTH = 520
LINE_HEIGHT = 26


def draw_player_panel(surface, fonts, player, rect=PLAYER_PANEL):
    """Class and level, a red HP bar, a blue resource bar, then XP and gold."""
    inside = theme.draw_frame(surface, rect)
    small = fonts["small"]
    widgets.text(surface, fonts["normal"], t("player_label", cls=player.class_name, level=player.level),
                 theme.GOLD, inside.topleft)
    widgets.bar(surface, (inside.x, inside.y + 28, inside.width, 22), player.hp, player.max_hp,
                theme.HP, theme.HP_BACK, t("hp_label", hp=player.hp, max_hp=player.max_hp), small)
    widgets.bar(surface, (inside.x, inside.y + 54, inside.width, 22), player.resource, player.max_resource,
                theme.RESOURCE, theme.RESOURCE_BACK,
                t("res_label", res=player.resource_name, r=player.resource, max_r=player.max_resource), small)
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
