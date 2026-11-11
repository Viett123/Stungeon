"""How a monster on the map decides its next step towards the player (owner: A). No pygame here.

The path itself is the job of ai/pathfinding.py (owner C). While that is still a
placeholder that finds no path, the monster uses a simple fallback: step straight
towards the player. That is enough for a chase that starts 2 tiles away, but it can
get stuck behind a corner. A real A* fixes that without any change here.
"""
from ai.pathfinding import astar


def distance(a, b):
    """How many steps apart two tiles are, counting diagonal steps as one."""
    return max(abs(a[0] - b[0]), abs(a[1] - b[1]))


def _straight_steps(start, goal):
    """The one or two neighbour tiles that bring start closer to goal, the bigger gap first."""
    dx = (goal[0] > start[0]) - (goal[0] < start[0])     # -1, 0 or 1
    dy = (goal[1] > start[1]) - (goal[1] < start[1])
    across, down = (start[0] + dx, start[1]), (start[0], start[1] + dy)
    steps = [across, down] if abs(goal[0] - start[0]) >= abs(goal[1] - start[1]) else [down, across]
    return [step for step in steps if step != start]


def next_step(floor, start, goal, blocked):
    """The tile a monster at `start` should step on to reach `goal`, or None if it can't move.

    blocked is a set of tiles it may not enter (other monsters, closed chests).
    The result can be `goal` itself: then the monster has reached the player.
    """
    path = astar(floor.grid, start, goal)        # owner C; [] while it is a placeholder
    if path and path[0] == start:
        path = path[1:]                          # accept paths that list the start tile first
    options = path[:1] or _straight_steps(start, goal)
    for step in options:
        if floor.is_walkable(*step) and step not in blocked:
            return step
    return None
