"""Floor generation (owner: A).

PLACEHOLDER: every floor is one empty room with stairs in the corner.
A replaces generate_floor() with real random rooms and corridors. Keep the signature.
"""
import random
from dataclasses import dataclass, field

FLOOR = 0
WALL = 1
STAIRS = 2


@dataclass
class Floor:
    number: int
    width: int
    height: int
    grid: list            # grid[y][x], one of FLOOR / WALL / STAIRS
    start: tuple          # (x, y) where the player appears
    stairs: tuple         # (x, y)
    enemies: list = field(default_factory=list)   # filled in by A later

    def is_walkable(self, x, y):
        return 0 <= x < self.width and 0 <= y < self.height and self.grid[y][x] != WALL


def generate_floor(floor_number, seed, demo=False) -> Floor:
    rng = random.Random(seed)   # use only this rng, so the same seed always gives the same floor
    width, height = 26, 14      # 26 x 48 px = 1248 px, fits in 1280 x 720 with a status line
    grid = [[WALL if x in (0, width - 1) or y in (0, height - 1) else FLOOR
             for x in range(width)] for y in range(height)]
    stairs = (width - 3, height - 3)
    grid[stairs[1]][stairs[0]] = STAIRS
    _ = rng  # TODO(A): use rng for rooms, corridors and enemy placement
    return Floor(floor_number, width, height, grid, start=(2, 2), stairs=stairs)
