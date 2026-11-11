"""Fog of war: which cells the player has seen (owner: A). No pygame here.

A floor starts hidden. Standing in a room shows that whole room and the walls around
it. Standing in a corridor shows only the few cells around the player. Cells that were
seen once stay visible.
"""

ROOM_MARGIN = 2        # cells shown around a room: its walls, and the cap row above the back wall
CORRIDOR_RADIUS = 2    # cells shown around the player in a corridor


def cells_in_view(floor, pos):
    """The set of (x, y) cells the player can see from pos."""
    x, y = pos
    room = floor.room_at(x, y)
    if room is not None:
        room_x, room_y, width, height = floor.rooms[room]
        left, top = room_x - ROOM_MARGIN, room_y - ROOM_MARGIN
        right, bottom = room_x + width + ROOM_MARGIN, room_y + height + ROOM_MARGIN
    else:
        left, top = x - CORRIDOR_RADIUS, y - CORRIDOR_RADIUS
        right, bottom = x + CORRIDOR_RADIUS + 1, y + CORRIDOR_RADIUS + 1
    return {(cell_x, cell_y)
            for cell_y in range(max(0, top), min(floor.height, bottom))
            for cell_x in range(max(0, left), min(floor.width, right))}
