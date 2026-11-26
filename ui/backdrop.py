"""The dungeon room shown behind the title menu and the new-game screens (owner: B).

It is a wall with burning torches at the top and a stone floor below, made from the
same tile art as the dungeon. The edges are darkened (a "vignette"), so the middle of
the screen, where the menu is, looks lit by the torches. Small embers float upwards.

The title screen asks for biomes=True: the screen is cut into three side by side, one for each
floor look (jungle | stone | desert), split by dark cracks.

The still picture is built once and shared by every screen, never inside draw().
Missing art is fine: tile_sprite() gives code-drawn tiles, and with no torch art
there are simply no torches.
"""
import random

import pygame

from core import settings
from dungeon import sprites
from systems.player import load_data

TILE = settings.TILE
WALL_ROWS = 2                  # rows of wall top, above the row of wall fronts
TORCH_EVERY = 4                # a torch on every 4th wall tile
TORCH_FPS = 8
EMBERS = 40                    # how many embers float up at once
EMBER_SPEED = (14, 34)         # pixels per second, slowest and fastest
EMBER_COLORS = [(255, 190, 90), (255, 140, 60), (240, 220, 150)]
FLOOR_VARIANT_CHANCE = 0.08    # how often a cracked or special floor tile appears
CLEAR_LEFT, CLEAR_RIGHT = 280, 960   # plain floor between these x positions, where the text is

TITLE_BIOMES = ("jungle", "stone", "desert")   # left, middle, right third: names from data/themes.json
CRACK_W = 10                   # width of the dark crack between two biomes

_pictures = {}                 # biomes True/False -> the still picture, made the first time it is needed


def _vignette(size):
    """A see-through middle that gets darker towards the edges.

    Drawing a smooth gradient pixel by pixel would be slow. Instead, rings of
    growing darkness are drawn on a tiny surface, which smoothscale then blows up:
    scaling up blurs the rings into a soft gradient for free.
    """
    small = pygame.Surface((64, 36), pygame.SRCALPHA)
    small.fill((0, 0, 0, 225))
    for step in range(16, 0, -1):                     # from the outside ring inwards
        alpha = int(225 * (step / 16) ** 1.6)
        rect = pygame.Rect(0, 0, 64 * step / 16 * 1.25, 36 * step / 16 * 1.25)
        rect.center = (32, 18)
        pygame.draw.ellipse(small, (0, 0, 0, alpha), rect)
    return pygame.transform.smoothscale(small, size)


def biome_columns():
    """Which floor look each third of the title screen shows: [(x where it starts, folder, background)]."""
    themes = load_data("themes.json")["themes"]
    third = settings.SCREEN_W // len(TITLE_BIOMES)
    return [(i * third, themes[name]["folder"], tuple(themes[name]["background"]))
            for i, name in enumerate(TITLE_BIOMES)]


def _biome_at(x, columns):
    """The (folder, background) of the third that the screen x position is in."""
    for start, folder, background in reversed(columns):
        if x >= start:
            return folder, background
    return columns[0][1], columns[0][2]


def _build_picture(biomes=False):
    width, height = settings.SCREEN_W, settings.SCREEN_H
    picture = pygame.Surface((width, height))
    picture.fill(sprites.VOID)
    rng = random.Random(7)                            # the same room every time the game starts
    columns = width // TILE + 1
    thirds = biome_columns() if biomes else [(0, "", sprites.VOID)]
    for row in range(height // TILE + 1):
        for column in range(columns):
            folder, background = _biome_at(column * TILE, thirds)
            if row < WALL_ROWS:
                if folder:                             # the themes have no wall-top art: use their dark colour
                    picture.fill(background, (column * TILE, row * TILE, TILE, TILE))
                    continue
                name, variant = "tile_wall_top", None
            elif row == WALL_ROWS:
                name, variant = "tile_wall_front", rng.randrange(3) if rng.random() < 0.15 else None
            else:
                name = "tile_floor"
                variant = rng.randrange(8) if rng.random() < FLOOR_VARIANT_CHANCE else None
                if CLEAR_LEFT <= column * TILE <= CLEAR_RIGHT:
                    variant = None             # no skulls or cracks behind the titles and menus
            picture.blit(sprites.tile_sprite(name, variant, folder), (column * TILE, row * TILE))
    if biomes:
        for start, _, _ in thirds[1:]:                 # a dark crack where two biomes meet
            pygame.draw.rect(picture, sprites.VOID, (start - CRACK_W // 2, 0, CRACK_W, height))
            pygame.draw.line(picture, (0, 0, 0), (start, 0), (start, height), 2)
    picture.blit(_vignette((width, height)), (0, 0))
    return picture


class Backdrop:
    def __init__(self, biomes=False):
        if biomes not in _pictures:
            _pictures[biomes] = _build_picture(biomes)
        self.picture = _pictures[biomes]
        self.torches = sprites.torch_frames()
        # The torches hang on the wall front row, which the vignette darkens a little less in the middle.
        self.torch_spots = [(x * TILE + TILE // 2, WALL_ROWS * TILE + TILE // 2)
                            for x in range(1, settings.SCREEN_W // TILE, TORCH_EVERY)]
        self.time = 0.0
        self.rng = random.Random()
        self.embers = [self._new_ember(anywhere=True) for _ in range(EMBERS)]

    def _new_ember(self, anywhere=False):
        """[x, y, speed, colour]. New embers start at the bottom; the first ones start anywhere."""
        y = self.rng.uniform(0, settings.SCREEN_H) if anywhere else settings.SCREEN_H + 4
        return [self.rng.uniform(0, settings.SCREEN_W), y, self.rng.uniform(*EMBER_SPEED),
                self.rng.choice(EMBER_COLORS)]

    def update(self, dt):
        self.time += dt
        for i, ember in enumerate(self.embers):
            ember[1] -= ember[2] * dt                  # float up
            ember[0] += self.rng.uniform(-10, 10) * dt  # and drift a little sideways
            if ember[1] < -4:
                self.embers[i] = self._new_ember()

    def draw(self, surface):
        surface.blit(self.picture, (0, 0))
        if self.torches:
            frame = self.torches[int(self.time * TORCH_FPS) % len(self.torches)]
            for spot in self.torch_spots:
                surface.blit(frame, frame.get_rect(center=spot))
        for x, y, _, color in self.embers:
            # Embers get smaller as they rise, so they look like they burn away.
            size = 3 if y > settings.SCREEN_H * 0.6 else 2
            pygame.draw.rect(surface, color, (round(x), round(y), size, size))
