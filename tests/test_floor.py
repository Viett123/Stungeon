from collections import deque

import pytest

from dungeon.floor import STAIRS, WALL, generate_floor

SEEDS = range(30)


def reachable(floor):
    """Every tile you can walk to from the start (breadth-first search)."""
    seen, todo = {floor.start}, deque([floor.start])
    while todo:
        x, y = todo.popleft()
        for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if (nx, ny) not in seen and floor.is_walkable(nx, ny):
                seen.add((nx, ny))
                todo.append((nx, ny))
    return seen


@pytest.mark.parametrize("seed", SEEDS)
@pytest.mark.parametrize("number", [1, 2, 3])
def test_every_floor_tile_and_enemy_is_reachable(number, seed):
    floor = generate_floor(number, seed)
    walkable = {(x, y) for y in range(floor.height) for x in range(floor.width) if floor.grid[y][x] != WALL}
    assert reachable(floor) == walkable
    assert all(e["pos"] in walkable for e in floor.enemies)


def test_boss_guards_the_stairs_and_nobody_stands_on_the_start():
    floor = generate_floor(1, seed=5)
    bosses = [e for e in floor.enemies if e["boss"]]
    assert len(bosses) == 1 and bosses[0]["pos"] == floor.stairs
    assert floor.grid[floor.stairs[1]][floor.stairs[0]] == STAIRS
    assert all(e["pos"] != floor.start for e in floor.enemies)
    assert len({e["pos"] for e in floor.enemies}) == len(floor.enemies)   # no two on one tile


def test_grid_is_y_then_x_and_has_wall_border():
    floor = generate_floor(1, seed=123)
    assert len(floor.grid) == floor.height and len(floor.grid[0]) == floor.width
    assert all(cell == WALL for cell in floor.grid[0] + floor.grid[-1])


def test_same_seed_same_floor():
    a, b = generate_floor(2, seed=7), generate_floor(2, seed=7)
    assert a.grid == b.grid and a.enemies == b.enemies


def test_demo_floors_have_fewer_enemies():
    assert len(generate_floor(3, 1, demo=True).enemies) < len(generate_floor(3, 1).enemies)
