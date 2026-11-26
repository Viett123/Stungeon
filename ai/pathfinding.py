"""A* pathfinding for enemies on the map (owner: C). No pygame here.

PLACEHOLDER: always returns "no path".
TODO(B): real A* on grid[y][x] with a Manhattan-distance heuristic.
"""

import heapq


def manhattan(a, b) -> int:
    """How many up/down/left/right steps it takes to go from tile a to tile b, ignoring walls."""
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def astar(grid, start, goal) -> list[tuple[int, int]]:
    """Return the (x, y) tiles from start to goal, shortest first, with start as the first tile.

    Returns [] when there is no route, or when start or goal is a wall or outside the map.
    When start and goal are the same tile, the route is just [start].
    """
    if not grid or not grid[0]:
        return []
    height, width = len(grid), len(grid[0])

    def walkable(tile):
        x, y = tile
        return 0 <= x < width and 0 <= y < height and grid[y][x] != 1

    start, goal = tuple(start), tuple(goal)
    if not walkable(start) or not walkable(goal):
        return []
    if start == goal:
        return [start]

    # The "to look at next" list. Each entry is (guess of the total steps, steps so far, tile).
    # heapq always hands back the entry with the smallest guess first.
    to_visit = [(manhattan(start, goal), 0, start)]
    # came_from[tile] is the tile we stepped from to reach it. It is how we find the way back.
    came_from = {}
    # best_steps[tile] is the fewest steps found so far to reach that tile.
    best_steps = {start: 0}

    while to_visit:
        _, steps, current = heapq.heappop(to_visit)
        if current == goal:
            return _way_back(came_from, current)
        if steps > best_steps[current]:
            continue                      # an old entry: a shorter route to this tile was already found

        x, y = current
        for next_tile in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if not walkable(next_tile):
                continue
            new_steps = steps + 1
            if new_steps < best_steps.get(next_tile, float("inf")):
                best_steps[next_tile] = new_steps
                came_from[next_tile] = current
                guess = new_steps + manhattan(next_tile, goal)
                heapq.heappush(to_visit, (guess, new_steps, next_tile))

    return []                             # nothing left to look at: the goal cannot be reached


def _way_back(came_from, end) -> list[tuple[int, int]]:
    """Follow came_from from the goal back to the start, then turn the list around."""
    route = [end]
    while end in came_from:
        end = came_from[end]
        route.append(end)
    route.reverse()
    return route
