"""Decides how each grid cell looks in the three-quarter view. No pygame here.

You look at the dungeon from above and slightly from the south. A wall is built from parts:

  brick  - the brick face. A wall cell shows it when there is floor directly below it
           (the wall behind a room) or directly above it (the wall in front of a room).
  cap    - the light stone strip on top of a brick face. It is drawn in the cell ABOVE
           the brick, on top of whatever is there (often the last row of floor).
  side   - a thin vertical line beside a room: in the rock cell left or right of a
           floor or brick cell.
  corner - a small piece that closes the gap where a side line meets a cap.

Rock that touches nothing is not drawn at all.
"""
from dungeon.floor import STAIRS, WALL

FLOOR = "tile_floor"
STAIRS_TILE = "tile_stairs"
BRICK = "tile_wall_front"
CAP = "tile_wall_cap"
SIDE_LEFT = "tile_wall_side_left"        # the line is on the right edge of this cell
SIDE_RIGHT = "tile_wall_side_right"      # the line is on the left edge of this cell
CORNER_LEFT = "tile_wall_corner_left"
CORNER_RIGHT = "tile_wall_corner_right"


def is_open(grid, x, y):
    """True if (x, y) is inside the grid and not a wall."""
    return 0 <= y < len(grid) and 0 <= x < len(grid[0]) and grid[y][x] != WALL


def is_brick(grid, x, y):
    """True for a wall cell that shows its brick face."""
    inside = 0 <= y < len(grid) and 0 <= x < len(grid[0])
    return inside and grid[y][x] == WALL and (is_open(grid, x, y + 1) or is_open(grid, x, y - 1))


def has_cap(grid, x, y):
    """True if a cap is drawn in this cell: the cell below is brick and this one is not."""
    return is_brick(grid, x, y + 1) and not is_brick(grid, x, y)


def _is_solid(grid, x, y):
    """Floor or brick: something a side line can run along."""
    return is_open(grid, x, y) or is_brick(grid, x, y)


def base_tiles(grid, x, y):
    """The tile names to draw in this cell, bottom one first. Empty list = draw nothing."""
    if is_open(grid, x, y):
        return [STAIRS_TILE if grid[y][x] == STAIRS else FLOOR]
    if is_brick(grid, x, y):
        return [BRICK]
    names = []
    if _is_solid(grid, x + 1, y):
        names.append(SIDE_LEFT)
    if _is_solid(grid, x - 1, y):
        names.append(SIDE_RIGHT)
    if not names and not has_cap(grid, x, y):
        # Plain rock next to a cap: close the corner.
        if has_cap(grid, x + 1, y):
            names.append(CORNER_LEFT)
        if has_cap(grid, x - 1, y):
            names.append(CORNER_RIGHT)
    return names


def in_wall_shadow(grid, x, y):
    """True for an open cell with brick directly above it: the wall casts a shadow on it."""
    return is_open(grid, x, y) and is_brick(grid, x, y - 1)
