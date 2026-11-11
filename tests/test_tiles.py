"""The wall rules of the three-quarter view (dungeon/tiles.py)."""
from dungeon import tiles
from dungeon.floor import FLOOR as F, STAIRS as S, WALL as W, generate_floor

# A small room: two rows of floor (with stairs), surrounded by rock.
#        x: 0  1  2  3  4  5
GRID = [
    [W, W, W, W, W, W],   # y 0
    [W, W, W, W, W, W],   # y 1  <- brick behind the room
    [W, W, F, S, W, W],   # y 2
    [W, W, F, F, W, W],   # y 3
    [W, W, W, W, W, W],   # y 4  <- brick in front of the room
    [W, W, W, W, W, W],   # y 5
]


def test_floor_and_stairs():
    assert tiles.base_tiles(GRID, 2, 2) == [tiles.FLOOR]
    assert tiles.base_tiles(GRID, 3, 2) == [tiles.STAIRS_TILE]


def test_walls_above_and_below_a_room_show_brick():
    assert tiles.base_tiles(GRID, 2, 1) == [tiles.BRICK]     # behind the room
    assert tiles.base_tiles(GRID, 3, 4) == [tiles.BRICK]     # in front of the room


def test_every_brick_has_a_cap_in_the_cell_above_it():
    assert tiles.has_cap(GRID, 2, 0)        # above the back wall: a rock cell
    assert tiles.has_cap(GRID, 2, 3)        # above the front wall: the last row of floor
    assert not tiles.has_cap(GRID, 2, 2)    # the first row of floor has floor below it
    assert not tiles.has_cap(GRID, 2, 1)    # brick itself never has a cap


def test_side_lines_run_beside_floor_and_brick():
    for y in (1, 2, 3, 4):                  # beside both brick rows and both floor rows
        assert tiles.base_tiles(GRID, 1, y) == [tiles.SIDE_LEFT]
        assert tiles.base_tiles(GRID, 4, y) == [tiles.SIDE_RIGHT]


def test_corner_pieces_close_the_gap_beside_the_top_cap():
    assert tiles.base_tiles(GRID, 1, 0) == [tiles.CORNER_LEFT]
    assert tiles.base_tiles(GRID, 4, 0) == [tiles.CORNER_RIGHT]


def test_rock_far_from_any_floor_is_not_drawn():
    assert tiles.base_tiles(GRID, 0, 0) == []
    assert tiles.base_tiles(GRID, 5, 5) == []
    assert tiles.base_tiles(GRID, 2, 5) == []                # below the front wall


def test_a_thin_wall_between_two_corridors_gets_both_side_lines():
    grid = [[W, W, W], [F, W, F], [F, W, F], [W, W, W]]
    assert tiles.base_tiles(grid, 1, 1) == [tiles.SIDE_LEFT, tiles.SIDE_RIGHT]


def test_shadow_falls_on_floor_directly_below_brick():
    assert tiles.in_wall_shadow(GRID, 2, 2)
    assert not tiles.in_wall_shadow(GRID, 2, 3)


def test_every_room_on_a_real_floor_has_brick_behind_it():
    floor = generate_floor(1, seed=3)
    for x, y, w, h in floor.rooms:
        assert tiles.is_brick(floor.grid, x + 1, y - 1)      # x + 1: a room's corner cell may be cut off
