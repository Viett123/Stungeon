"""Small drawing helpers shared by all screens (owner: B)."""
import pygame

from ui import theme

# Characters the default font cannot draw (they would show as boxes) -> what to draw instead.
# The question bank uses "→" in 162 plural questions.
_REPLACEMENTS = {"→": "->"}


def drawable(string):
    for char, plain in _REPLACEMENTS.items():
        string = string.replace(char, plain)
    return string


def text(surface, font, string, color, pos, anchor="topleft"):
    """Draw one line of text. anchor says which point of the text sits at pos. Returns its rect."""
    image = font.render(drawable(string), True, color)
    rect = image.get_rect(**{anchor: pos})
    surface.blit(image, rect)
    return rect


def wrap(font, string, width):
    """Split a string into lines that fit inside `width` pixels."""
    lines, line = [], ""
    for word in drawable(string).split():
        test = f"{line} {word}".strip()
        if font.size(test)[0] <= width or not line:
            line = test
        else:
            lines.append(line)
            line = word
    if line:
        lines.append(line)
    return lines


def wrapped(surface, font, string, color, topleft, width, line_gap=6):
    """Draw text over several lines. Returns the y just below the last line."""
    x, y = topleft
    for line in wrap(font, string, width):
        text(surface, font, line, color, (x, y))
        y += font.get_height() + line_gap
    return y


BUBBLE_PAD = 10          # space between the edge of a talk bubble and its text
BUBBLE_TAIL = 12         # how far the little point under a talk bubble sticks out
BUBBLE_FILL = (238, 230, 210)
BUBBLE_TEXT = (40, 32, 30)


def speech_bubble(font, string, max_width):
    """A talk bubble picture, like in a comic: light box, dark text, a point at the bottom middle.

    Make it once and blit it every frame with its midbottom on the speaker's head.
    """
    lines = wrap(font, string, max_width - 2 * BUBBLE_PAD)
    line_h = font.get_height()
    width = max(font.size(line)[0] for line in lines) + 2 * BUBBLE_PAD
    height = len(lines) * line_h + 2 * BUBBLE_PAD
    bubble = pygame.Surface((width + 4, height + BUBBLE_TAIL + 4), pygame.SRCALPHA)
    box = pygame.Rect(2, 2, width, height)
    middle = box.centerx
    tail = [(middle - BUBBLE_TAIL, box.bottom - 2), (middle + BUBBLE_TAIL // 2, box.bottom - 2), (middle, box.bottom + BUBBLE_TAIL)]
    pygame.draw.polygon(bubble, theme.OUTLINE, [(x, y + 2) for x, y in tail])        # dark edge of the point
    pygame.draw.rect(bubble, theme.OUTLINE, box.inflate(4, 4), border_radius=8)      # dark edge of the box
    pygame.draw.rect(bubble, BUBBLE_FILL, box, border_radius=6)
    pygame.draw.polygon(bubble, BUBBLE_FILL, tail)
    for i, line in enumerate(lines):
        image = font.render(line, True, BUBBLE_TEXT)
        bubble.blit(image, image.get_rect(midtop=(middle, box.y + BUBBLE_PAD + i * line_h)))
    return bubble


_dim_cover = None   # made once, the first time dim() is used


def dim(surface):
    """Darken everything drawn so far, so a menu on top of the game is easy to read."""
    global _dim_cover
    if _dim_cover is None or _dim_cover.get_size() != surface.get_size():
        _dim_cover = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        _dim_cover.fill((0, 0, 0, 170))
    surface.blit(_dim_cover, (0, 0))


def bar(surface, rect, value, maximum, color, back, label="", font=None, trail=None):
    """A bar that shows value out of maximum (HP, resource), with an optional label on it.

    trail: a value a little behind `value` (see ui/anim.py Trail). The part between
    the two is drawn pale, so a sudden loss stays visible for a moment.
    """
    rect = pygame.Rect(rect)
    pygame.draw.rect(surface, theme.OUTLINE, rect)
    inside = rect.inflate(-4, -4)
    pygame.draw.rect(surface, back, inside)
    if trail is not None and maximum > 0 and trail > value:
        lost = inside.copy()
        lost.width = round(inside.width * min(trail, maximum) / maximum)
        pale = tuple(min(255, c + 90) for c in color)      # a lighter shade of the bar's own colour
        pygame.draw.rect(surface, pale, lost)
    if maximum > 0 and value > 0:
        filled = inside.copy()
        filled.width = max(1, round(inside.width * min(value, maximum) / maximum))
        pygame.draw.rect(surface, color, filled)
        # A lighter line along the top makes the bar look slightly rounded.
        lighter = tuple(min(255, c + 40) for c in color)
        pygame.draw.line(surface, lighter, filled.topleft, (filled.right - 1, filled.top))
    if label and font:
        # A dark copy one pixel lower keeps the label readable on any bar colour.
        text(surface, font, label, theme.OUTLINE, (rect.centerx + 1, rect.centery + 1), "center")
        text(surface, font, label, theme.TEXT, rect.center, "center")
