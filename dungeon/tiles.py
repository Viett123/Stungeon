"""Decides how each grid cell looks in the three-quarter view. No pygame here.

In a three-quarter top-down view you look at the dungeon from above and slightly from
the south. So a wall with floor directly BELOW it (to the south) shows its front face.
Other walls next to a floor only show their dark top. Walls far from any floor are not
drawn at all (they are solid rock).
"""
from dungeon.floor import STAIRS, WALL

LOOK_FLOOR = "floor"
LOOK_STAIRS = "stairs"
LOOK_WALL_FRONT = "wall_front"
LOOK_WALL_TOP = "wall_top"
LOOK_VOID = "void"

_NEIGHBOURS = [(-1, -1), (0, -1), (1, -1), (-1, 0), (1, 0), (-1, 1), (0, 1), (1, 1)]


def _is_open(grid, x, y):
    """True if (x, y) is inside the grid and not a wall."""
    return 0 <= y < len(grid) and 0 <= x < len(grid[0]) and grid[y][x] != WALL


def tile_look(grid, x, y):
    """Which of the LOOK_ kinds the cell grid[y][x] should be drawn as."""
    cell = grid[y][x]
    if cell == STAIRS:
        return LOOK_STAIRS
    if cell != WALL:
        return LOOK_FLOOR
    if _is_open(grid, x, y + 1):
        return LOOK_WALL_FRONT
    if any(_is_open(grid, x + dx, y + dy) for dx, dy in _NEIGHBOURS):
        return LOOK_WALL_TOP
    return LOOK_VOID


def in_wall_shadow(grid, x, y):
    """True for an open cell with a wall directly above it: the wall casts a shadow on it."""
    return _is_open(grid, x, y) and not _is_open(grid, x, y - 1)
