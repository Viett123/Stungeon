"""Floor generation (owner: A). No drawing here.

A floor is a grid of walls with up to MAX_ROOMS rooms carved out, joined left to right by
L-shaped corridors, so every room is reachable. Every room has a KIND:

  start     the left-most room, where the player appears. Nothing else is placed here.
  boss      the right-most room: the stairs, guarded by the floor's boss.
  treasure  a mini-boss guarding extra chests.
  trap      spikes on the floor (the middle row and column stay free, so there is a safe way through).
  den       a room crowded with monsters.
  normal    everything else.

Some rooms have their four corners cut off, so not every room is a plain rectangle.
Same floor_number + seed + modifiers = the same floor every time.
"""
import random
from dataclasses import dataclass, field

from systems.enemies import elite_rules, floor_spawns

FLOOR = 0
WALL = 1
STAIRS = 2

# PLACEHOLDER numbers. TODO(A): choose the real floor size, room numbers and room kinds.
# The floor is bigger than the screen (about 27 x 14 tiles fit), so the camera scrolls.
WIDTH, HEIGHT = 44, 26
MAX_ROOMS = 9
ROOM_W = (5, 9)   # smallest and biggest room width, in tiles
ROOM_H = (4, 6)
CUT_CORNER_CHANCE = 0.4     # share of rooms that get their corners cut off
DEN_ENEMIES = 3             # monsters that are put into the den first
TREASURE_CHESTS = 2         # extra chests in the treasure room
SPECIAL_KINDS = ["treasure", "trap", "den"]   # handed out to the middle rooms, in this order


@dataclass
class Floor:
    number: int
    width: int
    height: int
    grid: list            # grid[y][x], one of FLOOR / WALL / STAIRS
    start: tuple          # (x, y) where the player appears
    stairs: tuple         # (x, y)
    # [{"id": enemy id, "pos": (x, y), "boss": bool, "elite": bool, "guard": bool}]
    # guard = stands still (the boss and the mini-boss); elite = stronger and better loot
    enemies: list = field(default_factory=list)
    chests: list = field(default_factory=list)    # [{"pos": (x, y), "opened": bool}]
    rooms: list = field(default_factory=list)     # [(x, y, w, h)]
    room_kinds: list = field(default_factory=list)   # one kind per room, same order as rooms
    traps: set = field(default_factory=set)       # {(x, y)} floor cells with spikes

    def is_walkable(self, x, y):
        return 0 <= x < self.width and 0 <= y < self.height and self.grid[y][x] != WALL

    def room_at(self, x, y):
        """The number of the room this cell is in, or None in a corridor."""
        for index, (rx, ry, rw, rh) in enumerate(self.rooms):
            if rx <= x < rx + rw and ry <= y < ry + rh:
                return index
        return None


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


def _carve_room(grid, room, cut_corners):
    x, y, w, h = room
    corners = {(x, y), (x + w - 1, y), (x, y + h - 1), (x + w - 1, y + h - 1)} if cut_corners else set()
    for row in range(y, y + h):
        for col in range(x, x + w):
            if (col, row) not in corners:
                grid[row][col] = FLOOR


def _carve_corridor(grid, a, b, rng):
    (x1, y1), (x2, y2) = a, b
    corner = (x2, y1) if rng.random() < 0.5 else (x1, y2)
    for (sx, sy), (ex, ey) in ((a, corner), (corner, b)):
        for x in range(min(sx, ex), max(sx, ex) + 1):
            for y in range(min(sy, ey), max(sy, ey) + 1):
                grid[y][x] = FLOOR


def _room_kinds(count, rng):
    """One kind per room: start, boss, and the special kinds spread over the middle rooms."""
    kinds = ["normal"] * count
    kinds[0], kinds[-1] = "start", "boss"
    middle = list(range(1, count - 1))
    rng.shuffle(middle)
    for index, kind in zip(middle, SPECIAL_KINDS):
        kinds[index] = kind
    return kinds


def _open_cells(grid, room):
    """The floor cells of a room (a room with cut corners has four fewer)."""
    x, y, w, h = room
    return [(col, row) for row in range(y, y + h) for col in range(x, x + w) if grid[row][col] == FLOOR]


def _spikes(grid, room):
    """Spikes in a checker pattern, leaving the room's middle row and column free."""
    center_x, center_y = _center(room)
    return {(x, y) for x, y in _open_cells(grid, room)
            if (x + y) % 2 == 0 and x != center_x and y != center_y}


def _take(rng, cells, count):
    """Pick up to `count` cells at random and remove them from the list."""
    picked = rng.sample(cells, min(count, len(cells)))
    for cell in picked:
        cells.remove(cell)
    return picked


def generate_floor(floor_number, seed, demo=False, modifiers=None) -> Floor:
    """modifiers: changes chosen between floors, e.g. {"elite_bonus": 0.2, "extra_chests": 2, "extra_enemies": 3}."""
    modifiers = modifiers or {}
    rng = random.Random(f"{seed}-{floor_number}")   # only use this rng, so floors repeat exactly
    grid = [[WALL] * WIDTH for _ in range(HEIGHT)]
    rooms = _place_rooms(rng)
    kinds = _room_kinds(len(rooms), rng)
    for room in rooms:
        _carve_room(grid, room, cut_corners=rng.random() < CUT_CORNER_CHANCE)
    for a, b in zip(rooms, rooms[1:]):
        _carve_corridor(grid, _center(a), _center(b), rng)

    start = _center(rooms[0])
    stairs = _center(rooms[-1])
    grid[stairs[1]][stairs[0]] = STAIRS

    traps = set()
    for room, kind in zip(rooms, kinds):
        if kind == "trap":
            traps |= _spikes(grid, room)

    # Free cells per room kind. Nothing is ever placed in the start room or on spikes.
    cells = {kind: [] for kind in ["normal", "boss", "treasure", "trap", "den"]}
    for room, kind in zip(rooms, kinds):
        if kind != "start":
            cells[kind] += [c for c in _open_cells(grid, room) if c not in traps]

    spawns = floor_spawns(floor_number)
    enemies = [{"id": spawns["boss"], "pos": stairs, "boss": True, "elite": False, "guard": True}]
    treasure_rooms = [room for room, kind in zip(rooms, kinds) if kind == "treasure"]
    if spawns.get("miniboss") and treasure_rooms:
        guard_pos = _center(treasure_rooms[0])
        cells["treasure"].remove(guard_pos)
        enemies.append({"id": spawns["miniboss"], "pos": guard_pos, "boss": False, "elite": False, "guard": True})

    count = max(1, spawns["count"] // 2) if demo else spawns["count"] + modifiers.get("extra_enemies", 0)
    den_spots = _take(rng, cells["den"], min(DEN_ENEMIES, count))
    anywhere = cells["normal"] + cells["boss"] + cells["trap"] + cells["den"]
    spots = den_spots + _take(rng, anywhere, count - len(den_spots))
    elite_chance = elite_rules()["chance"] + modifiers.get("elite_bonus", 0)
    for pos in spots:
        enemies.append({"id": rng.choice(spawns["pool"]), "pos": pos, "boss": False,
                        "elite": rng.random() < elite_chance, "guard": False})

    # Chests: some in the treasure room, the rest on cells that are still free anywhere.
    chest_spots = _take(rng, cells["treasure"], TREASURE_CHESTS if treasure_rooms else 0)
    anywhere = [c for c in anywhere if c not in spots]
    chest_spots += _take(rng, anywhere, spawns.get("chests", 0) + modifiers.get("extra_chests", 0))
    chests = [{"pos": pos, "opened": False} for pos in chest_spots]

    return Floor(floor_number, WIDTH, HEIGHT, grid, start, stairs, enemies, chests, rooms, kinds, traps)
