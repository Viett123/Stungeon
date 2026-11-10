from dungeon import tiles
from dungeon.floor import FLOOR as F, STAIRS as S, WALL as W, generate_floor

# A small room: one row of floor with stairs, surrounded by rock.
GRID = [
    [W, W, W, W, W, W],
    [W, W, W, W, W, W],
    [W, W, F, S, W, W],
    [W, W, W, W, W, W],
    [W, W, W, W, W, W],
]


def test_floor_and_stairs():
    assert tiles.tile_look(GRID, 2, 2) == tiles.LOOK_FLOOR
    assert tiles.tile_look(GRID, 3, 2) == tiles.LOOK_STAIRS


def test_wall_above_a_floor_shows_its_front():
    assert tiles.tile_look(GRID, 2, 1) == tiles.LOOK_WALL_FRONT
    assert tiles.tile_look(GRID, 3, 1) == tiles.LOOK_WALL_FRONT


def test_walls_beside_and_below_a_floor_show_their_top():
    assert tiles.tile_look(GRID, 1, 2) == tiles.LOOK_WALL_TOP    # left of the floor
    assert tiles.tile_look(GRID, 2, 3) == tiles.LOOK_WALL_TOP    # below the floor
    assert tiles.tile_look(GRID, 1, 1) == tiles.LOOK_WALL_TOP    # diagonal corner


def test_rock_far_from_any_floor_is_not_drawn():
    assert tiles.tile_look(GRID, 0, 0) == tiles.LOOK_VOID
    assert tiles.tile_look(GRID, 5, 4) == tiles.LOOK_VOID


def test_shadow_falls_on_open_cells_below_a_wall():
    assert tiles.in_wall_shadow(GRID, 2, 2)
    assert not tiles.in_wall_shadow(GRID, 2, 1)   # a wall itself has no shadow


def test_every_room_on_a_real_floor_has_a_front_wall_above_it():
    floor = generate_floor(1, seed=3)
    for x, y, w, h in floor.rooms:
        assert tiles.tile_look(floor.grid, x, y - 1) == tiles.LOOK_WALL_FRONT
