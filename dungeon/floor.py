"""Floor generation (owner: A). No drawing here.

A floor is a grid of walls with up to MAX_ROOMS rooms carved out, joined left to right by
L-shaped corridors, so every room is reachable. The player starts in the left-most
room; the stairs are in the right-most room, guarded by the floor's boss.
Same floor_number + seed = the same floor every time.
"""
import random
from dataclasses import dataclass, field

from systems.enemies import floor_spawns

FLOOR = 0
WALL = 1
STAIRS = 2

# PLACEHOLDER sizes. TODO(A): choose the real floor size and room numbers.
# The floor is bigger than the screen (about 27 x 14 tiles fit), so the camera scrolls.
WIDTH, HEIGHT = 44, 26
MAX_ROOMS = 9
ROOM_W = (5, 9)   # smallest and biggest room width, in tiles
ROOM_H = (4, 6)


@dataclass
class Floor:
    number: int
    width: int
    height: int
    grid: list            # grid[y][x], one of FLOOR / WALL / STAIRS
    start: tuple          # (x, y) where the player appears
    stairs: tuple         # (x, y)
    enemies: list = field(default_factory=list)   # [{"id": enemy id, "pos": (x, y), "boss": bool}]
    rooms: list = field(default_factory=list)     # [(x, y, w, h)]

    def is_walkable(self, x, y):
        return 0 <= x < self.width and 0 <= y < self.height and self.grid[y][x] != WALL


def _overlaps(a, b):
    ax, ay, aw, ah = a
    bx, by, bw, bh = b
    # "<=" instead of "<" also rejects rooms that touch, so there is a wall between rooms
    return ax <= bx + bw and bx <= ax + aw and ay <= by + bh and by <= ay + ah


def _center(room):
    x, y, w, h = room
    return (x + w // 2, y + h // 2)


def _place_rooms(rng):
    rooms = []
    for _ in range(400):
        if len(rooms) == MAX_ROOMS:
            break
        w, h = rng.randint(*ROOM_W), rng.randint(*ROOM_H)
        room = (rng.randint(1, WIDTH - w - 1), rng.randint(1, HEIGHT - h - 1), w, h)
        if not any(_overlaps(room, other) for other in rooms):
            rooms.append(room)
    if len(rooms) < 2:   # almost never happens; fall back to two fixed rooms
        rooms = [(1, 1, 6, 5), (WIDTH - 8, HEIGHT - 7, 6, 5)]
    return sorted(rooms)   # left to right


def _carve_corridor(grid, a, b, rng):
    (x1, y1), (x2, y2) = a, b
    corner = (x2, y1) if rng.random() < 0.5 else (x1, y2)
    for (sx, sy), (ex, ey) in ((a, corner), (corner, b)):
        for x in range(min(sx, ex), max(sx, ex) + 1):
            for y in range(min(sy, ey), max(sy, ey) + 1):
                grid[y][x] = FLOOR


def generate_floor(floor_number, seed, demo=False) -> Floor:
    rng = random.Random(f"{seed}-{floor_number}")   # only use this rng, so floors repeat exactly
    grid = [[WALL] * WIDTH for _ in range(HEIGHT)]
    rooms = _place_rooms(rng)
    for x, y, w, h in rooms:
        for row in range(y, y + h):
            for col in range(x, x + w):
                grid[row][col] = FLOOR
    for a, b in zip(rooms, rooms[1:]):
        _carve_corridor(grid, _center(a), _center(b), rng)

    start = _center(rooms[0])
    stairs = _center(rooms[-1])
    grid[stairs[1]][stairs[0]] = STAIRS

    spawns = floor_spawns(floor_number)
    enemies = [{"id": spawns["boss"], "pos": stairs, "boss": True}]
    # Normal enemies go in any room except the first, never on the stairs.
    free = [(x, y) for rx, ry, rw, rh in rooms[1:] for y in range(ry, ry + rh) for x in range(rx, rx + rw)
            if (x, y) != stairs]
    count = max(1, spawns["count"] // 2) if demo else spawns["count"]
    for pos in rng.sample(free, min(count, len(free))):
        enemies.append({"id": rng.choice(spawns["pool"]), "pos": pos, "boss": False})

    return Floor(floor_number, WIDTH, HEIGHT, grid, start, stairs, enemies, rooms)
