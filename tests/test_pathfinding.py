"""Tests for the A* route finder (ai/pathfinding.py) and the monster step that uses it (dungeon/chase.py).

Plain logic: no pygame needed.
"""
import random
from collections import deque

from ai.pathfinding import astar
from dungeon import chase


def test_straight_corridor():
    grid = [[0, 0, 0, 0, 0]]
    assert astar(grid, (0, 0), (4, 0)) == [(0, 0), (1, 0), (2, 0), (3, 0), (4, 0)]


def test_path_around_a_wall():
    # 1 is a wall. It fills the top two rows of the middle column, so the only way is along the bottom row.
    grid = [
        [0, 1, 0],
        [0, 1, 0],
        [0, 0, 0],
    ]
    assert astar(grid, (0, 0), (2, 0)) == [(0, 0), (0, 1), (0, 2), (1, 2), (2, 2), (2, 1), (2, 0)]


def test_no_path_when_the_goal_is_walled_in():
    grid = [
        [0, 0, 0],
        [0, 0, 1],
        [0, 1, 0],
    ]
    assert astar(grid, (0, 0), (2, 2)) == []


def test_start_equals_goal_gives_just_that_tile():
    grid = [[0, 0], [0, 0]]
    assert astar(grid, (1, 1), (1, 1)) == [(1, 1)]


def test_a_wall_or_a_tile_off_the_map_has_no_route():
    grid = [[0, 1], [0, 0]]
    assert astar(grid, (1, 0), (0, 0)) == []     # the start is a wall
    assert astar(grid, (0, 0), (1, 0)) == []     # the goal is a wall
    assert astar(grid, (0, 0), (9, 9)) == []     # the goal is off the map


def _shortest_by_breadth_first(grid, start, goal):
    """Steps of the shortest route, or None. A simple, slow method to check A* against."""
    height, width = len(grid), len(grid[0])
    seen = {start: 0}
    queue = deque([start])
    while queue:
        tile = queue.popleft()
        if tile == goal:
            return seen[tile]
        x, y = tile
        for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if 0 <= nx < width and 0 <= ny < height and grid[ny][nx] != 1 and (nx, ny) not in seen:
                seen[(nx, ny)] = seen[tile] + 1
                queue.append((nx, ny))
    return None


def test_routes_are_as_short_as_breadth_first_search_and_step_one_tile_at_a_time():
    rng = random.Random(3)
    for _ in range(300):
        width, height = rng.randint(1, 10), rng.randint(1, 10)
        grid = [[1 if rng.random() < 0.3 else 0 for _ in range(width)] for _ in range(height)]
        start = (rng.randrange(width), rng.randrange(height))
        goal = (rng.randrange(width), rng.randrange(height))
        grid[start[1]][start[0]] = grid[goal[1]][goal[0]] = 0

        route = astar(grid, start, goal)
        shortest = _shortest_by_breadth_first(grid, start, goal)
        if shortest is None:
            assert route == []
            continue
        assert len(route) - 1 == shortest
        assert route[0] == start and route[-1] == goal
        for a, b in zip(route, route[1:]):
            assert abs(a[0] - b[0]) + abs(a[1] - b[1]) == 1     # up, down, left or right only
            assert grid[b[1]][b[0]] != 1


# --- the monster's step (dungeon/chase.py) -----------------------------------

class GridFloor:
    """Just enough of a floor for the chase code: the grid and is_walkable."""

    def __init__(self, rows):
        self.grid = rows

    def is_walkable(self, x, y):
        return 0 <= y < len(self.grid) and 0 <= x < len(self.grid[0]) and self.grid[y][x] != 1


# The wall stands between the monster at (1, 1) and the player at (3, 1). The way round is down.
WALL_IN_THE_WAY = [
    [0, 0, 1, 0, 0],
    [0, 0, 1, 0, 0],
    [0, 0, 0, 0, 0],
]


def test_a_monster_with_astar_walks_round_the_wall():
    assert chase.next_step(GridFloor(WALL_IN_THE_WAY), (1, 1), (3, 1), set()) == (1, 2)


def test_without_astar_the_monster_is_stuck_behind_the_wall():
    assert chase.next_step(GridFloor(WALL_IN_THE_WAY), (1, 1), (3, 1), set(), use_astar=False) is None
