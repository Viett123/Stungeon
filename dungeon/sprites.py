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
VOID = (14, 12, 12)
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


_TILE_PLACEHOLDERS = {
    "tile_wall_front": _wall_front_placeholder,
    "tile_wall_top": _wall_top_placeholder,
    "tile_stairs": _stairs_placeholder,
}


def tile_sprite(name, variant=0):
    """A 48x48 tile. name is tile_floor, tile_wall_front, tile_wall_top or tile_stairs."""
    if name == "tile_floor":
        # A special floor picture for this variant (tile_floor_0.png, tile_floor_1.png, ...)
        # if there is one, otherwise the normal tile_floor.png.
        image = assets.load_sprite(f"tile_floor_{variant}") or assets.load_sprite("tile_floor")
    else:
        image = assets.load_sprite(name)
    if image is not None:
        return image
    if name == "tile_floor":
        return assets.scale_up(_floor_placeholder(variant))
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


def character_sprite(name, color, letter="", font=None, big=False):
    """A character sprite. Bosses (big=True) are drawn 4 times bigger instead of 3.

    letter is drawn on placeholder bodies so enemies can be told apart before there is art.
    """
    factor = settings.TILE_SCALE + 1 if big else settings.TILE_SCALE
    image = assets.load_sprite(name, factor)
    if image is not None:
        return image
    image = assets.scale_up(_character_placeholder(color), factor)
    if letter and font:
        mark = font.render(letter, True, OUTLINE)
        image.blit(mark, mark.get_rect(center=(image.get_width() // 2, 12 * factor)))
    return image
