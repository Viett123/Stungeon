"""The look of every screen: colours and the stone-and-metal frame (owner: B).

Change a colour here and it changes everywhere. Frames are drawn in code with plain
rectangles, so they need no art files.
"""
import pygame

from core import assets

# Colours (R, G, B): dark, muted and earthy.
BACKGROUND = (16, 14, 14)
OUTLINE = (10, 9, 9)
STONE = (58, 54, 56)
STONE_LIGHT = (92, 86, 86)
METAL = (150, 128, 88)
METAL_DARK = (88, 73, 52)
PANEL_FILL = (27, 24, 27)
SLOT_FILL = (38, 34, 36)

TEXT = (226, 218, 200)
TEXT_DIM = (150, 142, 130)
GOLD = (218, 182, 100)
GOLD_BRIGHT = (255, 232, 160)   # selected things pulse between GOLD and this
GOOD = (124, 186, 110)
BAD = (204, 84, 72)
DISABLED = (96, 90, 88)

HP = (170, 50, 44)
HP_BACK = (56, 22, 22)
RESOURCE = (62, 104, 178)
RESOURCE_BACK = (22, 34, 60)

# Placeholder colour for a move's icon, by tier.
TIER_COLORS = {
    "basic": (112, 100, 84),
    "skill": (84, 122, 86),
    "power": (150, 76, 62),
    "ultimate": (116, 80, 150),
    "utility": (70, 118, 124),
}

FRAME_ART_SCALE = 2   # the frame art is drawn 2 times its size
FRAME_CORNER = 14     # size of a corner piece on screen: 7 art pixels x 2
FRAME_PAD = 14   # how far the inside of a frame is from its outer edge


def inner(rect):
    """The area inside a frame where content may be drawn."""
    return pygame.Rect(rect).inflate(-2 * FRAME_PAD, -2 * FRAME_PAD)


_borders = {}   # (style, width, height) -> a finished border picture, made once per panel size

# Which floor look the frames follow: "" (stone), "jungle" or "desert", the same folder names as
# data/themes.json. Each look has its own ui_frame.png in that folder; the dungeon sets it.
_style = ""


def set_frame_style(style):
    """Use the frame of this floor look from now on (the folder name from data/themes.json)."""
    global _style
    _style = style or ""


def frame_style():
    return _style


def frame_art(style):
    """The frame picture of a floor look, e.g. assets/sprites/jungle/ui_frame.png.

    A look without its own frame uses assets/sprites/ui_frame.png. None if there is no frame art at all.
    """
    if style:
        art = assets.load_sprite(f"{style}/ui_frame", FRAME_ART_SCALE)
        if art is not None:
            return art
    return assets.load_sprite("ui_frame", FRAME_ART_SCALE)


def _art_border(size, style=None):
    """The border of a panel of this size, built from the floor look's ui_frame.png. None without that art.

    style: the floor look to use; None = the one set by set_frame_style.
    The art is one small square frame. It is cut into 9 pieces: the 4 corners are used
    as they are, and the 4 edge pieces are repeated to fill the sides ("9-slice").
    """
    style = _style if style is None else style
    key = (style, size[0], size[1])
    if key in _borders:
        return _borders[key]
    art = frame_art(style)
    if art is None or size[0] < 2 * FRAME_CORNER or size[1] < 2 * FRAME_CORNER:
        _borders[key] = None
        return None
    width, height = size
    side = art.get_width()
    corner, middle = FRAME_CORNER, side - 2 * FRAME_CORNER     # middle = length of one edge piece
    border = pygame.Surface(size, pygame.SRCALPHA)
    for x in range(corner, width - corner, middle):            # top and bottom edges
        length = min(middle, width - corner - x)
        border.blit(art, (x, 0), (corner, 0, length, corner))
        border.blit(art, (x, height - corner), (corner, side - corner, length, corner))
    for y in range(corner, height - corner, middle):           # left and right edges
        length = min(middle, height - corner - y)
        border.blit(art, (0, y), (0, corner, corner, length))
        border.blit(art, (width - corner, y), (side - corner, corner, corner, length))
    for x, source_x in ((0, 0), (width - corner, side - corner)):          # the four corners
        for y, source_y in ((0, 0), (height - corner, side - corner)):
            border.blit(art, (x, y), (source_x, source_y, corner, corner))
    _borders[key] = border
    return border


def draw_frame(surface, rect, highlight=False, fill=PANEL_FILL, style=None):
    """Draw a framed panel: dark outline, stone border, metal line, dark inside, metal corner studs.

    highlight=True uses bright metal for the line (for the selected card or slot).
    style: which floor look's frame to use ("", "jungle", "desert"); None = the current one.
    Returns the inner rect for content.
    """
    rect = pygame.Rect(rect)
    border = _art_border(rect.size, style)
    if border is not None:
        pygame.draw.rect(surface, fill, rect.inflate(-10, -10))
        surface.blit(border, rect)
        if highlight:
            from ui import anim              # imported here because ui/anim.py imports this file
            pygame.draw.rect(surface, anim.glow_gold(), rect.inflate(-24, -24), width=3)
        return inner(rect)
    # No frame art: draw the frame with plain rectangles.
    pygame.draw.rect(surface, OUTLINE, rect)
    pygame.draw.rect(surface, STONE, rect.inflate(-4, -4))
    pygame.draw.rect(surface, STONE_LIGHT, rect.inflate(-4, -4), width=2)
    line = METAL_DARK
    if highlight:
        from ui import anim              # imported here because ui/anim.py imports this file
        line = anim.glow_gold()
    pygame.draw.rect(surface, line, rect.inflate(-14, -14))
    pygame.draw.rect(surface, fill, rect.inflate(-18, -18))
    for corner in ("topleft", "topright", "bottomleft", "bottomright"):
        stud = pygame.Rect(0, 0, 10, 10)
        setattr(stud, corner, getattr(rect, corner))
        pygame.draw.rect(surface, OUTLINE, stud)
        pygame.draw.rect(surface, METAL, stud.inflate(-4, -4))
    return inner(rect)
