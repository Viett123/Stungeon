from dungeon.floor import generate_floor


def test_start_and_stairs_are_walkable():
    floor = generate_floor(1, seed=123)
    assert floor.is_walkable(*floor.start)
    assert floor.is_walkable(*floor.stairs)


def test_grid_is_y_then_x():
    floor = generate_floor(1, seed=123)
    assert len(floor.grid) == floor.height
    assert len(floor.grid[0]) == floor.width


def test_same_seed_same_floor():
    assert generate_floor(2, seed=7).grid == generate_floor(2, seed=7).grid
