"""Sprites for the dungeon: real art if the file exists, otherwise a placeholder drawn in code.

Placeholders are drawn on a tiny 16x16 surface and then scaled up 3 times, the same
way real pixel art is. That keeps the blocky pixel look even without any art files.
Colours are muted and earthy to fit the dark fantasy direction.
"""
import random

import pygame

from core import assets, settings

SRC = settings.TILE_SRC   # 16: size of one tile in the art

# Placeholder palette (R, G, B)
VOID = (34, 34, 34)          # the colour behind everything; matches the art pack's walls
WALL_LINE = (176, 158, 138)  # the light stone line on top of and beside walls
FLOOR = (78, 69, 59)
FLOOR_SPECKS = [(66, 58, 50), (90, 80, 68), (72, 66, 60)]
WALL_BRICK = (92, 80, 68)
WALL_MORTAR = (62, 53, 46)
WALL_LEDGE = (120, 106, 90)
WALL_TOP = (34, 30, 30)
WALL_TOP_SPECK = (44, 39, 37)
STAIRS = [(150, 122, 76), (122, 98, 60), (94, 74, 46), (66, 52, 34)]
OUTLINE = (20, 16, 16)


def _blank(width=SRC, height=SRC):
    return pygame.Surface((width, height), pygame.SRCALPHA)


# --- tiles ----------------------------------------------------------------
def _floor_placeholder(variant):
    image = _blank()
    image.fill(FLOOR)
    rng = random.Random(variant)   # the same variant always looks the same
    for _ in range(7):
        image.set_at((rng.randrange(SRC), rng.randrange(SRC)), rng.choice(FLOOR_SPECKS))
    return image


def _wall_front_placeholder():
    """The front face of a wall: rows of bricks with a lighter ledge on top."""
    image = _blank()
    image.fill(WALL_BRICK)
    for y in (5, 10, 15):                               # lines between brick rows
        pygame.draw.line(image, WALL_MORTAR, (0, y), (SRC, y))
    for row, y in enumerate((2, 6, 11)):                # short lines between bricks
        for x in range(3 if row % 2 else 7, SRC, 8):    # every other row is shifted
            pygame.draw.line(image, WALL_MORTAR, (x, y), (x, y + 3))
    pygame.draw.line(image, WALL_LEDGE, (0, 0), (SRC, 0))
    pygame.draw.line(image, WALL_LEDGE, (0, 1), (SRC, 1))
    return image


def _wall_top_placeholder():
    """The top of a wall, seen from above: dark with a few specks."""
    image = _blank()
    image.fill(WALL_TOP)
    for x, y in ((3, 4), (11, 2), (7, 10), (13, 13), (2, 12)):
        image.set_at((x, y), WALL_TOP_SPECK)
    return image


def _stairs_placeholder():
    image = _blank()
    for i, color in enumerate(STAIRS):                  # four steps going down into the dark
        pygame.draw.rect(image, color, (0, i * 4, SRC, 4))
        pygame.draw.line(image, OUTLINE, (0, i * 4 + 3), (SRC, i * 4 + 3))
    return image


def _line_placeholder(rect):
    """A see-through tile with one light stone line on it (wall caps, sides and corners)."""
    def draw():
        image = _blank()
        pygame.draw.rect(image, OUTLINE, pygame.Rect(rect).inflate(2, 2))
        pygame.draw.rect(image, WALL_LINE, rect)
        return image
    return draw


_TILE_PLACEHOLDERS = {
    "tile_wall_front": _wall_front_placeholder,
    "tile_wall_top": _wall_top_placeholder,
    "tile_stairs": _stairs_placeholder,
    "tile_wall_cap": _line_placeholder((0, 12, 16, 3)),          # along the bottom
    "tile_wall_side_left": _line_placeholder((12, 0, 3, 16)),    # along the right edge
    "tile_wall_side_right": _line_placeholder((1, 0, 3, 16)),    # along the left edge
    "tile_wall_corner_left": _line_placeholder((12, 12, 3, 4)),  # bottom-right corner
    "tile_wall_corner_right": _line_placeholder((1, 12, 3, 4)),  # bottom-left corner
}


def tile_sprite(name, variant=None, folder=""):
    """A 48x48 tile, e.g. tile_floor, tile_wall_front, tile_wall_cap, tile_stairs.

    variant: with a number, the picture <name>_<variant>.png is used if it exists
             (a cracked floor, a wall with a banner), otherwise the normal <name>.png.
    folder:  a theme folder inside assets/sprites/ (e.g. "jungle"). A picture that is
             missing there is taken from assets/sprites/ itself.
    """
    names = [f"{name}_{variant}", name] if variant is not None else [name]
    places = [f"{folder}/", ""] if folder else [""]
    for place in places:
        for candidate in names:
            image = assets.load_sprite(place + candidate)
            if image is not None:
                return image
    if name == "tile_floor":
        return assets.scale_up(_floor_placeholder(variant or 0))
    return assets.scale_up(_TILE_PLACEHOLDERS[name]())


# --- characters -----------------------------------------------------------
def _lighter(color, amount=40):
    return tuple(min(255, c + amount) for c in color)


def _character_placeholder(color):
    """A small figure, 16 wide and 20 tall, so its head overlaps the tile above it."""
    image = _blank(SRC, 20)
    pygame.draw.ellipse(image, (0, 0, 0, 90), (2, 16, 12, 4))          # shadow on the floor
    pygame.draw.rect(image, OUTLINE, (3, 6, 10, 12))                   # body outline
    pygame.draw.rect(image, color, (4, 7, 8, 10))                      # body
    pygame.draw.rect(image, OUTLINE, (4, 0, 8, 8))                     # head outline
    pygame.draw.rect(image, _lighter(color), (5, 1, 6, 6))             # head
    image.set_at((6, 4), OUTLINE)                                      # eyes
    image.set_at((9, 4), OUTLINE)
    return image


def character_frames(name, action, color, letter="", font=None, big=False):
    """The animation frames of a character for one action ("idle", "run" or "hit").

    Looks for <name>_<action>_0.png, _1.png, ... If the character has no frames for
    this action, its idle frames are used; if it has no art at all, one placeholder.
    Bosses (big=True) are drawn 4 times bigger instead of 3.
    """
    factor = settings.TILE_SCALE + 1 if big else settings.TILE_SCALE
    frames = assets.load_frames(f"{name}_{action}", factor) or assets.load_frames(f"{name}_idle", factor)
    if frames:
        return frames
    still = assets.load_sprite(name, factor)   # a single picture without animation
    if still is not None:
        return [still]
    image = assets.scale_up(_character_placeholder(color), factor)
    if letter and font:
        # The letter tells enemies apart while there is no art.
        mark = font.render(letter, True, OUTLINE)
        image.blit(mark, mark.get_rect(center=(image.get_width() // 2, 12 * factor)))
    return [image]


def chest_frames():
    """Frames of a chest opening: the first is closed, the last is fully open."""
    frames = assets.load_frames("chest")
    if frames:
        return frames
    closed, opened = _blank(), _blank()
    for image, lid in ((closed, (150, 100, 40)), (opened, (60, 40, 20))):
        pygame.draw.rect(image, OUTLINE, (1, 4, 14, 11))
        pygame.draw.rect(image, (120, 76, 30), (2, 8, 12, 6))
        pygame.draw.rect(image, lid, (2, 5, 12, 3))
    return [assets.scale_up(closed), assets.scale_up(opened)]
